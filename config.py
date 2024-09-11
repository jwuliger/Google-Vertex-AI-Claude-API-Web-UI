# config.py
import logging

# Google Cloud configuration
PROJECT_ID: str = "speak-sense"
LOCATION: str = "us-east5"

# Claude model configuration
MODEL: str = "claude-3-5-sonnet@20240620"
MAX_TOKENS: int = 8192
TEMPERATURE: float = 0.7

# Application configuration
APP_TITLE: str = "Chat with Claude"
MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB

# File extensions
CODE_EXTENSIONS: tuple = (
    ".py",
    ".js",
    ".html",
    ".css",
    ".json",
    ".cpp",
    ".java",
    ".rb",
    ".php",
    ".swift",
    ".kt",
)

# Configure logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Development mode
DEBUG: bool = False

# Session management
SESSION_EXPIRY: int = 3600  # 1 hour default

# Performance
CACHE_TTL: int = 300  # 5 minutes default
