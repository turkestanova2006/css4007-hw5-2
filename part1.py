import json
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

with open("data/helpdesk.json", encoding="utf-8") as f:
    data = json.load(f)

class State(TypedDict):
    message: str
    category: str
    reply: str

def read_request(state):
    text = state["message"].lower()
    if "wifi" in text or "wi-fi" in text:
        category = "wifi"
    elif "password" in text:
        category = "password"
    else:
        category = "other"
    return {"category": category}

def read_request_v2(state):
    text = state["message"].lower()
    wifi = "wifi" in text or "wi-fi" in text
    password = "password" in text
    if wifi and password:
        return {"category": "clarify"}
    return read_request(state)

def wifi_help(state):
    info = data["instructions"]["wifi"]
    return {"reply": info["title"] + "\n" + "\n".join(info["steps"])}

def password_help(state):
    info = data["instructions"]["password"]
    return {"reply": info["title"] + "\n" + "\n".join(info["steps"])}

def other_help(state):
    return {"reply": "Is your problem about Wi-Fi or password?"}

def clarify_problem(state):
    return {"reply": "Do you need Wi-Fi help or password help first?"}

def create_graph(updated=False):
    builder = StateGraph(State)
    builder.add_node("read_request", read_request_v2 if updated else read_request)
    builder.add_node("wifi_help", wifi_help)
    builder.add_node("password_help", password_help)
    builder.add_node("other_help", other_help)

    routes = {
        "wifi": "wifi_help",
        "password": "password_help",
        "other": "other_help"
    }

    if updated:
        builder.add_node("clarify_problem", clarify_problem)
        routes["clarify"] = "clarify_problem"

    builder.add_edge(START, "read_request")
    builder.add_conditional_edges(
        "read_request",
        lambda state: state["category"],
        routes
    )

    for node in routes.values():
        builder.add_edge(node, END)

    return builder.compile()

if __name__ == "__main__":
    messages = [
        "I cannot connect to Wi-Fi.",
        "I forgot my PASSWORD.",
        "My laptop screen is broken.",
        "My Wi-Fi password does not work."
    ]

    for updated in [False, True]:
        graph = create_graph(updated)
        print("\nUPDATED:", updated)

        for message in messages:
            result = graph.invoke({
                "message": message,
                "category": "",
                "reply": ""
            })
            print(message, "->", result["category"])
