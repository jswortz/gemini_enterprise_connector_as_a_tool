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

PROJECT_ID = "679926387543" # Keep for reference or remove if unused
# LOCATION = "global" # Unused for Jira
# DATASTORE_ID = "jira_1759440079662_issue" # Unused for Jira
# COLLECTION_ID = "jira_1759440079662" # Unused for Jira

def perform_jira_action(query: str, tool_context: ToolContext) -> str:
    """
    Performs an action in Jira using the authenticated user's credentials.

    Args:
        query: The action to perform or query to run.
        tool_context: The tool context provided by ADK.

    Returns:
        A string summary of the action result.
    """
    print(f"DEBUG: Entering perform_jira_action with query: {query}")

    TOKEN_CACHE_KEY = "jira_oauth_token"
    # Standard Jira Cloud scopes
    SCOPES = ["read:jira-work", "write:jira-work", "offline_access"]

    # Define the AuthConfig for Jira OAuth2
    auth_config = AuthConfig(
        auth_scheme=OAuth2(
            type=SecuritySchemeType.oauth2,
            flows=OAuthFlows(
                authorizationCode=OAuthFlowAuthorizationCode(
                    authorizationUrl="https://auth.atlassian.com/authorize",
                    tokenUrl="https://auth.atlassian.com/oauth/token",
                    scopes={
                        "read:jira-work": "Read Jira data",
                        "write:jira-work": "Write Jira data",
                        "offline_access": "Access data offline"
                    }
                )
            )
        ),
        raw_auth_credential=AuthCredential(
            auth_type=AuthCredentialTypes.OAUTH2,
            oauth2=OAuth2Auth(
                client_id=os.getenv("OAUTH_CLIENT_ID"),
                client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
                # Jira requires audience for offline_access sometimes, but usually just scopes are enough.
                # Note: Atlassian might require 'audience' parameter in the authorization URL for some flows,
                # but standard OAuth2 flow usually handles it via scopes.
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
                # Note: Google's Credentials.refresh might send parameters specific to Google.
                # If this fails for Jira, we might need a custom refresh logic.
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
                token_uri="https://auth.atlassian.com/oauth/token",
                client_id=os.getenv("OAUTH_CLIENT_ID"),
                client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
                scopes=SCOPES,
            )
            tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json())

    # Step 3: Initiate Authentication Request
    if not creds:
        tool_context.request_credential(auth_config)
        return "Please authenticate to access Jira."

    # Step 4: Make Authenticated API Call
    try:
        # Ensure token is fresh
        if not creds.valid:
             creds.refresh(Request())
             tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json())

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Placeholder for Jira API call
        # To make a real call, we need the cloudid.
        # Usually, we first call https://api.atlassian.com/oauth/token/accessible-resources
        
        resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
        print(f"DEBUG: Fetching accessible resources from {resources_url}")
        resources_response = requests.get(resources_url, headers=headers)
        resources_response.raise_for_status()
        resources = resources_response.json()
        
        if not resources:
            return "No accessible Jira resources found."
            
        # Use the first available resource
        cloud_id = resources[0]['id']
        site_name = resources[0]['name']
        
        # Example: Get Myself
        myself_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself"
        print(f"DEBUG: Fetching myself from {myself_url}")
        myself_response = requests.get(myself_url, headers=headers)
        myself_response.raise_for_status()
        myself_data = myself_response.json()
        
        display_name = myself_data.get("displayName", "Unknown User")
        
        return f"Successfully authenticated with Jira site '{site_name}'. User: {display_name}. Query received: {query}"

    except requests.exceptions.RequestException as e:
        error_msg = f"API Request Error: {str(e)}"
        if e.response is not None:
             error_msg += f"\nResponse: {e.response.text}"
        return error_msg
    except Exception as e:
        return f"Error interacting with Jira: {str(e)}"
