# utils/session.py

import random  # Import random for generating random keys

import streamlit as st


def initialize_session_state() -> None:
    """Initializes the Streamlit session state with necessary variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "attached_files" not in st.session_state:
        st.session_state.attached_files = []
    if "last_message_content" not in st.session_state:
        st.session_state.last_message_content = None
    if "max_tokens_reached" not in st.session_state:
        st.session_state.max_tokens_reached = False
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = ""
    if "files" not in st.session_state:  # Initialize files dictionary
        st.session_state.files = {}
    if "file_uploader_key" not in st.session_state:  # Initialize file_uploader_key
        st.session_state.file_uploader_key = random.randint(0, 1000000)


def reset_conversation() -> None:
    """Resets the conversation state."""
    st.session_state.messages = []
    st.session_state.attached_files = []
    st.session_state.last_message_content = None
    st.session_state.max_tokens_reached = False
    st.session_state.files = {}  # Clear the files dictionary
    st.session_state.file_uploader_key = random.randint(
        0, 1000000
    )  # Reset the file uploader key
    # Clear the file uploader state
    st.session_state.pop("file_uploader", None)
