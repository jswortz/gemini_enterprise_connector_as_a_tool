# Gemini Enterprise Tool Agent

This agent interfaces with a Google Cloud Discovery Engine Datastore to search for enterprise documents.

## Configuration

The agent is pre-configured to connect to the following Datastore:

- **Datastore ID**: `drive-files_1759434882635_google_drive`
- **Location**: `global`
- **Collection**: `default_collection`

## Environment Variables

Ensure your `.env` file contains:

```env
PROJECT_ID=your-google-cloud-project-id
```

## OAuth Configuration

For testing with `flowName=GeneralOAuthFlow`, add this redirect URI:
`http://localhost:8000/dev-ui/`

## Tools

### `search_datastore`

- **Description**: Converses with the Gemini Enterprise Datastore using the Conversational API. It maintains a session (conversation) across calls to provide context-aware responses.
- **Authentication**: Uses ADK's `ToolContext` to handle OAuth2 authentication.
- **Output**: Returns a conversational reply along with supporting document citations.

## Development

- **Run Agent**: `uv run adk run gemini_enterprise_connector_agent_sample`
- **Test Tool**: `uv run python test_tool_direct.py`
