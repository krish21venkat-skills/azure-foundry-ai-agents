import os
from dotenv import load_dotenv
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from azure.core.credentials import AzureKeyCredential

load_dotenv()

client = ContentSafetyClient(
    endpoint=os.environ["FOUNDRY_BASE_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["FOUNDRY_API_KEY"]),
)


def check_text(text: str):
    request = AnalyzeTextOptions(text=text)
    response = client.analyze_text(request)

    flagged = False
    for category in [TextCategory.HATE, TextCategory.SELF_HARM, TextCategory.SEXUAL, TextCategory.VIOLENCE]:
        result = next((r for r in response.categories_analysis if r.category == category), None)
        if result and result.severity > 0:
            print(f"  {category}: severity {result.severity}")
            flagged = True
    if not flagged:
        print("  No concerning content detected.")


if __name__ == "__main__":
    sample = input("Enter text to check: ")
    check_text(sample)
