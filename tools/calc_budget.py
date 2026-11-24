import json
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"E:\Antigravity\aoitori-rw5")
SRC = ROOT / "src"
OUT_BUDGET = ROOT / "reports/budget.json"


def estimate_zip_bytes(path: Path) -> int:
    # Measure actual deflate compressed size of a directory/file or raw bytes for already-compressed formats
    raw = path.stat().st_size
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".opus"):
        return raw + 64
    # Deflate estimate for text/js/json/otf
    import zlib
    comp = zlib.compress(path.read_bytes(), level=6)
    return len(comp) + 64


def main():
    categories = {
        "story": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
        "images_bg_ev": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
        "images_h_adult": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
        "sprites_base": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
        "sprites_faces": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
        "opening": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
        "audio": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
        "font": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
        "code_and_other": {"files": 0, "rawBytes": 0, "estZipBytes": 0},
    }

    for p in sorted(SRC.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(SRC).as_posix()
        # Exclude raw JSON duplicates when .js module exists
        if rel in ("common/sprite-meta.json", "common/opening-meta.json"):
            continue
        raw = p.stat().st_size
        est = estimate_zip_bytes(p)

        if rel.startswith("common/story/"):
            cat = "story"
        elif rel.startswith("common/images/"):
            cat = "images_h_adult" if p.name.startswith("h_") else "images_bg_ev"
        elif rel.startswith("common/sprites/"):
            cat = "sprites_base"
        elif rel.startswith("common/faces/"):
            cat = "sprites_faces"
        elif rel.startswith("common/opening/"):
            cat = "opening"
        elif p.suffix.lower() == ".opus":
            cat = "audio"
        elif p.suffix.lower() in (".otf", ".ttf"):
            cat = "font"
        else:
            cat = "code_and_other"

        categories[cat]["files"] += 1
        categories[cat]["rawBytes"] += raw
        categories[cat]["estZipBytes"] += est

    total_files = sum(v["files"] for v in categories.values())
    total_raw = sum(v["rawBytes"] for v in categories.values())
    total_est = sum(v["estZipBytes"] for v in categories.values())
    # Add ~40 KB overhead for compiled QuickApp bundle (manifest + app.js + index.js + ZIP central dir)
    est_with_overhead = total_est + total_files * 90 + 45000

    report = {
        "hardLimits": {
            "maxPackageBytes": 25000000,
            "maxZipEntries": 4100,
        },
        "estimated": {
            "totalFiles": total_files + 4,
            "totalRawBytes": total_raw,
            "estimatedPackageBytes": est_with_overhead,
            "headroomBytes": 25000000 - est_with_overhead,
            "entryHeadroom": 4100 - (total_files + 4),
            "withinBudget": (est_with_overhead < 25000000) and ((total_files + 4) <= 4100),
        },
        "breakdown": categories,
    }
    OUT_BUDGET.write_text(json.dumps(report, indent=2, ensure_ascii=False), "utf-8")
    print(f"Budget report: files={total_files+4}/4100, raw={total_raw:,} B, estPkg={est_with_overhead:,} B (< 25,000,000? {report['estimated']['withinBudget']})")
    for k, v in categories.items():
        print(f"  {k:16s}: files={v['files']:4d}, raw={v['rawBytes']:10,d} B, estZip={v['estZipBytes']:10,d} B")


if __name__ == "__main__":
    main()
