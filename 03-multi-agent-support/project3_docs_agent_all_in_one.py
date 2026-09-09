import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool

load_dotenv()

AGENT_NAME = "docs-agent"

project = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
openai_client = project.get_openai_client()


def ensure_agent_exists():
    """Create docs-agent if it doesn't already exist; reuse it if it does."""
    try:
        project.agents.get(agent_name=AGENT_NAME)
        print(f"Using existing agent: {AGENT_NAME}")
    except Exception:
        print(f"Creating agent: {AGENT_NAME}")
        learn_mcp_tool = MCPTool(
            server_label="microsoft_learn",
            server_url="https://learn.microsoft.com/api/mcp",
        )
        agent = project.agents.create_version(
            agent_name=AGENT_NAME,
            definition=PromptAgentDefinition(
                model=os.environ["MODEL_DEPLOYMENT"],
                instructions=(
                    "You answer questions by searching Microsoft Learn documentation "
                    "using the connected MCP tool. Summarize what you find concisely."
                ),
                tools=[learn_mcp_tool],
            ),
        )
        print(f"Created: {agent.name} v{agent.version}")


def ask_docs_agent(question: str) -> str:
    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}},
        input=question,
    )
    return response.output_text


if __name__ == "__main__":
    ensure_agent_exists()
    print("\nDocs Agent (MCP-powered) — type 'exit' to quit.\n")
    while True:
        question = input("You: ")
        if question.strip().lower() == "exit":
            print("Goodbye!")
            break
        answer = ask_docs_agent(question)
        print(f"Agent: {answer}\n")
