from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import Optional

import streamlit as st
from anthropic import AnthropicVertex

from utils import process_message


def render_chat_interface(client: AnthropicVertex) -> None:
    """
    Renders the chat interface in the Streamlit UI.

    This function handles the display of the chat history, user input,
    and processing of messages using the Claude AI model.

    Args:
        client: The AnthropicVertex client instance for interacting with Claude.
    """
    # Chat message area
    chat_container = st.container()

    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                """
                <div class="chat-icon-container">
                    <i class="fas fa-comments chat-icon"></i>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Display conversation history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # Input for user message
    user_input: Optional[str] = st.chat_input("Type your message here...")

    if user_input:
        # Check if there's only one file attached
        if (
            st.session_state.attached_files
            and len(st.session_state.attached_files) == 1
        ):
            file = st.session_state.attached_files[0]
            # Include file content in the message
            user_input += f"\n\nAttached file: {file.name}\n\`\`\`\n{file.read().decode('utf-8')}\n\`\`\`"
            # Clear attached files after including it in the message
            st.session_state.attached_files = []

        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Process message and get Claude's response
        try:
            response: Optional[str] = process_message(
                [{"type": "text", "text": user_input}], client
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return

        # Display Claude's response and add to history if successful
        if response:
            # Only render the new assistant message if it's not already displayed
            if (
                st.session_state.messages[-1]["role"] != "assistant"
                or st.session_state.messages[-1]["content"] != response
            ):
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

    # Continue button (only shown when max tokens were reached)
    if st.session_state.get("max_tokens_reached", False):
        if st.button("Continue Response"):
            st.session_state.max_tokens_reached = False
            try:
                process_message([], client, continue_last=True)
            except Exception as e:
                st.error(f"An error occurred: {e}")
