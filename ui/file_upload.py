# ui/file_upload.py

from typing import Any, Dict, List

import streamlit as st

from utils.file_handler import process_file


def render_file_upload() -> List[Dict[str, Any]]:
    """
    Renders the file upload component in the Streamlit UI and returns processed files.

    This function allows users to upload files, processes them, and returns a list of
    processed file data. Files are not stored in the session state, ensuring they are
    only associated with the current message.

    Returns:
        A list of dictionaries containing processed file data. Each dictionary
        contains metadata and content for a single uploaded file.
    """
    uploaded_files = st.file_uploader(
        "Attach a file",
        type=["txt", "py", "js", "html", "css", "json", "jpg", "jpeg", "png", "md"],
        accept_multiple_files=True,
        key="file_uploader",
    )

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
        return f"```{file['language']}\n{preview}\n```"
    elif file["type"] == "image":
        return f"[Image Preview for {file['name']}]"
    elif file["type"] == "markdown":
        preview = (
            file["content"][:100] + "..."
            if len(file["content"]) > 100
            else file["content"]
        )
        return f"```markdown\n{preview}\n```"
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
