import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
SEARCH_CONNECTION_NAME = os.environ["SEARCH_CONNECTION_NAME"]

project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())

print("=== All connections in this project ===")
for conn in project.connections.list():
    print(f"name={conn.name!r}  type={conn.type!r}  id={conn.id}")

print("\n=== Resolving your configured SEARCH_CONNECTION_NAME ===")
try:
    conn = project.connections.get(SEARCH_CONNECTION_NAME)
    print(f"Found: name={conn.name!r}  type={conn.type!r}  id={conn.id}")
except Exception as e:
    print(f"FAILED to resolve '{SEARCH_CONNECTION_NAME}':")
    print(e)
