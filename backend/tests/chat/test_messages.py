import uuid

from app.chat.messages import UIMessage, content_to_ui_message, latest_user_text, to_stored_content


def test_latest_user_text_returns_last_message_text() -> None:
    messages = [
        UIMessage(role="user", parts=[{"type": "text", "text": "first"}]),
        UIMessage(role="assistant", parts=[{"type": "text", "text": "reply"}]),
        UIMessage(role="user", parts=[{"type": "text", "text": "second"}]),
    ]
    assert latest_user_text(messages) == "second"


def test_latest_user_text_joins_multiple_parts() -> None:
    messages = [
        UIMessage(role="user", parts=[{"type": "text", "text": "hello "}, {"type": "text", "text": "world"}]),
    ]
    assert latest_user_text(messages) == "hello world"


def test_latest_user_text_empty_list() -> None:
    assert latest_user_text([]) == ""


def test_to_stored_content_shape() -> None:
    content = to_stored_content("assistant", "hi there")
    assert content == {"role": "assistant", "parts": [{"type": "text", "text": "hi there"}]}


def test_content_to_ui_message_round_trip() -> None:
    message_id = uuid.uuid4()
    content = to_stored_content("user", "hello")
    ui_message = content_to_ui_message(message_id, content)
    assert ui_message.id == str(message_id)
    assert ui_message.role == "user"
    assert ui_message.parts[0].text == "hello"
