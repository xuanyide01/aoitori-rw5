import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

# 1. Inspect intcode L2 and L3
p_ic = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intcode.bin")
hdr, labels, code, text = parse_ps3_raw(p_ic)
lb = 4 * len(labels)
print("=== intcode L0 / L2 / L3 / L4 head ===")
for li in (0, 2, 3, 4, 10):
    off = labels[li] + lb
    nxt = min([la + lb for la in labels if la + lb > off] + [len(code)])
    ins = disasm(code, text, off, nxt, lb)
    print(f"-- intcode L{li} @ 0x{off:05x} ({len(ins)} insns) --")
    for o, t in ins[:45]:
        print(f"  {o:05x}: {t}")

# 2. Inspect sn101 stdlib L14, L106, L114, L139, L119, L120, L122, L124, L143, L151, L182 head
p101 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\sn101.ps3")
h1, l1, c1, t1 = parse_ps3_raw(p101)
lb1 = 4 * len(l1)
print("\n=== stdlib sprite/bg function heads ===")
for li in (14, 13, 12, 106, 114, 139, 119, 120, 122, 124, 126, 143, 151, 182, 183, 167, 172, 26, 28, 77, 18):
    off = l1[li] + lb1
    nxt = min([la + lb1 for la in l1 if la + lb1 > off] + [h1[8]])
    ins = disasm(c1, t1, off, nxt, lb1)
    # Find R* params and G[...] accesses in first 45 lines
    print(f"-- stdlib L{li} @ 0x{off:05x} ({len(ins)} insns) --")
    for o, t in ins[:35]:
        print(f"  {o:05x}: {t}")

# 3. Inspect sn299 L186 and sn603 choices
for stem, lidx in [("sn299", 186), ("sn603", 186), ("sn603", 209)]:
    p = Path(rf"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\{stem}.ps3")
    h, l, c, tx = parse_ps3_raw(p)
    lb_s = 4 * len(l)
    if lidx < len(l):
        off = l[lidx] + lb_s
        ins = disasm(c, tx, off, min(len(c), off + 500), lb_s)
        print(f"\n=== {stem} L{lidx} @ 0x{off:05x} ===")
        for o, t in ins[:45]:
            print(f"  {o:05x}: {t}")

# Inspect sn603 around 0x62c50..0x62d50
p603 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\sn603.ps3")
h, l, c, tx = parse_ps3_raw(p603)
lb_s = 4 * len(l)
print("\n=== sn603 branch @ 0x62c00..end ===")
for o, t in disasm(c, tx, 0x62c00, len(c), lb_s):
    print(f"  {o:05x}: {t}")
