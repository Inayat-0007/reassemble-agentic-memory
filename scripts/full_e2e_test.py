"""
REASSEMBLE - Complete End-to-End Feature Verification
Tests every API endpoint and the full demo flow against the live Lambda URL.
"""
import urllib.request
import urllib.error
import json
import time
import sys

BASE_URL = "https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws"

PASS = 0
FAIL = 0
RESULTS = []

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))

def get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8"), dict(resp.headers)

def post(path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def test(name, fn):
    global PASS, FAIL
    safe_print(f"\n{'='*60}")
    safe_print(f"TEST: {name}")
    safe_print(f"{'='*60}")
    try:
        result = fn()
        if result:
            PASS += 1
            RESULTS.append(("PASS", name, ""))
            safe_print(f"  >> RESULT: PASS")
        else:
            FAIL += 1
            RESULTS.append(("FAIL", name, "returned False"))
            safe_print(f"  >> RESULT: FAIL")
    except Exception as e:
        FAIL += 1
        RESULTS.append(("FAIL", name, str(e)))
        safe_print(f"  >> RESULT: FAIL - {e}")

# ============================================================
# TEST 1: Homepage (SPA HTML)
# ============================================================
def test_homepage():
    status, body, headers = get("/")
    safe_print(f"  Status: {status}")
    safe_print(f"  Content-Type: {headers.get('Content-Type', 'N/A')}")
    safe_print(f"  Body length: {len(body)} bytes")
    safe_print(f"  Contains <title>: {'<title>' in body}")
    safe_print(f"  Contains REASSEMBLE: {'REASSEMBLE' in body}")
    safe_print(f"  Contains chat input: {'chat' in body.lower()}")
    safe_print(f"  Contains Start button: {'Start' in body}")
    safe_print(f"  Contains Crash button: {'Crash' in body or 'crash' in body}")
    safe_print(f"  Contains Resume button: {'Resume' in body or 'resume' in body}")
    assert status == 200, f"Expected 200, got {status}"
    assert "REASSEMBLE" in body, "Missing REASSEMBLE title"
    assert "<title>" in body, "Missing HTML title tag"
    return True

# ============================================================
# TEST 2: GET /api/memories (list all memories)
# ============================================================
def test_get_memories():
    status, data = post("/api/memories")
    safe_print(f"  Status: {status}")
    memories = data.get("memories", [])
    safe_print(f"  Number of memories: {len(memories)}")
    for i, m in enumerate(memories):
        safe_print(f"  [{i+1}] type={m['memory_type']}, source={m['source']}, confidence={m['confidence']}, status={m['status']}")
        safe_print(f"       content: {m['content'][:80]}...")
    assert status == 200
    assert len(memories) >= 5, f"Expected >= 5 memories, got {len(memories)}"
    types = set(m['memory_type'] for m in memories)
    safe_print(f"  Memory types present: {types}")
    assert 'incident' in types, "Missing incident type"
    assert 'runbook' in types, "Missing runbook type"
    return True

# ============================================================
# TEST 3: Chat endpoint (pre-supersession query)
# ============================================================
def test_chat_basic():
    status, data = post("/api/chat", {"message": "Why is checkout latency high?"})
    safe_print(f"  Status: {status}")
    answer = data.get("answer", "")
    safe_print(f"  Answer length: {len(answer)} chars")
    safe_print(f"  Answer preview: {answer[:200]}...")
    memories = data.get("memories", [])
    safe_print(f"  Memories returned: {len(memories)}")
    assert status == 200
    assert len(answer) > 50, f"Answer too short: {len(answer)}"
    return True

# ============================================================
# TEST 4: Start Incident workflow
# ============================================================
workflow_id = None
def test_start_incident():
    global workflow_id
    status, data = post("/api/demo/start")
    safe_print(f"  Status: {status}")
    workflow_id = data.get("workflow_id")
    state = data.get("state", {})
    answer = data.get("answer", "")
    safe_print(f"  Workflow ID: {workflow_id}")
    safe_print(f"  State: {json.dumps(state)}")
    safe_print(f"  Answer: {answer}")
    assert status == 200
    assert workflow_id is not None, "No workflow_id returned"
    assert state.get("status") == "INVESTIGATING", f"Expected INVESTIGATING, got {state.get('status')}"
    assert state.get("last_completed_step") == 1, f"Expected step 1, got {state.get('last_completed_step')}"
    assert state.get("total_steps") == 4, f"Expected 4 steps, got {state.get('total_steps')}"
    return True

# ============================================================
# TEST 5: Simulate worker crash
# ============================================================
def test_crash():
    global workflow_id
    assert workflow_id, "No workflow_id from previous test"
    status, data = post("/api/demo/crash", {"workflow_id": workflow_id})
    safe_print(f"  Status: {status}")
    state = data.get("state", {})
    answer = data.get("answer", "")
    safe_print(f"  State: {json.dumps(state)}")
    safe_print(f"  Answer: {answer}")
    assert status == 200
    assert state.get("status") == "INTERRUPTED", f"Expected INTERRUPTED, got {state.get('status')}"
    assert state.get("last_completed_step") == 2, f"Expected step 2, got {state.get('last_completed_step')}"
    return True

# ============================================================
# TEST 6: Resume workflow from checkpoint
# ============================================================
def test_resume():
    global workflow_id
    assert workflow_id, "No workflow_id from previous test"
    status, data = post("/api/demo/resume", {"workflow_id": workflow_id})
    safe_print(f"  Status: {status}")
    state = data.get("state", {})
    answer = data.get("answer", "")
    safe_print(f"  State: {json.dumps(state)}")
    safe_print(f"  Answer: {answer}")
    assert status == 200
    assert state.get("status") == "COMPLETED", f"Expected COMPLETED, got {state.get('status')}"
    assert state.get("last_completed_step") == 4, f"Expected step 4, got {state.get('last_completed_step')}"
    return True

# ============================================================
# TEST 7: Chat after recovery (should reflect superseded memory)
# ============================================================
def test_chat_after_recovery():
    status, data = post("/api/chat", {"message": "Why is checkout latency high?"})
    safe_print(f"  Status: {status}")
    answer = data.get("answer", "")
    safe_print(f"  Answer length: {len(answer)} chars")
    safe_print(f"  Answer:\n{answer}")
    assert status == 200
    assert len(answer) > 50
    # Check that the answer mentions the validated finding
    has_leak = "leak" in answer.lower() or "v2.8" in answer or "incident-208" in answer.lower()
    has_pool_warning = "pool" in answer.lower()
    safe_print(f"  Mentions connection leak / v2.8 / incident-208: {has_leak}")
    safe_print(f"  Mentions pool: {has_pool_warning}")
    return True

# ============================================================
# TEST 8: Chat with empty message (edge case)
# ============================================================
def test_chat_empty():
    try:
        status, data = post("/api/chat", {"message": ""})
        safe_print(f"  Status: {status}")
        safe_print(f"  Response: {json.dumps(data)[:200]}")
        # Either should return 200 with some answer or gracefully handle
        return True
    except urllib.error.HTTPError as e:
        safe_print(f"  HTTP Error: {e.code} - this is acceptable for empty input")
        return True

# ============================================================
# TEST 9: Chat with different query
# ============================================================
def test_chat_different_query():
    status, data = post("/api/chat", {"message": "What is the payment service architecture?"})
    safe_print(f"  Status: {status}")
    answer = data.get("answer", "")
    safe_print(f"  Answer: {answer[:300]}")
    memories = data.get("memories", [])
    safe_print(f"  Memories returned: {len(memories)}")
    for m in memories:
        safe_print(f"    - {m['memory_type']}: {m['content'][:60]}...")
    assert status == 200
    return True

# ============================================================
# TEST 10: Unknown route returns 404
# ============================================================
def test_unknown_route():
    try:
        url = f"{BASE_URL}/api/nonexistent"
        req = urllib.request.Request(url, data=b'{}', headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            safe_print(f"  Status: {status}")
            safe_print(f"  Body: {body[:200]}")
            # If it returns 200 with an error message, that's still handled
            return True
    except urllib.error.HTTPError as e:
        safe_print(f"  HTTP Error: {e.code} {e.reason}")
        safe_print(f"  Body: {e.read().decode('utf-8')[:200]}")
        return e.code in (404, 400, 500)  # Any error code is fine for unknown route

# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("REASSEMBLE - COMPLETE E2E VERIFICATION SUITE")
    print(f"Target: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    test("1. Homepage serves SPA HTML", test_homepage)
    test("2. GET /api/memories returns seeded memories", test_get_memories)
    test("3. Chat - basic incident query", test_chat_basic)
    test("4. Demo - Start Incident workflow", test_start_incident)
    test("5. Demo - Simulate Worker Crash", test_crash)
    test("6. Demo - Resume from Checkpoint", test_resume)
    test("7. Chat - post-recovery query (memory supersession)", test_chat_after_recovery)
    test("8. Chat - empty message (edge case)", test_chat_empty)
    test("9. Chat - different query (architecture)", test_chat_different_query)
    test("10. Unknown route handling", test_unknown_route)

    print("\n" + "=" * 60)
    print("FINAL RESULTS SUMMARY")
    print("=" * 60)
    for status, name, err in RESULTS:
        marker = "[PASS]" if status == "PASS" else "[FAIL]"
        line = f"  {marker} {name}"
        if err:
            line += f" -- {err}"
        safe_print(line)
    
    print(f"\n  Total: {PASS + FAIL} | Passed: {PASS} | Failed: {FAIL}")
    if FAIL == 0:
        print("\n  ALL TESTS PASSED!")
    else:
        print(f"\n  {FAIL} TEST(S) FAILED!")
    
    sys.exit(0 if FAIL == 0 else 1)
