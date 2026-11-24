import json
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LONG_CODE = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
DISK_PS3 = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")
OUT_REPORT = Path(r"E:\Antigravity\aoitori-rw5\reports\stop0\script_inventory.json")
OUT_DUMP = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3_strings")
OUT_DUMP.mkdir(parents=True, exist_ok=True)

PUSH_BEG = b"\x01\x02\x20\x01"
PUSH_END = b"\x0f\x02\x30\x04"

# Also check if there are strings pushed with slightly different opcodes (e.g. without 0f023004, or with 01022001 <rva>)
def parse_ps3(data: bytes):
    hdr = struct.unpack("<4s11I", data[:48])
    magic, hdr_size, un0, dec_key, label_count, code_sz, un_sz, text_sz, beg_pc, comp_sz, uncomp_sz, un3 = hdr
    code_seg_start = hdr_size
    code_seg_len = code_sz + 4 * label_count + un_sz
    text_seg_start = code_seg_start + code_seg_len
    code_seg = data[code_seg_start:text_seg_start]
    text_seg = data[text_seg_start:]

    # Extract all strings in text_seg by offset
    def read_cstr(rva):
        if rva >= len(text_seg):
            return None
        end = text_seg.find(b"\x00", rva)
        if end < 0:
            end = len(text_seg)
        raw = text_seg[rva:end]
        return raw.decode("gbk", errors="replace")

    # Find all 01 02 20 01 <uint32> ... patterns and also check what opcode follows!
    pushed = []
    pos = 0
    while True:
        idx = code_seg.find(PUSH_BEG, pos)
        if idx < 0 or idx + 8 > len(code_seg):
            break
        rva = struct.unpack_from("<I", code_seg, idx + 4)[0]
        next_op = code_seg[idx + 8 : idx + 12]
        s = read_cstr(rva)
        if s is not None:
            pushed.append((idx, rva, next_op.hex(), s))
        pos = idx + 4

    # Filter dialogue/narrative strings vs asset/system strings
    asset_exts = (".ogg", ".wav", ".mv2", ".pb3", ".pb2", ".ps3", ".ps2", ".cur", ".cmv", ".mgv", ".png", ".txt", ".ttf", ".otf", ".o2")
    text_lines = []
    h_cgs = set()
    cmvs = set()
    st_sprites = set()
    up_sprites = set()
    script_refs = set()
    bgm_refs = set()

    for off, rva, nop, s in pushed:
        low = s.lower()
        if any(ext in low for ext in asset_exts):
            if low.endswith(".pb3"):
                if low.startswith("h_"):
                    h_cgs.add(s)
                elif low.startswith("st-"):
                    st_sprites.add(s)
                elif low.startswith("up-"):
                    up_sprites.add(s)
            elif low.endswith(".cmv"):
                cmvs.add(s)
            elif low.endswith(".ps3"):
                script_refs.add(s)
            elif low.endswith(".ogg") and (low.startswith("bgm") or "bgm" in low or low.startswith("aoitori")):
                bgm_refs.add(s)
        elif nop == "0f023004":
            # Check if CJK or meaningful text
            if s.strip():
                text_lines.append((off, s))

    # Also scan full text_seg for any strings missed by 01022001
    all_pool_strs = [x.decode("gbk", errors="replace") for x in text_seg.split(b"\x00") if x]
    # Count Chinese characters in text_lines
    cjk_lines = [t for _, t in text_lines if any("\u4e00" <= c <= "\u9fff" for c in t)]

    # Check labels / chapters / choices
    has_select = any(b"\x10\x22" in code_seg or b"\x70\x23" in code_seg for _ in [1]) # 0x2210 or 0x2370 in LE!
    select_hits = code_seg.count(b"\x10\x22") + code_seg.count(b"\x70\x23")
    # Check 0x2210 / 0x2370 as uint16 opcodes in code_seg
    op_2210 = sum(1 for i in range(0, len(code_seg)-1, 2) if code_seg[i:i+2] in (b"\x10\x22", b"\x70\x23"))

    return {
        "header": {
            "labelCount": label_count,
            "codeSegLen": code_seg_len,
            "textSegLen": len(text_seg),
        },
        "pushedCount": len(pushed),
        "textLineCount": len(text_lines),
        "cjkLineCount": len(cjk_lines),
        "hCgCount": len(h_cgs),
        "hCgs": sorted(h_cgs),
        "cmvRefs": sorted(cmvs),
        "stSpriteCount": len(st_sprites),
        "upSpriteCount": len(up_sprites),
        "scriptRefs": sorted(script_refs),
        "bgmRefs": sorted(bgm_refs),
        "selectOpHits": op_2210,
        "sampleCjk": cjk_lines[:6],
        "pushed": pushed,
    }

inventory = []
all_scripts = sorted(p.name for p in LONG_CODE.glob("*.ps3"))
if "intcode.ps3" not in all_scripts:
    all_scripts.insert(0, "intcode.ps3")

total_cjk = 0
total_h_scripts = 0
for name in all_scripts:
    if (LONG_CODE / name).exists():
        data = (LONG_CODE / name).read_bytes()
        src = "Longinus.dat"
    else:
        data = (DISK_PS3 / (Path(name).stem + ".bin")).read_bytes()
        src = "data/code"
    info = parse_ps3(data)
    pushed = info.pop("pushed")
    # Write sample / full pushed strings for key scripts
    (OUT_DUMP / (Path(name).stem + ".json")).write_text(
        json.dumps([{"off": o, "nop": n, "s": s} for o, _, n, s in pushed], ensure_ascii=False, indent=1),
        "utf-8"
    )
    is_adult = name.startswith("snh") or info["hCgCount"] > 0
    if is_adult:
        total_h_scripts += 1
    total_cjk += info["cjkLineCount"]
    entry = {"script": name, "source": src, "adult": is_adult, **info}
    inventory.append(entry)

summary = {
    "totalScripts": len(inventory),
    "adultScripts": total_h_scripts,
    "totalCjkLines": total_cjk,
    "scripts": inventory,
}
OUT_REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")

print(f"Parsed {len(inventory)} scripts: adultScripts={total_h_scripts}, totalCjkLines={total_cjk}")
print("System / special scripts:")
for e in inventory:
    if not e["script"].startswith("sn"):
        print(f"  {e['script']:<14s} cjk={e['cjkLineCount']:4d} text={e['textLineCount']:4d} hCG={e['hCgCount']:2d} sel={e['selectOpHits']:2d} refs={e['scriptRefs'][:5]}")
print("Story scripts with choices or adult or cmv:")
for e in inventory:
    if e["script"].startswith("sn") and (e["selectOpHits"] > 0 or e["adult"] or e["cmvRefs"]):
        print(f"  {e['script']:<14s} cjk={e['cjkLineCount']:4d} adult={str(e['adult']):<5s} hCG={e['hCgCount']:2d} sel={e['selectOpHits']:2d} cmv={e['cmvRefs']} refs={e['scriptRefs']}")
print("Sample sn101 CJK:", next(e["sampleCjk"] for e in inventory if e["script"] == "sn101.ps3"))
