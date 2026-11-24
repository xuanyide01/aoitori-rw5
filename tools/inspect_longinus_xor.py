import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 1. Check the 13 files in probe/longinus_ps3/
ps3_ok_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_ps3")
ok_files = sorted(ps3_ok_dir.glob("*.bin"))
print(f"longinus_ps3 (UnpackPs2 ok): {len(ok_files)}")
for p in ok_files[:5]:
    d = p.read_bytes()
    h = struct.unpack("<4s11I", d[:48])
    print(f"  {p.name}: len={len(d):,}, hdr[1..11]={[hex(x) for x in h[1:]]}")
    print("    tail[-200:] gbk:", repr(d[-200:].decode("gbk", errors="replace")))

# 2. Check entry_033 raw vs dec around 0x30 and at tail
raw33 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_raw\entry_033_63fa3269.ps3").read_bytes()
dec33 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_dec\entry_033_63fa3269.bin").read_bytes()
print("\nentry_033 raw==dec?", raw33 == dec33)
print("raw33[0x30:0x60]:", raw33[0x30:0x60].hex())
print("dec33[0x30:0x60]:", dec33[0x30:0x60].hex())
print("raw33[-64:]:", raw33[-64:].hex())
print("dec33[-64:]:", dec33[-64:].hex())

# 3. Check entry_035 raw vs dec
raw35 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_raw\entry_035_3410454f.ps3").read_bytes()
dec35 = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_dec\entry_035_3410454f.bin").read_bytes()
print("\nentry_035 raw==dec?", raw35 == dec35)
print("raw35[0x30:0x60]:", raw35[0x30:0x60].hex())
print("dec35[0x30:0x60]:", dec35[0x30:0x60].hex())
print("raw35[-64:]:", raw35[-64:].hex())
print("dec35[-64:]:", dec35[-64:].hex())

# 4. Compare with disk intproc.bin (which is uncompressed/decrypted)
disk_intproc = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3\intproc.bin").read_bytes()
print("\ndisk intproc.bin len:", len(disk_intproc), "hdr:", [hex(x) for x in struct.unpack("<4s11I", disk_intproc[:48])[1:]])
print("disk intproc[0x30:0x60]:", disk_intproc[0x30:0x60].hex())
