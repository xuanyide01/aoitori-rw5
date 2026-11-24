import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")
ldat = SRC / "Longinus.dat"

def lhash(s: str) -> int:
    h = 0
    for b in s.upper().encode("utf-16le"):
        h = (h * 131 + b) & 0x7FFFFFFF
    return h

with open(ldat, "rb") as f:
    magic, v1, v2, v3, v4, count = struct.unpack("<8s4BI", f.read(16))
    entries = [struct.unpack("<III", f.read(12)) for _ in range(count)]

hash_map = {h: (i, sz, off) for i, (h, sz, off) in enumerate(entries)}

# Collect all candidate filenames from data/ + inside unpacked ps3 string pools!
candidates = set()
for p in (SRC / "data").rglob("*"):
    if p.is_file():
        candidates.add(p.name)
        candidates.add(str(p.relative_to(SRC / "data")).replace("\\", "/"))
        candidates.add(str(p.relative_to(SRC / "data")).replace("/", "\\"))

import re
fname_re = re.compile(rb"[a-zA-Z0-9_\-\.]+\.(?:pb3|ps3|png|bmp|ogg|cmv)")
for p in (Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_raw")).glob("*.ps3"):
    for m in fname_re.findall(p.read_bytes()):
        s = m.decode("ascii", errors="ignore")
        candidates.add(s)
        candidates.add("image/" + s)
        candidates.add("image/chip/" + s)
        candidates.add("image/update/" + s)
        candidates.add("image/event/" + s)
for p in (Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")).glob("*.bin"):
    for m in fname_re.findall(p.read_bytes()):
        s = m.decode("ascii", errors="ignore")
        candidates.add(s)

# Also add common title/ui names
for stem in ["title", "title_bg", "title01", "title02", "title_logo", "logo", "config", "save", "load", "backlog", "cg", "bgm", "scene", "omake", "system", "dialog", "menu", "extra", "staff", "credit", "ending", "ed", "op"]:
    for ext in [".pb3", ".png", ".bmp", ".ps3"]:
        candidates.add(stem + ext)

matched = {}
for c in sorted(candidates):
    h = lhash(c)
    if h in hash_map:
        idx, sz, off = hash_map[h]
        matched[idx] = (c, h, sz, off)

print(f"Matched {len(matched)} / {len(entries)} Longinus entries!")
unmatched_imgs = []
for i, (h, sz, off) in enumerate(entries):
    if i in matched:
        c, _, _, _ = matched[i]
        if not c.endswith(".ps3"):
            print(f"  IMG [{i:3d}] 0x{h:08x} size={sz:10,d} -> {c}")
    else:
        unmatched_imgs.append((i, h, sz, off))
print(f"Unmatched entries ({len(unmatched_imgs)}):")
for i, h, sz, off in unmatched_imgs:
    print(f"  [{i:3d}] 0x{h:08x} size={sz:10,d}")
