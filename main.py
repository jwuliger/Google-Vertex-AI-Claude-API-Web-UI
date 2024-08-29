# main.py

import logging

import streamlit as st

import config
from ui import render_chat_interface, render_file_upload
from utils import get_claude_client
from utils.message_handler import clear_conversation, process_message
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

    st.session_state.system_prompt = st.text_area(
        "System Prompt (optional)",
        value=st.session_state.system_prompt,
        help="Enter a system prompt to guide Claude's behavior",
    )

    # File upload
    attached_files = render_file_upload()

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is your question?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in process_message(
                [{"type": "text", "text": prompt}],
                client,
                attached_files=attached_files,
            ):
                full_response = response
                message_placeholder.markdown(response)
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

    # Clear conversation button (only shown when there are messages)
    if st.session_state.messages:
        if st.button("Clear Conversation"):
            clear_conversation()

    # Continue response button (only shown when max tokens were reached)
    if st.session_state.get("max_tokens_reached", False):
        if st.button("Continue Response"):
            st.session_state.max_tokens_reached = False
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in process_message([], client, continue_last=True):
                    full_response = response
                    message_placeholder.markdown(response)
            # Update the last assistant message in the conversation history
            if (
                st.session_state.messages
                and st.session_state.messages[-1]["role"] == "assistant"
            ):
                st.session_state.messages[-1]["content"] = full_response
            else:
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )


if __name__ == "__main__":
    main()
