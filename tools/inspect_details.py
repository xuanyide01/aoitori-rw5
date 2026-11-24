import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm


def dump_stdlib_funcs(names):
    p = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\sn101.ps3")
    hdr, labels, code_seg, text_seg = parse_ps3_raw(p)
    lbl_base = 4 * len(labels)
    beg = hdr[8]
    insns = disasm(code_seg, text_seg, lbl_base, beg, lbl_base)
    lbl_rev = {}
    for li, la in enumerate(labels):
        off = la + lbl_base
        if off < beg:
            lbl_rev.setdefault(off, []).append(li)
    cur = False
    out = []
    for off, txt in insns:
        if off in lbl_rev:
            cur = any(x in names for x in lbl_rev[off])
            if cur:
                out.append(f"-- L{lbl_rev[off]} @ 0x{off:05x} --")
        if cur:
            out.append(f"  {off:05x}: {txt}")
    return out


if __name__ == "__main__":
    lines = dump_stdlib_funcs({60, 102, 111, 118, 121, 103, 112, 138, 12, 13, 14, 167, 170, 172, 182})
    Path(r"E:\Antigravity\aoitori-rw5\probe\stdlib_key_funcs.txt").write_text("\n".join(lines), "utf-8")
    print(f"Wrote stdlib_key_funcs.txt ({len(lines)} lines)")

    # Check sn108 branching, sn299, sn399, sn499, sn605, hscene, omake P_writes
    code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
    for stem in ["sn108", "sn299", "sn399", "sn499", "sn605", "sn901"]:
        p = code_dir / f"{stem}.ps3"
        hdr, labels, code_seg, text_seg = parse_ps3_raw(p)
        insns = disasm(code_seg, text_seg, hdr[8], len(code_seg), 4 * len(labels))
        tail = insns[-120:] if stem == "sn108" else insns
        txt_out = "\n".join(f"  {o:05x}: {t}" for o, t in tail)
        Path(rf"E:\Antigravity\aoitori-rw5\probe\disasm_{stem}_key.txt").write_text(txt_out, "utf-8")
        print(f"Wrote disasm_{stem}_key.txt ({len(tail)} lines)")

    # Search P[2156] across ALL 85 longinus scripts AND ALL 86 ps3/ bins
    print("\n=== Searching P[2156], P[2145], P[2157], hscene across all scripts ===")
    for p in sorted(code_dir.glob("*.ps3")):
        hdr, labels, code_seg, text_seg = parse_ps3_raw(p)
        insns = disasm(code_seg, text_seg, 4 * len(labels), len(code_seg), 4 * len(labels))
        for off, t in insns:
            if any(k in t for k in ("2156", "2145", "2157", "hscene", "select_button")):
                if off >= hdr[8] or p.stem in ("menu", "omake", "main"):
                    if "2156" in t or "2145" in t or "2157" in t or "hscene" in t:
                        print(f"  {p.stem}@0x{off:05x}: {t}")
