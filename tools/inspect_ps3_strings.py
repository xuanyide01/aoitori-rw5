import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = Path(r"E:\Antigravity\aoitori-rw5\probe\sn101_unpacked.bin").read_bytes()
hdr = struct.unpack("<4s11I", data[:48])
# Check where strings live!
# Notice hdr[5] = 0x60ada (395,994) + 0x30 = 0x60b0a? Let's check!
# Actually hdr[7]=0x1855e (99,678), hdr[8]=0x3cabc (248,508), hdr[9]=0x1fcbd (130,237)
# Wait: 0x30 + hdr[7] + hdr[8] = 0x5504a? Wait: 0x1855e + 0x3cabc = 0x5501a!
# Wait: 0x5501a + 0x30 = 0x5504a; 0x79384 + 0x30 = 0x793b4 = len(data)!
# What is 0x79384 - 0x1fcbd = 0x596c7! Wait: 0x596c7 + 0x30 = 0x596f7!
# Let's check where null-terminated strings start!
pos = len(data) - 1
# Count non-ASCII bytes in the string pool (last ~130KB)
str_pool = data[0x30 + hdr[7] + hdr[8]:]
print(f"After hdr[7]+hdr[8] (0x{0x30+hdr[7]+hdr[8]:x}), remaining len={len(str_pool):,}, hdr[9]={hdr[9]:,}")
# Actually find where strings start by scanning backwards for binary vs printable
str_start = len(data) - hdr[9]
print(f"len(data) - hdr[9] = 0x{str_start:x} ({str_start:,})")
print("Around str_start:", repr(data[str_start-32:str_start+128]))

# Split strings by \x00 from str_start
strs = [s for s in data[str_start:].split(b"\x00") if s]
print(f"Total null-terminated strings in pool: {len(strs)}")
has_cjk = 0
for s in strs:
    for b in s:
        if b >= 0x80:
            has_cjk += 1
            break
print(f"Strings with bytes >= 0x80: {has_cjk}")
for s in strs[:20]:
    print(" ", s.decode("utf-8", errors="replace"))
print("--- last 15 ---")
for s in strs[-15:]:
    print(" ", s.decode("utf-8", errors="replace"))
