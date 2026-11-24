import os
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")

def hex_dump(data: bytes, n=64):
    return " ".join(f"{b:02x}" for b in data[:n])

def ascii_preview(data: bytes, n=64):
    return "".join(chr(b) if 32 <= b < 127 else "." for b in data[:n])

samples = [
    ("ps.cpz", SRC / "data/pack/ps.cpz"),
    ("bg.cpz", SRC / "data/pack/bg.cpz"),
    ("stand.cpz", SRC / "data/pack/stand.cpz"),
    ("up.cpz", SRC / "data/pack/up.cpz"),
    ("balloon.cpz", SRC / "data/pack/balloon.cpz"),
    ("main.ps3", SRC / "data/code/main.ps3"),
    ("sn101.ps3", SRC / "data/code/sn101.ps3"),
    ("h_mr01_01r.pb3", SRC / "data/image/event/h_mr01_01r.pb3"),
    ("op.cmv", SRC / "data/video/op.cmv"),
    ("R18Patch.bin", SRC / "AoiToriR18Patchv1.04.bin"),
]

# Also pick one from chip/, update/, imgvideo/
for sub in ["data/image/chip", "data/image/update", "data/imgvideo"]:
    d = SRC / sub
    files = sorted(p for p in d.iterdir() if p.is_file())
    if files:
        samples.append((f"{sub}/{files[0].name}", files[0]))

for label, p in samples:
    with open(p, "rb") as f:
        head = f.read(128)
    print(f"=== {label} ({p.stat().st_size:,} B) ===")
    print("  hex[0:64]:  ", hex_dump(head, 64))
    print("  ascii[0:64]:", ascii_preview(head, 64))
    print("  hex[64:128]:", hex_dump(head[64:], 64))
    print("  asc[64:128]:", ascii_preview(head[64:], 64))
