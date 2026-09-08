import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    FunctionTool,
    AzureAISearchTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType,
)

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
AGENT_NAME = os.environ["AGENT_NAME"]
MODEL_DEPLOYMENT = os.environ["MODEL_DEPLOYMENT"]  # gpt-4o for everything
SEARCH_CONNECTION_NAME = os.environ["SEARCH_CONNECTION_NAME"]
SEARCH_INDEX_NAME = os.environ["SEARCH_INDEX_NAME"]

project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())

# Resolve the search connection Foundry needs to reach your index
search_connection = project.connections.get(SEARCH_CONNECTION_NAME)

# --- Custom function tool definition ---
lookup_order_tool = FunctionTool(
    name="lookup_order_status",
    description="Look up the shipping status of a Contoso Basics order by order ID.",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The order ID, e.g. ORD-1042",
            }
        },
        "required": ["order_id"],
    },
)

# --- Knowledge connection tool (RAG) ---
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
    agent_name=AGENT_NAME,
    definition=PromptAgentDefinition(
        model=MODEL_DEPLOYMENT,
        instructions=(
            "You are the Contoso Basics store support agent. "
            "Use the connected knowledge base to answer questions about returns, "
            "shipping, and warranty policy — do not make up policy details. "
            "Use the lookup_order_status tool whenever the user asks about a "
            "specific order's status. Be concise and friendly."
        ),
        tools=[lookup_order_tool, search_tool],
    ),
)

print(f"Agent created: name={agent.name}, version={agent.version}")
