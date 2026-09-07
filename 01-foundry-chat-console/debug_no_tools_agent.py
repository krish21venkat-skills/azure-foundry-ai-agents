import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT = os.environ["FOUNDRY_DEPLOYMENT"]

project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())

# Create a bare-bones agent with NO tools, to isolate whether the search tool is the problem
agent = project.agents.create_version(
    agent_name="debug-agent-no-tools",
    definition=PromptAgentDefinition(
        model=MODEL_DEPLOYMENT,
        instructions="You are a helpful assistant.",
    ),
)
print(f"Created debug agent: {agent.name}, version {agent.version}")

openai_client = project.get_openai_client()
conversation = openai_client.conversations.create()

try:
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="What's your returns policy?",
    )
    print("SUCCESS")
    print(response.output_text)
except Exception as e:
    print("FAILED even with no tools:")
    print(e)
