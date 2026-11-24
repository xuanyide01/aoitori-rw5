import hashlib
import json
import sys
from pathlib import Path
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"E:\Antigravity\aoitori-rw5")
RAW_SP_DIR = ROOT / "probe/sprites_scaled"
OUT_SP_DIR = ROOT / "src/common/sprites"
OUT_FACE_DIR = ROOT / "src/common/faces"
OUT_META = ROOT / "converted/sprite-meta.json"


def quantize_png(im: Image.Image, out_path: Path) -> bytes:
    # FastOctree 256-color quantization preserving RGBA alpha cleanly
    q = im.convert("RGBA").quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    import io
    buf = io.BytesIO()
    q.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    out_path.write_bytes(data)
    return data


def main():
    for d in (OUT_SP_DIR, OUT_FACE_DIR):
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.png"):
            old.unlink()

    req = json.loads((ROOT / "converted/image-requests.json").read_text("utf-8"))["sprites"]
    # Group by (pose_key, width, height) so face diffs never mix mismatched dimensions
    size_groups = {}
    pose_dims_seen = {}
    for asset in sorted(req):
        sp_path = RAW_SP_DIR / f"{asset}.png"
        if not sp_path.exists():
            continue
        with Image.open(sp_path) as im_hdr:
            sw, sh = im_hdr.size
        pose_key = asset[:-2] if len(asset) > 2 and asset[-2:].isdigit() else asset
        pose_dims_seen.setdefault(pose_key, set()).add((sw, sh))
        size_groups.setdefault((pose_key, sw, sh), []).append(asset)

    groups = {}
    for (pose_key, sw, sh), items in sorted(size_groups.items()):
        base_key = pose_key if len(pose_dims_seen[pose_key]) == 1 else f"{pose_key}_{sw}x{sh}"
        groups[base_key] = items

    meta = {}
    face_dedup = {}
    base_bytes = 0
    face_bytes = 0
    base_count = 0
    face_count = 0

    for pose_key, items in sorted(groups.items()):
        # Pick *01 as canonical base if present, else first item
        items_sorted = sorted(items)
        base_asset = next((x for x in items_sorted if x.endswith("01")), items_sorted[0])
        base_im = Image.open(RAW_SP_DIR / f"{base_asset}.png").convert("RGBA")
        w, h = base_im.size
        base_arr = np.array(base_im, dtype=np.int16)

        base_out = OUT_SP_DIR / f"{pose_key}.png"
        b_data = quantize_png(base_im, base_out)
        base_bytes += len(b_data)
        base_count += 1

        for asset in items_sorted:
            if asset == base_asset:
                meta[asset] = [pose_key, "", 0, 0, 0, 0, 0, w, h]
                continue
            im = Image.open(RAW_SP_DIR / f"{asset}.png").convert("RGBA")
            arr = np.array(im, dtype=np.int16)
            diff = np.abs(arr - base_arr).sum(axis=2)
            # Ignore tiny bicubic noise (<= 24)
            ys, xs = np.where(diff > 24)
            if len(xs) == 0:
                meta[asset] = [pose_key, "", 0, 0, 0, 0, 0, w, h]
                continue
            alpha_erased = bool(np.any((base_arr[:, :, 3] > 32) & (arr[:, :, 3] < 16)))
            x0, x1 = max(0, int(xs.min()) - 1), min(w, int(xs.max()) + 2)
            y0, y1 = max(0, int(ys.min()) - 1), min(h, int(ys.max()) + 2)
            pw, ph = x1 - x0, y1 - y0
            if alpha_erased or (pw * ph > w * h * 0.45):
                # Fallback full quantized sprite
                import io
                q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
                buf = io.BytesIO()
                q.save(buf, format="PNG", optimize=True)
                data = buf.getvalue()
                hsh = hashlib.sha256(data).hexdigest()[:16]
                fn = face_dedup.get(hsh)
                if not fn:
                    fn = f"{asset}.png"
                    (OUT_FACE_DIR / fn).write_bytes(data)
                    face_dedup[hsh] = fn
                    face_bytes += len(data)
                    face_count += 1
                meta[asset] = [pose_key, fn, 0, 0, w, h, 1, w, h]
            else:
                patch = im.crop((x0, y0, x1, y1))
                import io
                q = patch.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
                buf = io.BytesIO()
                q.save(buf, format="PNG", optimize=True)
                data = buf.getvalue()
                hsh = hashlib.sha256(data).hexdigest()[:16]
                fn = face_dedup.get(hsh)
                if not fn:
                    fn = f"{asset}.png"
                    (OUT_FACE_DIR / fn).write_bytes(data)
                    face_dedup[hsh] = fn
                    face_bytes += len(data)
                    face_count += 1
                meta[asset] = [pose_key, fn, x0, y0, pw, ph, 0, w, h]

    # Alias missing st-ak_a812 if absent to closest valid pose or up-ak_a812
    for asset in req:
        if asset not in meta:
            alt = "up-" + asset[3:] if asset.startswith("st-") else "st-" + asset[3:]
            if alt in meta:
                meta[asset] = list(meta[alt])
                print(f"Aliased missing {asset} -> {alt}")
            else:
                same_prefix = sorted(k for k in meta if k.startswith(asset[:7]))
                if same_prefix:
                    meta[asset] = list(meta[same_prefix[0]])
                    print(f"Fallback missing {asset} -> {same_prefix[0]}")

    OUT_META.write_text(json.dumps(meta, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"Packed {len(meta)} sprites: {base_count} bases ({base_bytes:,} B), {face_count} unique faces ({face_bytes:,} B), total={base_bytes + face_bytes:,} B")


if __name__ == "__main__":
    main()
