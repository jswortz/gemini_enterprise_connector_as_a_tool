from google.adk import Agent
from .tool import perform_jira_action
from dotenv import load_dotenv

load_dotenv()

root_agent = Agent(
    name="gemini_enterprise_tool_agent",
    tools=[perform_jira_action],
    model="gemini-2.5-flash", # Default model, can be overridden
    instruction="You are a helpful agent that can perform actions in Jira. Use the perform_jira_action tool to interact with Jira. You may need to ask the user to authenticate first.",
)
