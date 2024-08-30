# utils/message_handler.py

from __future__ import annotations  # Enable postponed evaluation of annotations

import logging
from typing import Any, Dict, Generator, List, Optional

import streamlit as st
from anthropic import AnthropicVertex, APIError

import config
from utils.session import initialize_session_state

from .file_handler import format_file_for_message

logger = logging.getLogger(__name__)


def ensure_message_alternation(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensures that messages alternate between "user" and "assistant" roles.

    Args:
        messages: A list of message dictionaries.

    Returns:
        A list of validated message dictionaries with correct role alternation.
    """
    validated_messages = []
    for message in messages:
        if not validated_messages or message["role"] != validated_messages[-1]["role"]:
            validated_messages.append(message)
        else:
            # If the roles are the same, combine the content
            validated_messages[-1]["content"] += f"\n\n{message['content']}"

    # Ensure the last message is from the user
    if validated_messages and validated_messages[-1]["role"] == "assistant":
        validated_messages.append({"role": "user", "content": "Please continue."})

    return validated_messages


def process_message(
    messages: List[Dict[str, Any]],
    client: AnthropicVertex,
    continue_last: bool = False,
    attached_files: List[Dict[str, Any]] = [],
) -> Generator[str, None, None]:
    """
    Processes a message and gets a response from Claude.

    Args:
        messages: The content of the message to send to Claude.
        client: The AnthropicVertex client instance.
        continue_last: Whether to continue the last response.
        attached_files: List of files attached to this specific message.

    Returns:
        Claude's response as a string, or None if an error occurred.
    """
    # Ensure message alternation
    messages = ensure_message_alternation(messages)

    # Prepare file contents for this specific message
    file_contents = []
    for file in attached_files:
        file_contents.extend(format_file_for_message(file))

    # Compose the message
    if file_contents:
        if messages[-1]["role"] == "user":
            if isinstance(messages[-1]["content"], str):
                messages[-1]["content"] += "\n\n" + "\n".join(
                    str(item) for item in file_contents
                )
            elif isinstance(messages[-1]["content"], list):
                messages[-1]["content"].extend(file_contents)
        else:
            messages.append({"role": "user", "content": file_contents})

    if continue_last and messages[-1]["role"] != "user":
        messages.append(
            {
                "role": "user",
                "content": "Please continue your previous response.",
            }
        )

    # Ensure the messages list ends with a user message
    if messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": "Please continue."})

    full_response = ""
    try:
        with client.messages.stream(
            max_tokens=config.MAX_TOKENS, messages=messages, model=config.MODEL
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield full_response

        # Check if max tokens were reached
        st.session_state.max_tokens_reached = (
            len(full_response.split()) >= config.MAX_TOKENS
        )
        if st.session_state.max_tokens_reached:
            st.warning(
                "Claude's response has reached the maximum token limit. You can click 'Continue Response' to get more."
            )

    except APIError as e:
        logger.exception("Claude API error: %s", e)
        st.error(
            f"An error occurred while communicating with Claude: {e.message}. Please try again later or contact support."
        )
        return None
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        st.error(f"An unexpected error occurred: {e}. Please try again later.")
        return None

    return full_response


def add_message_to_history(role: str, content: str) -> None:
    """
    Adds a message to the conversation history.

    Args:
        role: The role of the message sender (e.g., "user" or "assistant").
        content: The content of the message.
    """
    st.session_state.messages.append({"role": role, "content": content})


def clear_conversation() -> None:
    """Clears the conversation history and resets the session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()
    # Clear the file uploader state
    st.session_state.pop("file_uploader", None)


def get_conversation_history() -> List[Dict[str, Any]]:
    """
    Gets the conversation history from the session state.

    Returns:
        A list of message dictionaries representing the conversation history.
    """
    return st.session_state.messages
