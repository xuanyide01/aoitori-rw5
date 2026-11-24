import struct
f = open(r"G:\SteamLibrary\steamapps\common\Aoi Tori\data\video\op.cmv", "rb")
res = struct.unpack("<4sI", f.read(8))[1]
for fid in (0, 30, 100, 240, 2914):
    f.seek(44 + fid * 20)
    seq, csz, usz, rtype, foff = struct.unpack("<5I", f.read(20))
    f.seek(res + foff)
    b = f.read(csz)
    flags = struct.unpack_from("<H", b, 8)[0]
    smask = struct.unpack_from("<I", b, 0x2C)[0]
    n_sec = b[0x142]
    sec_blks = sum(b[0x144 + s * 2] * b[0x144 + s * 2 + 1] for s in range(n_sec) if (smask >> s) & 1)
    pop = sum(bin(x).count("1") for x in b[0x164 : 0x164 + 450]) if (flags & 0x1000) else -1
    print(f"Frame {fid:4d}: flags=0x{flags:04x} smask=0x{smask:04x} sec_blks={sec_blks:4d} mask_pop={pop:4d} head={b[0x164:0x17c].hex()}")
    if fid == 30:
        nz = [(i, f"{x:02x}") for i, x in enumerate(b[0x164 : 0x164 + 452]) if x != 0xFF]
        print("  Frame 30 non-FF bytes (offset, val):", nz[:30], "len=", len(nz))
