import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ps3_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")

real_non_ascii = []
for p in sorted(ps3_dir.glob("*.bin")):
    data = p.read_bytes()
    # Find string pool start: in PS2A, look for message01.pb3 or start from last bytecode end
    # Actually let's check both: hdr[5], hdr[7], hdr[8], hdr[9]
    h = struct.unpack("<4s11I", data[:48])
    # Notice earlier sn101 message01.pb3 was at 0x60e9f, while 0x30+h[5] was 0x60b0a (395 bytes earlier)
    # Wait: what is 0x60e9f - 0x60b0a = 0x395? Let's check from the first printable string after h[5]!
    mpos = data.find(b"message01.pb3")
    if mpos < 0:
        mpos = max(0x30 + h[5], 0)
    pool = data[mpos:]
    for s in pool.split(b"\x00"):
        if not s:
            continue
        if any(b >= 0x80 for b in s):
            # Ignore known control/opcode bytes if mpos fell back
            if any(b < 0x20 for b in s):
                continue
            real_non_ascii.append((p.name, s.decode("cp932", errors="replace"), s.decode("gbk", errors="replace"), s.hex()))

print(f"Total clean non-ASCII strings in string pools across all 86 PS3 files: {len(real_non_ascii)}")
seen = set()
for fn, j, g, hx in real_non_ascii:
    if hx not in seen:
        seen.add(hx)
        print(f"  [{fn}] cp932={j!r} | gbk={g!r} | hex={hx}")
