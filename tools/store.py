import json

class EvidenceStore:
    def __init__(self, path="evidence/store.json"):
        self.path, self.items = path, []
    def add(self, ev):
        self.items.append(ev)
        with open(self.path, "w") as f:
            json.dump(self.items, f, indent=2)
        return ev["evidence_id"]
    def get(self, eid):
        return next((e for e in self.items if e["evidence_id"] == eid), None)
