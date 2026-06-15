import sys
from tools.executor import run_vol
from tools.store import EvidenceStore

PLUGINS = ["windows.info", "windows.pslist", "windows.pstree",
           "windows.cmdline", "windows.netscan", "windows.malfind",
           "windows.dlllist"]

store = EvidenceStore()
image = sys.argv[1]
for p in PLUGINS:
    ev = run_vol(image, p)
    eid = store.add(ev)
    print(f"{eid}  {p}  {len(ev['parsed'])} rows")
