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

project = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

search_connection = project.connections.get(os.environ["SEARCH_CONNECTION_NAME"])

# --- Policy Agent: gpt-4o-mini + RAG (hosted search tool needs GPT-family) ---
search_tool = AzureAISearchTool(
    azure_ai_search=AzureAISearchToolResource(
        indexes=[
            AISearchIndexResource(
                project_connection_id=search_connection.id,
                index_name=os.environ["SEARCH_INDEX_NAME"],
                query_type=AzureAISearchQueryType.SIMPLE,
            )
        ]
    )
)

policy_agent = project.agents.create_version(
    agent_name="policy-agent",
    definition=PromptAgentDefinition(
        model=os.environ["MODEL_DEPLOYMENT"],
        instructions=(
            "You are the Contoso Basics policy specialist. Answer only questions about "
            "returns, shipping, and warranty policy, grounded in the connected knowledge base. "
            "If asked about anything else (like order status), say that's handled by another "
            "specialist and you can't help with it."
        ),
        tools=[search_tool],
    ),
)
print(f"Created: {policy_agent.name} v{policy_agent.version}")

# --- Order Agent: Phi-4-mini-instruct + function calling ---
lookup_order_tool = FunctionTool(
    name="lookup_order_status",
    description="Look up the shipping status of a Contoso Basics order by order ID.",
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "e.g. ORD-1042"}},
        "required": ["order_id"],
    },
)

order_agent = project.agents.create_version(
    agent_name="order-agent",
    definition=PromptAgentDefinition(
        model=os.environ["MODEL_DEPLOYMENT"],
        instructions=(
            "You are the Contoso Basics order specialist. Only handle questions about a "
            "specific order's status using the lookup_order_status tool. If asked about "
            "policy questions (returns, shipping rules, warranty), say that's handled by "
            "another specialist."
        ),
        tools=[lookup_order_tool],
    ),
)
print(f"Created: {order_agent.name} v{order_agent.version}")
