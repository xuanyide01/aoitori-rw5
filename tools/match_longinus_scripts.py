import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Match Longinus plaintext PS2A scripts to disk unpacked English PS3 scripts via:
# 1) .ogg / .pb3 / .cmv asset references inside the string pool!
# 2) hdr[4] (label count)
disk_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")
long_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_raw")

asset_re = re.compile(rb"[a-zA-Z0-9_\-]+\.(?:ogg|pb3|cmv)")

def get_assets(data):
    mpos = data.find(b"message01.pb3")
    pool = data[mpos:] if mpos >= 0 else data
    return set(m.decode("ascii", errors="ignore").lower() for m in asset_re.findall(pool))

disk_info = {}
for p in sorted(disk_dir.glob("*.bin")):
    d = p.read_bytes()
    h = struct.unpack("<4s11I", d[:48])
    disk_info[p.stem + ".ps3"] = (h[4], get_assets(d))

long_files = sorted(long_dir.glob("*.ps3"))
print(f"Disk scripts: {len(disk_info)}, Longinus PS2A scripts: {len(long_files)}")

mapping = {}
unmatched = []
for lp in long_files:
    ld = lp.read_bytes()
    lh = struct.unpack("<4s11I", ld[:48])
    l_assets = get_assets(ld)
    best = None
    best_score = -1
    for name, (dh4, d_assets) in disk_info.items():
        if not l_assets and not d_assets:
            score = 1 if lh[4] == dh4 else 0
        else:
            inter = len(l_assets & d_assets)
            union = len(l_assets | d_assets) or 1
            score = inter / union + (0.01 if abs(lh[4] - dh4) <= 5 else 0)
        if score > best_score:
            best_score = score
            best = name
    # Parse hash from filename entry_XXX_HHHHHHHH.ps3
    parts = lp.stem.split("_")
    idx = int(parts[1])
    hval = int(parts[2], 16)
    mapping[idx] = (hval, best, best_score, len(l_assets))
    if best_score < 0.8:
        unmatched.append((idx, f"0x{hval:08x}", best, best_score, len(l_assets)))

print("Sample mappings:")
for idx in sorted(mapping)[:20]:
    hval, best, sc, na = mapping[idx]
    print(f"  [{idx:3d}] 0x{hval:08x} -> {best:<15s} (score={sc:.4f}, assets={na})")
print("Low-score / unmatched:", unmatched)
