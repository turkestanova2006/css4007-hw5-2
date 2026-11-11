import os
import sqlite3
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.sqlite import SqliteSaver

os.makedirs("outputs/memory", exist_ok=True)

PREF_DB = os.environ.get("HW5_PREF_DB", "outputs/memory/preferences.db")
CHAT_DB = os.environ.get("HW5_CHAT_DB", "outputs/memory/conversations.db")

def save_language(user_id, language):
    with sqlite3.connect(PREF_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences
            (user_id TEXT PRIMARY KEY, language TEXT)
        """)
        conn.execute(
            "INSERT OR REPLACE INTO preferences VALUES (?, ?)",
            (user_id, language)
        )

def get_language(user_id):
    with sqlite3.connect(PREF_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences
            (user_id TEXT PRIMARY KEY, language TEXT)
        """)
        row = conn.execute(
            "SELECT language FROM preferences WHERE user_id=?",
            (user_id,)
        ).fetchone()
    return row[0] if row else None

def create_memory_agent():
    connection = sqlite3.connect(
        CHAT_DB, check_same_thread=False
    )
    checkpointer = SqliteSaver(connection)

    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    def assistant(state, config):
        user_id = config["configurable"]["user_id"]
        latest = state["messages"][-1]

        if latest.type == "human":
            text = latest.content.lower()
            if "prefer replies in kazakh" in text:
                save_language(user_id, "Kazakh")

        language = get_language(user_id)

        instruction = """
        You are a university IT helpdesk assistant.
        Remember the current conversation.
        Do not invent previous messages or troubleshooting steps.
        Never reveal another user's information.
        If you do not know something, say so.
        """

        if language:
            instruction += f"\nReply in {language}."

        response = model.invoke(
            [SystemMessage(content=instruction)]
            + state["messages"]
        )
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_edge(START, "assistant")

    graph = builder.compile(checkpointer=checkpointer)
    return graph, connection

def chat(graph, user_id, thread_id, message):
    config = {
        "configurable": {
            "thread_id": user_id + ":" + thread_id,
            "user_id": user_id
        }
    }
    result = graph.invoke(
        {"messages": [("user", message)]},
        config=config
    )
    return result["messages"][-1].content
