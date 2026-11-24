import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")

# 1. Inspect L186 full body in sn101.ps3
p101 = code_dir / "sn101.ps3"
hdr, labels, code, text = parse_ps3_raw(p101)
lb = 4 * len(labels)
print(f"sn101 L186=0x{labels[186]+lb:x}, L187=0x{labels[187]+lb:x}, L188=0x{labels[188]+lb:x}, L189=0x{labels[189]+lb:x}, L198=0x{labels[198]+lb:x}")
insns = disasm(code, text, labels[186] + lb, labels[188] + lb, lb)
out = [f"  {o:05x}: {t}" for o, t in insns if "P[" in t or "G[" in t or "SYS" in t or "CALL" in t or "EXPR" in t and ("=" in t or "'" in t)]
Path(r"E:\Antigravity\aoitori-rw5\probe\l186_inspect.txt").write_text("\n".join(f"  {o:05x}: {t}" for o, t in insns), "utf-8")
print(f"Wrote l186_inspect.txt ({len(insns)} lines)")

# 2. Check ALL occurrences of P[...] writes across ALL 85 scripts (after beg_pc AND inside stdlib)
print("\n=== ALL P[...] assignments across all 85 scripts ===")
for p in sorted(code_dir.glob("*.ps3")):
    hdr, labels, code, text = parse_ps3_raw(p)
    lb = 4 * len(labels)
    start = hdr[8] if p.stem != "sn101" else lb
    insns = disasm(code, text, start, len(code), lb)
    for o, t in insns:
        if "P[" in t and ("=" in t or "++" in t) and "==" not in t and "!=" not in t:
            loc = "stdlib" if o < hdr[8] else "body"
            print(f"  {p.stem:10s} [{loc:6s}] @ 0x{o:05x}: {t}")

# 3. Check ALL snh* scripts: how do they end and what L0/flags do they have?
print("\n=== All snh* scripts flow ===")
for p in sorted(code_dir.glob("snh*.ps3")):
    hdr, labels, code, text = parse_ps3_raw(p)
    lb = 4 * len(labels)
    insns = disasm(code, text, hdr[8], len(code), lb)
    head = [t for _, t in insns[:25]]
    tail = [t for _, t in insns[-35:]]
    opens = [t for _, t in insns if ".ps3" in t or "CALL L19" in t or "CALL L18" in t or "CALL L0" in t or "sys_int_call" in t]
    print(f"  {p.stem:10s}: opens={opens}")
