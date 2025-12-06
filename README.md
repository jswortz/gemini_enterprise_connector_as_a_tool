# Gemini Enterprise Connector Agent Sample

This project implements a Google ADK agent that interfaces with a specific Google Cloud Discovery Engine Datastore. It demonstrates how to build an agent that can query enterprise data using the `google-cloud-discoveryengine` library and handle authentication via ADK's `ToolContext`.

## Features

- **Datastore Search**: specific tool `search_datastore` to query a configured Google Cloud Discovery Engine Datastore.
- **Authentication**: Implements OAuth2 flow using ADK's `ToolContext` to securely access the datastore on behalf of the user.
- **Gemini Integration**: Uses Gemini 2.5 model (configurable) as the underlying model.

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) for dependency management.
- A Google Cloud Project with the **Discovery Engine API** enabled.
- Access to the target Datastore (ID: `drive-files_1759434882635_google_drive`).

## Setup

1.  **Clone the repository** (if applicable).

2.    **Configure Environment Variables**:
    Copy `.env.template` to `.env` and fill in your values:


```bash
cp .env.template .env
```
    
Ensure your `.env` contains:
    
```env
PROJECT_ID=your-google-cloud-project-id
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE
```


3.  **Install Dependencies**:
    Use `uv` to sync the project dependencies:
    ```bash
    uv sync
    ```

4.  **Configure Redirect URI**:
    For testing with `flowName=GeneralOAuthFlow`, add this redirect URI:
    `http://localhost:8000/dev-ui/`

## Usage

### Running the Agent

To run the agent using the ADK CLI:

```bash
uv run adk run gemini_enterprise_connector_agent_sample
```

Once running, you can interact with the agent via the ADK interface (e.g., ADK Web or CLI chat). The agent will prompt you to authenticate if you haven't already.

### Testing the Tool Directly

You can also test the `search_datastore` tool directly using the provided test script:

```bash
uv run python test_tool_direct.py
```

## Project Structure

- `gemini_enterprise_connector_agent_sample/`: Contains the agent and tool code.
    - `agent.py`: Defines the ADK Agent and registers the tool.
    - `tool.py`: Implements the `search_datastore` function with Discovery Engine logic and OAuth handling.
- `test_tool_direct.py`: A script to test the tool logic in isolation.
- `GEMINI.md`: Quick reference documentation for the agent.

## Authentication Flow

The `search_datastore` tool checks for cached credentials in the `ToolContext`. If none are found or if they are invalid, it requests authentication from the user via the ADK client. This ensures secure access to the enterprise data.
