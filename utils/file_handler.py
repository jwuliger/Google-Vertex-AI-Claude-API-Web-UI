# utils/file_handler.py

import base64
import io
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Union

import PyPDF2
import streamlit as st
from PIL import Image

from config import CODE_EXTENSIONS, MAX_FILE_SIZE

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""

    pass


@contextmanager
def safe_file_handler(file: st.runtime.uploaded_file_manager.UploadedFile):
    """
    Context manager for safe file handling.

    Args:
        file: The uploaded file object.

    Yields:
        The file object for processing.

    Raises:
        FileProcessingError: If there's an error during file processing.
    """
    try:
        yield file
    except Exception as e:
        logger.exception(f"Error processing file {file.name}: {str(e)}")
        raise FileProcessingError(f"Error processing file {file.name}: {str(e)}")
    finally:
        file.close()


def process_file(file: st.runtime.uploaded_file_manager.UploadedFile) -> Dict[str, Any]:
    """
    Processes an uploaded file and returns its content and metadata.

    Args:
        file: The uploaded file object.

    Returns:
        A dictionary containing file metadata and content, or an error message.

    Raises:
        FileProcessingError: If there's an error during file processing.
    """
    if file.size > MAX_FILE_SIZE:
        raise FileProcessingError(
            f"File {file.name} exceeds the maximum size limit of {MAX_FILE_SIZE/1024/1024:.2f} MB"
        )

    file_ext = os.path.splitext(file.name)[1].lower()

    with safe_file_handler(file) as safe_file:
        if file_ext in CODE_EXTENSIONS or file_ext in [".txt", ".xml"]:
            return process_text_file(safe_file, file_ext)
        elif file_ext in [".jpg", ".jpeg", ".png"]:
            return process_image_file(safe_file)
        elif file_ext == ".md":
            return process_markdown_file(safe_file)
        elif file_ext == ".pdf":
            return process_pdf_file(safe_file)
        else:
            raise FileProcessingError(f"Unsupported file type: {file_ext}")


def process_text_file(
    file: st.runtime.uploaded_file_manager.UploadedFile, file_ext: str
) -> Dict[str, Any]:
    """Process text and code files."""
    try:
        content = file.read().decode("utf-8")
        return {
            "name": file.name,
            "type": "code" if file_ext in CODE_EXTENSIONS else "text",
            "content": content,
            "language": file_ext[1:] if file_ext in CODE_EXTENSIONS else "text",
        }
    except UnicodeDecodeError as e:
        raise FileProcessingError(
            f"Error decoding file {file.name}. Please ensure it's in a valid UTF-8 encoding."
        )


def process_image_file(
    file: st.runtime.uploaded_file_manager.UploadedFile,
) -> Dict[str, Any]:
    """Process image files."""
    try:
        img = Image.open(file)
        img = img.convert("RGB")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return {"name": file.name, "type": "image", "content": img_str}
    except Image.UnidentifiedImageError as e:
        raise FileProcessingError(
            f"Error processing image file {file.name}. Please ensure it's a valid image format (JPG, JPEG, or PNG)."
        )


def process_markdown_file(
    file: st.runtime.uploaded_file_manager.UploadedFile,
) -> Dict[str, Any]:
    """Process markdown files."""
    try:
        content = file.read().decode("utf-8")
        return {
            "name": file.name,
            "type": "markdown",
            "content": content,
        }
    except UnicodeDecodeError as e:
        raise FileProcessingError(
            f"Error decoding markdown file {file.name}. Please ensure it's in a valid UTF-8 encoding."
        )


def process_pdf_file(
    file: st.runtime.uploaded_file_manager.UploadedFile,
) -> Dict[str, Any]:
    """Process PDF files."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text_content = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n\n"

        if not text_content.strip():
            raise FileProcessingError(
                f"No readable text content found in PDF file {file.name}"
            )

        return {
            "name": file.name,
            "type": "pdf",
            "content": text_content.strip(),
        }
    except Exception as e:
        raise FileProcessingError(f"Error processing PDF file {file.name}: {str(e)}")


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
    processed_files = []
    for file in files:
        try:
            processed_file = process_file(file)
            processed_files.append(processed_file)
        except FileProcessingError as e:
            logger.error(str(e))
            st.error(str(e))
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
