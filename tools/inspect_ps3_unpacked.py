import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = Path(r"E:\Antigravity\aoitori-rw5\probe\sn101_unpacked.bin").read_bytes()
print(f"Length: {len(data):,}")
# Header fields (12 uint32 = 48 bytes)
hdr = struct.unpack("<4s11I", data[:48])
print("Header (4s + 11*uint32):")
print("  magic:", hdr[0])
for idx, val in enumerate(hdr[1:], 1):
    print(f"  [{idx}] 0x{val:08x} ({val:,})")

# Check if sections after 0x30 contain readable strings (UTF-8 / Shift-JIS / GBK)!
for off in [0x30, hdr[6], hdr[6] + hdr[7], hdr[6] + hdr[7] + hdr[8]]:
    chunk = data[off:off+64]
    print(f"Offset 0x{off:x}: {' '.join(f'{b:02x}' for b in chunk[:32])}")

# Scan for runs of Japanese/Chinese/ASCII text in sn101_unpacked.bin
tail = data[-2000:]
print("Tail utf-8/cp932/gbk check:")
for enc in ("cp932", "gbk", "utf-8"):
    try:
        s = tail.decode(enc, errors="ignore")
        print(f"  [{enc}] sample:", repr(s[:200]))
    except Exception as e:
        print(f"  [{enc}] err:", e)
