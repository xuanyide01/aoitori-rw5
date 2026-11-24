import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")
code_names = [p.name for p in (SRC / "data/code").glob("*.ps3")]

# Test BKDR (mul=131) with various forms against target 0x353f037d (sn101.ps3)
target = 0x353f037d
def bkdr(b, mul=131, init=0):
    h = init
    for x in b:
        h = (h * mul + x) & 0x7FFFFFFF
    return h

forms = []
for n in ["sn101.ps3", "code/sn101.ps3", "code\\sn101.ps3", "data/code/sn101.ps3", "data\\code\\sn101.ps3", "sn101"]:
    for s in [n, n.upper(), n.lower()]:
        for enc in ["ascii", "utf-16le"]:
            b = s.encode(enc)
            for suf in [b"", b"\x00", b"\x00\x00"]:
                for init in [0, 1, 5381]:
                    if bkdr(b + suf, 131, init) == target:
                        print("EXACT BKDR MATCH!", s, enc, suf, init)

#Wait: what if Longinus hash is BKDR over string length? Let's test reverse string or different seed!
for n in ["sn101.ps3", "code/sn101.ps3", "code\\sn101.ps3", "data/code/sn101.ps3", "data\\code\\sn101.ps3"]:
    for s in [n, n.upper(), n.lower()]:
        b = s.encode("ascii")
        # Try 131 forward and reverse, and check where 0x53d6a163 = 131^9 mod 2^31 comes from!
        # Wait: in "code\\sn101.ps3" (14 chars), '1' is at index 8 (5 chars from end), in utf-16le '1' is 10 bytes from end!
        # What has '1' at 9 bytes from end? "sn101.ps3" + 5 bytes! e.g. "sn101.ps3" + ".long"? No, what about "data/code/sn101.ps3"? No!
        # What about hashing backwards? "sn101.ps3" backwards: index of '1' is 4 -> wait: in "data\\code\\sn101.ps3", index of '1' from start is 12; in "code/sn101.ps3", index of '1' is 9!!
        # WAIT: "code/sn101.ps3"[9] is '1'!! Index 9 from the LEFT means if hashed RIGHT-TO-LEFT, changing index 9 multiplies by 131^9!!
        if bkdr(b[::-1]) == target:
            print("REVERSE BKDR MATCH!", s)

# Also dump first 5 Longinus OTHER image entries as PNG (BGRA -> RGBA) to see dimensions/content!
import struct
out_img_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_img")
out_img_dir.mkdir(parents=True, exist_ok=True)
ldat = SRC / "Longinus.dat"
with open(ldat, "rb") as f:
    magic, v1, v2, v3, v4, count = struct.unpack("<8s4BI", f.read(16))
    entries = [struct.unpack("<III", f.read(12)) for _ in range(count)]
    for i, (h, sz, off) in enumerate(entries):
        if sz == 3686400:
            f.seek(off)
            raw = f.read(sz)
            im = Image.frombytes("RGBA", (1280, 720), raw, "raw", "BGRA")
            im.save(out_img_dir / f"img_{i:03d}_{h:08x}.png")
            if i >= 5:
                break
print("Saved sample 1280x720 Longinus images!")
