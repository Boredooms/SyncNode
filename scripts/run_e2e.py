"""Live E2E test — submit a run and poll for completion."""
import httpx, json, time, sys

base = "http://127.0.0.1:8000"
client = httpx.Client(base_url=base, timeout=300)

goal = "Write a short original paragraph about a tree standing beside a quiet industrial road, save it as a Word document named SyncNode_Verifier_Demo.docx in the SyncNode demo workspace, open the document in Microsoft Word, verify visually and structurally that the paragraph is present, then create a browser email draft addressed to the demo recipient with the document attached. Do not send the email. Stop at the human approval boundary and report the final verified state."
print("[E2E] Posting run...")
r = client.post("/api/v1/runs", json={"goal": goal, "failure_mode": "none"})
print(f"[E2E] Response: {r.status_code}")
data = r.json()
run_id = data["run_id"]
model = data.get("model_id", "unknown")
print(f"[E2E] Run ID: {run_id}")
print(f"[E2E] Model:  {model}")

terminal = {"completed", "failed", "waiting_approval", "cancelled"}
deadline = time.time() + 3600
final_status = "unknown"

while time.time() < deadline:
    r2 = client.get(f"/api/v1/runs/{run_id}")
    st = r2.json()["status"]
    err = r2.json().get("error_message", "")
    print(f"[POLL] status={st} err={err[:60] if err else ''}", flush=True)
    if st in terminal:
        final_status = st
        break
    time.sleep(4)

print(f"\n[E2E] Final status: {final_status}")

# Steps
sr = client.get(f"/api/v1/runs/{run_id}/steps")
steps = sr.json().get("steps", [])
print(f"[E2E] Steps ({len(steps)}):")
for s in steps:
    print(f"  {s['step_key']:30s}  {s['status']:20s}  verify={s['verification']}")

# Audit
ar = client.get(f"/api/v1/runs/{run_id}/audit")
events = ar.json().get("events", [])
print(f"[E2E] Audit events: {len(events)}")
for e in events[:15]:
    print(f"  [{e['seq']:3d}] {e['type']}")

if final_status in ("completed", "waiting_approval"):
    print("\n[E2E] RESULT: SUCCESS ✓")
    sys.exit(0)
else:
    print("\n[E2E] RESULT: FAILED ✗")
    sys.exit(1)
