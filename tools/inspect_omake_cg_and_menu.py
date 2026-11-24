import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")

# 1. Inspect menu.ps3 button registrations
pm = code_dir / "menu.ps3"
hm, lm, cm, txm = parse_ps3_raw(pm)
insm = disasm(cm, txm, hm[8], len(cm), 4 * len(lm))
print("=== menu.ps3 select_button registrations ===")
for i, (o, t) in enumerate(insm):
    if "select_button_parts_registration" in t or "title0" in t or "select_button_create" in t:
        ctx = [insm[j][1] for j in range(max(0, i-4), i+1)]
        print(f"  0x{o:05x}: {t} | prev={ctx[:-1]}")

# 2. Inspect omake.ps3 CG Gallery (0x4e000..end) & Scene Replay (0x46000..0x4b000) & BGM (0x4b400..0x4e000)
po = code_dir / "omake.ps3"
ho, lo, co, txo = parse_ps3_raw(po)
inso = disasm(co, txo, ho[8], len(co), 4 * len(lo))
print("\n=== omake.ps3 BG/CG tables & labels after 0x4e000 ===")
bg_map = json.loads(Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_bg_map.json").read_text("utf-8"))
# Dump integers pushed near end of omake or in CG gallery section
nums = []
for i, (o, t) in enumerate(inso):
    if o >= 0x4e200:
        m = re.match(r"EXPR\(0200\): (\d+)$", t)
        if m:
            v = int(m.group(1))
            if str(v) in bg_map and v >= 3000:
                nums.append((o, v, bg_map[str(v)]))
print(f"CG IDs referenced in omake >= 0x4e200: {len(nums)}")
for o, v, fn in nums[:40]:
    print(f"  0x{o:05x}: {v} -> {fn}")

# Also search `A*[...]` or data arrays in omake >= 0x4e000 or all labels of omake
print("\n=== omake labels >= 207 ===")
lbo = 4 * len(lo)
for idx in range(207, len(lo)):
    off = lo[idx] + lbo
    nxt = min([la + lbo for la in lo if la + lbo > off] + [len(co)])
    ins_l = disasm(co, txo, off, nxt, lbo)
    strs = [re.findall(r"'([^']+)'", t) for _, t in ins_l]
    strs = [s for sub in strs for s in sub][:6]
    syss = sorted({t for _, t in ins_l if t.startswith("SYS ")})[:5]
    print(f"  L{idx:3d} @ 0x{off:05x} ({len(ins_l):4d} insns) strs={strs} sys={syss}")

# 3. Check all snh* and sn* scripts for h_*.pb3 references!
print("\n=== Scanning ALL 85 scripts for CGs (ev_*, h_*) & P[2157] ===")
for p in sorted(code_dir.glob("*.ps3")):
    if not p.stem.startswith("sn"):
        continue
    h, l, c, tx = parse_ps3_raw(p)
    ins = disasm(c, tx, h[8], len(c), 4 * len(l))
    h_cgs = []
    ev_cgs = []
    for i, (o, t) in enumerate(ins):
        if t in ("CALL L182", "CALL L183", "CALL L167", "CALL L172", "CALL L171", "CALL L170", "CALL L173"):
            # check preceding pushed ints
            for j in range(max(0, i-8), i):
                m = re.match(r"EXPR\(0200\): (\d+)$", ins[j][1])
                if m:
                    v = int(m.group(1))
                    fn = bg_map.get(str(v), "")
                    if fn.startswith("h_"):
                        h_cgs.append(fn)
                    elif fn.startswith("ev_"):
                        ev_cgs.append(fn)
    if h_cgs or p.stem.startswith("snh"):
        print(f"  {p.stem:10s}: h_cgs={len(set(h_cgs))} ({sorted(set(h_cgs))[:4]}...), ev_cgs={len(set(ev_cgs))}")
