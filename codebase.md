# pyproject.toml

```toml
[tool.poetry]
name = "claude-chat-ui"
version = "0.1.0"
description = ""
authors = ["Jared Wuliger <hello@jaredwuliger.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
streamlit = "^1.38.0"
anthropic = "^0.34.1"
pillow = "^10.4.0"
httpx = "^0.27.2"
google-auth = "^2.34.0"
google-auth-oauthlib = "^1.2.1"
google-auth-httplib2 = "^0.2.0"
google-cloud-aiplatform = "^1.64.0"
black = "^24.8.0"
pypdf2 = "^3.0.1"


[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

```

# main.py

```py
# main.py

import logging
import random
import uuid

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
        # Process newly uploaded files
        attached_files = []
        message_id = str(uuid.uuid4())  # Generate a unique ID for the message
        if uploaded_files:
            attached_files = render_file_upload(uploaded_files)
            # Store files in session state with the message ID
            st.session_state.files[message_id] = attached_files
            # Reset the file uploader key
            st.session_state.file_uploader_key = random.randint(0, 1000000)

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
        st.session_state.files = {}

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


if __name__ == "__main__":
    main()

```

# config.py

```py
# config.py
import logging

# config.py
PROJECT_ID: str = "speak-sense"  # Google Cloud project ID
LOCATION: str = "us-east5"  # Google Cloud location
MODEL: str = "claude-3-5-sonnet@20240620"  # Claude model name
MAX_TOKENS: int = 8192  # Maximum number of tokens for Claude's responses
APP_TITLE: str = "Chat with Claude"  # Title of the Streamlit application
TEMPERATURE: int = 0.7

# Configure logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

```

# utils\__init__.py

```py
# utils/__init__.py
from .claude_client import get_claude_client
from .message_handler import process_message

__all__ = ["get_claude_client", "process_message"]

```

# utils\session.py

```py
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

```

# utils\message_handler.py

```py
# utils/message_handler.py

from __future__ import annotations  # Enable postponed evaluation of annotations

import logging
from typing import Any, Dict, Generator, List, Optional

import streamlit as st
from anthropic import AnthropicVertex, APIError

import config
from utils.session import initialize_session_state

logger = logging.getLogger(__name__)


def process_message(
    messages: List[Dict[str, Any]],
    client: AnthropicVertex,
    continue_last: bool = False,
    user_prompt: str = "",
    system_prompt: str = "",
    message_id: Optional[str] = None,  # Add message_id parameter
) -> Generator[str, None, None]:
    # Use the existing messages without modification
    current_messages = messages.copy()

    # Ensure message alternation
    if current_messages and current_messages[-1]["role"] == "user":
        current_messages.pop()

    # Add the new message
    if continue_last:
        if current_messages and current_messages[-1]["role"] == "assistant":
            current_messages.append(
                {"role": "user", "content": "Please continue your previous response."}
            )
    else:
        # Include file content if it's the initial message with attachments
        if message_id and message_id in st.session_state.files:
            attached_files = st.session_state.files[message_id]
            for file in attached_files:
                user_prompt += f"\n\nAttached File: {file['name']} ({file['type']})\n\`\`\`\n{file['content']}\n\`\`\`"

        current_messages.append({"role": "user", "content": user_prompt})

    full_response = ""
    try:
        with client.messages.stream(
            max_tokens=config.MAX_TOKENS,
            messages=current_messages,
            model=config.MODEL,
            temperature=config.TEMPERATURE,
            system=system_prompt,
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield full_response

        # Check if max tokens were reached
        st.session_state.max_tokens_reached = (
            len(full_response.split()) >= config.MAX_TOKENS
        )
        if st.session_state.max_tokens_reached:
            st.warning(
                "Claude's response has reached the maximum token limit. You can click 'Continue Response' to get more."
            )

    except APIError as e:
        logger.exception("Claude API error: %s", e)
        st.error(
            f"An error occurred while communicating with Claude: {e.message}. Please try again later or contact support."
        )
        return None
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        st.error(f"An unexpected error occurred: {e}. Please try again later.")
        return None

    return full_response


def add_message_to_history(
    role: str, content: str, message_id: Optional[str] = None
) -> None:
    st.session_state.messages.append(
        {"role": role, "content": content, "message_id": message_id}
    )


def clear_conversation() -> None:
    """Clears the conversation history and resets the session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()
    # Clear the file uploader state
    st.session_state.pop("file_uploader", None)


def get_conversation_history() -> List[Dict[str, Any]]:
    """
    Gets the conversation history from the session state.

    Returns:
        A list of message dictionaries representing the conversation history.
    """
    return st.session_state.messages

```

