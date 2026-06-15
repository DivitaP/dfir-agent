import subprocess, json, uuid, datetime, hashlib, os

CACHE_DIR = "evidence/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def run_vol(image, plugin, pid=None):
    key = hashlib.md5(f"{image}:{plugin}:{pid}".encode()).hexdigest()
    cache_file = f"{CACHE_DIR}/{key}.json"

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            print(f"  [cache hit] {plugin}")
            return json.load(f)

    cmd = ["vol", "-r", "json", "-f", image, plugin]
    if pid:
        cmd += ["--pid", str(pid)]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    parsed = json.loads(out.stdout) if out.stdout.strip() else []
    ev = make_evidence("volatility", plugin, " ".join(cmd), out.stdout, parsed)

    with open(cache_file, "w") as f:
        json.dump(ev, f)
    return ev

def make_evidence(tool, action, command, raw, parsed):
    return {
        "evidence_id": f"EV-{uuid.uuid4().hex[:8]}",
        "tool": tool,
        "action": action,
        "command": command,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "raw_output": raw[:20000],
        "parsed": parsed,
    }
