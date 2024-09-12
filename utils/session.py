# utils/session.py

import random
import time
from typing import Any, Dict

import streamlit as st

import config


def initialize_session_state() -> None:
    """Initializes the Streamlit session state with necessary variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "message_ids" not in st.session_state:
        st.session_state.message_ids = []
    if "attached_files" not in st.session_state:
        st.session_state.attached_files = []
    if "last_message_content" not in st.session_state:
        st.session_state.last_message_content = None
    if "max_tokens_reached" not in st.session_state:
        st.session_state.max_tokens_reached = False
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = ""
    if "files" not in st.session_state:
        st.session_state.files = {}
    if "file_uploader_key" not in st.session_state:
        st.session_state.file_uploader_key = random.randint(0, 1000000)
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()


def reset_conversation() -> None:
    """Resets the conversation state."""
    st.session_state.messages = []
    st.session_state.message_ids = []
    st.session_state.attached_files = []
    st.session_state.last_message_content = None
    st.session_state.max_tokens_reached = False
    st.session_state.files = {}
    st.session_state.file_uploader_key = random.randint(0, 1000000)
    st.session_state.last_activity = time.time()
    # Clear the file uploader state
    st.session_state.pop("file_uploader", None)


def check_session_expiry() -> bool:
    """
    Checks if the current session has expired.

    Returns:
        bool: True if the session has expired, False otherwise.
    """
    if "last_activity" not in st.session_state:
        return False

    current_time = time.time()
    time_elapsed = current_time - st.session_state.last_activity
    return time_elapsed > config.SESSION_EXPIRY


def update_last_activity() -> None:
    """Updates the last activity timestamp for the current session."""
    st.session_state.last_activity = time.time()


def get_session_data() -> Dict[str, Any]:
    """
    Retrieves all relevant session data.

    Returns:
        Dict[str, Any]: A dictionary containing all session data.
    """
    return {
        "messages": st.session_state.messages,
        "message_ids": st.session_state.message_ids,
        "attached_files": st.session_state.attached_files,
        "last_message_content": st.session_state.last_message_content,
        "max_tokens_reached": st.session_state.max_tokens_reached,
        "system_prompt": st.session_state.system_prompt,
        "files": st.session_state.files,
        "last_activity": st.session_state.last_activity,
    }


def set_session_data(data: Dict[str, Any]) -> None:
    """
    Sets the session data from a dictionary.

    Args:
        data (Dict[str, Any]): A dictionary containing session data to be set.
    """
    for key, value in data.items():
        setattr(st.session_state, key, value)

    # Regenerate the file uploader key to ensure it's unique
    st.session_state.file_uploader_key = random.randint(0, 1000000)


def clear_file_data() -> None:
    """Clears all file-related data from the session state."""
    st.session_state.attached_files = []
    st.session_state.files = {}
    st.session_state.file_uploader_key = random.randint(0, 1000000)
    st.session_state.pop("file_uploader", None)
