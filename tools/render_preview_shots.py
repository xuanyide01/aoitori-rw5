import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"E:\Antigravity\aoitori-rw5")
COMMON = ROOT / "src" / "common"
OUT_SPRITES = ROOT / "reports" / "sprites"
OUT_REPORTS = ROOT / "reports"
FONT_PATH = COMMON / "aoitori-text.otf"

SPRITE_META = json.loads((ROOT / "converted" / "sprite-meta.json").read_text("utf-8-sig"))


def load_font(size):
    return ImageFont.truetype(str(FONT_PATH), size)


def parse_chunks_find(chunk_name, predicate):
    path = COMMON / "story" / f"{chunk_name}.txt"
    bg = "black"
    sprites = {}
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.rstrip("\r\n")
            if not raw:
                continue
            if raw.startswith("@bg\t"):
                bg = raw.split("\t")[1]
            elif raw.startswith("@sp0"):
                sprites.clear()
            elif raw.startswith("@sp-\t"):
                sprites.pop(raw.split("\t")[1], None)
            elif raw.startswith("@sp\t"):
                pts = raw.split("\t")
                sprites[pts[1]] = {
                    "cid": pts[1],
                    "kind": pts[2],
                    "asset": pts[3],
                    "x": int(pts[4]),
                    "y": int(pts[5]),
                    "w": int(pts[6]),
                    "h": int(pts[7]),
                }
            else:
                spk, txt = raw.split("\t", 1) if "\t" in raw else ("", raw)
                snap = {k: dict(v) for k, v in sprites.items()}
                if predicate(bg, snap, spk, txt):
                    return bg, snap, spk, txt
    raise RuntimeError(f"Predicate not matched in {chunk_name}")


def render_stage(bg_name, sprites_dict):
    bg_file = COMMON / "images" / f"{bg_name}.jpg"
    if not bg_file.exists():
        bg_file = COMMON / "images" / "black.jpg"
    stage = Image.open(bg_file).convert("RGBA").resize((432, 243), Image.Resampling.LANCZOS)

    for cid in sorted(sprites_dict.keys(), key=lambda c: int(c)):
        sp = sprites_dict[cid]
        entry = SPRITE_META.get(sp["asset"])
        if not entry:
            continue
        base_key, face_file, fx, fy, fw, fh = entry[:6]
        full_flag = entry[6] if len(entry) > 6 else 0
        x, y, w, h = sp["x"], sp["y"], sp["w"], sp["h"]
        if not full_flag:
            base_img = Image.open(COMMON / "sprites" / f"{base_key}.png").convert("RGBA")
            if base_img.size != (w, h):
                base_img = base_img.resize((w, h), Image.Resampling.LANCZOS)
            stage.alpha_composite(base_img, (x, y))
        if face_file:
            face_img = Image.open(COMMON / "faces" / face_file).convert("RGBA")
            if full_flag:
                if face_img.size != (w, h):
                    face_img = face_img.resize((w, h), Image.Resampling.LANCZOS)
                stage.alpha_composite(face_img, (x, y))
            else:
                if face_img.size != (fw, fh):
                    face_img = face_img.resize((fw, fh), Image.Resampling.LANCZOS)
                stage.alpha_composite(face_img, (x + fx, y + fy))
    return stage.convert("RGB")


def wrap_text(txt, font, max_w, draw):
    lines = []
    cur = ""
    for ch in txt:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        test = cur + ch
        if draw.textlength(test, font=font) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines[:5]


def render_watch_game_screen(bg_name, sprites_dict, speaker, text):
    screen = Image.new("RGB", (432, 514), (10, 24, 36))
    stage = render_stage(bg_name, sprites_dict)
    screen.paste(stage, (0, 0))
    dlg_bg = Image.open(COMMON / "ui" / "dlg_bg.jpg").convert("RGB").resize((432, 271), Image.Resampling.LANCZOS)
    screen.paste(dlg_bg, (0, 243))
    draw = ImageDraw.Draw(screen)

    f_spk = load_font(18)
    f_dlg = load_font(20)
    f_btn = load_font(16)

    if speaker:
        tw = draw.textlength(speaker, font=f_spk)
        draw.rounded_rectangle([(12, 250), (36 + tw, 278)], radius=4, fill=(11, 27, 42), outline=(194, 157, 88), width=1)
        draw.text((24, 254), speaker, font=f_spk, fill=(247, 230, 192))

    y = 290
    for line in wrap_text(text, f_dlg, 400, draw):
        draw.text((16, y), line, font=f_dlg, fill=(245, 239, 226))
        y += 30

    draw.rectangle([(0, 466), (432, 514)], fill=(10, 22, 34))
    draw.line([(0, 466), (432, 466)], fill=(138, 110, 59), width=1)
    btns = ["上一句", "自动", "回想", "菜单", "下一句 ›"]
    bx = 10
    for i, b in enumerate(btns):
        bw = 66 if i < 4 else 92
        fill = (92, 58, 16) if i == 4 else (20, 41, 59)
        outline = (212, 168, 85) if i == 4 else (125, 100, 56)
        draw.rounded_rectangle([(bx, 473), (bx + bw, 507)], radius=5, fill=fill, outline=outline, width=1)
        tw = draw.textlength(b, font=f_btn)
        draw.text((bx + (bw - tw) / 2, 480), b, font=f_btn, fill=(247, 238, 220))
        bx += bw + 8
    return screen


