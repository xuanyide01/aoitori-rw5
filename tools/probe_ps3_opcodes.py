import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load syscall table from RxCMVS/etc/note.md
syscalls = {}
note = Path(r"E:\Antigravity\aoitori-rw5\tools\refs\RxCMVS\RxCMVS-main\etc\note.md").read_text("utf-8")
for line in note.splitlines():
    if line.startswith("OPCode:0x2"):
        parts = line.split(":", 2)
        op = int(parts[1], 16)
        name = parts[2].split("::")[-1].strip() if len(parts) > 2 and parts[2].strip() else f"sys_{op:04x}"
        syscalls[op] = name

def dump_code_slice(path: Path, start_off: int, length: int):
    data = path.read_bytes()
    hdr = struct.unpack("<4s11I", data[:48])
    _, hdr_size, _, _, label_count, code_sz, un_sz, text_sz, beg_pc, comp_sz, uncomp_sz, un3 = hdr
    code_seg_len = code_sz + 4 * label_count + un_sz
    code_seg = data[hdr_size : hdr_size + code_seg_len]
    text_seg = data[hdr_size + code_seg_len :]
    print(f"=== {path.name}: labelCount={label_count}, code_sz=0x{code_sz:x}, un_sz=0x{un_sz:x}, code_seg_len=0x{code_seg_len:x}, beg_pc=0x{beg_pc:x} ===")
    print("Labels[0..15]:", [hex(struct.unpack_from("<I", code_seg, i*4)[0]) for i in range(min(15, label_count))])
    sl = code_seg[start_off : start_off + length]
    for off in range(0, len(sl), 16):
        ch = sl[off : off + 16]
        print(f"  {start_off+off:05x}: {' '.join(f'{b:02x}' for b in ch)}")

dump_code_slice(Path(r"E:\Antigravity\aoitori-rw5\probe/longinus_named/code/menu.ps3"), 0x3b400, 512)
dump_code_slice(Path(r"E:\Antigravity\aoitori-rw5\probe/longinus_named/code/sn101.ps3"), 0x3b500, 512)
dump_code_slice(Path(r"E:\Antigravity\aoitori-rw5\probe/ps3/intcode.bin"), 0x3c, 256)
