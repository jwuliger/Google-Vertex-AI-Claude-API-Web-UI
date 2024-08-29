import streamlit as st


def initialize_session_state() -> None:
    """Initializes the Streamlit session state with necessary variables."""
    st.session_state.messages = []
    st.session_state.attached_files = []
    st.session_state.last_message_content = None
    st.session_state.max_tokens_reached = False
    st.session_state.system_prompt = ""
