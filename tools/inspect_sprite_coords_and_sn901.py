import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
p101 = code_dir / "sn101.ps3"
h, l, c, tx = parse_ps3_raw(p101)
lb = 4 * len(l)

def dump_l(idx, fname):
    off = l[idx] + lb
    nxt = min([la + lb for la in l if la + lb > off] + [h[8]])
    ins = disasm(c, tx, off, nxt, lb)
    return [f"-- L{idx} @ 0x{off:05x} ({len(ins)} insns) --"] + [f"  {o:05x}: {t}" for o, t in ins]

out = []
for idx in [103, 112, 138, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 14, 13, 12, 108, 110, 143, 152, 153]:
    out.extend(dump_l(idx, "stdlib"))
Path(r"E:\Antigravity\aoitori-rw5\probe\sprite_system_disasm.txt").write_text("\n".join(out), "utf-8")
print(f"Wrote sprite_system_disasm.txt ({len(out)} lines)")

# Show first 20 sprite-related calls in sn101.ps3 body
ins101 = disasm(c, tx, h[8], len(c), lb)
sprite_calls = {"CALL L12", "CALL L13", "CALL L14", "CALL L106", "CALL L114", "CALL L139",
                "CALL L140", "CALL L115", "CALL L141", "CALL L117", "CALL L120", "CALL L127",
                "CALL L129", "CALL L131", "CALL L133", "CALL L143", "CALL L108", "CALL L151", "CALL L121", "CALL L15"}
print("\n=== First 40 sprite-related calls in sn101.ps3 ===")
cnt = 0
for i, (o, t) in enumerate(ins101):
    if t in sprite_calls:
        prev = [ins101[j][1] for j in range(max(0, i-8), i) if ins101[j][1].startswith("EXPR")]
        print(f"  0x{o:05x}: {t:10s} args(push-order)={prev[-5:]}")
        cnt += 1
        if cnt >= 45:
            break

# Inspect sn901.ps3 first 40 lines
p901 = code_dir / "sn901.ps3"
h9, l9, c9, tx9 = parse_ps3_raw(p901)
ins901 = disasm(c9, tx9, h9[8], len(c9), 4 * len(l9))
print("\n=== sn901.ps3 head & strings ===")
strs901 = [t for _, t in ins901 if "CALL L77" in t or "CALL L193" in t or ".ps3" in t or "'" in t][:25]
for s in strs901:
    print(" ", s)
