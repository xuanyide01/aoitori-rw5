import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")

print("=== Non-sn scripts & select_button usage ===")
for p in sorted(code_dir.glob("*.ps3")):
    hdr, labels, code_seg, text_seg = parse_ps3_raw(p)
    lbl_base = 4 * len(labels)
    insns = disasm(code_seg, text_seg, hdr[8], len(code_seg), lbl_base)
    sels = [txt for _, txt in insns if "select" in txt.lower() or "sys_script_open" in txt]
    ps3s = []
    for i, (off, txt) in enumerate(insns):
        for m in re.findall(r"'([^']*\.ps3)'", txt):
            ps3s.append((f"0x{off:05x}", m))
    p_writes = set()
    p_reads = set()
    g_flags = set()
    for _, txt in insns:
        for m in re.finditer(r"P\[([^\]]+)\]", txt):
            p_reads.add(m.group(1))
        for m in re.finditer(r"P\[([^\]]+)\]\s+\d+\s+=", txt):
            p_writes.add(m.group(1))
    if not p.stem.startswith("sn") or sels or ps3s or p_reads:
        print(f"{p.stem:12s}: labels={len(labels)} sels={len(sels)} ps3s={ps3s[:12]} P_reads={sorted(p_reads)[:10]} P_writes={sorted(p_writes)[:10]}")

print("\n=== Omake strings (.pb3 / .ps3 / bgm) ===")
om_hdr, om_labels, om_code, om_text = parse_ps3_raw(code_dir / "omake.ps3")
om_insns = disasm(om_code, om_text, om_hdr[8], len(om_code), 4 * len(om_labels))
for kw in ("ev_", "h_", "snh", "bgm", "unlock"):
    hits = []
    for _, txt in om_insns:
        for m in re.findall(r"'([^']+)'", txt):
            if kw in m.lower() and m not in hits:
                hits.append(m)
    print(f"  omake '{kw}': count={len(hits)} sample={hits[:15]}")
