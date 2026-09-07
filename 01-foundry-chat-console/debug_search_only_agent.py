import os
import azure.ai.projects as aip
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    AzureAISearchTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType,
)

load_dotenv()

print(f"azure-ai-projects version: {aip.__version__}\n")

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT = os.environ["FOUNDRY_GPT_DEPLOYMENT"]
SEARCH_CONNECTION_NAME = os.environ["SEARCH_CONNECTION_NAME"]
SEARCH_INDEX_NAME = os.environ["SEARCH_INDEX_NAME"]

project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())

search_connection = project.connections.get(SEARCH_CONNECTION_NAME)
print(f"Using index name: {SEARCH_INDEX_NAME!r} on connection id: {search_connection.id}\n")

search_tool = AzureAISearchTool(
    azure_ai_search=AzureAISearchToolResource(
        indexes=[
            AISearchIndexResource(
                project_connection_id=search_connection.id,
                index_name=SEARCH_INDEX_NAME,
                query_type=AzureAISearchQueryType.SIMPLE,
            )
        ]
    )
)

agent = project.agents.create_version(
    agent_name="debug-agent-search-only",
    definition=PromptAgentDefinition(
        model=MODEL_DEPLOYMENT,
        instructions="You are a helpful assistant. Use the connected knowledge base to answer questions.",
        tools=[search_tool],
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
    print("FAILED with search tool only:")
    print(e)
