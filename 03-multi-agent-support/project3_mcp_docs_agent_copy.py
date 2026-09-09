import asyncio
import os
from dotenv import load_dotenv
from azure.identity.aio import AzureCliCredential
from agent_framework import ChatAgent, MCPStreamableHTTPTool
from agent_framework.azure import AzureAIAgentClient

load_dotenv()

os.environ["AZURE_AI_PROJECT_ENDPOINT"] = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"] = os.environ["MODEL_DEPLOYMENT"]


async def main():
    async with (
        AzureCliCredential() as credential,
        MCPStreamableHTTPTool(
            name="Microsoft Learn MCP",
            url="https://learn.microsoft.com/api/mcp",
        ) as mcp_server,
        ChatAgent(
            chat_client=AzureAIAgentClient(async_credential=credential),
            name="DocsAgent",
            instructions="You help with Microsoft documentation questions.",
        ) as agent,
    ):
        result = await agent.run(
            "Search Microsoft Learn docs and summarize what Azure AI Foundry Agent Service is.",
            tools=mcp_server,
        )
        print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
