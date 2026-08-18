import urllib.request
import json
import time

BASE_URL = "https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws"

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))

def post(path, body={}):
    url = f"{BASE_URL}{path}"
    print(f"POST {url} ...")
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        print(e.read().decode("utf-8"))
        raise e
    except Exception as e:
        print(f"Error: {e}")
        raise e

def run_workflow_test():
    print("=== STARTING WORKFLOW DEMO VERIFICATION ===")
    
    # 1. Start Incident
    print("\n--- STEP 1: Starting Incident ---")
    res = post("/api/demo/start")
    workflow_id = res.get("workflow_id")
    safe_print(f"Workflow ID: {workflow_id}")
    safe_print(f"Response: {res.get('answer')}")
    safe_print(f"State: {json.dumps(res.get('state'))}")
    
    # 2. Ask agent before crash
    print("\n--- STEP 2: Ask Agent (Before Crash/Recovery) ---")
    chat_res = post("/api/chat", {"message": "Why is checkout latency high?", "workflow_id": workflow_id})
    safe_print(f"Agent Answer:\n{chat_res.get('answer')}")
    
    # 3. Simulate Crash
    print("\n--- STEP 3: Simulating Worker Crash ---")
    crash_res = post("/api/demo/crash", {"workflow_id": workflow_id})
    safe_print(f"Response: {crash_res.get('answer')}")
    safe_print(f"State: {json.dumps(crash_res.get('state'))}")
    
    # 4. Resume Workflow
    print("\n--- STEP 4: Resuming Workflow ---")
    resume_res = post("/api/demo/resume", {"workflow_id": workflow_id})
    safe_print(f"Response: {resume_res.get('answer')}")
    safe_print(f"State: {json.dumps(resume_res.get('state'))}")
    
    # 5. Ask agent after recovery
    print("\n--- STEP 5: Ask Agent (After Crash/Recovery) ---")
    chat_res_after = post("/api/chat", {"message": "Why is checkout latency high?", "workflow_id": workflow_id})
    safe_print(f"Agent Answer:\n{chat_res_after.get('answer')}")
    
    print("\n=== DEMO VERIFICATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_workflow_test()
