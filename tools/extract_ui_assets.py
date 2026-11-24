import io
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(r"E:\Antigravity\aoitori-rw5")
LONGINUS_IMG = ROOT / "probe" / "longinus_named" / "image"
UI_RAW = ROOT / "probe" / "ui_raw"
OUT_UI = ROOT / "src" / "common" / "ui"
OUT_IMG = ROOT / "src" / "common" / "images"


def load_raw_bgra(filename: str, width: int) -> Image.Image:
    raw = (LONGINUS_IMG / filename).read_bytes()
    h = len(raw) // (width * 4)
    arr = np.frombuffer(raw, dtype=np.uint8).reshape(h, width, 4)
    rgba = arr[:, :, [2, 1, 0, 3]].copy()
    return Image.fromarray(rgba, "RGBA")


def save_quant_png(im: Image.Image, out_path: Path):
    q = im.convert("RGBA").quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    q.save(buf, format="PNG", optimize=True)
    out_path.write_bytes(buf.getvalue())


def extract_title_buttons():
    OUT_UI.mkdir(parents=True, exist_ok=True)
    sheet = load_raw_bgra("title03_chip.pb3", 1280)
    names = ["tbtn_start", "tbtn_akari", "tbtn_load", "tbtn_extra", "tbtn_config", "tbtn_exit"]
    for idx, name in enumerate(names):
        y0 = 722 + 62 * idx + 4
        crop = sheet.crop((0, y0, 300, y0 + 52))
        arr = np.array(crop)
        ys, xs = np.where(arr[:, :, 3] > 24)
        trimmed = crop.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
        tw = 216
        th = 37
        resized = trimmed.resize((tw, th), Image.Resampling.LANCZOS)
        save_quant_png(resized, OUT_UI / f"{name}.png")
        print(f"Sliced {name}.png: {trimmed.size} -> {resized.size} ({(OUT_UI / f'{name}.png').stat().st_size:,} B)")


def extract_clean_logo_alpha(t1_rgb: Image.Image):
    l1 = np.array(t1_rgb.crop((250, 24, 1020, 358)), dtype=np.float32)
    redness = l1[:, :, 0] - 0.35 * l1[:, :, 2]
    alpha = np.clip((np.maximum(l1.max(axis=2), redness) - 42.0) / 145.0, 0.0, 1.0)
    # Remove the 3 lit mansion windows & red cloud in bottom-right corner of title01 under 'リ' (y > 245, x > 490)
    # Wait: 'リ' stroke itself stops around y=252, and white/yellow mansion windows have G > 140 while red logo has G < 130!
    win_mask = (np.arange(l1.shape[0])[:, None] > 200) & (np.arange(l1.shape[1])[None, :] > 360) & (l1[:, :, 1] > 105)
    cloud_mask = (np.arange(l1.shape[0])[:, None] > 270) & (np.arange(l1.shape[1])[None, :] > 450)
    alpha[win_mask | cloud_mask] = 0.0
    l1[win_mask | cloud_mask] = 0.0
    return l1, alpha