def render_watch_title_screen(true_unlocked=True):
    bg_name = "title03.jpg" if true_unlocked else "title01.jpg"
    screen = Image.open(COMMON / "images" / bg_name).convert("RGBA").resize((432, 514), Image.Resampling.LANCZOS)
    if true_unlocked:
        btns = ["tbtn_start.png", "tbtn_akari.png", "tbtn_load.png", "tbtn_extra.png", "tbtn_config.png", "tbtn_exit.png"]
        by = 214
    else:
        btns = ["tbtn_start.png", "tbtn_load.png", "tbtn_extra.png", "tbtn_config.png", "tbtn_exit.png"]
        by = 232
    for fn in btns:
        b = Image.open(COMMON / "ui" / fn).convert("RGBA")
        screen.alpha_composite(b, (14, by))
        by += 38
    return screen.convert("RGB")


def side_by_side(left_img, right_img, left_label, right_label):
    pad = 16
    w = left_img.width + right_img.width + pad * 3
    h = max(left_img.height, right_img.height) + pad * 2 + 28
    canvas = Image.new("RGB", (w, h), (14, 22, 32))
    draw = ImageDraw.Draw(canvas)
    f = load_font(18)
    draw.text((pad, 8), left_label, font=f, fill=(230, 212, 175))
    draw.text((pad * 2 + left_img.width, 8), right_label, font=f, fill=(230, 212, 175))
    canvas.paste(left_img, (pad, 36))
    canvas.paste(right_img, (pad * 2 + left_img.width, 36))
    return canvas


def main():
    OUT_SPRITES.mkdir(parents=True, exist_ok=True)
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)

    bg1, sp1, _, _ = parse_chunks_find("sn101_p2_0", lambda bg, sp, s, t: "2" in sp and sp["2"]["kind"] == "st")
    render_stage(bg1, sp1).save(OUT_SPRITES / "01_single_st_center.png")

    bg2, sp2, _, _ = parse_chunks_find("sn101_p2_0", lambda bg, sp, s, t: "2" in sp and sp["2"]["kind"] == "up")
    render_stage(bg2, sp2).save(OUT_SPRITES / "02_single_up_closeup.png")

    bg3, sp3, _, _ = parse_chunks_find("sn102b_1", lambda bg, sp, s, t: len(sp) == 2)
    img3 = render_stage(bg3, sp3)
    img3.save(OUT_SPRITES / "03_two_chars_side_by_side.png")

    bg4a, sp4a, _, _ = parse_chunks_find("sn101_p2_0", lambda bg, sp, s, t: "2" in sp and sp["2"]["asset"] == "st-ak_a812")
    bg4b, sp4b, _, _ = parse_chunks_find("sn101_p2_0", lambda bg, sp, s, t: "2" in sp and sp["2"]["asset"] == "st-ak_a421")
    side_by_side(render_stage(bg4a, sp4a), render_stage(bg4b, sp4b), "Slot 2: st-ak_a812", "Slot 2: st-ak_a421").save(
        OUT_SPRITES / "04_expr_diff_swap_same_slot.png"
    )

    bg5, sp5, spk5, txt5 = parse_chunks_find("sn105_0", lambda bg, sp, s, t: len(sp) >= 3)
    img5 = render_stage(bg5, sp5)
    img5.save(OUT_SPRITES / "05_three_chars_watch_stage.png")

    t1 = render_watch_title_screen(false := False)
    t3 = render_watch_title_screen(True)
    side_by_side(t1, t3, "Title State 0 (title01, 5 buttons)", "Title State 2 (title03, 6 buttons)").save(
        OUT_REPORTS / "compare_01_title.png"
    )

    side_by_side(img3, img5, "2-Char Native Proportions + Phone", "3-Char Native Stage Layout").save(
        OUT_REPORTS / "compare_02_sprite_stage.png"
    )

    render_watch_game_screen(bg5, sp5, spk5 or "律", txt5).save(OUT_REPORTS / "compare_03_dialogue_ui.png")
    print("Rendered refreshed sprite & comparison screenshots OK")


if __name__ == "__main__":
    main()
