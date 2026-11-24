import json
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")
OUT = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named")
OUT.mkdir(parents=True, exist_ok=True)

def lhash(s: str) -> int:
    h = 0
    for b in s.upper().encode("utf-16le"):
        h = (h * 131 + b) & 0x7FFFFFFF
    return h

# Build complete candidate map
candidates = {}
for p in (SRC / "data").rglob("*"):
    if p.is_file():
        candidates[lhash(p.name)] = p.name
        rel = str(p.relative_to(SRC / "data")).replace("\\", "/")
        candidates[lhash(rel)] = rel

fname_re = re.compile(rb"[a-zA-Z0-9_\-\.]+\.(?:pb3|ps3|png|bmp|ogg|cmv)")
for p in (Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_raw")).glob("*.ps3"):
    for m in fname_re.findall(p.read_bytes()):
        s = m.decode("ascii", errors="ignore")
        candidates[lhash(s)] = s
for stem in ["title01_chip", "title02_chip", "title03_chip", "title_chip_trial", "title_chip_trial_v2",
             "unlock01", "unlock02", "unlock03", "unlock04", "unlock05", "eyecatch00", "eyecatch01",
             "eyecatch02", "eyecatch03", "eyecatch04", "eyecatch05", "eyecatch06", "fontcolor", "gesture"]:
    candidates[lhash(stem + ".pb3")] = stem + ".pb3"

ldat = SRC / "Longinus.dat"
manifest = []
with open(ldat, "rb") as f:
    magic, v1, v2, v3, v4, count = struct.unpack("<8s4BI", f.read(16))
    entries = [struct.unpack("<III", f.read(12)) for _ in range(count)]
    for i, (h, sz, off) in enumerate(entries):
        name = candidates.get(h, f"unknown_{i:03d}_{h:08x}.bin")
        f.seek(off)
        raw = f.read(sz)
        kind = "ps3" if raw[:4] == b"PS2A" else "bgra"
        sub = "code" if kind == "ps3" else "image"
        dest = OUT / sub / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        manifest.append({"index": i, "hash": f"0x{h:08x}", "name": name, "kind": kind, "size": sz})

(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")
print(f"Extracted {len(manifest)} Longinus.dat entries ({sum(1 for m in manifest if m['kind']=='ps3')} ps3, {sum(1 for m in manifest if m['kind']=='bgra')} bgra)")
