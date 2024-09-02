# utils/session.py

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


def reset_conversation() -> None:
    """Resets the conversation state."""
    st.session_state.messages = []
    st.session_state.last_message_content = None
    st.session_state.max_tokens_reached = False