# utils\file_handler.py

```py
# utils/file_handler.py

import base64
import io
import logging
import os
from typing import Any, Dict, List, Union

import PyPDF2
import streamlit as st
from PIL import Image

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
CODE_EXTENSIONS = [
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
]


def process_file(file: st.runtime.uploaded_file_manager.UploadedFile) -> Dict[str, Any]:
    """
    Processes an uploaded file and returns its content and metadata.

    Args:
        file: The uploaded file object.

    Returns:
        A dictionary containing file metadata and content, or an error message.
        Example:
        {
            "name": "myfile.py",
            "type": "code",
            "content": "print('Hello, world!')",
            "language": "python"
        }
        or
        {
            "error": "File myfile.txt exceeds the maximum size limit of 5 MB"
        }
    """
    if file.size > MAX_FILE_SIZE:
        return {"error": f"File {file.name} exceeds the maximum size limit of 5 MB"}

    file_ext = os.path.splitext(file.name)[1].lower()

    if file_ext in CODE_EXTENSIONS or file_ext == ".txt":
        try:
            content = file.read().decode("utf-8")
            return {
                "name": file.name,
                "type": "code" if file_ext in CODE_EXTENSIONS else "text",
                "content": content,
                "language": file_ext[1:] if file_ext in CODE_EXTENSIONS else "text",
            }
        except UnicodeDecodeError as e:
            logger.exception("Error decoding file: %s", e)
            return {
                "error": f"Error decoding file {file.name}. Please ensure it's in a valid UTF-8 encoding."
            }
        except Exception as e:
            logger.exception("Error processing file: %s", e)
            return {"error": f"Error processing file {file.name}: {str(e)}"}
    elif file_ext in [".jpg", ".jpeg", ".png"]:
        try:
            img = Image.open(file)
            img = img.convert("RGB")  # Convert to RGB mode
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {"name": file.name, "type": "image", "content": img_str}
        except Image.UnidentifiedImageError as e:
            logger.exception("Error processing image file: %s", e)
            return {
                "error": f"Error processing image file {file.name}. Please ensure it's a valid image format (JPG, JPEG, or PNG)."
            }
        except Exception as e:
            logger.exception("Error processing image file: %s", e)
            return {"error": f"Error processing image file {file.name}: {str(e)}"}
    elif file_ext == ".md":  # Handle markdown files
        try:
            content = file.read().decode("utf-8")
            return {
                "name": file.name,
                "type": "markdown",
                "content": content,
            }
        except UnicodeDecodeError as e:
            logger.exception("Error decoding markdown file: %s", e)
            return {
                "error": f"Error decoding markdown file {file.name}. Please ensure it's in a valid UTF-8 encoding."
            }
        except Exception as e:
            logger.exception("Error processing markdown file: %s", e)
            return {"error": f"Error processing markdown file {file.name}: {str(e)}"}
    elif file_ext == ".pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n\n"

            if not text_content.strip():
                return {
                    "error": f"No readable text content found in PDF file {file.name}"
                }

            return {
                "name": file.name,
                "type": "pdf",
                "content": text_content.strip(),
            }
        except Exception as e:
            logger.exception("Error processing PDF file: %s", e)
            return {"error": f"Error processing PDF file {file.name}: {str(e)}"}
    else:
        return {"error": f"Unsupported file type: {file_ext}"}


def process_files(
    files: List[st.runtime.uploaded_file_manager.UploadedFile],
) -> List[Dict[str, Any]]:
    """
    Processes a list of uploaded files.

    Args:
        files: A list of uploaded file objects.

    Returns:
        A list of dictionaries containing file metadata and content, or error messages.
    """
    return [process_file(file) for file in files]


def get_file_preview(file: Dict[str, Any]) -> str:
    """
    Generates a preview for a file.

    Args:
        file: A dictionary containing file metadata and content.

    Returns:
        A string representation of the file preview.
    """
    if file["type"] == "code" or file["type"] == "text":
        preview = (
            file["content"][:100] + "..."
            if len(file["content"]) > 100
            else file["content"]
        )
        return f"\`\`\`{file.get('language', 'text')}\n{preview}\n\`\`\`"
    elif file["type"] == "image":
        return f"[Image Preview for {file['name']}]"
    elif file["type"] == "markdown":
        preview = (
            file["content"][:100] + "..."
            if len(file["content"]) > 100
            else file["content"]
        )
        return f"\`\`\`markdown\n{preview}\n\`\`\`"
    elif file["type"] == "pdf":
        preview = (
            file["content"][:100] + "..."
            if len(file["content"]) > 100
            else file["content"]
        )
        return f"PDF Content Preview:\n{preview}"
    else:
        return "Preview not available"


def format_file_for_message(file: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Formats a file for inclusion in a message to Claude.

    Args:
        file: A dictionary containing file metadata and content.

    Returns:
        A list of content items formatted for Claude's message structure.
    """
    if file["type"] == "code" or file["type"] == "text":
        return [
            {
                "type": "text",
                "text": f"\`\`\`{file.get('language', 'text')}\n{file['content']}\n\`\`\`\nFile: {file['name']}",
            }
        ]
    elif file["type"] == "image":
        return [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": file["content"],
                },
            },
            {"type": "text", "text": f"Image file: {file['name']}"},
        ]
    elif file["type"] == "markdown":
        return [
            {
                "type": "text",
                "text": f"\`\`\`markdown\n{file['content']}\n\`\`\`\nFile: {file['name']}",
            }
        ]
    elif file["type"] == "pdf":
        return [
            {
                "type": "text",
                "text": f"PDF file: {file['name']}\n\nContent:\n\n{file['content']}",
            }
        ]
    else:
        return [{"type": "text", "text": f"Unsupported file type: {file['name']}"}]

```

