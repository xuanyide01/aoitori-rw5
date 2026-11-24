import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm


def dump_range(ps3_path: Path, out_path: Path, start: int, end: int | None):
    hdr, labels, code_seg, text_seg = parse_ps3_raw(ps3_path)
    lbl_base = 4 * len(labels)
    if end is None:
        end = len(code_seg)
    if start == 0:
        start = lbl_base
    insns = disasm(code_seg, text_seg, start, end, lbl_base)
    lbl_rev = {}
    for li, la in enumerate(labels):
        lbl_rev.setdefault(la + lbl_base, []).append(li)
    lines = [
        f"# {ps3_path.name} beg_pc=0x{hdr[8]:x} labels={len(labels)} lbl_base=0x{lbl_base:x} range=0x{start:x}..0x{end:x}"
    ]
    for off, txt in insns:
        if off in lbl_rev:
            lines.append(f"-- L{lbl_rev[off]} @ 0x{off:05x} --")
        lines.append(f"  {off:05x}: {txt}")
    out_path.write_text("\n".join(lines), "utf-8")
    print(f"Wrote {out_path} ({len(lines)} lines)")


if __name__ == "__main__":
    base = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
    ps3_en = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")
    out = Path(r"E:\Antigravity\aoitori-rw5\probe")
    dump_range(ps3_en / "intcode.bin", out / "disasm_intcode.txt", 0, None)
    dump_range(ps3_en / "intproc.bin", out / "disasm_intproc.txt", 0, None)
    hdr, *_ = parse_ps3_raw(base / "sn101.ps3")
    dump_range(base / "sn101.ps3", out / "disasm_stdlib.txt", 0, hdr[8])
