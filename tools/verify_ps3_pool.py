import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ps3_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")

# Find exact string pool start in sn101.bin
sn101 = (ps3_dir / "sn101.bin").read_bytes()
idx_msg = sn101.find(b"message01.pb3")
print(f"sn101 message01.pb3 at 0x{idx_msg:x} (len={len(sn101)}, tail_from_msg={len(sn101)-idx_msg}, hdr[9]=0x{struct.unpack('<I', sn101[40:44])[0]:x})")
# Check bytes right before message01.pb3
print("Before message01.pb3:", repr(sn101[idx_msg-64:idx_msg+32]))
# Notice hdr[5] = 0x60ada, hdr[7] = 0x1855e, hdr[8] = 0x3cabc, hdr[9] = 0x1fcbd, hdr[10] = 0x79384
# Wait: idx_msg - 48? Let's check!
# Actually scan backwards from idx_msg to find where opcode bytes end
# In every .bin, "message01.pb3" is near the start of the string pool!
eng_files = 0
jp_strings = []
gbk_like_strings = []
all_pool_counts = 0

for p in sorted(ps3_dir.glob("*.bin")):
    data = p.read_bytes()
    mpos = data.find(b"message01.pb3")
    if mpos < 0:
        mpos = data.find(b"bg000a.pb3")
    if mpos < 0:
        continue
    # Walk backwards to last opcode/null separator
    pool = data[mpos:]
    strs = [s for s in pool.split(b"\x00") if s]
    all_pool_counts += len(strs)
    has_eng = any(b" " in s and all(32 <= b < 127 for b in s) for s in strs)
    if has_eng:
        eng_files += 1
    for s in strs:
        if any(b >= 0x80 for b in s):
            # Decode as cp932 vs gbk
            j = s.decode("cp932", errors="ignore")
            g = s.decode("gbk", errors="ignore")
            if len(jp_strings) < 25:
                jp_strings.append((p.name, s.hex(), j, g))

print(f"Scripts with message01.pb3/bg000a.pb3: {eng_files} English-containing files, total strings from marker: {all_pool_counts}")
print(f"Non-ASCII strings in string pools (sample up to 25, total found={len(jp_strings)}):")
for fn, hx, j, g in jp_strings:
    print(f"  [{fn}] cp932={j!r} | gbk={g!r} | hex={hx}")