# utils\claude_client.py

```py
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

```

# ui\__init__.py

```py
# ui/__init__.py
from .chat_interface import render_chat_interface
from .file_upload import render_file_upload

__all__ = ["render_chat_interface", "render_file_upload"]

```

# ui\file_upload.py

```py
# ui/file_upload.py

from typing import Any, Dict, List

import streamlit as st

from utils.file_handler import process_file


def render_file_upload(
    uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile],
) -> List[Dict[str, Any]]:
    """
    Processes uploaded files and returns a list of processed file data.

    Args:
        uploaded_files: A list of uploaded file objects.

    Returns:
        A list of dictionaries containing processed file data.
    """
    processed_files = []

    if uploaded_files:
        for uploaded_file in uploaded_files:
            processed_file = process_file(uploaded_file)
            if "error" not in processed_file:
                processed_files.append(processed_file)
                st.success(f"File '{uploaded_file.name}' attached.")
            else:
                st.error(
                    f"Error processing file '{uploaded_file.name}': {processed_file['error']}"
                )

        # Clear the uploaded_files list after processing
        uploaded_files = []

    return processed_files


def get_file_preview(file: Dict[str, Any]) -> str:
    """
    Generates a preview for a file.

    Args:
        file: A dictionary containing file metadata and content.

    Returns:
        A string representation of the file preview.
    """
    if file["type"] == "code" or file["type"] == "text":
        preview = (
            file["content"][:100] + "..."
            if len(file["content"]) > 100
            else file["content"]
        )
        return f"\`\`\`{file.get('language', 'text')}\n{preview}\n\`\`\`"
    elif file["type"] == "image":
        return f"[Image Preview for {file['name']}]"
    elif file["type"] == "markdown":
        preview = (
            file["content"][:100] + "..."
            if len(file["content"]) > 100
            else file["content"]
        )
        return f"\`\`\`markdown\n{preview}\n\`\`\`"
    elif file["type"] == "pdf":
        preview = (
            file["content"][:100] + "..."
            if len(file["content"]) > 100
            else file["content"]
        )
        return f"PDF Content Preview:\n{preview}"
    else:
        return "Preview not available"


def display_file_previews(files: List[Dict[str, Any]]) -> None:
    """
    Displays previews for uploaded files in the Streamlit UI.

    Args:
        files: A list of dictionaries containing file metadata and content.
    """
    if files:
        st.write("Attached files:")
        for file in files:
            with st.expander(f"{file['name']} ({file['type']})"):
                st.code(get_file_preview(file), language=file.get("language", "text"))

```

