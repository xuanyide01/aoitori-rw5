import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Test 5th root (or k=1..8) for Longinus hash:
# Known pairs:
#   "sn101.ps3" (or "code/sn101.ps3") -> 0x353f037d
#   "sn102.ps3" (or "code/sn102.ps3") -> 0x0915a4e0
#   diff = 0x53d6a163 mod 2^31
target = 0x53d6a163
for k in [1, 3, 5, 7, 9]:
    roots = [x for x in range(16) if pow(x, k, 16) == target % 16]
    for bit in range(4, 31):
        m = 1 << (bit + 1)
        nr = []
        for r in roots:
            for cand in (r, r + (1 << bit)):
                if pow(cand, k, m) == target % m:
                    nr.append(cand)
        roots = nr
    print(f"k={k} roots: {[f'{r} (0x{r:x})' for r in roots[:10]]}")

# Also inspect JbpReader header vs JBPD header!
op100 = Path(r"E:\Antigravity\aoitori-rw5\probe\op_frame100.jbp").read_bytes()
print("JBPD header fields (11 uint32):", struct.unpack("<4s10I", op100[:44]))
print("JBPD header as uint16:", struct.unpack("<4s20H", op100[:44]))
