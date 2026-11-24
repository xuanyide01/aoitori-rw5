import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")
ldat = SRC / "Longinus.dat"

with open(ldat, "rb") as f:
    hdr = f.read(16)
    magic, v1, v2, v3, v4, count = struct.unpack("<8s4BI", hdr)
    print(f"Longinus magic={magic!r}, flags=({v1},{v2},{v3},{v4}), count={count}")
    entries = []
    for i in range(count):
        h, size, off = struct.unpack("<III", f.read(12))
        entries.append((i, h, size, off))
    print(f"Index end: 0x{f.tell():x}, first off: 0x{entries[0][3]:x}")
    for i, h, size, off in entries:
        f.seek(off)
        head = f.read(min(32, size))
        hx = head[:16].hex()
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in head[:16])
        if size < 1000000 or i < 20 or head[:4] == b"PS2A":
            print(f"  [{i:3d}] hash=0x{h:08x} size={size:10,d} off=0x{off:08x} head={hx} | {asc}")

# Also inspect first frame payload of op.cmv and bg070a.cmv
for cmv_name, off in [("data/video/op.cmv", 0xe3fc), ("data/imgvideo/bg070a.cmv", 0xb0f20)]:
    with open(SRC / cmv_name, "rb") as f:
        f.seek(off)
        d = f.read(64)
        print(f"\n{cmv_name} @ 0x{off:x}: {d[:32].hex()} | {''.join(chr(b) if 32<=b<127 else '.' for b in d[:32])}")
        # Also look at frame 100 in op.cmv (maybe frame 0 is black)
        if "op.cmv" in cmv_name:
            f.seek(0x2c + 100 * 20)
            fid, csz, usz, typ, foff = struct.unpack("<5I", f.read(20))
            f.seek(off + foff)
            d100 = f.read(64)
            print(f"  op.cmv frame 100 (fid={fid}, csz={csz}, usz={usz}, typ={typ}, off=0x{foff:x}): {d100[:32].hex()}")
            # Also check end of op.cmv after last frame!
            f.seek(0x2c + 2914 * 20)
            lfid, lcsz, lusz, ltyp, lfoff = struct.unpack("<5I", f.read(20))
            print(f"  op.cmv last frame {lfid}: end=0x{off + lfoff + lcsz:x} ({off + lfoff + lcsz:,}) vs file={ (SRC/cmv_name).stat().st_size:,}")
            f.seek(0x2c + 2915 * 20)
            extra = f.read(20)
            print(f"  bytes at 0x2c+2915*20: {extra.hex()}")
