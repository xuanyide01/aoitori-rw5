import struct
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NKA_PATH = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori\AoiToriR18Patchv1.04.bin")

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
    print(f"Parsed {len(entries)} entries! data_start = 0x{data_start:x} ({data_start:,})")
    # Check if data_start + last(offset + size) == file size
    last = entries[-1]
    file_size = NKA_PATH.stat().st_size
    print(f"data_start + last_end = {data_start + last[7] + last[8]:,}, actual file_size = {file_size:,}")
    print("f1 counts:", Counter(e[1] for e in entries))
    print("f2 counts:", Counter(e[2] for e in entries))
    print("f3 counts:", Counter(e[3] for e in entries))
    print("f4 counts:", Counter(e[4] for e in entries))
    print("h1_len counts:", Counter(len(e[5]) for e in entries))
    print("h2_len counts:", Counter(len(e[6]) for e in entries))
    prefixes = Counter(e[0].split("/")[0] if "/" in e[0] else "(root)" for e in entries)
    print("Top-level dirs:", prefixes.most_common(20))
    for i in range(5):
        e = entries[i]
        f.seek(data_start + e[7])
        head = f.read(min(64, e[8]))
        print(f"  [{i}] {e[0]} f=({e[1]},{e[2]},{e[3]},{e[4]}) off={e[7]} size={e[8]} h1={e[5].hex()[:16]}.. h2={e[6].hex()[:16]}..")
        print(f"      data[0:32]: {' '.join(f'{b:02x}' for b in head[:32])}")
        print(f"      asc[0:32]:  {''.join(chr(b) if 32<=b<127 else '.' for b in head[:32])}")
    # Also sample entries with different (f1, f2, f3, f4) combinations
    seen = set()
    for e in entries:
        k = (e[1], e[2], e[3], e[4])
        if k not in seen:
            seen.add(k)
            f.seek(data_start + e[7])
            head = f.read(min(64, e[8]))
            print(f"  combo {k}: {e[0]} size={e[8]} data[0:32]={' '.join(f'{b:02x}' for b in head[:32])} | {''.join(chr(b) if 32<=b<127 else '.' for b in head[:32])}")
