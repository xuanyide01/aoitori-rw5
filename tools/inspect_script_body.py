import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3_strings")

for name in ["snhmr3.json", "sn101.json", "sn108.json", "menu.json", "omake.json"]:
    rows = json.loads((d / name).read_text("utf-8"))
    print(f"=== {name} (total={len(rows)}) ===")
    start = 240
    for r in rows[start : start + 50]:
        print(f"  [{r['off']:05x}] ({r['nop']}) {r['s']!r}")
