import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori")
ldat = SRC / "Longinus.dat"

with open(ldat, "rb") as f:
    hdr = f.read(16)
    magic, v1, v2, v3, v4, count = struct.unpack("<8s4BI", hdr)
    entries = [struct.unpack("<III", f.read(12)) for _ in range(count)]

hashes = {h: (i, sz, off) for i, (h, sz, off) in enumerate(entries)}
print(f"Loaded {len(entries)} Longinus entries")

# Notice earlier:
# [48] 0x353f037d, [49] 0x0915a4e0 -> diff = 0x53d6a163 mod 2^31
# [22..28] 7 consecutive hashes each adding 0x53d6a163 mod 2^31! (e.g. menu01..menu07 or cg01..07 or save01..07?)
# Let's test standard polynomial hashes mod 2^31 (0x7fffffff mask vs % 0x7fffffff):
# Notice in 31-bit hash: h = (h * p + c) & 0x7fffffff (Wait: if c changes by +1 at index k from end, diff = p^k mod 2^31!)
# If p = 131 (BKDR) -> 131^4 = 294499921 = 0x118d9951 (not 0x53d6a163). Wait: what about 0x53d6a163?
# Wait: 0x53d6a163 is odd! If diff = p^4 mod 2^31 (for "X.ps3", 4 chars ".ps3" after X) OR p^k:
# Let's check what p has p^k == 0x53d6a163 (mod 2^31)! Or maybe it's NOT mod 2^31 at each step, maybe & 0x7fffffff only at the end!
# Wait: if & 0x7fffffff is at each step or end, (h * p + c) mod 2^31 is identical to masking at the end!
# Let's find small roots / common multipliers (31, 33, 131, 133, 65599, 13131, etc.) or test pow(p, k, 2**31) for k in 0..15!
target = 0x53d6a163
MOD = 1 << 31
for k in range(1, 16):
    # Solve p^k == target mod 2^31? Wait: for odd p, let's check common seeds/multipliers!
    pass

# Even faster: test common hash algorithms on "sn101.ps3", "code/sn101.ps3", "data/code/sn101.ps3", "intproc.ps3", etc.!
code_names = [p.name for p in (SRC / "data/code").glob("*.ps3")]
candidates = []
for n in code_names:
    candidates.extend([n, f"code/{n}", f"code\\{n}", f"data/code/{n}", f"data\\code\\{n}", n.upper(), n.lower()])

def test_hash(name, fn):
    hits = sum(1 for c in candidates if fn(c) in hashes)
    if hits > 0:
        print(f"  HIT {name}: {hits} matches!")
        for c in candidates:
            h = fn(c)
            if h in hashes:
                print(f"    {c} -> 0x{h:08x} (idx={hashes[h][0]}, sz={hashes[h][1]})")
                break

# Common multipliers for BKDR / SDBM / DJB2 / JS / RS / ELF / Murmur / FNV
# Wait: notice [22..28] AND [48..49] BOTH had step 0x53d6a163!
# What if [22..28] are images ending in ".pb3" (4 chars after digit) AND [48..49] are scripts ending in ".ps3" (4 chars after digit)!!
# Both ".pb3" and ".ps3" have length 4!! So p^4 == 0x53d6a163 (mod 2^31)!!
# Let's find ALL p in [0, 2^31) with p^4 == 0x53d6a163 (mod 2^31) using Hensel lifting!
roots = [x for x in range(16) if (x**4) % 16 == target % 16]
for bit in range(4, 31):
    m = 1 << (bit + 1)
    new_roots = []
    for r in roots:
        for cand in (r, r + (1 << bit)):
            if pow(cand, 4, m) == target % m:
                new_roots.append(cand)
    roots = new_roots
print("4th roots of 0x53d6a163 mod 2^31:", [f"{r} (0x{r:x})" for r in roots])
for r in roots:
    for init in (0, 5381, 0x811c9dc5):
        def h_fn(s, mul=r, h0=init):
            h = h0
            for b in s.encode("ascii"):
                h = (h * mul + b) & 0x7FFFFFFF
            return h
        hits = sum(1 for c in candidates if h_fn(c) in hashes)
        if hits:
            print(f"  SOLVED! mul={r} (0x{r:x}), init={init}: {hits} hits!")
