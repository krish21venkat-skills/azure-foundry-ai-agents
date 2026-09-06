import os
import json
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.storage.blob import BlobServiceClient

load_dotenv()

# ---- Config ----
FOUNDRY_ENDPOINT = os.environ["FOUNDRY_ENDPOINT"]
FOUNDRY_DEPLOYMENT = os.environ["FOUNDRY_DEPLOYMENT"]
FOUNDRY_API_KEY = os.environ["FOUNDRY_API_KEY"]
STORAGE_CONNECTION_STRING = os.environ["STORAGE_CONNECTION_STRING"]
STORAGE_CONTAINER = os.environ["STORAGE_CONTAINER"]

# ---- Clients ----
client = AzureOpenAI(
    azure_endpoint=FOUNDRY_ENDPOINT,
    api_key=FOUNDRY_API_KEY,
    api_version="2024-10-21",
)

blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
container_client = blob_service.get_container_client(STORAGE_CONTAINER)


def ask_model(conversation):
    response = client.chat.completions.create(
        model=FOUNDRY_DEPLOYMENT,
        messages=conversation,
    )
    return response.choices[0].message.content


def save_transcript(conversation):
    transcript_id = str(uuid.uuid4())
    blob_name = f"chat-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{transcript_id}.json"
    data = json.dumps(conversation, indent=2)
    container_client.upload_blob(name=blob_name, data=data, overwrite=True)
    print(f"\n[Saved transcript to blob: {blob_name}]")


def main():
    print("Basic Foundry Chatbot — type 'exit' to quit.\n")
    conversation = [
        {"role": "system", "content": "You are a concise, helpful assistant."}
    ]

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            save_transcript(conversation)
            print("Goodbye!")
            break

        conversation.append({"role": "user", "content": user_input})
        reply = ask_model(conversation)
        conversation.append({"role": "assistant", "content": reply})
        print(f"Assistant: {reply}\n")


if __name__ == "__main__":
    main()