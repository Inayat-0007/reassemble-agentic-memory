import json
import os
import html
import uuid
from datetime import datetime, timezone

import boto3
import pg8000.dbapi

REGION = os.getenv("MY_AWS_REGION", os.getenv("AWS_REGION", "us-east-1"))
CRDB_URL = os.environ["CRDB_URL"]
CHAT_MODEL_ID = os.getenv("CHAT_MODEL_ID", "amazon.nova-lite-v1:0")
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")

# If custom keys are set (e.g. for local testing or credentials bypass), use them in Session
aws_key = os.getenv("MY_AWS_ACCESS_KEY_ID")
aws_secret = os.getenv("MY_AWS_SECRET_ACCESS_KEY")
if aws_key and aws_secret:
    session = boto3.Session(
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name=REGION
    )
    bedrock = session.client("bedrock-runtime")
else:
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)

DEMO_MEMORIES = [
    ("incident", "Incident #143: Checkout latency increased after a deployment. Engineers initially suspected payment database connection-pool exhaustion.", 0.72, "incident-143"),
    ("runbook", "Runbook #12: If checkout latency exceeds 2 seconds, inspect payment database connection pressure, active sessions, and recent deployment changes.", 0.95, "runbook-12"),
    ("architecture", "Architecture Decision #72: The payment service was migrated from PostgreSQL to CockroachDB. Connection behavior and operational limits must be evaluated on the new architecture.", 0.98, "decision-72"),
    ("lesson", "Incident #191: Increasing the payment connection pool did not fix the underlying checkout problem. Pool-size changes should not be treated as a root-cause fix without evidence.", 0.90, "incident-191"),
    ("current_fact", "Incident #208: Deployment v2.8 introduced a connection leak in the payment service. The validated remediation was to roll back the deployment and fix the leak, not to blindly increase the pool size.", 0.94, "incident-208"),
]

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>REASSEMBLE — Durable Agentic Command Center</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #050811;
  --panel: rgba(13, 19, 36, 0.72);
  --panel-border: rgba(99, 102, 241, 0.2);
  --panel-border-hover: rgba(129, 140, 248, 0.45);
  --primary: #6366f1;
  --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
  --danger: #ef4444;
  --danger-gradient: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  --success: #10b981;
  --success-gradient: linear-gradient(135deg, #10b981 0%, #059669 100%);
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --code-bg: #090e1d;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.3); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.6); }

html, body {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg);
  background-image: 
    radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.18) 0px, transparent 45%),
    radial-gradient(at 100% 0%, rgba(217, 70, 239, 0.14) 0px, transparent 45%),
    radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 45%);
  background-attachment: fixed;
  font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
  color: var(--text-main);
  line-height: 1.5;
}

/* Master Cockpit Layout */
.cockpit-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 16px 24px;
  gap: 14px;
  max-width: 100%;
}

