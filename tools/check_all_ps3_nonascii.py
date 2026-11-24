import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ps3_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")

all_non_ascii = set()
missing_marker = []
for p in sorted(ps3_dir.glob("*.bin")):
    data = p.read_bytes()
    h = struct.unpack("<4s11I", data[:48])
    pool_off = 0x30 + h[5]
    pool = data[pool_off:]
    strs = [s for s in pool.split(b"\x00") if s]
    for s in strs:
        if any(b >= 0x80 for b in s):
            all_non_ascii.add(s.decode("cp932", errors="replace"))
    if b"message01.pb3" not in data and b"bg000a.pb3" not in data:
        missing_marker.append(p.name)

print("Files without message01.pb3/bg000a.pb3:", missing_marker)
print(f"Unique non-ASCII CP932 strings across ALL 86 .ps3 files ({len(all_non_ascii)}):")
for s in sorted(all_non_ascii)[:60]:
    print(" ", repr(s))