def make_title_cgs():
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    H_W, W_W = 514, 432
    TITLE_SRC = ROOT / "probe" / "title_src"

    t1 = load_raw_bgra("title01_chip.pb3", 1280).crop((0, 0, 1280, 720)).convert("RGB")
    t3 = load_raw_bgra("title03_chip.pb3", 1280).crop((0, 0, 1280, 720)).convert("RGB")
    bg_night = Image.open(TITLE_SRC / "bg520c.png").convert("RGB")  # 2048x1024 textless night mansion
    bg_day = Image.open(TITLE_SRC / "bg520a.png").convert("RGB")    # 2048x1024 textless daylight mansion

    lw, lh = 392, round(334 * (392 / 770))
    l1_raw, alpha_raw = extract_clean_logo_alpha(t1)
    l1_s = np.array(Image.fromarray(l1_raw.astype(np.uint8)).resize((lw, lh), Image.Resampling.LANCZOS), dtype=np.float32)
    alpha_s = np.array(Image.fromarray((alpha_raw * 255).astype(np.uint8)).resize((lw, lh), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0
    alpha_s3 = alpha_s[:, :, None]

    # Soft blurred glow helper for logo readability on detailed backgrounds
    def make_glow(alpha_2d: np.ndarray, radius: float = 3.5) -> np.ndarray:
        im_a = Image.fromarray(np.clip(alpha_2d * 255.0, 0, 255).astype(np.uint8), "L")
        blurred = im_a.filter(ImageFilter.GaussianBlur(radius=radius))
        return (np.array(blurred, dtype=np.float32) / 255.0)[:, :, None]

    glow_s3 = make_glow(alpha_s, 4.0)

    # Exact 432:514 crop window at full 1024 height -> 861x1024 (centered horizontally around spire+mansion x=900..1761)
    crop_w = round(1024 * W_W / H_W)  # 861
    x0_mansion = 900

    # --- title01.jpg: Full un-extended 861x1024 crop of bg520c + red bird logo on top ---
    c1 = np.array(bg_night.crop((x0_mansion, 0, x0_mansion + crop_w, 1024)).resize((W_W, H_W), Image.Resampling.LANCZOS), dtype=np.float32)
    c1[18 : 18 + lh, 20 : 20 + lw] *= (1.0 - 0.65 * glow_s3)
    base1 = c1[18 : 18 + lh, 20 : 20 + lw]
    c1[18 : 18 + lh, 20 : 20 + lw] = np.maximum(base1, l1_s) * alpha_s3 + base1 * (1.0 - alpha_s3)
    Image.fromarray(np.clip(c1, 0, 255).astype(np.uint8), "RGB").save(OUT_IMG / "title01.jpg", format="JPEG", quality=64, optimize=True)

    # --- title02.jpg: Full un-extended 861x1024 crop of bg520a + crisp white logo on top ---
    c2 = np.array(bg_day.crop((x0_mansion, 0, x0_mansion + crop_w, 1024)).resize((W_W, H_W), Image.Resampling.LANCZOS), dtype=np.float32)
    white_logo = np.full((lh, lw, 3), [250.0, 253.0, 255.0], dtype=np.float32)
    shadow_col = np.array([14.0, 56.0, 114.0], dtype=np.float32)
    roi2 = c2[18 : 18 + lh, 20 : 20 + lw]
    roi2 = roi2 * (1.0 - 0.72 * glow_s3) + shadow_col * (0.72 * glow_s3)
    c2[18 : 18 + lh, 20 : 20 + lw] = white_logo * alpha_s3 + roi2 * (1.0 - alpha_s3)
    Image.fromarray(np.clip(c2, 0, 255).astype(np.uint8), "RGB").save(OUT_IMG / "title02.jpg", format="JPEG", quality=64, optimize=True)

    # --- title03.jpg: Full un-extended 605x720 crop of title03_chip (Akari intact) + crisp blue logo on top ---
    crop3_w = round(720 * W_W / H_W)  # 605
    ak3 = np.array(t3.crop((628, 0, 628 + crop3_w, 720)))
    # Erase tiny edge blue glow only at leftmost x < 16 if any
    sub_ak = ak3[145:235, :16]
    blue_sliver = ((sub_ak[:, :, 2].astype(np.int16) - sub_ak[:, :, 0].astype(np.int16)) > 20) & (sub_ak[:, :, 0] < 210)
    sub_ak[blue_sliver] = [255, 255, 255]
    c3 = np.array(Image.fromarray(ak3).resize((W_W, H_W), Image.Resampling.LANCZOS), dtype=np.float32)

    l3w, l3h = 264, round(334 * (264 / 770))
    a3_s = np.array(Image.fromarray((alpha_raw * 255).astype(np.uint8)).resize((l3w, l3h), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0
    ly_grad = np.clip(np.arange(l3h) / l3h, 0.0, 1.0)[:, None, None]
    blue_logo = np.array([22.0, 88.0, 174.0]) * (1.0 - ly_grad) + np.array([56.0, 146.0, 222.0]) * ly_grad
    a3_3 = a3_s[:, :, None]
    g3_3 = make_glow(a3_s, 4.5)
    roi3 = c3[14 : 14 + l3h, 12 : 12 + l3w]
    roi3 = roi3 * (1.0 - 0.88 * g3_3) + 255.0 * (0.88 * g3_3)
    c3[14 : 14 + l3h, 12 : 12 + l3w] = blue_logo * a3_3 + roi3 * (1.0 - a3_3)

    Image.fromarray(np.clip(c3, 0, 255).astype(np.uint8), "RGB").save(OUT_IMG / "title03.jpg", format="JPEG", quality=64, optimize=True)

    for fn in ("title01.jpg", "title02.jpg", "title03.jpg"):
        print(f"Built {fn}: {(OUT_IMG / fn).stat().st_size:,} B")


def make_dialogue_backdrop():
    # Take original message01 feather header (1280x180 -> 432x61) un-stretched at top + deep nocturnal gradient body below
    m1 = Image.open(UI_RAW / "message01.png").convert("RGB")
    header = np.array(m1.crop((0, 0, 1280, 180)).resize((432, 82), Image.Resampling.LANCZOS), dtype=np.float32)
    canvas = np.zeros((271, 432, 3), dtype=np.float32)
    canvas[:, :] = np.array([10.0, 24.0, 36.0])
    # Blend top 82px feather header softly into deep nocturnal #0a1824 below y=36..82
    fade = np.clip((82.0 - np.arange(82)) / 48.0, 0.0, 1.0)[:, None, None]
    # Keep top 2px sharp gold-cyan border & soft subtle glow
    tint = np.where(np.arange(82)[:, None, None] < 3, 0.95, 0.48)
    canvas[:82] = (header * tint + canvas[:82] * (1.0 - tint)) * fade + canvas[:82] * (1.0 - fade)
    # Subtle 1px bottom divider tint above toolbar (y=222)
    canvas[222] = np.array([62.0, 96.0, 128.0])
    Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGB").save(OUT_UI / "dlg_bg.jpg", format="JPEG", quality=55, optimize=True)
    print(f"Built dlg_bg.jpg: {(OUT_UI / 'dlg_bg.jpg').stat().st_size:,} B")


def main():
    extract_title_buttons()
    make_title_cgs()
    make_dialogue_backdrop()


if __name__ == "__main__":
    main()
