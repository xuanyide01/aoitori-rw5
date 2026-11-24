import struct
import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

bg_img = Image.open(r"E:\Antigravity\aoitori-rw5\probe\bg_sample.png")
print(f"bg_sample.png: size={bg_img.size}, mode={bg_img.mode}")

# Check ps_cpz files
for p in sorted(Path(r"E:\Antigravity\aoitori-rw5\probe\ps_cpz").iterdir()):
    raw = p.read_bytes()
    print(f"ps_cpz/{p.name}: {len(raw)} B, hex={raw[:32].hex()}")

# Scan all 86 unpacked .bin files in probe/ps3/
ps3_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")
total_strings = 0
non_ascii_samples = []
eng_samples = []
for p in sorted(ps3_dir.glob("*.bin")):
    data = p.read_bytes()
    hdr = struct.unpack("<4s11I", data[:48])
    # Notice hdr[7]=code1, hdr[8]=code2, hdr[9]=str_pool_size? Let's verify!
    # Wait: earlier hdr[10] = len(data) - 48! And what is hdr[5]? Let's find exact string pool offset!
    # In sn101: hdr[10] = 496516, hdr[9] = 130237. Let's check 48 + hdr[10] - hdr[9]!
    str_off = len(data) - hdr[9]
    # Also scan backwards a bit to see if strings start at str_off or 0x30 + hdr[5]
    pool = data[str_off:]
    strs = [s for s in pool.split(b"\x00") if s]
    total_strings += len(strs)
    for s in strs:
        if any(b >= 0x80 for b in s):
            if len(non_ascii_samples) < 30:
                # try utf-8, gbk, cp932
                u = s.decode("utf-8", errors="replace")
                g = s.decode("gbk", errors="replace")
                j = s.decode("cp932", errors="replace")
                non_ascii_samples.append((p.name, s[:40].hex(), u, g, j))
        else:
            if len(eng_samples) < 10 and len(s) > 20 and b" " in s:
                eng_samples.append((p.name, s.decode("ascii", errors="replace")))

print(f"Scanned 86 PS3 scripts: total strings={total_strings}")
print("English samples:")
for fn, txt in eng_samples:
    print(f"  [{fn}] {txt}")
print(f"Non-ASCII samples (showing {len(non_ascii_samples)}):")
for fn, hx, u, g, j in non_ascii_samples:
    print(f"  [{fn}] hex={hx} | utf8={u!r} | gbk={g!r} | cp932={j!r}")
