import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LONG_CODE = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
DISK_PS3 = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")

def get_text_seg(data):
    hdr = struct.unpack("<4s11I", data[:48])
    _, hdr_size, _, _, label_count, code_sz, un_sz, *_ = hdr
    return data[hdr_size + code_sz + 4 * label_count + un_sz :]

for name in ["snhmr3.ps3", "sn101.ps3", "omake.ps3", "menu.ps3", "intcode.ps3"]:
    p = LONG_CODE / name
    data = p.read_bytes() if p.exists() else (DISK_PS3 / (Path(name).stem + ".bin")).read_bytes()
    tseg = get_text_seg(data)
    strs = [s.decode("gbk", errors="replace") for s in tseg.split(b"\x00") if s]
    print(f"=== {name} text_seg ({len(strs)} strings) ===")
    interesting = [s for s in strs if any(k in s.lower() for k in ["h_", "st-", "up-", "bg", "ev", "title", "bgm", "op.", "omake"]) and ".ogg" not in s.lower()]
    print("  interesting (up to 40):", interesting[:40])
    # Also check where "h_mr" or "st-" appears in sn101/snhmr3!
    for prefix in ["st-", "up-", "h_", "ev_", "bg", "title"]:
        hits = [s for s in strs if s.lower().startswith(prefix)]
        if hits:
            print(f"  starts with {prefix!r} ({len(hits)}): {hits[:10]}")
