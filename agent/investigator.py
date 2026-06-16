import json, time, hashlib, os
from groq import Groq
from tools.summarize import summarize, store_overview, filter_rows
from tools.executor import run_vol

MODEL = "llama-3.1-8b-instant"
MAX_TURNS = 10
LLM_CACHE_DIR = "evidence/llm_cache"
os.makedirs(LLM_CACHE_DIR, exist_ok=True)

def strip_json(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1].replace("json", "", 1)
    return json.loads(t.strip())

def cached_llm_call(messages, temperature=0.1):
    key = hashlib.md5(json.dumps(messages, sort_keys=True).encode()).hexdigest()
    cache_file = f"{LLM_CACHE_DIR}/{key}.json"
    if os.path.exists(cache_file):
        print("  [llm cache hit]")
        with open(cache_file) as f:
            return json.load(f)["content"]
    client = Groq()
    try:
        resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=temperature)
        raw = resp.choices[0].message.content
    except Exception as e:
        if "429" in str(e):
            print("Rate limited. Waiting 65 seconds...")
            time.sleep(65)
            resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=temperature)
            raw = resp.choices[0].message.content
        else:
            raise
    with open(cache_file, "w") as f:
        json.dump({"content": raw}, f)
    return raw

def investigate(image, store, system_prompt):
    inspected = []

    # Minimal initial payload: overview + pslist only. Agent requests malfind/netscan via inspect.
    initial = {
        "overview": store_overview(store),
        "pslist": summarize(
            next(e for e in store.items if e["action"] == "windows.pslist"),
            max_rows=12, fields=["PID", "PPID", "ImageFileName"],
        ),
        "malfind": summarize(
            next(e for e in store.items if e["action"] == "windows.malfind"),
            max_rows=8, fields=["PID", "Process", "Protection"],
        ),
        "netscan": summarize(
            next(e for e in store.items if e["action"] == "windows.netscan"),
            max_rows=8, fields=["PID", "ForeignAddr", "State", "Owner"],
        ),
    }
    inspected += [e["evidence_id"] for e in store.items
                  if e["action"] in ("windows.pslist", "windows.malfind", "windows.netscan")]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(initial)},
    ]

    for turn in range(MAX_TURNS):
        already_run_plugins = [e["action"] for e in store.items]
        reminder = (
            f" Inspected: {inspected}. Plugins run: {already_run_plugins}."
            f" Do NOT repeat. Budget left: {MAX_TURNS - turn}."
        )

        # keep system + first user + last 4 turns only
        send = messages[:2] + messages[-4:] if len(messages) > 6 else messages[:]
        send = [m.copy() for m in send]
        send[-1]["content"] += reminder

        raw = cached_llm_call(send)
        messages.append({"role": "assistant", "content": raw})

        try:
            act = strip_json(raw)
        except json.JSONDecodeError:
            messages.append({"role": "user", "content": "Invalid JSON. One JSON action only."})
            continue

        print(f"[turn {turn}] {act.get('action')} {act.get('evidence_id') or act.get('plugin') or ''}")

        if act["action"] == "finalize":
            return act["findings"]

        if act["action"] == "inspect":
            eid = act["evidence_id"]
            ev = store.get(eid)
            if ev is None:
                result = {"error": f"'{eid}' not found. Use exact IDs from overview."}
            else:
                inspected.append(eid)
                result = summarize(ev, max_rows=10)

        elif act["action"] == "filter":
            eid = act["evidence_id"]
            ev = store.get(eid)
            if ev is None:
                result = {"error": f"'{eid}' not found. Use exact IDs from overview."}
            else:
                filter_key = f"{eid}:{act['key']}={act['value']}"
                if filter_key in inspected:
                    result = {"error": f"Already filtered {eid}. Move on."}
                else:
                    inspected.append(filter_key)
                    result = filter_rows(ev, act["key"], act["value"], max_rows=10)

        elif act["action"] == "run_plugin":
            plugin_name = act["plugin"]
            if plugin_name in already_run_plugins:
                result = {"error": f"Plugin '{plugin_name}' already run. Use inspect or filter."}
            else:
                ev = run_vol(image, plugin_name, act.get("pid"))
                store.add(ev)
                inspected.append(ev["evidence_id"])
                result = summarize(ev, max_rows=10)

        else:
            result = {"error": "unknown action"}

        messages.append({"role": "user", "content": json.dumps(result)})

    messages.append({"role": "user", "content": "Budget exhausted. Finalize now with findings JSON."})
    send = messages[:2] + messages[-4:] if len(messages) > 6 else messages
    raw = cached_llm_call(send)
    return strip_json(raw)["findings"]