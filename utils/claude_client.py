# utils/claude_client.py
import logging

import streamlit as st
from anthropic import AnthropicVertex
from google.auth import default
from google.auth.transport.requests import Request

import config

logger = logging.getLogger(__name__)


@st.cache_resource
def get_claude_client():
    """Initialize and return an AnthropicVertex client."""
    try:
        credentials, _ = default()
        if credentials.expired:
            credentials.refresh(Request())
        return AnthropicVertex(
            region=config.LOCATION,
            project_id=config.PROJECT_ID,
            credentials=credentials,
        )
    except Exception as e:
        logger.exception("Error initializing Claude client: %s", e)
        raise RuntimeError(
            "Failed to initialize Claude client. Please check your Google Cloud credentials and configuration."
        ) from e
