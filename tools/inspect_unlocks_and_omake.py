import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

# 1. Dump sn299 L186 tail
p299 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\sn299.ps3")
h, l, c, tx = parse_ps3_raw(p299)
lb = 4 * len(l)
print("=== sn299 L186 (0x360a0..0x36500) ===")
for o, t in disasm(c, tx, 0x360a0, 0x36500, lb):
    print(f"  {o:05x}: {t}")

# 2. Extract exact intcode L1 BG/CG/H/unlock table (G[700] -> filename)
p_ic = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intcode.bin")
hic, lic, cic, txic = parse_ps3_raw(p_ic)
lbic = 4 * len(lic)
off1 = lic[1] + lbic
off2 = lic[2] + lbic
ins1 = disasm(cic, txic, off1, off2, lbic)
# Map jump targets to filenames
addr_to_pb3 = {}
for i, (o, t) in enumerate(ins1):
    m = re.search(r"'([^']+\.pb3)'", t)
    if m:
        # find enclosing block start (after previous jmp32/RET)
        j = i
        while j > 0 and not ins1[j-1][1].startswith(("jmp32", "jeq_reg", "RET")):
            j -= 1
        addr_to_pb3[ins1[j][0]] = m.group(1)
id_to_pb3 = {}
for o, t in ins1:
    m = re.match(r"jeq_reg (\d+), 0x([0-9a-f]+)", t)
    if m:
        cg_id = int(m.group(1))
        tgt = int(m.group(2), 16)
        # look at tgt or next line
        pb3 = addr_to_pb3.get(tgt)
        if pb3:
            id_to_pb3[cg_id] = pb3
print(f"\n=== intcode L1 mapped {len(id_to_pb3)} CG/BG IDs ===")
for k in sorted(id_to_pb3):
    if k >= 8000 or "unlock" in id_to_pb3[k] or "h_" in id_to_pb3[k] or "ev_" in id_to_pb3[k]:
        if k >= 8700 or k % 100 == 0 or "unlock" in id_to_pb3[k]:
            print(f"  {k:5d} -> {id_to_pb3[k]}")

# Save complete intcode BG table for compiler reuse
out_ic = Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_bg_map.json")
out_ic.write_text(json.dumps({str(k): v for k, v in sorted(id_to_pb3.items())}, indent=2), "utf-8")
print(f"Wrote {out_ic}")

# 3. Inspect omake.ps3 around 0x3bdd2..0x4b000 for title/unlock/gallery/hscene rules
pom = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\omake.ps3")
hom, lom, com, txom = parse_ps3_raw(pom)
lbom = 4 * len(lom)
insom = disasm(com, txom, hom[8], len(com), lbom)
print(f"\n=== omake P[...] checks & label counts ({len(lom)} labels) ===")
for i, (o, t) in enumerate(insom):
    if "P[" in t or ".ps3" in t or ".pb3" in t:
        print(f"  {o:05x}: {t}")
