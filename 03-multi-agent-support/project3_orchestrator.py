import os
import json
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.storage.blob import BlobServiceClient

load_dotenv()

project = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
openai_client = project.get_openai_client()

blob_service = BlobServiceClient.from_connection_string(os.environ["STORAGE_CONNECTION_STRING"])
container_client = blob_service.get_container_client(os.environ["CHAT_CONTAINER"])

FAKE_ORDERS = {
    "ORD-1042": "Shipped — arriving in 2 days via standard shipping.",
    "ORD-2077": "Processing — will ship within 24 hours.",
}


def classify_intent(user_input: str) -> str:
    """Lightweight routing call using gpt-4o-mini directly (no agent needed for this step)."""
    response = openai_client.chat.completions.create(
        model=os.environ["MODEL_DEPLOYMENT"],
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the user's message as exactly one word: "
                    "POLICY (returns/shipping/warranty questions) or "
                    "ORDER (order status/tracking questions). Reply with only that one word."
                ),
            },
            {"role": "user", "content": user_input},
        ],
    )
    label = response.choices[0].message.content.strip().upper()
    return "ORDER" if "ORDER" in label else "POLICY"


def handle_tool_calls(response):
    outputs = []
    for item in response.output:
        if item.type == "function_call" and item.name == "lookup_order_status":
            args = json.loads(item.arguments)
            result = FAKE_ORDERS.get(args["order_id"], f"No order found with ID {args['order_id']}.")
            outputs.append({"type": "function_call_output", "call_id": item.call_id, "output": result})
    return outputs


def call_agent(agent_name, conversation_id, user_input):
    response = openai_client.responses.create(
        conversation=conversation_id,
        extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        input=user_input,
    )
    tool_outputs = handle_tool_calls(response)
    while tool_outputs:
        response = openai_client.responses.create(
            conversation=conversation_id,
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
            input=tool_outputs,
        )
        tool_outputs = handle_tool_calls(response)
    return response.output_text


def main():
    print("Contoso Basics Multi-Agent Support — type 'exit' to quit.\n")
    conversation = openai_client.conversations.create()
    transcript = []

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            blob_name = f"multiagent-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4()}.json"
            container_client.upload_blob(name=blob_name, data=json.dumps(transcript, indent=2), overwrite=True)
            print(f"[Saved transcript: {blob_name}]\nGoodbye!")
            break

        intent = classify_intent(user_input)
        agent_name = "policy-agent" if intent == "POLICY" else "order-agent"
        reply = call_agent(agent_name, conversation.id, user_input)

        transcript.append({"role": "user", "content": user_input})
        transcript.append({"role": "assistant", "agent": agent_name, "content": reply})
        print(f"[{agent_name}] {reply}\n")


if __name__ == "__main__":
    main()
