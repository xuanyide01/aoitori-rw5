import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

syscalls = {}
note = Path(r"E:\Antigravity\aoitori-rw5\tools\refs\RxCMVS\RxCMVS-main\etc\note.md").read_text("utf-8")
for line in note.splitlines():
    if line.startswith("OPCode:0x2"):
        parts = line.split(":", 2)
        op = int(parts[1], 16)
        name = parts[2].split("::")[-1].strip() if len(parts) > 2 and parts[2].strip() else f"sys_{op:04x}"
        syscalls[op] = name

EXPR_OPS = {
    0x0160: "*", 0x0161: "/", 0x0162: "%", 0x0163: "+", 0x0164: "-",
    0x0165: "&", 0x0166: "|", 0x0167: "^", 0x0168: "<<", 0x0169: ">>",
    0x016A: ">", 0x016B: ">=", 0x016C: "<", 0x016D: "<=",
    0x016E: "&&", 0x016F: "||",
    0x0170: "=", 0x0171: "==", 0x0172: "!=",
    0x0173: "++", 0x0174: "--",
}

def parse_ps3_raw(path: Path):
    data = path.read_bytes()
    hdr = struct.unpack("<4s11I", data[:48])
    _, hdr_size, _, _, label_count, code_sz, un_sz, text_sz, beg_pc, comp_sz, uncomp_sz, un3 = hdr
    code_seg_len = code_sz + 4 * label_count + un_sz
    code_seg = data[hdr_size : hdr_size + code_seg_len]
    text_seg = data[hdr_size + code_seg_len :]
    labels = [struct.unpack_from("<I", code_seg, i * 4)[0] for i in range(label_count)]
    return hdr, labels, code_seg, text_seg

def read_cstr(text_seg: bytes, rva: int) -> str:
    if rva >= len(text_seg):
        return f"<bad_rva:0x{rva:x}>"
    end = text_seg.find(b"\x00", rva)
    if end < 0:
        end = len(text_seg)
    return text_seg[rva:end].decode("gbk", errors="replace")

def parse_expr(code_seg: bytes, text_seg: bytes, pos: int, end: int):
    op = struct.unpack_from("<H", code_seg, pos)[0]
    pos += 2
    tokens = []
    while pos + 2 <= end:
        sub = struct.unpack_from("<H", code_seg, pos)[0]
        if sub == 0x020F:
            pos += 2
            break
        elif sub in (0x0200, 0x0201, 0x0202):
            sub_txt, pos = parse_expr(code_seg, text_seg, pos, end)
            tokens.append(f"({sub_txt})")
        elif sub == 0x0100:
            val = struct.unpack_from("<i", code_seg, pos + 2)[0]
            tokens.append(f"{val}")
            pos += 6
        elif sub == 0x0120:
            rva = struct.unpack_from("<I", code_seg, pos + 2)[0]
            tokens.append(repr(read_cstr(text_seg, rva)))
            pos += 6
        elif sub == 0x012A:
            val = struct.unpack_from("<f", code_seg, pos + 2)[0]
            tokens.append(f"{val:.4g}f")
            pos += 6
        elif sub in (0x0101, 0x0102):
            pos += 2
            idx_txt, pos = parse_expr(code_seg, text_seg, pos, end)
            name = "G" if sub == 0x0101 else "P"
            tokens.append(f"{name}[{idx_txt}]")
        elif sub == 0x0109:
            arr_id = struct.unpack_from("<i", code_seg, pos + 2)[0]
            pos += 6
            idx_txt, pos = parse_expr(code_seg, text_seg, pos, end)
            tokens.append(f"A{arr_id}[{idx_txt}]")
        elif sub in (0x0103, 0x0104, 0x0108, 0x010E, 0x010F, 0x0122, 0x0124, 0x0128):
            val = struct.unpack_from("<i", code_seg, pos + 2)[0]
            if sub == 0x0103: tokens.append(f"R{val}")
            elif sub == 0x0108: tokens.append(f"V{val}")
            elif sub == 0x010E: tokens.append(f"INT{val}")
            elif sub == 0x010F: tokens.append(f"RET")
            else: tokens.append(f"var_{sub:04x}({val})")
            pos += 6
        elif sub in EXPR_OPS:
            tokens.append(EXPR_OPS[sub])
            pos += 2
        else:
            tokens.append(f"ex_{sub:04x}")
            pos += 2
    return " ".join(tokens), pos

