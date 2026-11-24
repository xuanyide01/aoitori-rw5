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
    data_start = f.tell()

code_entries = [e for e in entries if e[0].startswith("code/")]
print(f"NKA code/ entries: {len(code_entries)}")
matches_h1 = 0
matches_h2 = 0
matches_neither = 0
missing_on_disk = 0
for e in code_entries:
    name, f1, f2, f3, f4, h1, h2, off, sz = e
    p = DATA / name
    if not p.exists():
        missing_on_disk += 1
        continue
    digest = hashlib.sha256(p.read_bytes()).digest()
    if digest == h1:
        matches_h1 += 1
    elif digest == h2:
        matches_h2 += 1
    else:
        matches_neither += 1
    if len(code_entries) and (name in ("code/intcode.ps3", "code/main.ps3", "code/omake.ps3", "code/sn101.ps3", "code/sn215.ps3")):
        print(f"  {name}: f=({f1},{f2},{f3},{f4}) disk==h1? {digest==h1} disk==h2? {digest==h2} disk_sz={p.stat().st_size}")

print(f"Summary code/: h1={matches_h1}, h2={matches_h2}, neither={matches_neither}, missing={missing_on_disk}")

# Also check image/event/ and video/
img_entries = [e for e in entries if e[0].startswith("image/")]
ih1 = ih2 = ine = imiss = 0
for e in img_entries:
    name, f1, f2, f3, f4, h1, h2, off, sz = e
    p = DATA / name
    if not p.exists():
        imiss += 1
        continue
    if f1 == 0 and sz == 0:
        continue
    digest = hashlib.sha256(p.read_bytes()).digest()
    if digest == h1:
        ih1 += 1
    elif digest == h2:
        ih2 += 1
    else:
        ine += 1
print(f"Summary image/ (non-empty NKA): h1={ih1}, h2={ih2}, neither={ine}, missing={imiss}")

# Check pack/ entries in NKA
pack_entries = [e for e in entries if e[0].startswith("pack/")]
print(f"NKA pack/ entries: {len(pack_entries)}, non-zero size: {sum(1 for e in pack_entries if e[8] > 0)}")
for e in pack_entries:
    if e[8] > 0 or not e[0].startswith("pack/voice"):
        if e[8] > 0:
            print("  non-zero pack:", e[0], e[1:5], e[8])
print("Sample pack/ entries:", [e[0] for e in pack_entries[:15]])
