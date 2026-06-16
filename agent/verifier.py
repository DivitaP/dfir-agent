import json
from groq import Groq

MODEL = "llama-3.1-8b-instant"

VERIFIER_SYSTEM = """You are a forensic evidence verifier. You receive a finding and the evidence it cites.
Does the cited evidence actually support the claim?

- If evidence directly supports the claim: {"verdict": "accept", "reason": "..."}
- If evidence is weak, missing, or contradicts: {"verdict": "reject", "reason": "..."}
- Be strict. Vague correlations are not enough.
- Respond ONLY with one JSON object, no markdown."""

def verify(findings, store):
    client = Groq()
    results = []

    for f in findings:
        cited = []
        for eid in f.get("evidence_ids", []):
            ev = store.get(eid)
            if ev:
                rows = ev["parsed"][:12] if isinstance(ev["parsed"], list) else []
                cited.append({"evidence_id": ev["evidence_id"], "action": ev["action"], "rows": rows})
            else:
                cited.append({"evidence_id": eid, "error": "NOT FOUND IN STORE"})

        payload = {"claim": f["claim"], "confidence": f.get("confidence", "unknown"), "cited_evidence": cited}

        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": VERIFIER_SYSTEM},
                    {"role": "user", "content": json.dumps(payload)},
                ],
                temperature=0.0,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].replace("json", "", 1).strip()
            verdict = json.loads(raw)
        except Exception as e:
            verdict = {"verdict": "reject", "reason": f"Verifier error: {str(e)}"}

        result = {**f, "verdict": verdict.get("verdict", "reject"), "verifier_reason": verdict.get("reason", "")}
        results.append(result)

        status = "ACCEPTED" if result["verdict"] == "accept" else "REJECTED"
        print(f"  [{status}] {f['claim'][:80]}")
        if result["verdict"] == "reject":
            print(f"           Reason: {result['verifier_reason']}")

    return results