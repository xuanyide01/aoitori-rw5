import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ps3_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")

# Check sn101.bin header and exact section boundaries
sn101 = (ps3_dir / "sn101.bin").read_bytes()
hdr = struct.unpack("<4s11I", sn101[:48])
print("sn101 hdr:", hdr[0], [hex(x) for x in hdr[1:]])
# Check offset 0x30 + hdr[5]
p_str = 0x30 + hdr[5]
print("Around 0x30 + hdr[5] (0x%x):" % p_str, repr(sn101[p_str-32:p_str+64]))

# Scan EVERY .bin file in probe/ps3/ for:
# 1) UTF-8 Chinese strings (3-byte CJK U+4E00..U+9FFF runs >= 2 chars)
# 2) GBK Chinese strings (2-byte GBK runs >= 3 chars, excluding Shift-JIS kana/fullwidth)
# 3) Printable ASCII/English strings >= 10 chars
utf8_cjk_re = re.compile(rb"(?:[\xe4-\xe9][\x80-\xbf]{2}){2,}")

total_utf8_cjk = 0
total_ascii_lines = 0
sample_strings_per_file = {}

for p in sorted(ps3_dir.glob("*.bin")):
    data = p.read_bytes()
    h = struct.unpack("<4s11I", data[:48])
    pool_off = 0x30 + h[5]
    pool = data[pool_off:] if pool_off < len(data) else b""
    u_hits = utf8_cjk_re.findall(data)
    total_utf8_cjk += len(u_hits)
    # Check pool strings
    strings = [s for s in pool.split(b"\x00") if s]
    non_ascii_pool = [s for s in strings if any(b >= 0x80 for b in s)]
    ascii_pool = [s for s in strings if all(32 <= b < 127 for b in s) and len(s) >= 8]
    total_ascii_lines += len(ascii_pool)
    if u_hits or non_ascii_pool or p.stem in ("main", "menu", "omake", "sn101", "sn201", "sn301"):
        print(f"{p.name}: len={len(data):,}, pool_off=0x{pool_off:x}, pool_strs={len(strings)}, non_ascii_pool={len(non_ascii_pool)}, utf8_cjk_anywhere={len(u_hits)}")
        for s in non_ascii_pool[:5]:
            print(f"    non_ascii: hex={s.hex()} cp932={s.decode('cp932', 'replace')!r} gbk={s.decode('gbk', 'replace')!r} utf8={s.decode('utf-8', 'replace')!r}")
        for s in ascii_pool[:3]:
            print(f"    ascii: {s.decode('ascii', 'replace')!r}")

print(f"TOTAL utf8_cjk hits across ALL 86 .ps3 files: {total_utf8_cjk}")
print(f"TOTAL ascii_pool strings (>=8 chars) across ALL 86 .ps3 files: {total_ascii_lines}")
