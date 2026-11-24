import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

# 1. Inspect sn101 0x3fe60..0x40550 to see exact sprite calls in context
p101 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\sn101.ps3")
h, l, c, tx = parse_ps3_raw(p101)
ins = disasm(c, tx, 0x3fe60, 0x40550, 4 * len(l))
Path(r"E:\Antigravity\aoitori-rw5\probe\sn101_sprite_sample.txt").write_text(
    "\n".join(f"  {o:05x}: {t}" for o, t in ins), "utf-8"
)
print(f"Wrote sn101_sprite_sample.txt ({len(ins)} lines)")

# 2. Check intcode L2 full body (0x1d072..0x1d2d6) and L10..L14 char codes
p_ic = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intcode.bin")
hic, lic, cic, txic = parse_ps3_raw(p_ic)
lbic = 4 * len(lic)
print("\n=== intcode L2 full ===")
for o, t in disasm(cic, txic, lic[2] + lbic, lic[4] + lbic, lbic):
    print(f"  {o:05x}: {t}")

# 3. Inspect omake.ps3 L208 (CG gallery) & L209 (H-scene gallery) & L210 (BGM)
pom = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\omake.ps3")
hom, lom, com, txom = parse_ps3_raw(pom)
lbom = 4 * len(lom)
# Check L209 (0x45d88..0x4b182) for H-scene entries: flag P[...] + script name
inso = disasm(com, txom, 0x45d88, 0x56000, lbom)
Path(r"E:\Antigravity\aoitori-rw5\probe\omake_galleries.txt").write_text(
    "\n".join(f"  {o:05x}: {t}" for o, t in inso), "utf-8"
)
print(f"Wrote omake_galleries.txt ({len(inso)} lines)")
