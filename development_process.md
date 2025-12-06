# Development Process: Gemini Enterprise Connector Agent

## 1. Project Overview
The **Gemini Enterprise Connector Agent** is a specialized Google ADK (Agent Development Kit) agent designed to interface with a Google Cloud Discovery Engine Datastore. Its primary purpose is to allow users to search and converse with enterprise documents (specifically a Google Drive datastore) using natural language, leveraging the Gemini Conversational API.

## 2. Planning Phase
**Objective**: Create a robust agent that can authenticate securely and maintain conversational context while querying a specific enterprise datastore.

**Key Requirements**:
*   **Target Datastore**: `drive-files_1759434882635_google_drive` (Location: `global`).
*   **Authentication**: Must use secure OAuth2 patterns via ADK's `ToolContext` compatible with Google Workspace.
*   **Context**: Must support multi-turn conversations (not just single-shot search).

**Architecture Decisions**:
*   **Single Tool Design**: The agent relies on a primary tool, `search_datastore`, to handle all external data interaction.
*   **REST API vs. Client Library**: A decision was made to use the **Discovery Engine REST API** via the `requests` library. This provided more granular control over the `conversations` resource and session management compared to high-level client libraries.

## 3. Implementation Phase

### 3.1 Project Setup
*   **Dependency Management**: `uv` was selected for fast, reliable dependency resolution.
*   **Configuration**: Environment variables (`PROJECT_ID`, `location`, etc.) were externalized to `.env` to ensure security and flexibility.

### 3.2 Tool Development (`tool.py`)
The core logic resides in `tool.py`. Key implementation details include:

*   **Authentication Strategy**:
    *   Implemented **OAuth2** using ADK's `ToolContext`.
    *   **Credential Management**: The agent accesses the user's OAuth credentials from `tool_context`, ensuring secure, user-scoped access to the datastore.
    *   **State Persistence**: Both the OAuth token and the active `conversation_name` are stored in `tool_context.state` to maintain continuity across multiple interaction turns.

*   **Session Management**:
    *   Leveraged ADK's `ToolContext` to persist a `conversation_name` across tool calls.
    *   **Logic**:
        1.  Check `tool_context.state` for an existing conversation ID.
        2.  If found, use it to call the `:converse` endpoint.
        3.  If not found (or if the API returns 404), call the `conversations` endpoint to create a new session and cache the ID.

*   **Error Handling**:
    *   **403 Permission Denied**: Explicitly catches this to warn users about Consumer (Gmail) vs. Workspace account mismatches.
    *   **404 Not Found**: Automatically clears the invalid session ID and retries/prompts for a new session.

### 3.3 Agent Configuration (`agent.py`)
*   **Model**: Configured to use `gemini-2.5-flash` for speed and efficiency.
*   **Instructions**: System instructions were tuned to ensure the agent relies on the tool for answers and doesn't hallucinate information not found in the datastore.

## 4. Challenges & Solutions

| Challenge | Root Cause | Solution |
| :--- | :--- | :--- |
| **Authentication Failures** | Users trying to access Enterprise data with personal Gmail accounts. | Added specific error handling for 403 responses to guide users to switch to Workspace accounts. |
| **Session Persistence** | Conversations were restarting every turn. | Implemented caching of `conversation_name` in `ToolContext.state`. |
| **OAuth Testing** | Localhost redirects failing during OAuth flow testing. | Updated documentation to include the specific redirect URI `http://localhost:8000/dev-ui/`. |
| **API Quotas** | Hitting "Quota exceeded" on experimental models. | Switched default model to stable `gemini-2.5-flash` and implemented better error reporting. |

## 5. Testing & Validation
*   **Isolation Testing**: Created `test_tool_direct.py` to validate the `search_datastore` function independently of the agent runtime. This allowed for rapid iteration on API payloads and auth logic.
*   **Integration Testing**: Verified end-to-end functionality using `adk web`, ensuring the chat interface correctly displayed citations and maintained context across multiple turns.

## 6. Current Status
The agent is fully functional and documented.
*   **Documentation**: `GEMINI.md` and `README.md` provide complete setup and usage instructions.
*   **Codebase**: Clean separation of concerns between `agent.py` (definition) and `tool.py` (logic).
