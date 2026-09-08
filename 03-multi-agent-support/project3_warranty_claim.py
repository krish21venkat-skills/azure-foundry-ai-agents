import base64
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


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def submit_warranty_claim(image_path: str, description: str):
    b64_image = encode_image(image_path)
    ext = image_path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"

    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": "policy-agent", "type": "agent_reference"}},
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"A customer submitted a warranty claim with this description: "
                            f"'{description}'. Look at the attached photo and assess whether "
                            f"this looks like a defect covered under our 1-year warranty, or "
                            f"accidental damage/wear which is not covered. Explain your reasoning."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime};base64,{b64_image}",
                    },
                ],
            }
        ],
    )

    result_text = response.output_text
    print(f"\nAssessment:\n{result_text}\n")

    blob_name = f"warranty-claim-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4()}.json"
    record = {"description": description, "image_file": image_path, "assessment": result_text}
    container_client.upload_blob(name=blob_name, data=json.dumps(record, indent=2), overwrite=True)
    print(f"[Saved claim record: {blob_name}]")


if __name__ == "__main__":
    image_path = input("Path to product photo (e.g. ./damaged_item.jpg): ").strip()
    description = input("Describe the issue: ").strip()
    submit_warranty_claim(image_path, description)
