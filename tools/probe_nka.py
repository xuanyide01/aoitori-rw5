import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NKA_PATH = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori\AoiToriR18Patchv1.04.bin")

with open(NKA_PATH, "rb") as f:
    raw = f.read(1024)

magic, version, count = struct.unpack("<4sII", raw[:12])
print(f"Magic: {magic!r}, version: {version}, count: {count}")
for off in range(12, 512, 16):
    chunk = raw[off:off+16]
    hx = " ".join(f"{b:02x}" for b in chunk)
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"{off:04x}: {hx:<48} {asc}")
