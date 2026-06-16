import sys, json
from tools.store import EvidenceStore
from agent.investigator import investigate
from agent.verifier import verify
from agent.reporter import generate_report
from agent.prompts import INVESTIGATOR_SYSTEM

image = sys.argv[1]

store = EvidenceStore()
with open("evidence/store.json") as f:
    store.items = json.load(f)

print("\n=== INVESTIGATOR ===")
findings = investigate(image, store, INVESTIGATOR_SYSTEM)
with open("evidence/findings.json", "w") as f:
    json.dump(findings, f, indent=2)
print(f"Produced {len(findings)} findings")

print("\n=== VERIFIER ===")
verified = verify(findings, store)
with open("evidence/verified.json", "w") as f:
    json.dump(verified, f, indent=2)

print("\n=== REPORT ===")
generate_report(verified, image, "evidence/report.html")
print("Done. Open evidence/report.html in your browser.")