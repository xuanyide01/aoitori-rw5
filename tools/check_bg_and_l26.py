import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

bg_map = json.loads(Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_bg_map.json").read_text("utf-8"))
all_bg_vals = set(bg_map.values())
cmv_bgs = ["bg070a", "bg220a", "bg220b", "bg220c", "bg260a", "bg260b", "bg260c", "bg260e",
           "bg280a_l", "bg280c_l", "bg280a", "bg280c", "bg290a", "bg290c", "bg580a", "bg580c", "bg580e", "bg731e"]
for b in cmv_bgs:
    matches = [v for v in sorted(all_bg_vals) if b[:5] in v]
    print(f"  {b:10s} -> intcode matches: {matches[:5]}")

# Check L26 call sites and stdlib L26/L28
code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
p101 = code_dir / "sn101.ps3"
h, l, c, tx = parse_ps3_raw(p101)
lb = 4 * len(l)
print("\n=== L26 first 60 insns & sample call sites ===")
for o, t in disasm(c, tx, l[26]+lb, l[26]+lb+400, lb):
    if "L" in t or "SYS" in t or "R" in t or "var" in t:
        print(f"  {o:05x}: {t}")
for p in [code_dir / "sn101.ps3", code_dir / "sn202.ps3"]:
    hp, lp, cp, txp = parse_ps3_raw(p)
    ins = disasm(cp, txp, hp[8], len(cp), 4*len(lp))
    for i, (o, t) in enumerate(ins):
        if t in ("CALL L26", "CALL L28", "CALL L168"):
            prev = [ins[j][1] for j in range(max(0, i-12), i) if ins[j][1].startswith("EXPR")]
            print(f"  {p.stem}@0x{o:05x} {t}: {prev[-8:]}")
            if i > 2000:
                break
