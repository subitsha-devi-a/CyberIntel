
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NEXUS_API_KEY")
BASE_URL = os.getenv("NEXUS_API_BASE_URL")

url = BASE_URL.rstrip("/") + "/v1/embeddings"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "text-embedding-3-small",
    "input": "Apache Log4j cybersecurity vulnerability"
}

try:
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60
    )

    print("HTTP Status:", response.status_code)
    print("Response:")

    if response.status_code == 200:
        result = response.json()
        embedding = result["data"][0]["embedding"]

        print("Embedding successful!")
        print("Vector dimensions:", len(embedding))
        print("First five values:", embedding[:5])
    else:
        print(response.text[:2000])

except requests.exceptions.RequestException as error:
    print("Request failed:", error)
