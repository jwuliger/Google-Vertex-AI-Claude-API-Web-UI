# utils/message_handler.py

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Generator, List, Optional

import streamlit as st
from anthropic import AnthropicVertex, APIError, APIStatusError

import config
from utils.file_handler import format_file_for_message
from utils.session import initialize_session_state, reset_conversation

logger = logging.getLogger(__name__)


def process_message(
    messages: List[Dict[str, Any]],
    client: AnthropicVertex,
    continue_last: bool = False,
    user_prompt: str = "",
    system_prompt: str = "",
    message_id: Optional[str] = None,
) -> Generator[str, None, None]:
    logger.debug("Initial messages: %s", messages)

    if not messages:
        logger.warning(
            "Received empty message history. Initializing with a default message."
        )
        messages = [{"role": "user", "content": "Hello"}]

    current_messages = messages.copy()

    # Ensure there's at least one user message in the conversation
    if current_messages[0]["role"] != "user":
        default_user_message = {"role": "user", "content": "Hello"}
        current_messages.insert(0, default_user_message)
        logger.debug("Added default user message to conversation")

    # Ensure the last message is from the assistant
    if current_messages and current_messages[-1]["role"] == "user":
        current_messages.pop()

    logger.debug("Current messages before continue_last: %s", current_messages)

    # Prepare the new user message
    new_user_message = ""

    # Include file content if it's the initial message with attachments
    if message_id and message_id in st.session_state.files:
        attached_files = st.session_state.files[message_id]
        for file in attached_files:
            formatted_file = format_file_for_message(file)
            new_user_message += "\n".join(
                [item["text"] for item in formatted_file if item["type"] == "text"]
            )
            new_user_message += "\n\n"

    # Add the user prompt
    new_user_message += user_prompt

    # Add the new message
    if continue_last:
        new_user_message = "Please continue your previous response."

    current_messages.append({"role": "user", "content": new_user_message.strip()})

    logger.debug("Current messages after adding user message: %s", current_messages)

    full_response = ""
    retries = 0
    max_retries = 3
    retry_delay = 1

    while retries < max_retries:
        try:
            logger.debug(
                "Messages sent to API (retry %d): %s", retries, current_messages
            )
            with client.messages.stream(
                max_tokens=config.MAX_TOKENS,
                messages=current_messages,
                model=config.MODEL,
                temperature=config.TEMPERATURE,
                system=system_prompt,
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    yield full_response

            break

        except (APIStatusError, APIError) as e:
            if (
                isinstance(e, APIStatusError) and e.status_code == 429
            ):  # Too Many Requests
                logger.warning(
                    "Vertex AI rate limit reached (retry %d), retrying in %d seconds...",
                    retries,
                    retry_delay,
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                retries += 1
            else:
                logger.exception("Claude API error: %s", e)
                st.error(
                    f"An error occurred while communicating with Claude: {e}. Please try again later or contact support."
                )
                reset_conversation()
                return
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            st.error(f"An unexpected error occurred: {e}. Please try again later.")
            reset_conversation()
            return

    if retries == max_retries:
        st.error("Maximum retries reached. Please try again later.")
        reset_conversation()
        return

    # Check if max tokens were reached
    st.session_state.max_tokens_reached = (
        len(full_response.split()) >= config.MAX_TOKENS
    )
    if st.session_state.max_tokens_reached:
        st.warning(
            "Claude's response has reached the maximum token limit. You can click 'Continue Response' to get more."
        )

    # Update the session state with the processed messages
    st.session_state.messages = current_messages
    logger.debug(
        f"Updated session state messages. Current count: {len(st.session_state.messages)}"
    )

    return full_response


def add_message_to_history(
    role: str, content: str, message_id: Optional[str] = None
) -> None:
    st.session_state.messages.append(
        {"role": role, "content": content, "message_id": message_id}
    )


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
