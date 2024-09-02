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

    return processed_files


def get_file_preview(file: Dict[str, Any]) -> str:
    """
    Generates a preview for a file.

    Args:
        file: A dictionary containing file metadata and content.

    Returns:
        A string representation of the file preview.
    """
    if file["type"] == "code":
        preview = (
            file["content"][:100] + "..."
            if len(file["content"]) > 100
            else file["content"]
        )
        return f"\`\`\`{file['language']}\n{preview}\n\`\`\`"
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
