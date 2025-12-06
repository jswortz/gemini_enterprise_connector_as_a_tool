
import os
from google.adk.apps import App
from gemini_enterprise_connector_agent_sample.agent import root_agent
from vertexai.preview import reasoning_engines
import vertexai

# Initialize Vertex AI
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")
staging_bucket = os.getenv("STAGING_BUCKET", "gs://wortz-project-352116-bucket") # Replace with your bucket if needed

vertexai.init(project=project_id, location=location, staging_bucket=staging_bucket)

# Wrap the agent in an App if it's not already (ADK agents usually need to be Apps for deployment if using AdkApp?)
# The doc says "To enable OpenTelemetry for AdkApp..."
# Let's check if we can deploy the agent directly or if we need AdkApp.
# reasoning_engines.ReasoningEngine.create(agent=...)
# If we pass an ADK agent, does it automatically wrap it?
# The doc says "AdkApp" in the context of telemetry.
# Let's try to use AdkApp from reasoning_engines if available or just pass the agent.
# Actually, reasoning_engines.AdkApp is a class available in vertexai.preview.reasoning_engines.
# But we might need to create the agent locally first.

# Create the agent locally
# root_agent is already created in agent.py

# Define requirements
requirements = [
    "google-adk>=1.15.1",
    "google-cloud-discoveryengine>=0.15.0",
    "python-dotenv>=1.0.0",
    "fastapi",
    "uvicorn",
    "google-auth",
    "google-auth-oauthlib",
    "google-auth-httplib2",
    "requests",
]

# Define environment variables for telemetry
env_vars = {
    "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
    "PROJECT_ID": project_id,
    "LOCATION": location,
    "DATASTORE_ID": "drive-files_1759434882635_google_drive", # Hardcoded as per previous steps
}

print("Deploying agent to Vertex AI Agent Engine...")

try:
    remote_agent = reasoning_engines.ReasoningEngine.create(
        reasoning_engines.AdkApp(
            agent=root_agent,
            enable_tracing=True,
            env_vars=env_vars,
        ),
        requirements=requirements,
        display_name="Gemini Enterprise Tool Agent",
        description="Agent that searches Gemini Enterprise Datastore",
    )
    print(f"Agent deployed successfully: {remote_agent}")
    print(f"Resource Name: {remote_agent.resource_name}")
except Exception as e:
    print(f"Deployment failed: {e}")
