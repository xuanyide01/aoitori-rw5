import io
import json
import sys
import zipfile
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(r"E:\Antigravity\aoitori-rw5")
sys.path.insert(0, str(ROOT / "tools"))
import rpk_signature


def main():
    dist = ROOT / "dist"
    rpk_files = sorted(dist.glob("*.rpk"))
    assert rpk_files, f"No .rpk found in {dist}"
    rpk_path = rpk_files[0]

    sig_info = rpk_signature.audit(rpk_path)
    assert sig_info["bytes"] < 25_000_000, f"Package too large: {sig_info['bytes']}"
    assert sig_info["entries"] <= 4100, f"Too many ZIP entries: {sig_info['entries']}"

    with zipfile.ZipFile(rpk_path, "r") as z:
        names = set(z.namelist())
        manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        assert manifest["package"] == "com.antigravity.aoitori.rw5", manifest["package"]
        assert manifest["name"] == "アオイトリ", manifest["name"]
        assert manifest["config"]["designWidth"] == 432, manifest["config"]

        # No redundant JSON bloat in common/
        assert "common/sprite-meta.json" not in names, "Unexpected common/sprite-meta.json"
        assert "common/opening-meta.json" not in names, "Unexpected common/opening-meta.json"

        # Audio & original UI checks
        for opus in ["common/title-bgm.opus", "common/title-true-bgm.opus", "common/opening-bgm.opus"]:
            assert opus in names, f"Missing {opus}"
            assert z.read(opus)[:4] == b"OggS", f"Invalid Opus header in {opus}"
        for ui in ["tbtn_start.png", "tbtn_akari.png", "tbtn_load.png", "tbtn_extra.png", "tbtn_config.png", "tbtn_exit.png", "dlg_bg.jpg"]:
            assert f"common/ui/{ui}" in names, f"Missing common/ui/{ui}"
        bad_audio = [n for n in names if n.endswith(".wav") or "voice" in n.lower()]
        assert not bad_audio, f"Unexpected audio files: {bad_audio}"

        # Font glyph coverage check across bundled story chunks + UI source
        otf_bytes = z.read("common/aoitori-text.otf")
        ttf = TTFont(io.BytesIO(otf_bytes))
        cmap = set(ttf.getBestCmap().keys())

        graph = json.loads((ROOT / "converted" / "graph.json").read_text("utf-8"))
        missing_chunks = []
        oversized_chunks = []
        needed_chars = set()
        for ch in (ROOT / "src" / "pages" / "index" / "index.ux").read_text("utf-8"):
            if ord(ch) > 127:
                needed_chars.add(ch)
        for node in graph["nodes"]:
            for cid in node["chunks"]:
                zp = f"common/story/{cid}.txt"
                if zp not in names:
                    missing_chunks.append(cid)
                    continue
                raw_chunk = z.read(zp)
                if len(raw_chunk) > 24576:
                    oversized_chunks.append((cid, len(raw_chunk)))
                for ch in raw_chunk.decode("utf-8"):
                    if ord(ch) > 127:
                        needed_chars.add(ch)
        assert not missing_chunks, f"Missing chunks: {missing_chunks[:10]}"
        assert not oversized_chunks, f"Oversized chunks >24KiB: {oversized_chunks[:10]}"
        missing_glyphs = [c for c in needed_chars if ord(c) not in cmap]
        assert not missing_glyphs, f"Missing glyphs in OTF: {missing_glyphs[:20]}"

        # BGs/CGs completeness
        reqs = json.loads((ROOT / "converted" / "image-requests.json").read_text("utf-8"))
        missing_bgs = [b for b in reqs["bgs"] if f"common/images/{b}.jpg" not in names]
        assert not missing_bgs, f"Missing BGs/CGs: {missing_bgs[:10]}"

        # Sprites & face diffs completeness
        sp_meta = json.loads((ROOT / "converted" / "sprite-meta.json").read_text("utf-8"))
        missing_sp = []
        for sp_name, entry in sp_meta.items():
            base_key, face_file = entry[0], entry[1]
            full_flag = entry[6] if len(entry) > 6 else 0
            if not full_flag and f"common/sprites/{base_key}.png" not in names:
                missing_sp.append(f"base:{base_key}")
            if face_file and f"common/faces/{face_file}" not in names:
                missing_sp.append(f"face:{face_file}")
        assert not missing_sp, f"Missing sprite parts: {missing_sp[:10]}"

        # OP frames completeness (0..416)
        missing_op = [i for i in range(417) if f"common/opening/f{i:04d}.jpg" not in names]
        assert not missing_op, f"Missing OP frames: {missing_op[:10]}"

    report = {
        "rpk": sig_info,
        "manifest": {
            "package": manifest["package"],
            "name": manifest["name"],
            "versionName": manifest["versionName"],
            "designWidth": manifest["config"]["designWidth"],
        },
        "limits": {
            "maxBytes": 25000000,
            "bytesMargin": 25000000 - sig_info["bytes"],
            "maxEntries": 4100,
            "entriesMargin": 4100 - sig_info["entries"],
        },
        "checks": {
            "fontBytes": len(otf_bytes),
            "nonAsciiCharsChecked": len(needed_chars),
            "missingGlyphs": 0,
            "storyNodes": len(graph["nodes"]),
            "storyChunks": graph["totalChunks"],
            "bgsChecked": len(reqs["bgs"]),
            "spritesChecked": len(sp_meta),
            "opFramesChecked": 417,
        },
        "physicalDeviceTested": False,
    }
    out = ROOT / "reports" / "audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
