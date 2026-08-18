import os
import boto3

env_vars = {}
with open(".env", "r") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")

# Set in os.environ
for k, v in env_vars.items():
    os.environ[k] = v

session = boto3.Session(
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1"
)

# Use the bedrock control plane client
client = session.client("bedrock")

print("Listing foundation models in us-east-1...")
try:
    response = client.list_foundation_models()
    models = response.get("modelSummaries", [])
    print(f"Found {len(models)} foundation models.")
    
    # Filter for Titan and Nova models
    print("\nTitan Models:")
    for m in models:
        if "titan" in m["modelId"]:
            print(f"  - {m['modelId']} (status: {m.get('modelLifecycle', {}).get('status')})")
            
    print("\nNova Models:")
    for m in models:
        if "nova" in m["modelId"]:
            print(f"  - {m['modelId']} (status: {m.get('modelLifecycle', {}).get('status')})")
except Exception as e:
    print(f"Failed to list foundation models: {e}")
