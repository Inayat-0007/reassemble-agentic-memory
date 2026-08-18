import os
import boto3
import json

# Load env variables from .env manually to ensure they are set
env_vars = {}
with open(".env", "r") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")

# Set them in os.environ
for k, v in env_vars.items():
    os.environ[k] = v

print("AWS Credentials:")
print(f"  AWS_ACCESS_KEY_ID: {os.environ.get('AWS_ACCESS_KEY_ID')}")
print(f"  AWS_SECRET_ACCESS_KEY: {os.environ.get('AWS_SECRET_ACCESS_KEY')[:5]}...")
print(f"  AWS_REGION: {os.environ.get('AWS_REGION')}")

# Try to call Bedrock
session = boto3.Session(
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_REGION")
)

client = session.client("bedrock-runtime")

payload = {
    "inputText": "Hello from REASSEMBLE local credentials verification test!",
    "dimensions": 1024,
    "normalize": True
}

print("Invoking model amazon.titan-embed-text-v2:0...")
try:
    response = client.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps(payload)
    )
    res_body = response["body"].read().decode("utf-8")
    data = json.loads(res_body)
    embedding = data.get("embedding")
    print(f"Success! Embedding generated. Dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
except Exception as e:
    print(f"Failed invoking model: {e}")
