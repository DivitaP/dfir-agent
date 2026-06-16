from datetime import datetime

def generate_report(verified_findings, image_path, output_path="evidence/report.html"):
    accepted = [f for f in verified_findings if f["verdict"] == "accept"]
    rejected = [f for f in verified_findings if f["verdict"] == "reject"]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    conf_color = {"high": "#dc2626", "medium": "#d97706", "low": "#2563eb"}

    def card(f, idx, is_accepted):
        color = conf_color.get(f.get("confidence", "low"), "#6b7280")
        border = "#16a34a" if is_accepted else "#dc2626"
        badge = "ACCEPTED" if is_accepted else "REJECTED"
        badge_bg = "#16a34a" if is_accepted else "#dc2626"
        eids = ", ".join(f"<code>{e}</code>" for e in f.get("evidence_ids", []))
        return f"""
        <div style="border-left:4px solid {border};background:#1e1e1e;border-radius:6px;padding:16px;margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-size:13px;font-weight:600;color:#e5e7eb;">Finding {idx}</span>
            <div>
              <span style="background:{badge_bg};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;margin-right:6px;">{badge}</span>
              <span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;">{f.get('confidence','?').upper()}</span>
            </div>
          </div>
          <p style="color:#f3f4f6;margin:0 0 8px 0;font-size:14px;">{f['claim']}</p>
          <p style="color:#9ca3af;font-size:12px;margin:0 0 4px 0;"><strong style="color:#6b7280;">Category:</strong> {f.get('category','unknown')}</p>
          <p style="color:#9ca3af;font-size:12px;margin:0 0 4px 0;"><strong style="color:#6b7280;">Evidence:</strong> {eids}</p>
          <p style="color:#9ca3af;font-size:12px;margin:0;"><strong style="color:#6b7280;">Verifier:</strong> {f.get('verifier_reason','')}</p>
        </div>"""

    cards_accepted = "".join(card(f, i+1, True) for i, f in enumerate(accepted))
    cards_rejected = "".join(card(f, i+1, False) for i, f in enumerate(rejected))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DFIR Investigation Report</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#111; color:#e5e7eb; padding:32px; }}
  .container {{ max-width:900px; margin:0 auto; }}
  h1 {{ font-size:24px; font-weight:700; color:#f9fafb; margin-bottom:4px; }}
  h2 {{ font-size:16px; font-weight:600; color:#9ca3af; margin:28px 0 12px 0; text-transform:uppercase; letter-spacing:0.05em; border-bottom:1px solid #374151; padding-bottom:6px; }}
  .meta {{ color:#6b7280; font-size:13px; margin-bottom:24px; }}
  .meta span {{ margin-right:20px; }}
  .stats {{ display:flex; gap:12px; margin-bottom:28px; }}
  .stat {{ background:#1e1e1e; border-radius:8px; padding:16px 24px; flex:1; text-align:center; }}
  .stat .num {{ font-size:28px; font-weight:700; }}
  .stat .label {{ font-size:12px; color:#6b7280; margin-top:2px; }}
  .green {{ color:#16a34a; }} .red {{ color:#dc2626; }} .blue {{ color:#2563eb; }}
  code {{ background:#374151; padding:1px 5px; border-radius:3px; font-size:11px; color:#93c5fd; }}
  .method {{ background:#1e1e1e; border-radius:6px; padding:14px; color:#9ca3af; font-size:13px; line-height:1.6; }}
  .pdf-btn {{ background:#2563eb; color:#fff; border:none; padding:10px 20px; border-radius:6px; font-size:13px; font-weight:600; cursor:pointer; float:right; margin-top:-8px; }}
  .pdf-btn:hover {{ background:#1d4ed8; }}
  @media print {{
    .pdf-btn {{ display:none; }}
    body {{ background:#fff; color:#111; padding:16px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <button class="pdf-btn" onclick="window.print()">Download PDF</button>
  <h1>DFIR Autonomous Investigation Report</h1>
  <div class="meta">
    <span>Image: <code>{image_path}</code></span>
    <span>Generated: {now}</span>
  </div>
  <div class="stats">
    <div class="stat"><div class="num blue">{len(verified_findings)}</div><div class="label">Total Findings</div></div>
    <div class="stat"><div class="num green">{len(accepted)}</div><div class="label">Accepted</div></div>
    <div class="stat"><div class="num red">{len(rejected)}</div><div class="label">Rejected by Verifier</div></div>
  </div>
  <h2>Accepted Findings</h2>
  {cards_accepted or '<p style="color:#6b7280;font-size:13px;">No accepted findings.</p>'}
  <h2>Rejected Findings — Caught by Verifier</h2>
  {cards_rejected or '<p style="color:#6b7280;font-size:13px;">No rejected findings.</p>'}
  <h2>Methodology</h2>
  <div class="method">
    An investigator agent autonomously selected and executed Volatility 3 plugins against the memory image.
    Every finding was required to cite specific evidence IDs from the evidence store.
    A separate verifier agent reviewed each finding alongside its cited evidence and issued an independent verdict.
    Findings with hallucinated, missing, or unsupported evidence IDs were rejected and are shown above.
    Only evidence-backed findings appear in the accepted section.
  </div>
</div>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Report written to {output_path}")
    return output_path