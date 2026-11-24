import hashlib
import json
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

# 1. Inspect L111, L91, and L138/L112 projection lines
p101 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code\sn101.ps3")
h, l, c, tx = parse_ps3_raw(p101)
lb = 4 * len(l)
print("=== L111 ===")
for o, t in disasm(c, tx, l[111]+lb, l[112]+lb, lb):
    print(f"  {o:05x}: {t}")
print("\n=== L91 ===")
for o, t in disasm(c, tx, l[91]+lb, l[92]+lb, lb):
    print(f"  {o:05x}: {t}")
print("\n=== L138 0x25e00..0x26100 ===")
for o, t in disasm(c, tx, 0x25e00, 0x26100, lb):
    print(f"  {o:05x}: {t}")
print("\n=== L112 0x203b0..0x205e0 ===")
for o, t in disasm(c, tx, 0x203b0, 0x205e0, lb):
    print(f"  {o:05x}: {t}")

# 2. Inspect Longinus.dat title01_chip / title02_chip / title03_chip & omake BG/chip dimensions
img_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\image")
print("\n=== Longinus localized images ===")
for p in sorted(img_dir.glob("*")):
    print(f"  {p.name:28s} {p.stat().st_size:10d}")
