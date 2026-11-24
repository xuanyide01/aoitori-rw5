import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")
ldat = SRC / "Longinus.dat"
out_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_raw")
out_dir.mkdir(parents=True, exist_ok=True)

with open(ldat, "rb") as f:
    hdr = f.read(16)
    magic, v1, v2, v3, v4, count = struct.unpack("<8s4BI", hdr)
    entries = []
    for i in range(count):
        h, size, off = struct.unpack("<III", f.read(12))
        entries.append((i, h, size, off))
    print(f"Total entries: {len(entries)}")
    ps2a_indices = []
    other_entries = []
    for i, h, size, off in entries:
        f.seek(off)
        head = f.read(min(16, size))
        if head[:4] == b"PS2A":
            ps2a_indices.append((i, h, size, off))
            f.seek(off)
            (out_dir / f"entry_{i:03d}_{h:08x}.ps3").write_bytes(f.read(size))
        else:
            other_entries.append((i, h, size, off, head.hex()))

print(f"PS2A entries: {len(ps2a_indices)}, Other entries: {len(other_entries)}")
for i, h, size, off, hx in other_entries:
    print(f"  OTHER [{i:3d}] hash=0x{h:08x} size={size:10,d} off=0x{off:08x} head={hx}")

# Also check op.cmv entry 2915 (audio?) and dump op.cmv frame 100 to probe/op_frame100.jbp
op_cmv = SRC / "data/video/op.cmv"
with open(op_cmv, "rb") as f:
    f.seek(0x2c + 100 * 20)
    fid, csz, usz, typ, foff = struct.unpack("<5I", f.read(20))
    f.seek(0xe3fc + foff)
    Path(r"E:\Antigravity\aoitori-rw5\probe\op_frame100.jbp").write_bytes(f.read(csz))

    f.seek(0x2c + 2915 * 20)
    afid, acsz, ausz, atyp, aoff = struct.unpack("<5I", f.read(20))
    f.seek(0xe3fc + aoff)
    ahead = f.read(64)
    print(f"\nop.cmv extra entry {afid}: csz={acsz:,}, ausz={ausz:,}, typ={atyp}, head={ahead[:32].hex()} | {''.join(chr(b) if 32<=b<127 else '.' for b in ahead[:32])}")

bg_cmv = SRC / "data/imgvideo/bg070a.cmv"
with open(bg_cmv, "rb") as f:
    f.seek(0x2c)
    fid, csz, usz, typ, foff = struct.unpack("<5I", f.read(20))
    f.seek(0xb0f20 + foff)
    Path(r"E:\Antigravity\aoitori-rw5\probe\bg070a_frame0.jbp").write_bytes(f.read(csz))
print("Dumped op_frame100.jbp and bg070a_frame0.jbp")
