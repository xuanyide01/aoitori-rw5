import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")

# Check L186 in sn108.ps3
p108 = code_dir / "sn108.ps3"
hdr, labels, code, text = parse_ps3_raw(p108)
lb = 4 * len(labels)
off = labels[186] + lb
print(f"sn108 L186 @ 0x{off:x}..0x{labels[187]+lb if len(labels)>187 else off+64:x}:")
for o, t in disasm(code, text, off, off + 200, lb)[:30]:
    print(f"  {o:05x}: {t}")

# Check ALL scripts for `L186`, `L187`, `L188`, `L189`, `L198`, `L0`, and `sys_int_call` values
print("\n=== L189 and sys_int_call across all scripts ===")
int_calls = {}
for p in sorted(code_dir.glob("*.ps3")):
    hdr, labels, code, text = parse_ps3_raw(p)
    lb = 4 * len(labels)
    insns = disasm(code, text, hdr[8], len(code), lb)
    for i, (o, t) in enumerate(insns):
        if t == "SYS sys_int_call" and i >= 2:
            ctx = [insns[j][1] for j in range(max(0, i-6), i+1)]
            int_calls.setdefault(insns[i-2][1], set()).add(p.stem)
    if p.stem in ("sn299", "sn399", "sn499", "sn605"):
        print(f"\n--- {p.stem} non-L77 calls / flag ops ---")
        for i, (o, t) in enumerate(insns):
            if ("P[" in t and "=" in t) or "L19" in t or "L186" in t or "L188" in t or "script_open" in t or "L0" in t:
                ctx = insns[i-1][1] if i > 0 else ""
                print(f"  {o:05x}: ({ctx}) -> {t}")

print("\nsys_int_call arg guesses:", {k: sorted(v)[:5] for k, v in int_calls.items()})

# Check intproc.bin functions for P[2156], 64, 37, CG gallery, choices
print("\n=== Inspecting intproc.bin ===")
p_ip = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intproc.bin")
hdr, labels, code, text = parse_ps3_raw(p_ip)
lb = 4 * len(labels)
ip_insns = disasm(code, text, lb, len(code), lb)
for i, (o, t) in enumerate(ip_insns):
    if any(k in t for k in ("2156", "2157", "2145", "G[64]", "G[37]", "select_button_create", "sn501")):
        print(f"  intproc@0x{o:05x}: {t}")
