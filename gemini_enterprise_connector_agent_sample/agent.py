from google.adk import Agent
from .tool import search_datastore
from dotenv import load_dotenv

load_dotenv()

root_agent = Agent(
    name="gemini_enterprise_tool_agent",
    tools=[search_datastore],
    model="gemini-2.5-flash", # Default model, can be overridden
    instruction="You are a helpful agent that can search a specific Gemini Enterprise Datastore. Use the search_datastore tool to find information. You may need to ask the user to authenticate first.",
)
