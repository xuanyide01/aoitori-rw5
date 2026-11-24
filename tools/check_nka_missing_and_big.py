import hashlib
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")
DATA = SRC / "data"
NKA_PATH = SRC / "AoiToriR18Patchv1.04.bin"

with open(NKA_PATH, "rb") as f:
    magic, version, count = struct.unpack("<4sII", f.read(12))
    entries = []
    for i in range(count):
        name_len = struct.unpack("<I", f.read(4))[0]
        name = f.read(name_len).decode("utf-8", errors="replace")
        f1, f2, f3, f4 = struct.unpack("<IIII", f.read(16))
        h1_len = struct.unpack("<I", f.read(4))[0]
        h1 = f.read(h1_len)
        h2_len = struct.unpack("<I", f.read(4))[0]
        h2 = f.read(h2_len)
        offset, size = struct.unpack("<QQ", f.read(16))
        entries.append((name, f1, f2, f3, f4, h1, h2, offset, size))

for e in entries:
    name, f1, f2, f3, f4, h1, h2, off, sz = e
    p = DATA / name
    if not p.exists():
        if not name.startswith("pack/"):
            print("Missing non-pack:", name, (f1, f2, f3, f4), sz)
    elif name.startswith("video/") or name in ("pack/balloon.cpz", "pack/stand.cpz", "pack/up.cpz"):
        # Check large files incrementally
        h = hashlib.sha256()
        with open(p, "rb") as pf:
            while True:
                buf = pf.read(4 * 1024 * 1024)
                if not buf:
                    break
                h.update(buf)
        d = h.digest()
        print(f"{name}: f=({f1},{f2},{f3},{f4}) disk_sz={p.stat().st_size:,} disk==h1? {d==h1} disk==h2? {d==h2}")
