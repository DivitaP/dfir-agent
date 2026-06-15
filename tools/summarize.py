def summarize(ev, max_rows=15, fields=None):
    if ev is None:
        return {"error": "evidence item is None"}
    rows = ev["parsed"] if isinstance(ev["parsed"], list) else []
    if fields:
        rows = [{k: r.get(k) for k in fields if k in r} for r in rows]
    return {
        "evidence_id": ev["evidence_id"],
        "action": ev["action"],
        "total_rows": len(rows),
        "rows": rows[:max_rows],
    }

def store_overview(store):
    return [
        {
            "evidence_id": e["evidence_id"],
            "action": e["action"],
            "rows": len(e["parsed"]) if isinstance(e["parsed"], list) else 0,
        }
        for e in store.items
    ]

def filter_rows(ev, key, value, max_rows=15):
    rows = [r for r in ev["parsed"] if str(r.get(key, "")) == str(value)]
    return {
        "evidence_id": ev["evidence_id"],
        "filter": f"{key}={value}",
        "total_rows": len(rows),
        "rows": rows[:max_rows],
    }
