import os
import json
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.storage.blob import BlobServiceClient

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
AGENT_NAME = os.environ["AGENT_NAME"]
STORAGE_CONNECTION_STRING = os.environ["STORAGE_CONNECTION_STRING"]
CHAT_CONTAINER = os.environ["CHAT_CONTAINER"]

project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
openai_client = project.get_openai_client()

blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
container_client = blob_service.get_container_client(CHAT_CONTAINER)

# --- Mock order data for the custom tool ---
FAKE_ORDERS = {
    "ORD-1042": "Shipped — arriving in 2 days via standard shipping.",
    "ORD-2077": "Processing — will ship within 24 hours.",
    "ORD-3090": "Delivered on the requested date.",
}


def lookup_order_status(order_id: str) -> str:
    return FAKE_ORDERS.get(order_id, f"No order found with ID {order_id}.")


def handle_tool_calls(response):
    """Look through response output for function_call items, execute them,
    and return the tool outputs to submit back to the agent."""
    tool_outputs = []
    for item in response.output:
        if item.type == "function_call" and item.name == "lookup_order_status":
            args = json.loads(item.arguments)
            result = lookup_order_status(args["order_id"])
            tool_outputs.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result,
            })
    return tool_outputs


def ask_agent(conversation_id, user_input, transcript):
    transcript.append({"role": "user", "content": user_input})

    response = openai_client.responses.create(
        conversation=conversation_id,
        extra_body={"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}},
        input=user_input,
    )

    tool_outputs = handle_tool_calls(response)
    while tool_outputs:
        response = openai_client.responses.create(
            conversation=conversation_id,
            extra_body={"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}},
            input=tool_outputs,
        )
        tool_outputs = handle_tool_calls(response)

    transcript.append({"role": "assistant", "content": response.output_text})
    return response.output_text


def save_transcript(transcript):
    transcript_id = str(uuid.uuid4())
    blob_name = f"agent-chat-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{transcript_id}.json"
    container_client.upload_blob(name=blob_name, data=json.dumps(transcript, indent=2), overwrite=True)
    print(f"\n[Saved transcript to blob: {blob_name}]")


def main():
    print("Contoso Basics Support Agent — type 'exit' to quit.\n")
    conversation = openai_client.conversations.create()
    transcript = []

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            save_transcript(transcript)
            print("Goodbye!")
            break

        reply = ask_agent(conversation.id, user_input, transcript)
        print(f"Agent: {reply}\n")


if __name__ == "__main__":
    main()
