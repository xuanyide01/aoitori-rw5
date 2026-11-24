import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
p101 = code_dir / "sn101.ps3"
hdr, labels, code, text = parse_ps3_raw(p101)
lb = 4 * len(labels)

def show_lbl(lidx, max_lines=80):
    off = labels[lidx] + lb
    # find next label offset > off
    nxt = min([la + lb for la in labels if la + lb > off] + [hdr[8]])
    insns = disasm(code, text, off, nxt, lb)
    print(f"\n=== sn101 stdlib L{lidx} @ 0x{off:05x}..0x{nxt:05x} ({len(insns)} insns) ===")
    for o, t in insns[:max_lines]:
        print(f"  {o:05x}: {t}")
    if len(insns) > max_lines:
        print(f"  ... ({len(insns) - max_lines} more)")

for lidx in (190, 191, 192, 1, 189, 188, 12, 13, 14, 15, 119, 120, 122, 124, 126, 127, 129, 131, 133, 134):
    show_lbl(lidx, 60)

# Also inspect L191 / L192 / L0 calls in sn299, sn399, sn499, sn605, sn101
print("\n=== L0/L190/L191/L192/L189 call sites ===")
for stem in ("sn101", "sn103", "sn108", "sn214", "sn299", "sn312", "sn399", "sn413", "sn499", "sn510", "sn603", "sn605", "snhmr3"):
    p = code_dir / f"{stem}.ps3"
    h, lbls, c, tx = parse_ps3_raw(p)
    ins = disasm(c, tx, h[8], len(c), 4 * len(lbls))
    for i, (o, t) in enumerate(ins):
        if t in ("CALL L0", "CALL L190", "CALL L191", "CALL L192", "CALL L189", "CALL L186", "CALL L198", "CALL L199"):
            args = [ins[j][1] for j in range(max(0, i-12), i)]
            print(f"  {stem:8s}@0x{o:05x} {t}: prev={args[-6:]}")
