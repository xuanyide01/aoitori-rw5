import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
bg_map = json.loads(Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_bg_map.json").read_text("utf-8"))

# 1. Inspect omake L208 (CG gallery) structure around 0x4dd70..end
pom = code_dir / "omake.ps3"
hom, lom, com, txom = parse_ps3_raw(pom)
lbom = 4 * len(lom)
inso = disasm(com, txom, 0x4dd70, len(com), lbom)

# Group L208 CG IDs by base CG (first ID per block)
print("=== omake L208 CG Gallery IDs ===")
cg_ids = []
for o, t in disasm(com, txom, 0x52800, 0x53400, lbom)[:60]:
    print(f"  {o:05x}: {t}")

# Also check L209 H-scene entries: flag P[...] -> snh/sn script
ins_h = disasm(com, txom, 0x45d88, 0x4b182, lbom)
print("\n=== omake L209 H-Scene Replay scripts ===")
for i, (o, t) in enumerate(ins_h):
    m = re.search(r"'([^']+\.ps3)'", t)
    if m:
        print(f"  0x{o:05x}: {m.group(1)}")

# Also check L210 BGM room
ins_m = disasm(com, txom, 0x4b182, 0x4dd70, lbom)
print("\n=== omake L210 Music Room BGM IDs ===")
bgm_calls = []
for i, (o, t) in enumerate(ins_m):
    if "L62" in t or "L63" in t or "sys_bgm" in t:
        prev = [ins_m[j][1] for j in range(max(0, i-4), i)]
        bgm_calls.append((o, t, prev))
print(f"Music room BGM calls: {len(bgm_calls)}")
for item in bgm_calls[:20]:
    print(" ", item)

# 2. Check all story scripts for wx/wy/wz, L129(x,y), L120(up), and all L77/BG/Sprite counts
wx_vals, wy_vals, wz_vals, xy_vals = set(), set(), set(), set()
up_calls = []
for p in sorted(code_dir.glob("sn*.ps3")):
    h, l, c, tx = parse_ps3_raw(p)
    ins = disasm(c, tx, h[8], len(c), 4 * len(l))
    stk = []
    last_expr = ""
    for o, t in ins:
        m = re.match(r"EXPR\(020[012]\): (.+)$", t)
        if m:
            last_expr = m.group(1)
        elif t == "PUSH_REG0":
            stk.append(last_expr)
        elif t.startswith("CALL "):
            fn = t[5:]
            if fn in ("L139", "L114", "L106", "L140", "L115", "L141", "L117"):
                # args: [a5, wz, wy, wx, expr, char] -> R8=stk[-1], R12=stk[-2], R16=wx, R20=wy, R24=wz
                if len(stk) >= 5:
                    wx_vals.add(stk[-3])
                    wy_vals.add(stk[-4])
                    wz_vals.add(stk[-5])
            elif fn == "L129" and len(stk) >= 3:
                xy_vals.add((stk[-2], stk[-3]))
            elif fn == "L120" and len(stk) >= 2:
                up_calls.append((p.stem, stk[-1], stk[-2]))
            stk.clear()
        elif t.startswith("SYS "):
            stk.clear()

print("\n=== Sprite parameter distributions across all sn* ===")
print("unique wx:", sorted(wx_vals)[:30], f"(total {len(wx_vals)})")
print("unique wy:", sorted(wy_vals)[:30], f"(total {len(wy_vals)})")
print("unique wz:", sorted(wz_vals)[:30], f"(total {len(wz_vals)})")
print("unique L129 (x, y):", sorted(xy_vals)[:30], f"(total {len(xy_vals)})")
print("L120(char, mode) values:", sorted(set((a, b) for _, a, b in up_calls)))
