import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")
ldat = SRC / "Longinus.dat"
with open(ldat, "rb") as f:
    head = f.read(512)
    f.seek(-512, 2)
    tail = f.read(512)

print(f"=== Longinus.dat ({ldat.stat().st_size:,} B) ===")
for off in range(0, 256, 16):
    chunk = head[off:off+16]
    hx = " ".join(f"{b:02x}" for b in chunk)
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"HEAD {off:04x}: {hx:<48} {asc}")
print("TAIL[-128:]:")
for off in range(len(tail)-128, len(tail), 16):
    chunk = tail[off:off+16]
    hx = " ".join(f"{b:02x}" for b in chunk)
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"TAIL {off:04x}: {hx:<48} {asc}")

# Also inspect op.cmv and bg070a.cmv frame table
for cmv_path in [SRC / "data/video/op.cmv", SRC / "data/imgvideo/bg070a.cmv"]:
    with open(cmv_path, "rb") as f:
        raw = f.read(512)
    print(f"\n=== {cmv_path.name} ({cmv_path.stat().st_size:,} B) ===")
    hdr = struct.unpack("<4s10I", raw[:44])
    print("  hdr:", hdr[0], [f"0x{x:x}({x})" for x in hdr[1:]])
    # Dump bytes 0x2c..0xb0
    for off in range(0x2c, 0xc0, 20):
        chunk = raw[off:off+20]
        if len(chunk) == 20:
            vals = struct.unpack("<5I", chunk)
            print(f"  0x{off:04x}: {[f'0x{v:x}({v})' for v in vals]}")
