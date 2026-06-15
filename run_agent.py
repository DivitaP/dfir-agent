import sys, json
from tools.store import EvidenceStore
from agent.investigator import investigate
from agent.prompts import INVESTIGATOR_SYSTEM

store = EvidenceStore()
with open("evidence/store.json") as f:
    store.items = json.load(f)

findings = investigate(sys.argv[1], store, INVESTIGATOR_SYSTEM)

with open("evidence/findings.json", "w") as f:
    json.dump(findings, f, indent=2)

for fd in findings:
    print(f"[{fd['confidence'].upper()}] {fd['claim']}  <- {fd['evidence_ids']}")
