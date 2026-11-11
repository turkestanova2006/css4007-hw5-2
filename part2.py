import json
import os
from langchain_core.tools import tool

def load_data(file):
    with open("data/" + file, encoding="utf-8") as f:
        return json.load(f)

@tool
def find_instructions(topic: str) -> str:
    """Find instructions for wifi or password."""
    data = load_data("helpdesk.json")
    topic = topic.lower().replace("wi-fi", "wifi")
    info = data["instructions"].get(topic)

    if not info:
        return "No instructions found."

    return json.dumps(info)

@tool
def check_service_status(service: str, profile: str = "normal") -> str:
    """Check the status of wifi or account_recovery."""
    data = load_data("service_status.json")
    profiles = data["profiles"]

    if profile not in profiles:
        return "Unknown status profile."

    result = profiles[profile].get(service)

    if result is None:
        return "Unknown service."

    return json.dumps(result)

@tool
def prepare_ticket(problem: str, steps_tried: str) -> str:
    """Prepare a local support ticket draft."""
    data = load_data("ticket_template.json")
    ticket = data["ticket"].copy()

    if not problem.strip() or not steps_tried.strip():
        return "Please provide the problem and steps tried."

    ticket["summary"] = problem
    ticket["steps_tried"] = [steps_tried]

    os.makedirs("outputs", exist_ok=True)

    with open("outputs/ticket_draft.json", "w") as f:
        json.dump(ticket, f, indent=2)

    return json.dumps(ticket)


from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition



def create_agent(profile="normal"):
    from langchain_core.tools import tool

    checked = {}
    user_texts = []
    conditional_request = {"value": False}

    @tool("check_service_status")
    def status_tool(service: str) -> str:
        """Check the selected service status."""
        service = service.lower().strip()
        if "wifi" in service or "wi-fi" in service or "wi fi" in service:
            service = "wifi"
        elif "password" in service or "recovery" in service:
            service = "account_recovery"
        result = check_service_status.invoke({
            "service": service,
            "profile": profile
        })
        try:
            checked[service] = json.loads(result)["status"]
        except (ValueError, KeyError, TypeError):
            checked[service] = "unknown"
        return result

    @tool("prepare_ticket")
    def ticket_tool(problem: str, steps_tried: str) -> str:
        """Prepare a local draft when enough details are known."""
        if conditional_request["value"]:
            if checked.get("wifi") != "operational":
                return "Ticket blocked: Wi-Fi is not confirmed operational."
        verified_steps = extract_steps(user_texts)
        if not verified_steps:
            return "Please tell me which steps you already tried."
        return save_ticket(problem, verified_steps, profile, checked.get("wifi"))

    selected_tools = [find_instructions, status_tool, ticket_tool]

    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    ).bind_tools(selected_tools)

    def assistant(state):
        user_messages = [
            m.content for m in state["messages"]
            if m.type == "human" and isinstance(m.content, str)
        ]
        user_texts[:] = user_messages
        last_request = user_messages[-1].lower() if user_messages else ""
        conditional_request["value"] = (
            "if" in last_request and
            ("operating" in last_request or "operational" in last_request)
        )

        system = SystemMessage(content="""
You are a university IT helpdesk assistant.
Use the tools for instructions and service statuses.
If a ticket depends on service status, check it first.
Prepare a conditional ticket only if service is operational.
If status is unknown, ask the user what to do next.
Do not invent problems, steps or repair times.
Ask for missing ticket details.
Tickets are local drafts, not submitted.
""")
        reply = model.invoke([system] + state["messages"])
        return {"messages": [reply]}

    graph = StateGraph(MessagesState)
    graph.add_node("assistant", assistant)
    graph.add_node("tools", ToolNode(selected_tools))
    graph.add_edge(START, "assistant")
    graph.add_conditional_edges("assistant", tools_condition)
    graph.add_edge("tools", "assistant")

    return graph.compile()



def save_ticket(problem, steps_tried, profile, service_status):
    from uuid import uuid4

    with open("data/ticket_template.json", encoding="utf-8") as f:
        ticket = json.load(f)["ticket"]

    if not problem.strip() or not steps_tried.strip():
        return "Please provide the problem and steps tried."

    ticket["ticket_id"] = str(uuid4())[:8]
    ticket["category"] = (
        "wifi" if "wi-fi" in problem.lower() or "wifi" in problem.lower()
        else "other"
    )
    ticket["summary"] = problem
    ticket["steps_tried"] = [steps_tried]
    ticket["service_status"] = service_status
    ticket["status_profile"] = profile if service_status else None

    os.makedirs("outputs/tickets", exist_ok=True)
    filename = f"outputs/tickets/{ticket['ticket_id']}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(ticket, f, indent=2)

    return json.dumps({"file": filename, "ticket": ticket})



def extract_steps(messages):
    text = " ".join(messages).lower()
    steps = []

    if "enabled wi-fi" in text or "enabled wifi" in text or "enabled it" in text:
        steps.append("Enabled Wi-Fi")

    if "forgot the saved network" in text:
        steps.append("Forgot the saved network")

    if ("reconnect" in text or
        "will not connect" in text or
        "still fails" in text):
        steps.append("Connection still fails")

    if "turned off airplane mode" in text:
        steps.append("Turned off airplane mode")

    return "; ".join(steps)
