HW5 — My LangGraph helpdesk
CSS-4007 — Artificial Intelligence
Part 1 — How the graph works
My graph and state
I created a LangGraph helpdesk without a language model.

Original graph: <img width="762" height="490" alt="image" src="https://github.com/user-attachments/assets/50a5c7a5-9f20-4805-ad2c-f83f95961b16" />



START → read_request
- wifi → wifi_help → END
- password → password_help → END
- other → other_help → END
The graph uses three state fields:
- message: the user's message.
- category: the detected problem type.
- reply: the helpdesk response.
The read_request node checks the message and updates category. The help nodes produce a reply. A node returns state updates. A conditional edge selects the next node. The next node receives the current state, including updates from earlier nodes. START begins execution, END finishes it, and compiling makes the graph runnable.
Predictions before running
Message	Predicted route	Actual route	What I learned
I cannot connect to Wi-Fi.	read_request → wifi_help	read_request → wifi_help	Wi-Fi is detected.
I forgot my PASSWORD.	read_request → password_help	read_request → password_help	Matching is case-insensitive.
My laptop screen is broken.	read_request → other_help	read_request → other_help	Unsupported problems use the other route.
My Wi-Fi password does not work.	read_request → wifi_help	read_request → wifi_help	The original graph checks Wi-Fi first.


I saved the first execution traces in outputs/part1_traces.json. I also saved the exact supplied scenarios in outputs/scenarios/S01.json to S05.json.
My change to the graph
I added clarify_problem when the same message mentions both Wi-Fi and password.

Updated graph:<img width="1100" height="525" alt="image" src="https://github.com/user-attachments/assets/8ef642a2-1b33-4ced-951c-db2ffa000f8a" />



START → read_request
- wifi → wifi_help → END
- password → password_help → END
- other → other_help → END
- clarify → clarify_problem → END
Example: “My Wi-Fi password does not work.”

Before the change: read_request → wifi_help.

After the change: read_request → clarify_problem.

The final category is clarify, and the graph asks which problem to solve first. LangGraph handles execution and state transitions. My Python functions decide the category and reply. No AI model is used in Part 1.
Part 2 — Model and tools
Model and provider
I used OpenAI gpt-4o-mini through LangChain and LangGraph. The model chooses the tools. LangGraph runs the nodes.
Tools
I created three tools:
1. find_instructions — reads Wi-Fi and password instructions from data/helpdesk.json.
2. check_service_status — reads simulated service status from data/service_status.json.
3. prepare_ticket — creates a local JSON ticket draft using data/ticket_template.json.
I tested the tools directly before testing the agent. A ticket draft is saved locally and is not submitted to a real service.
Model and tool loop
START → assistant → tools → assistant → END

If the assistant requests tools, LangGraph's tools_condition routes the graph to ToolNode. Tool results are added to messages, then the assistant responds or asks for another tool. Part 1 follows fixed Python rules; Part 2 lets the model select tools.
Answers to the four questions
1. The graph uses tools_condition to check for tool calls in the last AI message. If there is no tool call, the graph ends.
2. The AI model requests a tool. LangGraph's ToolNode executes it.
3. The tool output is added to the messages state, so the model can use it in its next response.
4. Part 1 uses rule-based routing. Part 2 uses model-driven tool selection.
Loop limit
I set recursion_limit=15 when running the Part 2 scenarios. It limits graph execution and helps prevent an endless tool loop. I did not implement a separate MAX_STEPS=5 constant.
Demonstrations
I ran the exact Part 2 inputs from data/scenarios.json and saved their logs in outputs/scenarios/.
- S06: The assistant called find_instructions, check_service_status, and prepare_ticket. I later corrected the saved ticket steps so the draft would not contain actions invented from the instructions. The updated S06 log records Enabled Wi-Fi; Forgot the saved network; Connection still fails.
- S07: Wi-Fi had an outage. The assistant did not prepare the conditional ticket.
- S08: The status source was unavailable. The assistant asked what to do next instead of preparing a conditional ticket.
- S09: The assistant first asked for the problem and tried steps, then created a draft after the next user message.
- S14: The account-recovery service had an outage. The assistant did not invent a repair time.
The ticket function creates a short unique ID, records the category and service status, and saves the draft in outputs/tickets/. This folder is ignored by Git. The demonstration log still contains the ticket tool output. The current Part 2 graph does not yet fill user_id and thread_id in tickets; these fields remain null.
Part 3 — Memory
Conversation memory
I used LangGraph SqliteSaver to persist conversation messages in SQLite. The thread_id identifies one conversation. My program uses user_id + ":" + thread_id as the checkpoint key to keep user threads separate.
User memory
I used a separate SQLite table for language preferences, with user_id as the primary key. The functions save_language() and get_language() store and read this preference. I did not use LangGraph SqliteStore in my version.

For my demonstrations, demo-user-a asked for Kazakh replies. demo-user-b had no stored language preference. This data was isolated.
Conversation persistence
The chat database is outputs/memory/conversations.db. The preference database is outputs/memory/preferences.db. Both are ignored by Git, so they are local runtime data.

