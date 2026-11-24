import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

for name in ["op_frame100.jbp", "bg070a_frame0.jbp"]:
    d = Path(rf"E:\Antigravity\aoitori-rw5\probe\{name}").read_bytes()
    print(f"=== {name} (len={len(d):,}) ===")
    for off in range(0, 256, 16):
        chunk = d[off:off+16]
        print(f"  {off:04x}: {' '.join(f'{b:02x}' for b in chunk)}")
    # Note: hdr: magic=JBPD, data_pos=44 (0x2c), format=0x58c00002, ? = 0x50, w=1280, h=720, bpp=24
    # dc_bytes = d[28:32], ac_bytes = d[32:36]
    dc_sz, ac_sz = struct.unpack("<II", d[28:36])
    print(f"  dc_sz={dc_sz}, ac_sz={ac_sz}, 44+dc+ac={44+dc_sz+ac_sz}, remaining={len(d)-(44+dc_sz+ac_sz)}")