# ui\chat_interface.py

```py
from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import Optional

import streamlit as st
from anthropic import AnthropicVertex

from utils import process_message


def render_chat_interface(client: AnthropicVertex) -> None:
    """
    Renders the chat interface in the Streamlit UI.

    This function handles the display of the chat history, user input,
    and processing of messages using the Claude AI model.

    Args:
        client: The AnthropicVertex client instance for interacting with Claude.
    """
    # Chat message area
    chat_container = st.container()

    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                """
                <div class="chat-icon-container">
                    <i class="fas fa-comments chat-icon"></i>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Display conversation history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # Input for user message
    user_input: Optional[str] = st.chat_input("Type your message here...")

    if user_input:
        # Check if there's only one file attached
        if (
            st.session_state.attached_files
            and len(st.session_state.attached_files) == 1
        ):
            file = st.session_state.attached_files[0]
            # Include file content in the message
            user_input += f"\n\nAttached file: {file.name}\n\`\`\`\n{file.read().decode('utf-8')}\n\`\`\`"
            # Clear attached files after including it in the message
            st.session_state.attached_files = []

        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Process message and get Claude's response
        try:
            response: Optional[str] = process_message(
                [{"type": "text", "text": user_input}], client
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return

        # Display Claude's response and add to history if successful
        if response:
            # Only render the new assistant message if it's not already displayed
            if (
                st.session_state.messages[-1]["role"] != "assistant"
                or st.session_state.messages[-1]["content"] != response
            ):
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

    # Continue button (only shown when max tokens were reached)
    if st.session_state.get("max_tokens_reached", False):
        if st.button("Continue Response"):
            st.session_state.max_tokens_reached = False
            try:
                process_message([], client, continue_last=True)
            except Exception as e:
                st.error(f"An error occurred: {e}")

```

# styles\main.css

```css
/* styles/main.css */
body {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

.stApp {
    background-color: #1e1e1e;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-radius: 5px;
    border: 1px solid #3d3d3d;
}

.stChatMessage {
    background-color: #2d2d2d;
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 10px;
}

.stChatMessage[data-role='user'] {
    background-color: #3a3a3a;
}

.stButton > button {
    background-color: #10a37f;
    color: #ffffff;
    border-radius: 5px;
    border: none;
    padding: 5px 10px;
    transition: background-color 0.3s ease;
}

.stButton > button:hover {
    background-color: #1a7f64;
}

/* Chat input styles */
.stChatInputContainer {
    padding-top: 2rem;
    padding-bottom: 2rem;
    margin-bottom: 2rem;
}

textarea {
    min-height: 100px !important;
}

.stChatInputContainer textarea {
    min-height: 60px !important;
    font-size: 16px !important;
}

.stChatInput {
    margin-top: 10px;
    margin-bottom: -30px;
}

/* Chat icon styles */
.chat-icon-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 200px;
}

.chat-icon {
    font-size: 64px;
    color: #10a37f;
}

/* File uploader styles */
.stFileUploader > div > button {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
}

/* Error and warning styles */
.stAlert {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
}

```