In the scenario runner, each message is sent through a new Python subprocess. This allows the runner to check that saved SQLite data can be opened by another process. For S11 and S12, the events also specify restart_process while preserving local storage.
Retrieval and memory
Reading instructions from helpdesk.json is retrieval from a reference file. Remembering a message in the same thread is conversation memory. Remembering a language preference across threads is user memory.
Memory test results
Situation	Command used	Log file	What happened
Refer to an earlier message	python run_memory.py	outputs/scenarios/S10.json	The agent recalled enabling Wi-Fi, forgetting the saved network, and the failed reconnection.
Close and resume in another process	python run_memory.py	outputs/scenarios/S11.json	The assistant recalled the Wi-Fi issue and replied in Kazakh.
Same user in a new thread	python run_memory.py	outputs/scenarios/S12.json	The assistant remembered the Kazakh language preference without replaying the first thread.
Different user	python run_memory.py	outputs/scenarios/S13.json	User B had no saved language or previous problem from User A.


Part 4 — Running and checking my work
Environment
I used Python 3.13.18 in Google Colab. The versions of the required libraries are pinned in requirements.txt. README.md explains installation, use, tests, and limitations.
Automated tests
I wrote 10 pytest cases (including parametrized cases) in tests/test_helpdesk.py. They cover:
- Three basic routes (Wi-Fi, password, unsupported request).
- The original two-topic route and the new clarification route.
- Three Wi-Fi status profiles: normal, outage, unknown.
- Extracting only user-provided steps, without inventing airplane-mode actions.
- Saving preferences for User A without assigning them to User B.
The tests use local functions and fixtures. They do not make calls to the OpenAI API. They do not test every model decision or a full process restart automatically.
Test results
Command: python -m pytest tests -v

Local result: 10 passed in 2.18 seconds, 0 failed.
GitHub Actions
Workflow file: .github/workflows/tests.yml.

It is configured to run on pushes, pull requests, and manual dispatch. It installs Python 3.13, installs requirements.txt, and runs pytest. I created the workflow in Colab; the GitHub Actions result still needs to be verified after uploading the project.
Security
.gitignore excludes .env, cached files, local SQLite memory, and local ticket drafts. The project uses fictional demo user IDs. API keys must be supplied through the environment and must not be committed. Real support tickets are not submitted.
Choices and limitations
My choices
I used LangGraph for routing, tools, and conversation history. I chose GPT-4o-mini for tool selection and SQLite for local persistence. A separate preferences table keeps language choices tied to user IDs. Pytest gives quick, API-free checks.
Limitations
This project uses fictional university helpdesk data. The service statuses are simulated. Only a small set of problem categories and phrases are supported. The language model needs an API key and internet access. Responses may vary between runs. Tickets are local drafts and are not actually sent. The current tests cover selected local logic, not all possible agent behaviors.
Supplied scenarios — my actual results
Scenario	Command or manual steps	Log file	What happened / what I changed
S01 — Simple Wi-Fi route	Part 1 scenario runner	outputs/scenarios/S01.json	Routed to wifi_help.
S02 — Case-insensitive password route	Part 1 scenario runner	outputs/scenarios/S02.json	Uppercase PASSWORD routed to password_help.
S03 — Unsupported request	Part 1 scenario runner	outputs/scenarios/S03.json	Routed to other_help.
S04 — Two topics before graph change	Original graph	outputs/scenarios/S04.json	Wi-Fi had priority.
S05 — Two topics after graph change	Updated graph	outputs/scenarios/S05.json	Routed to clarify_problem.
S06 — Instructions then local ticket	Part 2 agent, exact input	outputs/scenarios/S06.json	Three tools called; draft saved; steps corrected to avoid invented actions.
S07 — Wi-Fi outage	Part 2 agent	outputs/scenarios/S07.json	Detected outage; no conditional ticket.
S08 — Status source unavailable	Part 2 agent	outputs/scenarios/S08.json	Unknown status; asked what to do next.
S09 — Missing ticket details	Part 2 agent, two messages	outputs/scenarios/S09.json	Asked for details first, then drafted ticket.
S10 — Current conversation	python run_memory.py	outputs/scenarios/S10.json	Recalled previous Wi-Fi steps.
S11 — Restart and recall	python run_memory.py	outputs/scenarios/S11.json	Recalled problem and Kazakh preference from SQLite.
S12 — Preference across threads	python run_memory.py	outputs/scenarios/S12.json	Remembered Kazakh in a new thread.
S13 — Separate users	python run_memory.py	outputs/scenarios/S13.json	User B did not receive User A's memory.
S14 — Password recovery outage	Part 2 agent	outputs/scenarios/S14.json	Found account-recovery outage without inventing a repair time.


Final observations
In this homework, I learned to make a small university IT helpdesk with LangGraph. In Part 1, I built rule-based routes. In Part 2, I connected an AI model with three tools. In Part 3, I saved conversation history and language preferences in SQLite. I also learned to check the code using pytest and to set up a GitHub Actions workflow.

All 14 supplied scenarios were run and their logs were saved locally. My 10 API-free tests passed. The next final check is to upload the project to GitHub and verify the workflow there.
