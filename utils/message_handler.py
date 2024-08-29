# utils/message_handler.py

from __future__ import annotations  # Enable postponed evaluation of annotations

import json
import logging
from typing import Any, Dict, Generator, List, Optional

import streamlit as st
from anthropic import AnthropicVertex, APIError

import config

from .file_handler import format_file_for_message
from .session import initialize_session_state

logger = logging.getLogger(__name__)


def validate_message_alternation(
    messages: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Validates and corrects the alternation of user and assistant roles in the message list.

    Args:
        messages: A list of message dictionaries.

    Returns:
        A list of validated message dictionaries with correct role alternation.
    """
    validated_messages = []
    last_role = None
    for message in messages:
        if message["role"] == last_role == "user":
            # Combine consecutive user messages
            current_content = (
                json.loads(validated_messages[-1]["content"])
                if isinstance(validated_messages[-1]["content"], str)
                else validated_messages[-1]["content"]
            )
            new_content = (
                json.loads(message["content"])
                if isinstance(message["content"], str)
                else message["content"]
            )

            if isinstance(current_content, list) and isinstance(new_content, list):
                combined_content = current_content + new_content
            else:
                combined_content = str(current_content) + "\n\n" + str(new_content)

            validated_messages[-1]["content"] = json.dumps(combined_content)
        elif message["role"] != last_role or message["role"] == "system":
            # Convert content to JSON string for consistency
            message["content"] = json.dumps(message["content"])
            validated_messages.append(message)
            last_role = message["role"]
    return validated_messages


def process_message(
    content: List[Dict[str, Any]],
    client: AnthropicVertex,
    continue_last: bool = False,
    attached_files: List[Dict[str, Any]] = [],
) -> Generator[str, None, None]:
    """
    Processes a message and gets a response from Claude.

    Args:
        content: The content of the message to send to Claude.
        client: The AnthropicVertex client instance.
        continue_last: Whether to continue the last response.
        attached_files: List of files attached to this specific message.

    Returns:
        Claude's response as a string, or None if an error occurred.
    """
    messages = []

    # Check if system prompt has changed or if it's a new conversation
    if st.session_state.system_prompt and (
        "last_system_prompt" not in st.session_state
        or st.session_state.system_prompt != st.session_state.last_system_prompt
    ):
        messages.append({"role": "system", "content": st.session_state.system_prompt})
        st.session_state.last_system_prompt = st.session_state.system_prompt

    # Add conversation history
    messages.extend(st.session_state.messages)

    # Prepare file contents for this specific message
    file_contents = []
    for file in attached_files:
        file_contents.extend(format_file_for_message(file))

    # Compose the message
    if content or file_contents:
        user_message = []
        if content:
            user_message.append({"type": "text", "text": content[0]["text"]})
        user_message.extend(file_contents)
        messages.append({"role": "user", "content": user_message})

    if continue_last:
        # Update the last assistant message with the continued response
        last_assistant_message_index = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "assistant":
                last_assistant_message_index = i
                break

        if last_assistant_message_index != -1:
            messages.insert(
                last_assistant_message_index + 1,
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please continue your previous response.",
                        }
                    ],
                },
            )
        else:
            st.error("No previous assistant message to continue.")
            return None

    # Validate and correct message alternation
    messages = validate_message_alternation(messages)

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
    except ValueError as e:
        logger.exception("Value error: %s", e)
        st.error(f"Invalid input or file format: {e}. Please check your input.")
        return None
    except IOError as e:
        logger.exception("IO error: %s", e)
        st.error(
            f"Error reading or writing file: {e}. Please check your file permissions."
        )
        return None
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        st.error(f"An unexpected error occurred: {e}. Please try again later.")
        return None

    # Only append new assistant message if not continuing last response
    if not continue_last:
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
    else:
        # Update the last assistant message content
        st.session_state.messages[last_assistant_message_index][
            "content"
        ] = full_response

    st.session_state.last_message_content = full_response
    return full_response


def clear_conversation() -> None:
    """Clears the conversation history and resets the session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()


def get_conversation_history() -> List[Dict[str, Any]]:
    """
    Gets the conversation history from the session state.

    Returns:
        A list of message dictionaries representing the conversation history.
    """
    return st.session_state.messages


def add_message_to_history(role: str, content: str) -> None:
    """
    Adds a message to the conversation history.

    Args:
        role: The role of the message sender (e.g., "user" or "assistant").
        content: The content of the message.
    """
    st.session_state.messages.append({"role": role, "content": content})
