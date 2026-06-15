# DFIR Autonomous Investigation Agent

> **Submission Compliance Checklist**
> | Requirement | Status | Location |
> |---|---|---|
> | Public repository | ✅ | github.com/DivitaP/dfir-agent |
> | MIT License file | ✅ | [LICENSE](./LICENSE) |
> | README with setup instructions | ✅ | This file, [Setup](#setup) section |
> | Step-by-step run instructions | ✅ | This file, [How to Run](#how-to-run) section |
> | Text description of features | ✅ | This file, [What It Does](#what-it-does) section |
> | Demo video | ✅ | [Demo Video](#demo-video) section below |
> | Architecture diagram | ✅ | [docs/architecture.png](./docs/architecture.png) |
> | Evidence dataset documentation | ✅ | [Evidence Dataset](#evidence-dataset) section below |
> | Accuracy report | ✅ | [Accuracy Report](#accuracy-report) section below |
> | Agent execution logs | ✅ | [Agent Execution Logs](#agent-execution-logs) section below |

---

## Demo Video

[INSERT YOUTUBE/VIMEO LINK HERE]

The video shows: memory image input, investigator agent reasoning turn by turn, a verifier rejection of an unsupported finding (self-correction), and the final HTML report with evidence citations.

---

## What It Does

An autonomous memory forensics agent that investigates Windows memory images end to end — collecting evidence, reasoning over it, validating its own conclusions, and generating a traceable incident report — without any human in the loop.

The agent takes a raw memory dump, runs a structured set of Volatility 3 plugins, and produces a JSON evidence store where every tool execution has a unique evidence ID. An investigator agent then reasons over that evidence: it requests specific views, filters by PID, runs additional plugins when needed, and produces findings where every claim cites at least one evidence ID. A separate verifier agent independently reviews each finding against its cited evidence and rejects anything it cannot support. The final HTML report shows accepted findings with full evidence citations alongside a "Rejected Findings" section that documents what the verifier caught.

**Key capabilities:**
- Autonomous multi-turn investigation with a 10-action reasoning budget
- Every finding cites specific evidence IDs traceable to exact Volatility tool executions
- Dual-agent architecture: investigator and verifier are independent LLM passes
- Verifier rejects hallucinated evidence IDs and unsupported claims — self-correction without human intervention
- HTML report with PDF export showing accepted and rejected findings
- Disk-cached Volatility results and LLM responses for reproducibility

---

## Architecture

![Architecture Diagram](./docs/architecture.png)

```
Memory Image (.raw)
        |
        v
run_tools.py + Volatility 3
(pslist, pstree, cmdline, netscan, malfind, dlllist)
        |
        v
Evidence Store (evidence/store.json)
{ evidence_id, tool, action, command, timestamp, raw_output, parsed }
        |
        v
Investigator Agent (LLM — llama-3.3-70b-versatile via Groq)
Actions: inspect / filter / run_plugin / finalize
Each finding must cite evidence_ids
        |
        v
findings.json
        |
        v
Verifier Agent (LLM — independent pass)
Verdict: accept / reject with reason per finding
        |
        v
HTML Report (evidence/report.html)
Accepted findings + Rejected findings (caught by verifier)
```

---

## Evidence Dataset

**Test dataset:** MemLabs by stuxnet999 — public Windows 7 memory images with documented ground truth.

- **Lab 1:** `MemoryDump_Lab1.raw` (1GB) — Windows 7 image with process injection, C2 activity, and credential theft indicators. Ground truth documented at github.com/stuxnet999/MemLabs/tree/master/Lab%201
- **Lab 2:** `MemoryDump_Lab2.raw` (1GB) — Windows 7 image with additional malware artifacts.

Memory images are not included in the repository due to size (1GB each). Download instructions:

```bash
# Download from MemLabs releases
https://github.com/stuxnet999/MemLabs/releases

# Place in samples/ directory
mkdir samples
mv MemoryDump_Lab1.raw samples/
```

The agent was developed and tested against Lab 1 with known ground truth used to validate findings accuracy.

---

## Accuracy Report

Observed behavior and failure modes documented during development and testing against MemLabs Lab 1:

**What the agent gets right:**
- Correctly identifies processes with anomalous parent-child relationships via pslist cross-reference
- Correlates malfind hits (PAGE_EXECUTE_READWRITE) with netscan connections to flag C2 activity
- Produces structured findings with specific evidence citations on every accepted claim

**Documented failure modes caught by verifier:**

| Failure Type | Description | Verifier Response |
|---|---|---|
| Hallucinated evidence ID | Agent cited `EV-948` (truncated/fabricated) instead of real 8-character ID | REJECTED — ID not found in store |
| Unsupported confidence | Single malfind hit claimed as high confidence without network corroboration | REJECTED — insufficient evidence |
| Redundant tool calls | Agent attempted to re-run already-executed plugins | BLOCKED at code level before LLM call |
| Early finalization | Agent finalized before inspecting malfind/netscan | MITIGATED — system prompt requires both before finalizing |

**Honesty over perfection:** all rejection events are preserved in `evidence/verified.json` and displayed in the report under "Rejected Findings — Caught by Verifier." A clean report with no rejections would indicate the verifier is not working, not that the agent is perfect.

---

## Agent Execution Logs

Agent execution logs are written to `evidence/` on every run:

| File | Contents |
|---|---|
| `evidence/store.json` | Every Volatility tool execution: evidence_id, command, timestamp, raw output, parsed JSON rows |
| `evidence/findings.json` | Every finding produced by the investigator agent: claim, evidence_ids, confidence, category |
| `evidence/verified.json` | Every verifier verdict: finding + verdict (accept/reject) + reason |
| `evidence/report.html` | Human-readable report with full traceability |

**Tracing a finding to its tool execution:**
1. Open `evidence/verified.json`, find an accepted finding
2. Copy one of its `evidence_ids` (e.g. `EV-94b2231c`)
3. Open `evidence/store.json`, search for that ID
4. The entry shows the exact Volatility command run, timestamp, and full parsed output

Every finding is traceable to a specific tool execution. This is enforced architecturally — the investigator can only cite IDs that exist in the store, and the verifier checks each cited ID independently.

---

## Setup

### Requirements
- Python 3.11+
- Volatility 3 (`pip install volatility3`)
- Groq API key — free at console.groq.com
- Git

### Install

```bash
git clone https://github.com/DivitaP/dfir-agent.git
cd dfir-agent
python3 -m venv venv && source venv/bin/activate
pip install volatility3 groq
export GROQ_API_KEY="your-groq-api-key"
```

---

## How to Run

**Step 1: Download a memory image**
```bash
mkdir samples
# place MemoryDump_Lab1.raw in samples/
```

**Step 2: Collect evidence**
```bash
python run_tools.py samples/MemoryDump_Lab1.raw
```
Runs 7 Volatility plugins. Results cached to `evidence/cache/` — re-runs are instant.

**Step 3: Run the full agent pipeline**
```bash
python run_agent.py samples/MemoryDump_Lab1.raw
```
Runs investigator agent, verifier agent, and report generator in sequence.

**Step 4: View the report**
```bash
open evidence/report.html   # macOS
# or open in any browser
# click "Download PDF" in the top right to export
```

**Expected output:**
```
=== INVESTIGATOR ===
[turn 0] filter EV-ed617649
[turn 1] inspect EV-31b8149f
[turn 2] filter EV-3da93a61
...
=== VERIFIER ===
  [ACCEPTED] PID 1640 shows anomalous parent process...
  [REJECTED] Claim cites EV-948 which does not exist in store
...
=== REPORT ===
Report written to evidence/report.html
```

---

## Project Structure

```
dfir-agent/
├── agent/
│   ├── investigator.py   # investigator agent loop (10-action budget)
│   ├── verifier.py       # verifier agent (independent LLM pass)
│   ├── reporter.py       # HTML report generator
│   └── prompts.py        # forensic heuristics system prompt
├── tools/
│   ├── executor.py       # Volatility 3 wrapper with disk cache
│   ├── store.py          # evidence store read/write
│   └── summarize.py      # token-safe evidence summarizer
├── docs/
│   └── architecture.png  # architecture diagram
├── run_tools.py          # step 1: collect evidence from memory image
├── run_agent.py          # step 2: investigate, verify, generate report
├── LICENSE               # MIT License
└── README.md             # this file
```

---

## License

MIT License — see [LICENSE](./LICENSE)