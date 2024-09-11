# Chat with Claude (Google Vertex AI API)

Chat with Claude is a Streamlit-based web application that allows users to interact with Claude, an AI assistant powered by Anthropic's Claude 3.5 Sonnet model. The application provides a user-friendly interface for chatting with Claude, uploading files for analysis, and maintaining conversation history.

## Features

-   Interactive chat interface with Claude 3.5 Sonnet
-   File upload functionality (supports various file types including text, code, images, PDFs, and more)
-   Conversation history management
-   System prompt customization
-   Dark mode UI

## Requirements

-   Python 3.11 or higher
-   Google Cloud Platform account with Vertex AI API enable
-   Anthropic API access

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/your-username/chat-with-claude.git
    cd chat-with-claude
    ```

2. Install dependencies using Poetry:

    ```
    poetry install
    ```

3. Set up Google Cloud credentials:
    - Create a service account and download the JSON key file
    - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your JSON key file
4. Configure the application:
    - Update the `config.py` file with your Google Cloud Project ID and other settings

## Usage

To run the application, use the following command:

```
poetry run streamlit run main.py
```

The application will start, and you can access it through your web browser at `http://localhost:8501`.

Usage Examples:

1. Starting a conversation:
    - Type your message in the chat input box at the bottom of the page and press Enter or click the send button.
    - Claude will respond to your message using the chat interface.
2. Uploading a file:
    - Click on the "Attach a file" button to upload a file (supported types include .txt, .py, .js, .html, .css, .json, .jpg, .jpeg, .png, .md, .pdf, .xml).
    - Once uploaded, you can reference the file in your messages to Claude.
3. Customizing the system prompt:
    - Enter a custom system prompt in the "System Prompt (optional)" text area to guide Claude's behavior for the entire conversation.
4. Continuing a response:
    - If Claude's response is cut off due to token limits, a "Continue Response" button will appear. Click it to get the rest of the response.
5. Clearing the conversation:
    - Click the "Clear Conversation" button to start a new chat session.

Note: The application has a session expiry of 1 hour. After this time, the conversation will be automatically cleared.# Chat with Claude (Google Vertex AI API)

Chat with Claude is a Streamlit-based web application that allows users to interact with Claude, an AI assistant powered by Anthropic's Claude 3.5 Sonnet model. The application provides a user-friendly interface for chatting with Claude, uploading files for analysis, and maintaining conversation history.

## Features

-   Interactive chat interface with Claude 3.5 Sonnet
-   File upload functionality (supports various file types including text, code, images, PDFs, and more)
-   Conversation history management
-   System prompt customization
-   Dark mode UI

## Requirements

-   Python 3.11 or higher
-   Google Cloud Platform account with Vertex AI API enable
-   Anthropic API access

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/jwuliger/Google-Vertex-AI-Claude-API-Web-UI
    cd chat-with-claude
    ```

2. Install dependencies using Poetry:

    ```
    poetry install
    ```

3. Set up Google Cloud credentials:
    - Create a service account and download the JSON key file
    - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your JSON key file
4. Configure the application:
    - Update the `config.py` file with your Google Cloud Project ID and other settings

## Usage

To run the application, use the following command:

```
poetry run streamlit run main.py
```

The application will start, and you can access it through your web browser at `http://localhost:8501`.

Usage Examples:

1. Starting a conversation:
    - Type your message in the chat input box at the bottom of the page and press Enter or click the send button.
    - Claude will respond to your message using the chat interface.
2. Uploading a file:
    - Click on the "Attach a file" button to upload a file (supported types include .txt, .py, .js, .html, .css, .json, .jpg, .jpeg, .png, .md, .pdf, .xml).
    - Once uploaded, you can reference the file in your messages to Claude.
3. Customizing the system prompt:
    - Enter a custom system prompt in the "System Prompt (optional)" text area to guide Claude's behavior for the entire conversation.
4. Continuing a response:
    - If Claude's response is cut off due to token limits, a "Continue Response" button will appear. Click it to get the rest of the response.
5. Clearing the conversation:
    - Click the "Clear Conversation" button to start a new chat session.

Note: The application has a session expiry of 1 hour. After this time, the conversation will be automatically cleared.
