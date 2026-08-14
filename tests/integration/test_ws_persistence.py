"""Tests for the DB message payload round-trip in ws_handler.

Regression tests for the persistence half of the tool_use pairing bug:
assistant tool_calls were dropped when a session was saved to the DB, so
reloading a session and continuing the turn re-introduced the unpaired
tool_result 400.
"""
from harness.models import Message, ToolCall

from server.ws_handler import _message_to_db_payload, _db_payload_to_message


def test_assistant_tool_calls_survive_payload_roundtrip():
    msg = Message(
        role="assistant",
        content="Let me check the file.",
        tool_calls=[ToolCall(id="t1", name="read_file", arguments={"path": "a.py"})],
    )
    payload = _message_to_db_payload(msg)
    assert payload["content"] == "Let me check the file."
    assert payload["tool_calls"] == [{"id": "t1", "name": "read_file", "arguments": {"path": "a.py"}}]

    restored = _db_payload_to_message("assistant", payload)
    assert restored.content == "Let me check the file."
    assert restored.tool_calls[0].id == "t1"
    assert restored.tool_calls[0].name == "read_file"
    assert restored.tool_calls[0].arguments == {"path": "a.py"}


def test_tool_message_survives_payload_roundtrip():
    msg = Message(role="tool", content="Exit code: 0\nok", tool_call_id="t1")
    payload = _message_to_db_payload(msg)
    assert payload["tool_call_id"] == "t1"

    restored = _db_payload_to_message("tool", payload)
    assert restored.tool_call_id == "t1"
    assert restored.content == "Exit code: 0\nok"


def test_plain_message_survives_payload_roundtrip():
    msg = Message(role="user", content="hi")
    assert _message_to_db_payload(msg) == {"content": "hi"}

    restored = _db_payload_to_message("user", {"content": "hi"})
    assert restored.content == "hi"
    assert restored.tool_calls == []


def test_legacy_payload_without_tool_calls_loads_cleanly():
    """Messages persisted before tool_calls existed must still load."""
    restored = _db_payload_to_message("assistant", {"content": "old message"})
    assert restored.content == "old message"
    assert restored.tool_calls == []
