import os
import pg8000.dbapi
from urllib.parse import urlparse, unquote

# Read from environment or load from .env
CRDB_URL = os.environ.get("CRDB_URL")
if not CRDB_URL and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("CRDB_URL="):
                CRDB_URL = line.split("=", 1)[1].strip().strip('"').strip("'")

# Set environment
os.environ["CRDB_URL"] = CRDB_URL
os.environ["AWS_REGION"] = "us-east-1"
os.environ["CHAT_MODEL_ID"] = "amazon.nova-lite-v1:0"
os.environ["EMBED_MODEL_ID"] = "amazon.titan-embed-text-v2:0"

# Import from lambda_function.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from lambda_function import db, seed_memories, retrieve_memories, generate_answer

def run_test():
    print("Connecting to DB...")
    c = db()
    
    print("Seeding baseline memories...")
    seed_memories(c)
    print("Memories seeded successfully.")
    
    print("\nRetrieving memories for: 'checkout latency after deployment'...")
    mems = retrieve_memories(c, "checkout latency after deployment", 3)
    for i, m in enumerate(mems, 1):
        print(f"[{i}] {m['memory_type']} | Source: {m['source']} | Confidence: {m['confidence']:.2f}")
        print(f"    Content: {m['content']}")
        
    print("\nRunning local reasoning engine simulation...")
    answer = generate_answer("Why is checkout latency high?", mems)
    print("\nAnswer Output:")
    print(answer)
    
    c.close()

if __name__ == "__main__":
    run_test()
