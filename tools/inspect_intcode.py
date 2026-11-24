import json
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intcode.bin").read_bytes()
hdr = struct.unpack("<4s11I", data[:48])
_, hdr_size, _, _, label_count, code_sz, un_sz, text_sz, beg_pc, comp_sz, uncomp_sz, un3 = hdr
code_seg_len = code_sz + 4 * label_count + un_sz
code_seg = data[hdr_size : hdr_size + code_seg_len]
text_seg = data[hdr_size + code_seg_len :]

# Print ordered unique strings in text_seg (separated by \0) with their RVA!
entries = []
pos = 0
while pos < len(text_seg):
    end = text_seg.find(b"\x00", pos)
    if end < 0:
        end = len(text_seg)
    s = text_seg[pos:end].decode("cp932", errors="replace")
    if s:
        entries.append((pos, s))
    pos = end + 1

print(f"intcode.ps3: total non-empty strings={len(entries)}, labelCount={label_count}")
# Group consecutive prefixes or print sections
for i, (rva, s) in enumerate(entries):
    if i < 40 or (i > 0 and s[:3] != entries[i-1][1][:3] and not s.startswith(("ev_", "h_", "bg"))):
        print(f"  [{i:4d}] rva=0x{rva:05x} {s!r}")
    elif i in (200, 500, 1000, 1500, 2000, 2500, 3000, 3500):
        print(f"  [{i:4d}] rva=0x{rva:05x} {s!r}")
