import json
import urllib.request
import urllib.error
import os

# Load from env variable or .env
API_KEY = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "PLACEHOLDER")
REGION = "eu-north-1"
MODEL_ID = "amazon.titan-embed-text-v2:0"

def test_embeddings():
    if API_KEY == "PLACEHOLDER":
        print("Skipping: No API key configured.")
        return False
        
    url = f"https://bedrock-runtime.{REGION}.amazonaws.com/model/{MODEL_ID}/invoke"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "inputText": "Hello from REASSEMBLE local verification test!",
        "dimensions": 1024,
        "normalize": True
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    print(f"Sending request to {url}...")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            embedding = data.get("embedding")
            print(f"Success! Embedding generated successfully.")
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_embeddings()
