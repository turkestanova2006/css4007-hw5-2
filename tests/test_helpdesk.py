import pytest
import part3
from part1 import create_graph
from part2 import check_service_status, extract_steps

@pytest.mark.parametrize("message,expected", [
    ("I cannot connect to Wi-Fi.", "wifi"),
    ("I forgot my PASSWORD.", "password"),
    ("My laptop screen is broken.", "other"),
])
def test_original_routes(message, expected):
    graph = create_graph()
    result = graph.invoke({
        "message": message, "category": "", "reply": ""
    })
    assert result["category"] == expected

def test_original_two_topics():
    graph = create_graph()
    result = graph.invoke({
        "message": "My Wi-Fi password does not work.",
        "category": "", "reply": ""
    })
    assert result["category"] == "wifi"

def test_clarification():
    graph = create_graph(updated=True)
    result = graph.invoke({
        "message": "My Wi-Fi password does not work.",
        "category": "", "reply": ""
    })
    assert result["category"] == "clarify"

@pytest.mark.parametrize("profile,status", [
    ("normal", "operational"),
    ("wifi_outage", "outage"),
    ("status_unavailable", "unknown")
])
def test_wifi_status(profile, status):
    import json
    result = check_service_status.invoke({
        "service": "wifi", "profile": profile
    })
    assert json.loads(result)["status"] == status

def test_verified_steps():
    messages = [
        "I enabled Wi-Fi and forgot the saved network, "
        "but Campus-Demo still will not connect."
    ]
    result = extract_steps(messages)

    assert "Enabled Wi-Fi" in result
    assert "Forgot the saved network" in result
    assert "Connection still fails" in result
    assert "airplane mode" not in result

def test_user_preferences(tmp_path, monkeypatch):
    monkeypatch.setattr(
        part3, "PREF_DB", str(tmp_path / "preferences.db")
    )

    part3.save_language("demo-user-a", "Kazakh")

    assert part3.get_language("demo-user-a") == "Kazakh"
    assert part3.get_language("demo-user-b") is None
