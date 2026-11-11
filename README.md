# HW5 - University IT Helpdesk with LangGraph

CSS-4007 - Artificial Intelligence

## About the project

This project is a university IT helpdesk built with Python and LangGraph.

It helps users with Wi-Fi and password problems. It can find instructions, check service status, and prepare local support tickets. It also remembers conversations and language preferences.

The project uses fictional university data.

## Part 1 - Basic Graph

I created a LangGraph with three routes:

- wifi_help
- password_help
- other_help

I also added clarify_problem for messages about both Wi-Fi and password.

Run:

```bash
python part1.py
```

## Part 2 - AI and Tools

I used OpenAI GPT-4o-mini.

The three tools are:

1. find_instructions
2. check_service_status
3. prepare_ticket

The assistant uses local JSON data. Tickets are saved as drafts only.

To configure the model, set OPENAI_API_KEY in your environment.

## Part 3 - Memory

I used SQLite for persistent memory.

Conversation history is stored in:

outputs/memory/conversations.db

Language preferences are stored in:

outputs/memory/preferences.db

Different users have separate memory.

## Installation

Python version used: 3.13.18

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Activate the virtual environment before installing packages.

Set OPENAI_API_KEY before running the model examples.

## Run demonstrations

Run the Part 1 example:

```bash
python part1.py
```

Run the memory scenarios:

```bash
python run_memory.py
```

Part 2 can be run by importing create_agent from part2.py.
It needs an OpenAI API key.

The saved scenario results are in outputs/scenarios.

## Tests

Run tests without an API key:

```bash
python -m pytest tests -v
```

The first local test run passed 10 tests.

GitHub Actions also runs the tests automatically after pushing changes.

## Reset memory

Close the running program first.

Delete the SQLite files inside outputs/memory to start with empty memory.

## Limitations

This is a demonstration, not a real university helpdesk.
Tickets are local drafts and are not submitted.
The model needs an API key.
Some responses may vary between runs.
