import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Check Longinus_dec vs original PS3 headers and check for Chinese text!
dec_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_dec")
if dec_dir.exists():
    bins = sorted(dec_dir.glob("*.bin"))
    print(f"longinus_dec files: {len(bins)}")
    for p in bins[:5]:
        d = p.read_bytes()
        h = struct.unpack("<4s11I", d[:48])
        print(f"  {p.name}: len={len(d):,}, hdr={h[0]}, {[hex(x) for x in h[1:]]}")
        # Check tail for GBK/UTF-8 Chinese!
        tail = d[-600:]
        print("    gbk:", repr(tail.decode("gbk", errors="ignore")[:200]))
        print("    utf8:", repr(tail.decode("utf-8", errors="ignore")[:200]))
