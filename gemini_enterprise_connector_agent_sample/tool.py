import os
from typing import List, Optional
import json
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.adk.tools.tool_context import ToolContext
from google.adk.auth.auth_tool import AuthConfig
from google.adk.auth.auth_schemes import SecuritySchemeType
from fastapi.openapi.models import OAuth2, OAuthFlows, OAuthFlowAuthorizationCode
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, OAuth2Auth
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = "679926387543"
LOCATION = "global"
DATASTORE_ID = "drive-files_1759434882635_google_drive"
COLLECTION_ID = "default_collection"

def search_datastore(query: str, tool_context: ToolContext) -> str:
    """
    Searches the Gemini Enterprise Datastore for documents matching the query using the Conversational API via REST.

    Args:
        query: The search query string.
        tool_context: The tool context provided by ADK.

    Returns:
        A string summary of the search results or conversation reply.
    """
    print(f"DEBUG: Entering search_datastore with query: {query}")
    if not PROJECT_ID:
        return "Error: PROJECT_ID not found in environment variables."

    TOKEN_CACHE_KEY = "datastore_oauth_token"
    CONVERSATION_CACHE_KEY = "gemini_conversation_name"
    SCOPES = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/discoveryengine.readwrite"]

    # Define the AuthConfig for Google OAuth2
    auth_config = AuthConfig(
        auth_scheme=OAuth2(
            type=SecuritySchemeType.oauth2,
            flows=OAuthFlows(
                authorizationCode=OAuthFlowAuthorizationCode(
                    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
                    tokenUrl="https://oauth2.googleapis.com/token",
                    scopes={"https://www.googleapis.com/auth/cloud-platform": "Access Cloud Platform", "https://www.googleapis.com/auth/discoveryengine.readwrite": "Access Discovery Engine"}
                )
            )
        ),
        raw_auth_credential=AuthCredential(
            auth_type=AuthCredentialTypes.OAUTH2,
            oauth2=OAuth2Auth(
                client_id=os.getenv("OAUTH_CLIENT_ID"),
                client_secret=os.getenv("OAUTH_CLIENT_SECRET")
            )
        )
    )

    creds = None
    cached_token_info = tool_context.state.get(TOKEN_CACHE_KEY)
    
    # Step 1: Check for Cached & Valid Credentials
    if cached_token_info:
        try:
            creds = Credentials.from_authorized_user_info(cached_token_info, SCOPES)
            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json())
            elif not creds.valid:
                creds = None
                tool_context.state[TOKEN_CACHE_KEY] = None
        except Exception as e:
            print(f"Error loading/refreshing cached creds: {e}")
            creds = None
            tool_context.state[TOKEN_CACHE_KEY] = None

    # Step 2: Check for Auth Response from Client
    if not creds:
        auth_response = tool_context.get_auth_response(auth_config)
        if auth_response and auth_response.oauth2:
            access_token = auth_response.oauth2.access_token
            refresh_token = auth_response.oauth2.refresh_token
            
            creds = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("OAUTH_CLIENT_ID"),
                client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
                scopes=SCOPES,
            )
            tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json())

    # Step 3: Initiate Authentication Request
    if not creds:
        tool_context.request_credential(auth_config)
        return "Please authenticate to access the datastore."

    # Step 4: Make Authenticated API Call (Conversational REST API)
    try:
        # Ensure token is fresh
        if not creds.valid:
             creds.refresh(Request())
             tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json())

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
            "x-goog-user-project": PROJECT_ID
        }

        # Check for existing conversation
        conversation_name = tool_context.state.get(CONVERSATION_CACHE_KEY)
        base_url = "https://discoveryengine.googleapis.com/v1beta"
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION_ID}/dataStores/{DATASTORE_ID}"

        if not conversation_name:
            # Create a new conversation
            create_url = f"{base_url}/{parent}/conversations"
            create_payload = {
                "userPseudoId": "admin@jwortz.altostrat.com"
            }
            print(f"DEBUG: Creating conversation at {create_url} with payload {create_payload}")
            create_response = requests.post(create_url, headers=headers, json=create_payload)
            create_response.raise_for_status()
            conversation_data = create_response.json()
            conversation_name = conversation_data.get("name")
            tool_context.state[CONVERSATION_CACHE_KEY] = conversation_name
            print(f"DEBUG: Created new conversation: {conversation_name}")
        else:
            print(f"DEBUG: Using existing conversation: {conversation_name}")

        # Converse
        converse_url = f"{base_url}/{conversation_name}:converse"
        serving_config = f"{parent}/servingConfigs/default_search"
        
        converse_payload = {
            "query": {"input": query},
            "servingConfig": serving_config
        }
        
        print(f"DEBUG: Conversing at {converse_url}")
        converse_response = requests.post(converse_url, headers=headers, json=converse_payload)
        
        # Handle 404 (Conversation not found/expired)
        if converse_response.status_code == 404:
             print("DEBUG: Conversation not found (404), clearing cache and retrying creation.")
             tool_context.state[CONVERSATION_CACHE_KEY] = None
             return "Session expired. Please try your request again to start a new session."
        
        # Handle 403 (Permission Denied / Consumer Account)
        if converse_response.status_code == 403:
             print(f"DEBUG: Permission Denied (403): {converse_response.text}")
             # Clear cache just in case, though it might be an account issue
             tool_context.state[CONVERSATION_CACHE_KEY] = None
             return f"Permission Denied: {converse_response.json().get('error', {}).get('message', 'Unknown error')}. Please ensure you are authenticated with a Workspace account, not a consumer (Gmail) account."

        converse_response.raise_for_status()
        response_data = converse_response.json()
        
        reply = response_data.get("reply", {}).get("reply", "No reply text found.")
        
        # Format output with citations if available
        output = f"Reply: {reply}\n"
        
        search_results = response_data.get("searchResults", [])
        if search_results:
            output += "\n--- Supporting Documents ---\n"
            for result in search_results:
                doc_data = result.get("document", {}).get("derivedStructData", {})
                title = doc_data.get("title", "No Title")
                link = doc_data.get("link", "No Link")
                snippets = doc_data.get("snippets", [])
                snippet = snippets[0].get("snippet", "") if snippets else ""
                output += f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n\n"

        return output

    except requests.exceptions.RequestException as e:
        error_msg = f"API Request Error: {str(e)}"
        if e.response is not None:
             error_msg += f"\nResponse: {e.response.text}"
        return error_msg
    except Exception as e:
        return f"Error conversing with datastore: {str(e)}"
