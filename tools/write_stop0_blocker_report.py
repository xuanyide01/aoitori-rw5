import json
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ps3_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\ps3")
out_path = Path(r"E:\Antigravity\aoitori-rw5\reports\stop0\ps3_language_probe.json")
out_path.parent.mkdir(parents=True, exist_ok=True)

files = []
unique_non_ascii = set()
total_english_lines = 0

for p in sorted(ps3_dir.glob("*.bin")):
    data = p.read_bytes()
    h = struct.unpack("<4s11I", data[:48])
    mpos = data.find(b"message01.pb3")
    if mpos < 0:
        mpos = max(0x30 + h[5], 0)
    pool = data[mpos:]
    eng_count = 0
    non_ascii_count = 0
    for s in pool.split(b"\x00"):
        if not s:
            continue
        if any(b >= 0x80 for b in s):
            if any(b < 0x20 for b in s):
                continue
            non_ascii_count += 1
            unique_non_ascii.add(s.decode("cp932", errors="replace"))
        elif all(32 <= b < 127 for b in s) and b" " in s and len(s) >= 8:
            eng_count += 1
    total_english_lines += eng_count
    files.append({
        "script": p.stem + ".ps3",
        "unpackedBytes": len(data),
        "englishStrings": eng_count,
        "nonAsciiCleanStrings": non_ascii_count,
    })

report = {
    "status": "BLOCKED_NO_CHINESE_IN_PS3",
    "ps3FilesChecked": len(files),
    "totalEnglishStrings": total_english_lines,
    "uniqueNonAsciiStringsAcrossAllPs3": sorted(unique_non_ascii),
    "chineseStringsFound": 0,
    "psCpzEntries": ["maskeffectcut.o2", "maskeffectput.o2", "transeffect.o2"],
    "nkaMatchesDiskH1": {
        "code": "86/86 (1 deleted: code/sn215.ps3)",
        "image": "3378/3378 (1 deleted: image/chip/thanks.pb3)",
        "packsAndVideo": ["pack/balloon.cpz", "pack/stand.cpz", "pack/up.cpz", "video/op.cmv"],
    },
    "reason": "Steam版 data/code/*.ps3 与 AoiToriR18Patchv1.04.bin 均为官英文本（仅含少量 CP932 标点/调试/人名残余，0 条中文）。天之圣杯汉化组中文文本位于禁碰的 Longinus.dat/.dll/.ini 外挂运行时补丁中。",
    "files": files,
}

out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
print("Wrote", out_path)
