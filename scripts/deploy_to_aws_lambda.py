import os
import boto3
import json
import time

env_vars = {}
with open(".env", "r") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")

for k, v in env_vars.items():
    os.environ[k] = v

FUNCTION_NAME = "reassemble-agent"
ZIP_PATH = "reassemble-lambda.zip"
REGION = "us-east-1"

session = boto3.Session(
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=REGION
)

lambda_client = session.client("lambda")

def wait_for_active():
    print("Waiting for Lambda update to complete and become active...")
    for _ in range(30):
        try:
            config = lambda_client.get_function_configuration(FunctionName=FUNCTION_NAME)
            status = config.get("LastUpdateStatus")
            state = config.get("State")
            print(f"  Current State: {state}, Last Update Status: {status}")
            if status != "InProgress" and state == "Active":
                return True
        except Exception as e:
            print(f"  Error checking status: {e}")
        time.sleep(2)
    return False

def deploy():
    print(f"Deploying {ZIP_PATH} to Lambda function: {FUNCTION_NAME} in region {REGION}...")
    
    if not os.path.exists(ZIP_PATH):
        print(f"Error: {ZIP_PATH} not found. Build it first.")
        return
        
    with open(ZIP_PATH, "rb") as f:
        zip_bytes = f.read()
        
    try:
        response = lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_bytes
        )
        print("Successfully uploaded zip package to AWS Lambda.")
    except Exception as e:
        print(f"Failed to update function code: {e}")
        return

    # Wait for the update to complete
    if not wait_for_active():
        print("Timeout waiting for Lambda function to become active. Proceeding anyway...")

    # Update Environment Variables & Config
    print("\nUpdating environment variables and configuration...")
    try:
        variables = {
            "CRDB_URL": os.environ.get("CRDB_URL"),
            "CHAT_MODEL_ID": os.environ.get("CHAT_MODEL_ID", "amazon.nova-lite-v1:0"),
            "EMBED_MODEL_ID": os.environ.get("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0"),
            "MY_AWS_REGION": REGION
        }
        
        response = lambda_client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Runtime="python3.11",
            Handler="lambda_function.lambda_handler",
            Timeout=60,
            MemorySize=512,
            Environment={
                "Variables": variables
            }
        )
        print("Successfully updated Lambda configuration (Handler, Timeout, Memory, and Env Vars).")
    except Exception as e:
        print(f"Failed to update function configuration: {e}")
        return

    # Wait again after configuration change
    if not wait_for_active():
        print("Timeout waiting for Lambda function to become active after config change.")

    # Check or Create Function URL
    print("\nChecking Function URL configuration...")
    function_url = None
    try:
        response = lambda_client.get_function_url_config(
            FunctionName=FUNCTION_NAME
        )
        function_url = response.get("FunctionUrl")
        print(f"Found existing Function URL: {function_url}")
    except lambda_client.exceptions.ResourceNotFoundException:
        print("No Function URL found. Creating a new one...")
        try:
            response = lambda_client.create_function_url_config(
                FunctionName=FUNCTION_NAME,
                AuthType="NONE",
                Cors={
                    "AllowOrigins": ["*"],
                    "AllowMethods": ["*"],
                    "AllowHeaders": ["content-type"]
                }
            )
            function_url = response.get("FunctionUrl")
            print(f"Successfully created Function URL: {function_url}")
            
            print("Adding public permission to invoke Function URL...")
            lambda_client.add_permission(
                FunctionName=FUNCTION_NAME,
                StatementId="FunctionURLAllowPublicAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE"
            )
            print("Successfully configured public invocation permissions.")
        except Exception as e:
            print(f"Failed to create Function URL config: {e}")
    except Exception as e:
        print(f"Error checking Function URL: {e}")

    if function_url:
        print("=======================================================")
        print("DEPLOYMENT SUCCESSFUL!")
        print(f"Public Endpoint: {function_url}")
        print("=======================================================")

if __name__ == "__main__":
    deploy()
