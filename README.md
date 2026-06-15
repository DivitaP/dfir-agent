# DFIR Autonomous Investigation Agent

An autonomous memory forensics agent that investigates Windows memory images, validates every finding against raw evidence, and rejects unsupported conclusions before generating a traceable incident report.

Built for the Find Evil! hackathon on the SANS SIFT Workstation.

---

## The Problem

DFIR analysts spend hours manually triaging memory images — running the same Volatility plugins, correlating output across tools, and writing findings reports. The bottleneck is not running the tools; it is the reasoning layer: correlating a suspicious process in `pslist` with an injected region in `malfind` and an outbound connection in `netscan`, then writing a defensible finding with evidence citations.

LLMs can reason over structured tool output — but they hallucinate. An AI report without evidence citations is useless in real incident response and could not survive legal scrutiny.

This project solves both problems: an investigator agent that reasons autonomously over Volatility output, and a verifier agent that rejects any finding it cannot trace to a specific evidence artifact.

---

## Architecture

```
Memory Image (.raw)
        |
        v
 run_tools.py
        |
   Volatility 3 (pslist, pstree, cmdline, netscan, malfind, dlllist)
        |
        v
 Evidence Store (evidence/store.json)
 Each entry: { evidence_id, tool, action, command, timestamp, raw_output, parsed }
        |
        v
 Investigator Agent (LLM)
 - Receives pslist, malfind, netscan summaries upfront
 - Chooses actions: inspect, filter, run_plugin, finalize
 - Every finding must cite evidence_ids
 - Budget: 10 actions
        |
        v
 findings.json
        |
        v
 Verifier Agent (LLM)
 - Separate LLM pass, independent of investigator
 - Reads each finding alongside its cited evidence
 - Verdict: accept or reject with reason
 - Rejected findings appear in the report as caught errors
        |
        v
 Report Generator
 - HTML report with PDF export
 - Accepted findings with evidence citations
 - Rejected findings section (self-correction evidence)
 - Full methodology section
        |
        v
 evidence/report.html
```

---

![Architecture](./architecture-diagram.png)

---

## Self-Correction

The verifier agent is architecturally separate from the investigator. It receives each finding and the raw evidence it cited, then issues an independent verdict. Findings with:
- Hallucinated evidence IDs (not present in the store)
- Evidence that does not support the claim
- Vague or uncorroborated conclusions

...are rejected and appear in the report under "Rejected Findings — Caught by Verifier." This is not a scripted retry. It is a genuine second-pass validation that will catch the investigator hallucinating, citing the wrong evidence, or overclaiming from weak signals.

---

## Evidence Traceability

Every Volatility plugin execution produces an evidence artifact:

```json
{
  "evidence_id": "EV-94b2231c",
  "tool": "volatility",
  "action": "windows.pslist",
  "command": "vol -r json -f samples/MemoryDump_Lab1.raw windows.pslist",
  "timestamp": "2026-06-15T20:14:33.421Z",
  "parsed": [...]
}
```

Every finding the investigator produces must reference one or more evidence IDs:

```json
{
  "claim": "PID 1640 (cmd.exe) has PPID 1512 (explorer.exe) which is anomalous...",
  "evidence_ids": ["EV-ed617649", "EV-31b8149f"],
  "confidence": "high",
  "category": "process_anomaly"
}
```

Judges can open `evidence/store.json`, find the cited ID, and read the exact Volatility output that produced the finding.

---

## Setup

### Requirements
- Python 3.11+
- Volatility 3
- Groq API key (free tier at console.groq.com)
- SANS SIFT Workstation (or local environment)

### Install

```bash
git clone https://github.com/DivitaP/dfir-agent.git
cd dfir-agent
python3 -m venv venv && source venv/bin/activate
pip install volatility3 groq jinja2
export GROQ_API_KEY="your-key-here"
```

### Run

**Step 1: Collect evidence from memory image**
```bash
python run_tools.py samples/your_image.raw
```
This runs 7 Volatility plugins and populates `evidence/store.json`. Results are cached so re-runs are instant.

**Step 2: Run the agent pipeline**
```bash
python run_agent.py samples/your_image.raw
```
This runs the investigator agent, verifier agent, and report generator in sequence.

**Output files:**
- `evidence/store.json` — raw tool outputs with evidence IDs
- `evidence/findings.json` — investigator agent findings
- `evidence/verified.json` — verifier verdicts
- `evidence/report.html` — final report (open in browser, print to PDF)

---

## Test Data

Tested against MemLabs Lab 1 and Lab 2 — public Windows 7 memory images with documented ground truth, available at github.com/stuxnet999/MemLabs.

```bash
# Download Lab 1
# Place MemoryDump_Lab1.raw in samples/
python run_tools.py samples/MemoryDump_Lab1.raw
python run_agent.py samples/MemoryDump_Lab1.raw
```

---

## Accuracy Report

The investigator agent operates with a 10-action budget. Observed failure modes during development:

- **Hallucinated evidence IDs**: the agent occasionally cited shortened or fabricated evidence IDs (e.g. `EV-948` instead of a real 8-character ID). The verifier catches these — the cited evidence is not found in the store, and the finding is rejected.
- **Early finalization**: with an aggressive token budget, the agent sometimes finalized before inspecting all relevant plugins. Mitigated by requiring malfind and netscan inspection before finalizing.
- **Redundant tool calls**: without tracking, the agent re-ran plugins it had already executed. Fixed by passing the list of already-run plugins in every turn reminder.
- **Overclaiming from weak signals**: a single malfind hit without network correlation was sometimes reported as high confidence. The verifier downgrades or rejects these.

Hallucinations the verifier caught are documented in `evidence/verified.json` and shown in the report. Honesty over perfection.

---

## Project Structure

```
dfir-agent/
├── agent/
│   ├── investigator.py   # investigator agent loop
│   ├── verifier.py       # verifier agent
│   ├── reporter.py       # HTML report generator
│   └── prompts.py        # system prompts
├── tools/
│   ├── executor.py       # Volatility wrapper with disk cache
│   ├── store.py          # evidence store (read/write)
│   └── summarize.py      # token-safe evidence summarizer
├── run_tools.py          # step 1: collect evidence
├── run_agent.py          # step 2: investigate + verify + report
└── README.md
```
