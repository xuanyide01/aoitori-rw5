import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm


def extract_intcode_switch(insns):
    # Extract outfit prefixes and expr number mappings
    outfits = {}
    exprs = {}
    addr_to_str = {}
    for i, (o, t) in enumerate(insns):
        m = re.search(r"'([^']+)'", t)
        if m:
            j = i
            while j > 0 and not insns[j-1][1].startswith(("jmp32", "jeq_reg", "RET")):
                j -= 1
            addr_to_str.setdefault(insns[j][0], []).append(m.group(1))
    # Scan two switches: first on R8 (outfit), second on R12 (expr)
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
                if not in_r12:
                    outfits[k] = strs[0]
                else:
                    exprs[k] = strs[0]
    return outfits, exprs


p_ic = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intcode.bin")
hic, lic, cic, txic = parse_ps3_raw(p_ic)
lbic = 4 * len(lic)

chars_map = {}
for cid, lidx in [(0, 4), (1, 5), (2, 6), (3, 7), (4, 8), (5, 9), (6, 10)]:
    off = lic[lidx] + lbic
    nxt = min([la + lbic for la in lic if la + lbic > off] + [len(cic)])
    ins = disasm(cic, txic, off, nxt, lbic)
    outfits, exprs = extract_intcode_switch(ins)
    chars_map[cid] = {"outfits": outfits, "expr_sample": dict(list(exprs.items())[:10]), "expr_count": len(exprs)}
    print(f"char {cid}: outfits={outfits}, expr_count={len(exprs)}, sample={dict(list(exprs.items())[:8])}")

# Check stdlib L139, L114, L106, L12, L13, L14, L77 exact R8, R12, R16, R20, R24 usage
p101 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\sn101.ps3")
h1, l1, c1, tx1 = parse_ps3_raw(p101)
lb1 = 4 * len(l1)
print("\n=== stdlib R* parameter checks ===")
for li in (5, 11, 77, 78, 139, 114, 106, 140, 115, 141, 117, 12, 13, 14, 143, 151, 167, 168, 170, 171, 172, 173, 182, 183, 26, 28, 62, 18):
    off = l1[li] + lb1
    nxt = min([la + lb1 for la in l1 if la + lb1 > off] + [h1[8]])
    ins = disasm(c1, tx1, off, nxt, lb1)
    ret = [t for _, t in ins if t.startswith("RET ")][-1]
    regs = sorted({m.group(0) for _, t in ins for m in re.finditer(r"\bR\d+\b", t)}, key=lambda x: int(x[1:]))
    print(f"  L{li:3d}: {ret:8s} regs={regs}")
