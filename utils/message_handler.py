# utils/message_handler.py

from __future__ import annotations  # Enable postponed evaluation of annotations

import logging
from typing import Any, Dict, Generator, List, Optional

import streamlit as st
from anthropic import AnthropicVertex, APIError

import config
from utils.session import initialize_session_state

logger = logging.getLogger(__name__)


def process_message(
    messages: List[Dict[str, Any]],
    client: AnthropicVertex,
    continue_last: bool = False,
    user_prompt: str = "",
    system_prompt: str = "",
    message_id: Optional[str] = None,  # Add message_id parameter
) -> Generator[str, None, None]:
    # Use the existing messages without modification
    current_messages = messages.copy()

    # Ensure message alternation
    if current_messages and current_messages[-1]["role"] == "user":
        current_messages.pop()

    # Add the new message
    if continue_last:
        if current_messages and current_messages[-1]["role"] == "assistant":
            current_messages.append(
                {"role": "user", "content": "Please continue your previous response."}
            )
    else:
        # Include file content if it's the initial message with attachments
        if message_id and message_id in st.session_state.files:
            attached_files = st.session_state.files[message_id]
            for file in attached_files:
                user_prompt += f"\n\nAttached File: {file['name']} ({file['type']})\n```\n{file['content']}\n```"

        current_messages.append({"role": "user", "content": user_prompt})

    full_response = ""
    try:
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
