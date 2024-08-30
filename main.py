# main.py

import logging

import streamlit as st

import config
from ui import render_file_upload
from utils import get_claude_client
from utils.message_handler import (
    add_message_to_history,
    clear_conversation,
    process_message,
)
from utils.session import initialize_session_state

logger = logging.getLogger(__name__)

st.set_page_config(page_title=config.APP_TITLE, layout="wide")


def load_css() -> None:
    """Loads the CSS styles for the application."""
    # Load Font Awesome
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">',
        unsafe_allow_html=True,
    )

    # Load custom CSS
    with open("styles/main.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def handle_system_prompt() -> None:
    """Handles the system prompt input and updates the session state."""
    st.session_state.system_prompt = st.text_area(
        "System Prompt (optional)",
        value=st.session_state.get("system_prompt", ""),
        help="Enter a system prompt to guide Claude's behavior. This will be included only in the first message of the conversation.",
    )


def main() -> None:
    """Main function to run the Streamlit application."""
    initialize_session_state()
    load_css()
    st.title(config.APP_TITLE)

    try:
        client = get_claude_client()
    except Exception as e:
        logger.exception("Error initializing Claude client: %s", e)
        st.error(
            "Failed to initialize Claude client. Please check your Google Cloud credentials and configuration."
        )
        return

    handle_system_prompt()

    # File upload
    uploaded_files = st.file_uploader(
        "Attach a file",
        type=["txt", "py", "js", "html", "css", "json", "jpg", "jpeg", "png", "md"],
        accept_multiple_files=True,
        key="file_uploader",
    )

    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input():
        # Process newly uploaded files
        attached_files = []
        if uploaded_files:
            attached_files = render_file_upload(uploaded_files)
            # Include attached files in the prompt
            for file in attached_files:
                prompt += (
                    f"\n\nAttached file: {file['name']}\n```\n{file['content']}\n```"
                )
            # Clear the file uploader
            st.session_state.pop("file_uploader", None)

        # Prepare the full prompt
        full_prompt = prompt
        if not st.session_state.conversation_started and st.session_state.system_prompt:
            full_prompt = f"{st.session_state.system_prompt}\n\n{prompt}"
            st.session_state.conversation_started = True

        # Display the new user message
        with st.chat_message("user"):
            st.markdown(full_prompt)

        # Add user message to conversation history
        add_message_to_history("user", full_prompt)

        # Process the message and get Claude's response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in process_message(
                st.session_state.messages,
                client,
                attached_files=attached_files,
            ):
                full_response = response
                message_placeholder.markdown(response)

        # Add Claude's response to the conversation history
        add_message_to_history("assistant", full_response)

    # Clear conversation button
    if st.session_state.messages:
        if st.button("Clear Conversation"):
            clear_conversation()
            st.rerun()

    # Continue response button (only shown when max tokens were reached)
    if st.session_state.get("max_tokens_reached", False):
        if st.button("Continue Response"):
            st.session_state.max_tokens_reached = False
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in process_message(
                    st.session_state.messages, client, continue_last=True
                ):
                    full_response = response
                    message_placeholder.markdown(response)
            # Update the last assistant message in the conversation history
            if (
                st.session_state.messages
                and st.session_state.messages[-1]["role"] == "assistant"
            ):
                st.session_state.messages[-1]["content"] += full_response
            else:
                add_message_to_history("assistant", full_response)


if __name__ == "__main__":
    main()
