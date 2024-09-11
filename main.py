# main.py

import logging
import random
import uuid

import streamlit as st

import config
from ui import render_file_upload
from utils import get_claude_client
from utils.file_handler import FileProcessingError, process_files
from utils.message_handler import (
    add_message_to_history,
    clear_conversation,
    process_message,
    truncate_conversation_history,
)
from utils.session import (
    check_session_expiry,
    clear_file_data,
    initialize_session_state,
    update_last_activity,
)

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


def main() -> None:
    """Main function to run the Streamlit application."""
    initialize_session_state()
    load_css()
    st.title(config.APP_TITLE)

    # Check session expiry
    if check_session_expiry():
        clear_conversation()
        st.info("Your session has expired. Starting a new conversation.")
        st.rerun()

    try:
        client = get_claude_client()
    except Exception as e:
        logger.exception("Error initializing Claude client: %s", e)
        st.error(
            "Failed to initialize Claude client. Please check your Google Cloud credentials and configuration."
        )
        return

    system_prompt = st.text_area(
        "System Prompt (optional)",
        value=st.session_state.get("system_prompt", ""),
        help="Enter a system prompt to guide Claude's behavior.",
    )

    # File upload with dynamic key
    uploaded_files = st.file_uploader(
        "Attach a file",
        type=[
            "txt",
            "py",
            "js",
            "html",
            "css",
            "json",
            "jpg",
            "jpeg",
            "png",
            "md",
            "pdf",
        ],
        accept_multiple_files=True,
        key=st.session_state.file_uploader_key,
    )

    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input():
        if not prompt.strip():
            st.info("Please enter a message.")
            return

        update_last_activity()  # Update last activity time

        # Process newly uploaded files
        attached_files = []
        message_id = str(uuid.uuid4())  # Generate a unique ID for the message
        if uploaded_files:
            try:
                attached_files = process_files(uploaded_files)
                # Store files in session state with the message ID
                st.session_state.files[message_id] = attached_files
                # Reset the file uploader key
                st.session_state.file_uploader_key = random.randint(0, 1000000)
            except FileProcessingError as e:
                st.error(str(e))
                return

        # Prepare the message content
        display_content = prompt
        if attached_files:
            display_content += "\n\nAttached Files:\n"
            for file in attached_files:
                display_content += f"\n- {file['name']} ({file['type']})"

        # Display the new user message
        with st.chat_message("user"):
            st.markdown(display_content)

        # Add user message to conversation history (without file contents)
        add_message_to_history("user", display_content, message_id)

        # Truncate conversation history if it's too long
        truncate_conversation_history()

        # Get the conversation history without file contents
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.messages[:-1]  # Exclude the last message
        ]

        # Process the message and get Claude's response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in process_message(
                conversation_history,
                client,
                user_prompt=prompt,  # Only send the prompt, not file contents
                system_prompt=system_prompt,
                message_id=message_id,  # Pass the message ID
            ):
                full_response = response
                message_placeholder.markdown(response)

        # Add Claude's response to the conversation history
        add_message_to_history("assistant", full_response)

        # Clear the files after they have been processed
        clear_file_data()

    # Clear conversation button
    if st.session_state.messages:
        if st.button("Clear Conversation"):
            clear_conversation()
            st.rerun()

    # Continue response button (only shown when max tokens were reached)
    if st.session_state.get("max_tokens_reached", False):
        if st.button("Continue Response"):
            update_last_activity()  # Update last activity time
            st.session_state.max_tokens_reached = False
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in process_message(
                    st.session_state.messages,
                    client,
                    continue_last=True,
                    system_prompt=system_prompt,
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

    # Update last activity time
    update_last_activity()


if __name__ == "__main__":
    main()
