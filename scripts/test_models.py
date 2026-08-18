import json
import urllib.request
import urllib.error
import os

API_KEY = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "PLACEHOLDER")
REGION = "eu-north-1"

models = {
    "Claude 3 Haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "Claude 3.5 Sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0"
}

def test_model(name, model_id):
    if API_KEY == "PLACEHOLDER":
        print("Skipping: No API key configured.")
        return False
        
    url = f"https://bedrock-runtime.{REGION}.amazonaws.com/model/{model_id}/invoke"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Say hello!"}]
            }
        ],
        "max_tokens": 50,
        "temperature": 0.2
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    print(f"Testing {name} ({model_id})...")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print(f"  Success! Response: {res_body[:200]}")
            return True
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error: {e.code} {e.reason}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    for name, model_id in models.items():
        test_model(name, model_id)
