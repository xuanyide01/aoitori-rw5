import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm


def dump_stdlib_summary():
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

    # Map each label to its syscalls, int_calls, strings, and callees
    cur_lbls = None
    funcs = {}
    for off, txt in insns:
        if off in lbl_rev:
            cur_lbls = tuple(lbl_rev[off])
            funcs[cur_lbls] = {"off": off, "sys": [], "calls": [], "strs": [], "lines": 0}
        if cur_lbls is None:
            continue
        f = funcs[cur_lbls]
        f["lines"] += 1
        if txt.startswith("SYS "):
            s = txt[4:]
            if s not in f["sys"]:
                f["sys"].append(s)
        elif txt.startswith("CALL "):
            c = txt[5:]
            if c not in f["calls"]:
                f["calls"].append(c)
        for m in re.findall(r"'([^']+)'", txt):
            if m not in f["strs"] and len(f["strs"]) < 8:
                f["strs"].append(m)

    out_lines = []
    for lbls, f in funcs.items():
        name = "/".join(f"L{x}" for x in lbls)
        out_lines.append(
            f"{name:12s} @ 0x{f['off']:05x} ({f['lines']:4d} insns) sys={f['sys']} calls={f['calls']} strs={f['strs']}"
        )
    out = Path(r"E:\Antigravity\aoitori-rw5\probe\stdlib_summary.txt")
    out.write_text("\n".join(out_lines), "utf-8")
    print(f"Wrote {out} ({len(out_lines)} functions)")


def dump_intcode_summary():
    p = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intcode.bin")
    hdr, labels, code_seg, text_seg = parse_ps3_raw(p)
    lbl_base = 4 * len(labels)
    insns = disasm(code_seg, text_seg, lbl_base, len(code_seg), lbl_base)
    lbl_rev = {}
    for li, la in enumerate(labels):
        lbl_rev.setdefault(la + lbl_base, []).append(li)

    cur_lbls = None
    funcs = {}
    for off, txt in insns:
        if off in lbl_rev:
            cur_lbls = tuple(lbl_rev[off])
            funcs[cur_lbls] = {"off": off, "jeq": [], "sys": [], "strs": [], "lines": 0}
        if cur_lbls is None:
            continue
        f = funcs[cur_lbls]
        f["lines"] += 1
        if txt.startswith("SYS "):
            s = txt[4:]
            if s not in f["sys"]:
                f["sys"].append(s)
        elif txt.startswith("jeq_reg "):
            f["jeq"].append(txt)
        for m in re.findall(r"'([^']+)'", txt):
            if m not in f["strs"]:
                f["strs"].append(m)

    out_lines = []
    for lbls, f in funcs.items():
        name = "/".join(f"L{x}" for x in lbls)
        sample_strs = f["strs"][:12]
        out_lines.append(
            f"{name:10s} @ 0x{f['off']:05x} ({f['lines']:5d} insns) jeq={len(f['jeq'])} strs({len(f['strs'])})={sample_strs} sys={f['sys']}"
        )
    out = Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_summary.txt")
    out.write_text("\n".join(out_lines), "utf-8")
    print(f"Wrote {out} ({len(out_lines)} functions)")


if __name__ == "__main__":
    dump_stdlib_summary()
    dump_intcode_summary()
