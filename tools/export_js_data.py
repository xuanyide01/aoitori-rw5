import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"E:\Antigravity\aoitori-rw5")


def main():
    graph = json.loads((ROOT / "converted/graph.json").read_text("utf-8"))
    # Compact graph.js for direct require() in QuickApp & Node tests
    graph_js = "module.exports = " + json.dumps(graph, separators=(",", ":"), ensure_ascii=False) + ";\n"
    (ROOT / "src/common/graph.js").write_text(graph_js, "utf-8")
    print(f"Wrote src/common/graph.js: {len(graph_js):,} bytes")

    gallery = json.loads((ROOT / "converted/gallery.json").read_text("utf-8"))
    gallery_js = "module.exports = " + json.dumps(gallery, separators=(",", ":"), ensure_ascii=False) + ";\n"
    (ROOT / "src/common/gallery.js").write_text(gallery_js, "utf-8")
    print(f"Wrote src/common/gallery.js: {len(gallery_js):,} bytes")

    meta_p = ROOT / "converted/sprite-meta.json"
    if not meta_p.exists():
        meta_p = ROOT / "src/common/sprite-meta.json"
    if meta_p.exists():
        meta = json.loads(meta_p.read_text("utf-8-sig"))
        meta_js = "module.exports = " + json.dumps(meta, separators=(",", ":"), ensure_ascii=False) + ";\n"
        (ROOT / "src/common/sprite-meta.js").write_text(meta_js, "utf-8")
        print(f"Wrote src/common/sprite-meta.js: {len(meta_js):,} bytes")

    op_meta_p = ROOT / "converted/opening-meta.json"
    if not op_meta_p.exists():
        op_meta_p = ROOT / "src/common/opening-meta.json"
    if op_meta_p.exists():
        op_meta = json.loads(op_meta_p.read_text("utf-8-sig"))
        (ROOT / "src/common/opening-meta.js").write_text(
            "module.exports = " + json.dumps(op_meta, separators=(",", ":")) + ";\n", "utf-8"
        )
        print("Wrote src/common/opening-meta.js")


if __name__ == "__main__":
    main()