def disasm(code_seg: bytes, text_seg: bytes, start: int, end: int, lbl_base: int):
    pos = start
    out = []
    while pos < end:
        off = pos
        if pos + 2 > end:
            break
        op = struct.unpack_from("<H", code_seg, pos)[0]
        if op in (0x0200, 0x0201, 0x0202):
            txt, pos = parse_expr(code_seg, text_seg, pos, end)
            out.append((off, f"EXPR({op:04x}): {txt}"))
        elif op >= 0x2000:
            name = syscalls.get(op, f"sys_{op:04x}")
            out.append((off, f"SYS {name}"))
            pos += 2
        elif op == 0x0400:
            t = struct.unpack_from("<I", code_seg, pos + 2)[0] + lbl_base
            out.append((off, f"jmp32 0x{t:05x}"))
            pos += 6
        elif op == 0x0401:
            t = struct.unpack_from("<I", code_seg, pos + 2)[0] + lbl_base
            out.append((off, f"jz 0x{t:05x}"))
            pos += 6
        elif op == 0x0402:
            t = struct.unpack_from("<I", code_seg, pos + 2)[0] + lbl_base
            out.append((off, f"jnz 0x{t:05x}"))
            pos += 6
        elif op == 0x0403:
            imm, t = struct.unpack_from("<II", code_seg, pos + 2)
            out.append((off, f"jeq_reg {imm}, 0x{t+lbl_base:05x}"))
            pos += 10
        elif op == 0x0405:
            t = struct.unpack_from("<H", code_seg, pos + 2)[0] + lbl_base
            out.append((off, f"jmp16 0x{t:05x}"))
            pos += 4
        elif op == 0x0407:
            t = struct.unpack_from("<I", code_seg, pos + 2)[0] + lbl_base
            out.append((off, f"jmp32 0x{t:05x}"))
            pos += 6
        elif op == 0x0410:
            lbl = struct.unpack_from("<H", code_seg, pos + 2)[0]
            out.append((off, f"CALL L{lbl}"))
            pos += 4
        elif op == 0x0411:
            n = struct.unpack_from("<H", code_seg, pos + 2)[0]
            out.append((off, f"RET {n}"))
            pos += 4
        elif op == 0x0412:
            n = struct.unpack_from("<H", code_seg, pos + 2)[0]
            out.append((off, f"POP {n}"))
            pos += 4
        elif op == 0x0413:
            n = struct.unpack_from("<H", code_seg, pos + 2)[0]
            out.append((off, f"JMP_STK {n}"))
            pos += 4
        elif op == 0x0414:
            a, b = struct.unpack_from("<HH", code_seg, pos + 2)
            out.append((off, f"SWITCH {a}, {b}"))
            pos += 6
        elif op == 0x0416:
            out.append((off, "CALL_REG0"))
            pos += 2
        elif op == 0x0430:
            out.append((off, "PUSH_REG0"))
            pos += 2
        elif op in (0x0440, 0x0442):
            v1, v2 = struct.unpack_from("<HI", code_seg, pos + 2)
            out.append((off, f"ALLOC_{op:04x} {v1}, 0x{v2:x}"))
            pos += 8
        else:
            out.append((off, f"OP_{op:04x}"))
            pos += 2
    return out

if __name__ == "__main__":
    for name in ["main.ps3", "menu.ps3", "omake.ps3", "sn101.ps3", "sn108.ps3"]:
        p = Path(rf"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\{name}")
        hdr, labels, code_seg, text_seg = parse_ps3_raw(p)
        lbl_base = 4 * len(labels)
        beg = hdr[8]
        insns = disasm(code_seg, text_seg, beg, len(code_seg), lbl_base)
        out_txt = Path(rf"E:\Antigravity\aoitori-rw5\probe\disasm_{p.stem}.txt")
        lbl_rev = {}
        for li, la in enumerate(labels):
            lbl_rev.setdefault(la + lbl_base, []).append(li)
        lines = [f"# {name} beg_pc=0x{beg:x} labels={len(labels)} lbl_base=0x{lbl_base:x}"]
        for off, txt in insns:
            if off in lbl_rev:
                lines.append(f"-- L{lbl_rev[off]} @ 0x{off:05x} --")
            lines.append(f"  {off:05x}: {txt}")
        out_txt.write_text("\n".join(lines), "utf-8")
        print(f"Wrote {out_txt} ({len(lines)} lines)")
