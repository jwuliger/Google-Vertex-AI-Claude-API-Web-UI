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
