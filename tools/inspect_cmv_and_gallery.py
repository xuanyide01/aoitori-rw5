import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

# 1. Inspect intcode L4..L10 completely and dump intcode_sprite_map.json
p_ic = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intcode.bin")
hic, lic, cic, txic = parse_ps3_raw(p_ic)
lbic = 4 * len(lic)

def extract_switch(insns):
    addr_to_str = {}
    for i, (o, t) in enumerate(insns):
        m = re.search(r"'([^']+)'", t)
        if m:
            j = i
            while j > 0 and not insns[j-1][1].startswith(("jmp32", "jeq_reg", "RET")):
                j -= 1
            addr_to_str.setdefault(insns[j][0], []).append(m.group(1))
    outfits, exprs = {}, {}
    in_r12 = False
    for o, t in insns:
        if "EXPR(0200): R12" in t:
            in_r12 = True
        m = re.match(r"jeq_reg (\d+), 0x([0-9a-f]+)", t)
        if m:
            k = int(m.group(1))
            tgt = int(m.group(2), 16)
            strs = addr_to_str.get(tgt, [])
            if strs:
                (exprs if in_r12 else outfits)[k] = strs[0]
    return outfits, exprs

sprite_tables = {}
for cid, lidx in [(0, 4), (1, 5), (2, 6), (3, 7), (4, 8), (5, 9), (6, 10)]:
    off = lic[lidx] + lbic
    nxt = min([la + lbic for la in lic if la + lbic > off] + [len(cic)])
    outfits, exprs = extract_switch(disasm(cic, txic, off, nxt, lbic))
    sprite_tables[str(cid)] = {"outfits": outfits, "exprs": exprs}
Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_sprite_map.json").write_text(
    json.dumps(sprite_tables, indent=2), "utf-8"
)
print("Wrote intcode_sprite_map.json")

# 2. Inspect sn101 L168 (video BG ID -> cmv name), L128, L130, L132, L142
p101 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\sn101.ps3")
h1, l1, c1, tx1 = parse_ps3_raw(p101)
lb1 = 4 * len(l1)
print("\n=== stdlib L168 (video BG switch) ===")
off = l1[168] + lb1
nxt = l1[169] + lb1
ins168 = disasm(c1, tx1, off, nxt, lb1)
for o, t in ins168:
    if any(k in t for k in ("jeq_reg", ".cmv", "CALL", "SYS")):
        print(f"  {o:05x}: {t}")

# 3. Inspect omake L208 full CG list (calls to L229/L230 in 0x52800..0x58000)
pom = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\omake.ps3")
hom, lom, com, txom = parse_ps3_raw(pom)
lbom = 4 * len(lom)
inso = disasm(com, txom, 0x52800, 0x57600, lbom)
stk = []
last = ""
cg_groups = []
for o, t in inso:
    m = re.match(r"EXPR\(020[012]\): (.+)$", t)
    if m:
        last = m.group(1)
    elif t == "PUSH_REG0":
        stk.append(last)
    elif t == "CALL L229":
        # pushed: [count, base_id]
        if len(stk) >= 2:
            cg_groups.append((int(stk[-1]), int(stk[-2])))
        stk.clear()
    elif t.startswith(("CALL ", "SYS ")):
        stk.clear()
print(f"\n=== omake L208 CG gallery groups: {len(cg_groups)} ===")
bg_map = json.loads(Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_bg_map.json").read_text("utf-8"))
for base_id, cnt in cg_groups[:25]:
    print(f"  id={base_id:4d} count={cnt:2d} file={bg_map.get(str(base_id), '?')}")
total_vars = sum(c for _, c in cg_groups)
h_groups = [(b, c) for b, c in cg_groups if bg_map.get(str(b), "").startswith("h_")]
print(f"Total CG groups={len(cg_groups)} (H-groups={len(h_groups)}), total vars={total_vars}")
Path(r"E:\Antigravity\aoitori-rw5\probe\omake_cg_groups.json").write_text(
    json.dumps([{"baseId": b, "count": c, "baseFile": bg_map.get(str(b), "")} for b, c in cg_groups], indent=2),
    "utf-8",
)
