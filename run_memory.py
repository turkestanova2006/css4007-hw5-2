import json
import os
import sys
import subprocess

with open("data/scenarios.json", encoding="utf-8") as f:
    scenarios = json.load(f)["scenarios"]

os.makedirs("outputs/scenarios", exist_ok=True)

# Each message runs in a separate Python process
worker = """
import json
import sys
from part3 import create_memory_agent, chat, get_language

event = json.loads(sys.stdin.read())
graph, connection = create_memory_agent()

try:
    answer = chat(
        graph,
        event["user_id"],
        event["thread_id"],
        event["message"]
    )
    print(json.dumps({
        "answer": answer,
        "language": get_language(event["user_id"])
    }, ensure_ascii=False))
finally:
    connection.close()
"""

for scenario in scenarios:
    if scenario["part"] != 3:
        continue

    sid = scenario["id"]

    # Fresh database names avoid locked SQLite files in Windows/Jupyter.
    # Reusing names across runs is safe because each run uses a new folder.
    from uuid import uuid4
    session_dir = os.path.join("outputs", "memory", sid + "_" + uuid4().hex[:8])
    os.makedirs(session_dir, exist_ok=True)
    worker_env = os.environ.copy()
    worker_env["HW5_CHAT_DB"] = os.path.join(session_dir, "conversations.db")
    worker_env["HW5_PREF_DB"] = os.path.join(session_dir, "preferences.db")

    log = []

    for event in scenario["events"]:
        if event["action"] == "restart_process":
            log.append({
                "action": "restart_process",
                "preserve_local_storage": event["preserve_local_storage"]
            })
            continue

        result = subprocess.run(
            [sys.executable, "-c", worker],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            env=worker_env
        )

        if result.returncode != 0:
            print(result.stderr)
            raise RuntimeError(f"{sid} failed")

        response = json.loads(result.stdout.strip())

        print("\n", sid, "| USER:", event["user_id"])
        print("QUESTION:", event["message"])
        print("ANSWER:", response["answer"])
        print("LANGUAGE:", response["language"])

        log.append({
            "event": event,
            "response": response
        })

    with open(f"outputs/scenarios/{sid}.json",
              "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(sid, "SAVED!")

print("\nMemory scenarios finished!")