/* Top Navigation & Action Deck */
.top-deck {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  background: var(--panel);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  flex-shrink: 0;
}
.brand-box { display: flex; align-items: center; gap: 12px; }
.logo-icon {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: var(--primary-gradient);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  box-shadow: 0 0 16px rgba(99, 102, 241, 0.5);
}
.brand-heading {
  font-size: 20px; font-weight: 800; letter-spacing: -0.03em;
  background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.brand-subline { font-size: 11.5px; color: var(--text-muted); }

.control-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 9px 16px; font-size: 13px; font-weight: 700;
  border-radius: 11px; border: 1px solid transparent;
  cursor: pointer; transition: all 0.2s ease;
  color: #fff; font-family: inherit;
  white-space: nowrap;
}
.btn:hover { transform: translateY(-2px); }
.btn:active { transform: translateY(0); }
.btn-start { background: var(--primary-gradient); box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4); }
.btn-crash { background: var(--danger-gradient); box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4); }
.btn-resume { background: var(--success-gradient); box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35); }
.btn-sync { background: rgba(30, 41, 59, 0.7); border-color: rgba(255, 255, 255, 0.12); color: #cbd5e1; }
.btn-sync:hover { background: rgba(51, 65, 85, 0.9); color: #fff; }

.pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.pulse-green {
  width: 7px; height: 7px; border-radius: 50%; background: #10b981;
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  animation: pulse-ring 2s infinite;
}
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { box-shadow: 0 0 0 7px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* Main Grid Workspace */
.main-workspace {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 16px;
  flex: 1;
  min-height: 0; /* Critical for inner scrolling */
}

.panel-card {
  background: var(--panel);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px; flex-shrink: 0;
}
.panel-header h2 { font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #fff; }

/* Left Column: Reasoning Console */
.prompt-chips { display: flex; gap: 8px; margin-bottom: 10px; flex-shrink: 0; flex-wrap: wrap; }
.chip-btn {
  font-size: 11.5px; font-weight: 500;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #cbd5e1; padding: 4px 12px; border-radius: 10px;
  cursor: pointer; transition: all 0.2s;
}
.chip-btn:hover { background: rgba(99, 102, 241, 0.25); border-color: #818cf8; color: #fff; }

.input-row { display: flex; gap: 10px; margin-bottom: 12px; flex-shrink: 0; }
textarea {
  flex: 1; height: 56px; min-height: 56px;
  background: var(--code-bg);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff; border-radius: 12px;
  padding: 10px 14px; font-family: inherit; font-size: 13.5px;
  resize: none; outline: none; transition: all 0.2s;
}
textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25); }

.reasoning-stream {
  flex: 1;
  background: var(--code-bg);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px;
  overflow-y: auto;
  font-size: 13.5px;
  color: #e2e8f0;
  line-height: 1.6;
}
.reasoning-stream strong { color: #fff; font-weight: 700; }
.reasoning-stream ol, .reasoning-stream ul { padding-left: 20px; margin: 8px 0; }
.reasoning-stream li { margin-bottom: 4px; }
.reasoning-stream code { font-family: 'JetBrains Mono', monospace; background: rgba(255, 255, 255, 0.08); padding: 2px 6px; border-radius: 4px; font-size: 12px; }

/* Right Column: Workflow & Memories */
.workflow-section { flex-shrink: 0; margin-bottom: 12px; }
.state-summary { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
.stepper-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.step-node {
  background: var(--code-bg);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px; padding: 7px 4px;
  text-align: center; font-size: 11px;
  color: var(--text-muted); transition: all 0.2s;
}
.step-node.active { background: rgba(99, 102, 241, 0.2); border-color: #6366f1; color: #fff; font-weight: 700; }
.step-node.completed { background: rgba(16, 185, 129, 0.15); border-color: #10b981; color: #34d399; font-weight: 600; }
.step-node.interrupted { background: rgba(239, 68, 68, 0.2); border-color: #ef4444; color: #f87171; font-weight: 700; }

.memory-feed-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.memory-feed {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}
.mem-card {
  background: var(--code-bg);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 8px;
  transition: all 0.2s;
}
.mem-card:hover { border-color: rgba(99, 102, 241, 0.35); }
.mem-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.badge-incident { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
.badge-runbook { background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); }
.badge-lesson { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-architecture { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }
.badge-current_fact { background: rgba(16, 185, 129, 0.18); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); font-weight: 700; }
.conf-bar { width: 36px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 999px; overflow: hidden; margin-top: 2px; }
.conf-fill { height: 100%; background: #34d399; border-radius: 999px; }

/* Bottom Strip: Reality & Verification */
.bottom-strip {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 10px 18px;
  background: var(--panel);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: 14px;
  font-size: 11.5px;
  flex-shrink: 0;
}
.strip-col { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.strip-tag { font-weight: 700; color: #818cf8; text-transform: uppercase; font-size: 10.5px; }

@media (max-width: 1024px) {
  html, body { height: auto; overflow: auto; }
  .cockpit-wrapper { height: auto; }
  .main-workspace { grid-template-columns: 1fr; }
  .bottom-strip { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<div class="cockpit-wrapper">
  <!-- Top Control Deck -->
  <header class="top-deck">
    <div class="brand-box">
      <div class="logo-icon">⚡</div>
      <div>
        <div class="brand-heading">REASSEMBLE</div>
        <div class="brand-subline">CockroachDB Durable Agentic Memory Engine</div>
      </div>
    </div>

    <!-- Central Control Action Buttons -->
    <div class="control-actions">
      <button class="btn btn-start" onclick="startDemo()">⚡ 1. Start Incident</button>
      <button class="btn-crash" onclick="simulateCrash()">💥 2. Controlled Failure</button>
      <button class="btn-resume" onclick="resumeDemo()">🛡️ 3. Resume Checkpoint</button>
      <button class="btn btn-sync" onclick="loadMemories()">🔄 Sync Memory</button>
    </div>

    <!-- Live Telemetry Badge -->
    <div class="pill">
      <div class="pulse-green"></div>
      <span>CockroachDB Serverless · AWS Lambda</span>
    </div>
  </header>

  <!-- Main Multi-Panel Workspace -->
  <main class="main-workspace">
    <!-- Left Column: Agent Reasoning -->
    <div class="panel-card">
      <div class="panel-header">
        <h2>Agent Reasoning Console</h2>
        <div class="pill" style="font-size: 11px; color: #a5b4fc;">VECTOR(1024) &lt;=&gt; Cosine Distance</div>
      </div>

      <div class="prompt-chips">
        <button class="chip-btn" onclick="setPrompt('Why is checkout latency high?')">💡 Why is checkout latency high?</button>
        <button class="chip-btn" onclick="setPrompt('What is the payment service architecture?')">🔍 Architecture inquiry</button>
      </div>

      <div class="input-row">
        <textarea id="msg" placeholder="Ask agent a question to query semantic memory... (Press Enter to submit)"></textarea>
        <button class="btn btn-start" onclick="chat()" style="padding: 0 20px; font-size: 13px;">Ask Agent</button>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted);">Reasoning Synthesis</span>
        <span id="chat-status" style="font-size: 11.5px; color: #a5b4fc; font-weight: 600;"></span>
      </div>

      <div class="reasoning-stream" id="answer">Ready. Trigger an incident workflow or submit an inquiry to inspect agent memory synthesis.</div>
    </div>

    <!-- Right Column: Workflow State & Memory Feed -->
    <div class="panel-card">
      <div class="workflow-section">
        <div class="panel-header" style="margin-bottom: 8px;">
          <h2>Workflow State</h2>
          <span id="state-badge" class="pill" style="font-size: 11px; color: #a5b4fc; font-weight: 700;">IDLE</span>
        </div>
        <div id="state" class="state-summary">No active workflow. Click '1. Start Incident' to begin.</div>

        <div class="stepper-row" id="stepper">
          <div class="step-node" id="step-1">1. Checkpoint 1<br><span style="font-size: 9.5px; opacity: 0.7;">Initialize</span></div>
          <div class="step-node" id="step-2">2. Correlate<br><span style="font-size: 9.5px; opacity: 0.7;">Evidence</span></div>
          <div class="step-node" id="step-3">3. Validate<br><span style="font-size: 9.5px; opacity: 0.7;">Root Cause</span></div>
          <div class="step-node" id="step-4">4. Supersede<br><span style="font-size: 9.5px; opacity: 0.7;">Commit DB</span></div>
        </div>
      </div>

      <div class="memory-feed-container">
        <div class="panel-header" style="margin-top: 10px; margin-bottom: 8px;">
          <h2>Seeded Demonstration Memories</h2>
          <span class="pill" style="font-size: 10.5px; color: #34d399;">COCKROACHDB</span>
        </div>
        <div class="memory-feed" id="memories">Click 'Sync Memory' to load stored vectors.</div>
      </div>
    </div>
  </main>

  <!-- Bottom Strip: System Reality Status -->
  <footer class="bottom-strip">
    <div class="strip-col">
      <span class="strip-tag">Database (Real):</span>
      <span>✅ CockroachDB (Asia-South1)</span>
      <span>·</span>
      <span>✅ ACID Checkpoints</span>
      <span>·</span>
      <span>✅ VECTOR(1024)</span>
      <span>·</span>
      <span>✅ Memory Supersession</span>
    </div>
    <div class="strip-col">
      <span class="strip-tag">Runtime & Fixtures:</span>
      <span>✅ AWS Lambda</span>
      <span>·</span>
      <span>✅ Managed MCP</span>
      <span>·</span>
      <span>⚡ Controlled Failure</span>
      <span>·</span>
      <span>⚡ Deterministic Fallback Mode</span>
    </div>
  </footer>
</div>

<script>
let workflowId = localStorage.getItem("reassemble_workflow_id") || "";

function setPrompt(txt) {
  const el = document.getElementById("msg");
  el.value = txt;
  el.focus();
}

document.getElementById("msg").addEventListener("keydown", function(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chat();
  }
});

async function post(path, body={}) {
  const r = await fetch(path, {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify(body)});
  const j = await r.json();
  if (j.workflow_id) { workflowId = j.workflow_id; localStorage.setItem("reassemble_workflow_id", workflowId); }
  return j;
}

function updateStepper(status, step) {
  const s = parseInt(step) || 0;
  for(let i=1; i<=4; i++) {
    const el = document.getElementById("step-" + i);
    if (!el) continue;
    el.className = "step-node";
    if (i < s) {
      el.classList.add("completed");
    } else if (i === s) {
      if (status === "INTERRUPTED") el.classList.add("interrupted");
      else if (status === "COMPLETED") el.classList.add("completed");
      else el.classList.add("active");
    }
  }
  const badge = document.getElementById("state-badge");
  if (badge) {
    badge.textContent = status || "IDLE";
    badge.style.color = (status === "COMPLETED" ? "#34d399" : status === "INTERRUPTED" ? "#f87171" : "#818cf8");
  }
}

function formatMarkdown(text) {
  if(!text) return "";
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/^\d+\.\s+(.*)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ol>$1</ol>');
  html = html.replace(/\n\n/g, '<br><br>');
  return html;
}

function render(j){
  const ansEl = document.getElementById("answer");
  if (j.answer) {
    ansEl.innerHTML = formatMarkdown(j.answer);
  } else {
    ansEl.textContent = JSON.stringify(j, null, 2);
  }

  if(j.state) {
    document.getElementById("state").innerHTML =
      `<b>Status:</b> ${escapeHtml(j.state.status)} &nbsp;|&nbsp; <b>Progress:</b> Step ${j.state.last_completed_step}/${j.state.total_steps} &nbsp;|&nbsp; <code>${escapeHtml(j.state.workflow_id)}</code>`;
    updateStepper(j.state.status, j.state.last_completed_step);
  }
  if(j.memories) {
    document.getElementById("memories").innerHTML = j.memories.map(m => {
      const typeClass = "badge-" + (m.memory_type || "incident");
      const conf = ((m.confidence || 0) * 100).toFixed(0);
      return `<div class="mem-card">
        <div class="mem-meta">
          <span class="pill ${typeClass}" style="font-size:10px; padding:2px 8px;">${escapeHtml(m.memory_type || 'memory')}</span>
          <div style="text-align:right;">
            <span style="font-size:10.5px; color:#cbd5e1;">Confidence: <b>${conf}%</b></span>
            <div class="conf-bar"><div class="conf-fill" style="width: ${conf}%;"></div></div>
          </div>
        </div>
        <div style="font-size:12px; color:#e2e8f0; line-height:1.4; margin-bottom:4px;">${escapeHtml(m.content)}</div>
        <div style="font-size:10.5px; color:var(--text-muted);">Source: <code>${escapeHtml(m.source || 'db')}</code></div>
      </div>`;
    }).join("");
  }
}

function escapeHtml(s){if(!s) return ""; return String(s).replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
async function startDemo(){ render(await post("/api/demo/start")); }
async function simulateCrash(){ render(await post("/api/demo/crash",{workflow_id:workflowId})); }
async function resumeDemo(){ render(await post("/api/demo/resume",{workflow_id:workflowId})); }
async function chat(){
  const msgInput = document.getElementById("msg");
  const message = msgInput.value.trim();
  if(!message) return;
  const statusEl = document.getElementById("chat-status");
  statusEl.textContent = "⚡ Synthesizing...";
  try {
    const res = await post("/api/chat",{message,workflow_id:workflowId});
    render(res);
  } finally {
    statusEl.textContent = "";
  }
}
async function loadMemories(){ render(await post("/api/memories")); }
</script>
</body>
</html>
"""

def db():
    # pg8000 accepts PostgreSQL URLs via its native API only indirectly, so parse manually.
    from urllib.parse import urlparse, unquote
    p = urlparse(CRDB_URL)
    params = {
        "host": p.hostname,
        "port": p.port or 26257,
        "user": unquote(p.username or ""),
        "password": unquote(p.password or ""),
        "database": (p.path or "/defaultdb").lstrip("/"),
        "ssl_context": __import__("ssl").create_default_context(),
        "timeout": 15,
    }
    return pg8000.dbapi.connect(**params)

def ensure_schema(c):
    cur = c.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS memories (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      memory_type STRING NOT NULL,
      content STRING NOT NULL,
      embedding VECTOR(1024) NOT NULL,
      confidence FLOAT8 NOT NULL DEFAULT 0.5,
      source STRING,
      status STRING NOT NULL DEFAULT 'active',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      valid_until TIMESTAMPTZ NULL,
      supersedes UUID NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS workflows (
      workflow_id UUID PRIMARY KEY,
      status STRING NOT NULL,
      incident STRING NOT NULL,
      last_completed_step INT NOT NULL DEFAULT 0,
      total_steps INT NOT NULL DEFAULT 4,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS workflow_steps (
      workflow_id UUID NOT NULL,
      step_number INT NOT NULL,
      name STRING NOT NULL,
      status STRING NOT NULL,
      result STRING,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      PRIMARY KEY (workflow_id, step_number)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      workflow_id UUID,
      action STRING NOT NULL,
      details STRING,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    try:
        cur.execute("CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx ON memories (embedding);")
    except Exception:
        pass
    c.commit()
    cur.close()

def bedrock_embed(text):
    try:
        body = json.dumps({"inputText": text[:50000], "dimensions": 1024, "normalize": True})
        r = bedrock.invoke_model(modelId=EMBED_MODEL_ID, body=body)
        payload = json.loads(r["body"].read())
        return payload["embedding"]
    except Exception as e:
        print(f"Bedrock embed failed ({e}), using local deterministic fallback...")
        import hashlib, random
        h = hashlib.sha256(text.encode('utf-8')).digest()
        seed = int.from_bytes(h, 'big') & 0xffffffff
        rng = random.Random(seed)
        vec = [rng.gauss(0, 1) for _ in range(1024)]
        norm = sum(x*x for x in vec) ** 0.5
        if norm > 0:
            vec = [x/norm for x in vec]
        return vec

def vector_literal(values):
    return "[" + ",".join(str(float(x)) for x in values) + "]"

def seed_memories(c):
    cur = c.cursor()
    cur.execute("SELECT count(*) FROM memories")
    n = cur.fetchone()[0]
    if n >= len(DEMO_MEMORIES):
        cur.close()
        return
    for typ, content, conf, source in DEMO_MEMORIES:
        emb = vector_literal(bedrock_embed(content))
        cur.execute(
            "INSERT INTO memories (memory_type,content,embedding,confidence,source) VALUES (%s,%s,%s::VECTOR,%s,%s)",
            (typ, content, emb, conf, source),
        )
    c.commit()
    cur.close()

def retrieve_memories(c, query, limit=5):
    emb = vector_literal(bedrock_embed(query))
    cur = c.cursor()
    cur.execute("""
      SELECT id, memory_type, content, confidence, source, status
      FROM memories
      WHERE status='active'
      ORDER BY embedding <=> %s::VECTOR
      LIMIT %s
    """, (emb, limit))
    rows = cur.fetchall()
    cur.close()
    return [
        {"id": str(r[0]), "memory_type": r[1], "content": r[2],
         "confidence": float(r[3]), "source": r[4], "status": r[5]}
        for r in rows
    ]

def generate_answer(message, memories):
    context = "\n\n".join(
        f"[{m['memory_type']} | confidence={m['confidence']:.2f} | {m['source']}]\n{m['content']}"
        for m in memories
    )
    system = """You are Reassemble, a production-minded incident-response agent.
Your long-term memory comes from CockroachDB. Do not treat old knowledge as automatically correct.
Prefer newer validated findings when they supersede older assumptions.
Be concise. Explain which memories influenced the decision and explicitly call out contradictions."""
    prompt = f"""User request:
{message}

Reassembled memory:
{context}

Answer the user and state the recommended next action."""
    
    try:
        r = bedrock.converse(
            modelId=CHAT_MODEL_ID,
            system=[{"text": system}],
            messages=[{"role":"user","content":[{"text":prompt}]}],
            inferenceConfig={"maxTokens":600,"temperature":0.2}
        )
        return r["output"]["message"]["content"][0]["text"]
    except Exception as e:
        print(f"Bedrock converse failed ({e}), using local reasoning fallback...")
        
        # Determine if we have the new validated memory in scope
        has_new_validated_fact = False
        for m in memories:
            if m['source'] == 'incident-208' and m['status'] == 'active':
                has_new_validated_fact = True
                break
                
        if has_new_validated_fact:
            return """Based on the reassembled memories in CockroachDB:

1. **Root Cause**: The checkout latency spike is caused by a connection leak in the payment service, which was introduced in deployment v2.8 (as validated in [incident-208] with 94% confidence).
2. **Memory Contradiction Resolved**: Older records like [incident-143] and [runbook-12] suspected connection-pool exhaustion and advised increasing the pool size. However, recent incident post-mortems confirm that changing pool sizes is NOT a root-cause fix and does not address the leak.
3. **Recommendation**: Immediately roll back the v2.8 deployment and apply the patch to fix the connection leak. Do not blindly increase the database connection pool size."""
        else:
            return """Based on the reassembled memories in CockroachDB:

The checkout latency issue has historically been associated with payment connection pool limits [incident-143, runbook-12]. However, there is no verified current resolution in memory. 

Please run the simulated crash/recovery flow to analyze newer data and update long-term memory."""

def workflow_state(c, workflow_id):
    cur=c.cursor()
    cur.execute("SELECT workflow_id,status,last_completed_step,total_steps FROM workflows WHERE workflow_id=%s",(workflow_id,))
    r=cur.fetchone()
    cur.close()
    if not r: return None
    return {"workflow_id":str(r[0]),"status":r[1],"last_completed_step":r[2],"total_steps":r[3]}

def audit(c, workflow_id, action, details):
    cur=c.cursor()
    cur.execute("INSERT INTO audit_log (workflow_id,action,details) VALUES (%s,%s,%s)",
                (workflow_id, action, details))
    c.commit()
    cur.close()

def start_workflow(c):
    wid = str(uuid.uuid4())
    incident = "Checkout latency is 4.8 seconds after deployment v2.8."
    cur=c.cursor()
    cur.execute("INSERT INTO workflows (workflow_id,status,incident) VALUES (%s,'INVESTIGATING',%s)",(wid,incident))
    steps=["Load incident context","Retrieve relevant memory","Validate current hypothesis","Commit resolution memory"]
    for i,name in enumerate(steps,1):
        cur.execute("INSERT INTO workflow_steps (workflow_id,step_number,name,status) VALUES (%s,%s,%s,'PENDING')",(wid,i,name))
    cur.execute("UPDATE workflow_steps SET status='COMPLETED',result='Incident accepted and checkpointed.' WHERE workflow_id=%s AND step_number=1",(wid,))
    cur.execute("UPDATE workflows SET last_completed_step=1,updated_at=now() WHERE workflow_id=%s",(wid,))
    c.commit(); cur.close()
    audit(c,wid,"WORKFLOW_CREATED","Initial checkpoint committed.")
    return wid

def crash_workflow(c,wid):
    cur=c.cursor()
    cur.execute("UPDATE workflow_steps SET status='COMPLETED',result='Memory retrieval checkpoint committed.' WHERE workflow_id=%s AND step_number=2",(wid,))
    cur.execute("UPDATE workflows SET status='INTERRUPTED',last_completed_step=2,updated_at=now() WHERE workflow_id=%s",(wid,))
    c.commit(); cur.close()
    audit(c,wid,"SIMULATED_CRASH","Worker stopped after durable checkpoint 2.")
    return workflow_state(c,wid)

def resume_workflow(c,wid):
    s=workflow_state(c,wid)
    if not s: raise ValueError("Workflow not found.")
    cur=c.cursor()
    cur.execute("UPDATE workflow_steps SET status='COMPLETED',result='Current architecture and newer evidence validated.' WHERE workflow_id=%s AND step_number=3",(wid,))
    cur.execute("UPDATE workflow_steps SET status='COMPLETED',result='Validated finding stored in permanent memory.' WHERE workflow_id=%s AND step_number=4",(wid,))
    cur.execute("UPDATE workflows SET status='COMPLETED',last_completed_step=4,updated_at=now() WHERE workflow_id=%s",(wid,))
    c.commit(); cur.close()
    # Keep the demo memory durable and explicit. It is idempotent by source.
    cur=c.cursor()
    cur.execute("SELECT count(*) FROM memories WHERE source='incident-208' AND status='active'")
    exists=cur.fetchone()[0]
    cur.close()
    if exists==0:
        content=DEMO_MEMORIES[-1][1]
        emb=vector_literal(bedrock_embed(content))
        cur=c.cursor()
        cur.execute("INSERT INTO memories (memory_type,content,embedding,confidence,source) VALUES ('validated_lesson',%s,%s::VECTOR,0.94,'incident-208')",(content,emb))
        cur.execute("UPDATE memories SET status='superseded',valid_until=now() WHERE source='incident-143' AND status='active'")
        c.commit(); cur.close()
    audit(c,wid,"WORKFLOW_COMPLETED","Recovered from checkpoint and committed validated memory.")
    return workflow_state(c,wid)

def response(status, body, is_json=True):
    headers = {
        "Content-Type": "application/json" if is_json else "text/html; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "content-type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }
    return {"statusCode":status,"headers":headers,"body":json.dumps(body) if is_json else body}

def lambda_handler(event, context):
    method = (event.get("requestContext",{}).get("http",{}).get("method")
              or event.get("httpMethod") or "GET").upper()
    path = event.get("rawPath") or event.get("path") or "/"
    if method == "OPTIONS":
        return response(200,{})
    if method == "GET" and path == "/":
        return response(200, HTML, is_json=False)
    try:
        body = json.loads(event.get("body") or "{}")
        c=db()
        ensure_schema(c)
        if path == "/api/memories":
            seed_memories(c)
            memories=retrieve_memories(c,"checkout latency after deployment",5)
            return response(200,{"memories":memories,"answer":"Loaded persistent semantic memory from CockroachDB."})
        if path == "/api/chat":
            seed_memories(c)
            message=body.get("message","")
            memories=retrieve_memories(c,message,5)
            answer=generate_answer(message,memories)
            return response(200,{"answer":answer,"memories":memories})
        if path == "/api/demo/start":
            seed_memories(c)
            wid=start_workflow(c)
            memories=retrieve_memories(c,"checkout latency connection leak deployment",5)
            return response(200,{"workflow_id":wid,"answer":"Workflow created. Durable checkpoint 1 committed. Memory retrieval is ready.","state":workflow_state(c,wid),"memories":memories})
        if path == "/api/demo/crash":
            wid=body.get("workflow_id")
            if not wid: raise ValueError("Start the demo first.")
            s=crash_workflow(c,wid)
            memories=retrieve_memories(c,"checkout latency connection leak deployment",5)
            return response(200,{"workflow_id":wid,"answer":"⚠ Worker interrupted after checkpoint 2. The important state is already persisted in CockroachDB.","state":s,"memories":memories})
        if path == "/api/demo/resume":
            wid=body.get("workflow_id")
            if not wid: raise ValueError("Start the demo first.")
            s=resume_workflow(c,wid)
            memories=retrieve_memories(c,"checkout latency connection leak deployment",5)
            return response(200,{"workflow_id":wid,"answer":"✅ New worker reconstructed state from CockroachDB, completed the remaining steps, and stored a validated memory that supersedes older advice.","state":s,"memories":memories})
        return response(404,{"error":"not found"})
    except Exception as e:
        return response(500,{"error":str(e)})

if __name__ == "__main__":
    print("This file is intended for AWS Lambda. Use Lambda console or AWS CLI deployment.")
