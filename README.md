# Google Vertex AI Claude API Web UI

A streamlined web interface for interacting with Claude AI through Google Vertex AI, built with Streamlit and Python.

## Overview

This project provides a user-friendly web application that allows users to engage in conversations with Claude, an AI model by Anthropic, using Google Vertex AI. The application features a chat interface, file upload capabilities, and dynamic response handling.

## Features

-   Real-time chat interface with Claude AI
-   File upload support for code, images, and markdown files
-   Syntax highlighting for code snippets
-   Continuation of responses when max token limit is reached
-   Customizable system prompts
-   Dark mode UI for comfortable viewing

## Prerequisites

-   Python 3.7+
-   Google Cloud account with Vertex AI API enabled
-   Poetry for dependency management

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/jwuliger/google-vertex-ai-claude-web-ui.git
    cd google-vertex-ai-claude-web-ui
    ```

2. Install dependencies using Poetry:

    ```
    poetry install
    ```

3. Set up Google Cloud credentials:
    - Create a service account and download the JSON key file
    - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your JSON key file

## Configuration

Update the `config.py` file with your specific settings:

-   `PROJECT_ID`: Your Google Cloud project ID
-   `LOCATION`: The Google Cloud region for Vertex AI
-   `MODEL`: The Claude model version to use
-   `MAX_TOKENS`: Maximum number of tokens for Claude's responses
-   `APP_TITLE`: The title of your Streamlit application

## Usage

Run the Streamlit app using Poetry:

```
poetry run streamlit run main.py
```

Navigate to the provided local URL in your web browser to start chatting with Claude.

## Project Structure

-   `main.py`: Entry point of the application
-   `config.py`: Configuration settings
-   `utils/`: Utility functions for Claude client, file handling, and message processing
-   `ui/`: User interface components
-   `styles/`: CSS styling for the web application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](https://www.notion.so/LICENSE) file for details.

## Acknowledgements

-   [Anthropic](https://www.anthropic.com/) for the Claude AI model
-   [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai) for hosting the model
-   [Streamlit](https://streamlit.io/) for the web application framework

## Support

For support, please open an issue in the GitHub repository or contact the project maintainers.
