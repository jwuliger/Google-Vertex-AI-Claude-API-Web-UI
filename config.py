# config.py
import logging

# config.py
PROJECT_ID: str = "speak-sense"  # Google Cloud project ID
LOCATION: str = "us-east5"  # Google Cloud location
MODEL: str = "claude-3-5-sonnet@20240620"  # Claude model name
MAX_TOKENS: int = 8192  # Maximum number of tokens for Claude's responses
APP_TITLE: str = "Chat with Claude"  # Title of the Streamlit application

# Configure logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
