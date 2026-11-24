import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

ROOT = Path(r"E:\Antigravity\aoitori-rw5")
CODE_DIR = ROOT / "probe/longinus_named/code"
BG_MAP = json.loads((ROOT / "probe/intcode_bg_map.json").read_text("utf-8"))
SP_MAP = json.loads((ROOT / "probe/intcode_sprite_map.json").read_text("utf-8"))
OMAKE_GROUPS = json.loads((ROOT / "probe/omake_cg_groups.json").read_text("utf-8"))

OUT_STORY_DIR = ROOT / "src/common/story"
OUT_GRAPH_JSON = ROOT / "converted/graph.json"
OUT_GALLERY_JSON = ROOT / "converted/gallery.json"
OUT_ASSETS_JSON = ROOT / "converted/image-requests.json"
OUT_COORDS_JSON = ROOT / "reports/sprite-coords.json"
SPRITE_DIMS_PATH = ROOT / "probe/sprite_dims.json"
SPRITE_META_PATH = ROOT / "converted/sprite-meta.json"

SPRITE_DIMS = {}
if SPRITE_DIMS_PATH.exists():
    for k, v in json.loads(SPRITE_DIMS_PATH.read_text("utf-8-sig")).items():
        SPRITE_DIMS[k] = (int(v[0]), int(v[1]))
if SPRITE_META_PATH.exists():
    for k, v in json.loads(SPRITE_META_PATH.read_text("utf-8-sig")).items():
        if k not in SPRITE_DIMS and len(v) >= 9:
            SPRITE_DIMS[k] = (int(v[7]), int(v[8]))


def get_sprite_size(asset: str, kind: str):
    if asset in SPRITE_DIMS:
        return SPRITE_DIMS[asset]
    alt = ("up-" if asset.startswith("st-") else "st-") + asset[3:]
    if alt in SPRITE_DIMS:
        return SPRITE_DIMS[alt]
    if "td_" in asset:
        return (144, 144)
    return (175, 256) if kind == "up" else (155, 296)

L168_MAP = {
    70: "bg070a.pb3", 220: "bg220a.pb3", 221: "bg220b.pb3", 222: "bg220c.pb3",
    260: "bg260a.pb3", 261: "bg260b.pb3", 262: "bg260c.pb3", 264: "bg260e.pb3",
    270: "bg280a.pb3", 272: "bg280c.pb3", 280: "bg280a.pb3", 282: "bg280c.pb3",
    290: "bg290a.pb3", 292: "bg290c.pb3", 580: "bg580a.pb3", 582: "bg580c.pb3",
    584: "bg580e.pb3", 731: "bg731e.pb3", 900: None,
}

# Script flow definition verified from disassembly of menu.ps3, sn101..sn605, staff*, omake.ps3
ROUTE_CHAINS = [
    ("common", ["sn101", "sn102", "sn102b", "sn103", "sn104", "sn105", "sn106", "sn107", "sn108"]),
    ("risa", ["sn201", "sn202", "sn203", "sn204", "sn205", "sn206", "sn207", "sn208", "sn209", "sn210", "sn211", "sn212", "sn213", "sn214", "sn299"]),
    ("sayo", ["sn301", "sn302", "sn303", "sn304", "sn305", "sn307", "sn308", "sn309", "sn310", "sn311", "sn312", "sn399"]),
    ("mari", ["sn401", "sn402", "sn403", "sn404", "sn405", "sn406", "sn407", "sn408", "sn409", "sn410", "sn411", "sn412", "sn413", "sn499"]),
    ("true", ["sn501", "sn502", "sn503", "sn504", "sn505", "sn506", "sn507", "sn508", "sn509", "sn510", "sn601", "sn602", "sn603", "sn604", "sn605"]),
    ("extra", ["sn901"]),
    ("hscene", ["snhmr3", "snhmr4", "snhsy4", "snhak7", "snhrs4", "snhmk2", "snhrm2", "snhyk1", "snhhm1"]),
]

SCRIPT_TO_ROUTE = {s: r for r, lst in ROUTE_CHAINS for s in lst}

UNLOCK_RULES = {
    "sn103": ["title02"],
    "sn299": ["clear_risa"],
    "sn399": ["clear_sayo"],
    "sn499": ["clear_mari"],
    "sn605": ["clear_true"],
}

ROUTE_CN = {
    "common": "共通篇",
    "risa": "理沙篇",
    "sayo": "小夜篇",
    "mari": "玛丽篇",
    "true": "真相篇",
    "extra": "幕间",
    "hscene": "特典剧情",
}

TITLE_OVERRIDES = {
    "sn102b": "伊始的三天[2/3·续]",
    "sn299": "玛丽[尾声]",
    "sn399": "小夜[尾声]",
    "sn499": "理沙[尾声]",
    "sn605": "明里[尾声]",
}

SPEAKER_MAP = {
    "メアリー": "玛丽",
    "あかり": "明里",
    "電話の悪魔": "电话恶魔",
    "律＆メアリー＆あかり": "律＆玛丽＆明里",
}

JP_LINE_TRANS = {
    "建物は学園の敷地の外れにあり、誰かをかくまっていても、まったく気づかれずに過ごせるだろう。":
        "这座建筑位于学园用地的边缘地带，就算在这里藏着什么人，也完全不会被发现吧。",
    "「あっ、やっぱり……。あたしの愛液、りっくんの亀頭から、おちんちんに伝ってる……お尻まで……届いちゃってる？」":
        "「啊，果然……我的爱液，从阿律的龟头顺着肉棒流下来了……都快流到……屁股那里去了呢？」",
    "「あ、ふああぁっ、んあぁっ、ああぁっ！い、いっちゃ、うのっ、あたしっ、ぅああっ！ああぁぁっ！！」":
        "「啊、呼啊啊、嗯啊、啊啊！我、我要去了、呜啊！啊啊啊！！」",
    "「あー。あかりちゃんをお嬢様学校に通わせて家柄に箔をつけたい、みたいな？」":
        "「啊—。就是那种想让明里去读大小姐学校，好给家世贴金的感觉？」",
    "「り、律の、体……ずいぶん、熱い、のねっ……んぁっ……！ゆ、指も……舌、も……ふぅ、これが、普通っ、なの……？」":
        "「律、律的身体……好烫呢……嗯啊……！手、手指也好……舌头、也……呼，这、这样就是普通吗……？」",
    "「律っ、はっ、はふ、あ、好きな子に意地悪、する、の……ねっ……ふふっ、子ども、みたいっ……あっ、ああぁぁっ……！」":
        "「律、哈、哈呼、啊，你总是这样欺负喜欢的女孩子呢……呵呵，像个小孩子一样……啊、啊啊啊……！」",
    "「んひぃっ！さっきより、すご、あ、あ……舐められる、の、きもちいいっ……いいよぉっ……あっ、ぅぅああぁっ……！！」":
        "「嗯咿！比刚才还要厉害、啊、啊……被这样舔着，好舒服……好棒啊……啊、呜呜啊啊……！！」",
    "「ひっ、あぅっ、うぅっ、あぁぁっ、あぁぁっ！！深っ、いっ、よぉ！あっ、ああっ！」":
        "「咿、啊呜、呜呜、啊啊、啊啊啊！！太深了呀！啊、啊啊！」",
    "「こん、なにっ、気持ち、いいのっ、ああぁぁぅ！ふぁ、あ、お兄ちゃんとだから、よっ……あ、ぅぁぅ、ああぁぁぅっ！！」":
        "「居、居然会这么舒服吗、啊啊啊！呼啊、啊，因为是和哥哥在一起啊……啊、呜啊呜、啊啊啊！！」",
    "「ふふ、いい、よっ……いいよっ……！あ、は、ふぁ、ふぁあ……！ふあああぁぁっ！！」":
        "「呵呵，好棒……好舒服……！啊、哈、呼啊、呼啊……！呼啊啊啊！！」",
    "「お兄、ちゃん、すご、い……こんなに、出されたら、こぼれちゃう、わ……」":
        "「哥、哥哥，好厉害……射了这么多出来，都要溢出来了……」",
    "「それはない」 「それはない」 「それはない、です」":
        "「那不可能」 「那不可能」 「那不可能的」",
    "「うわ！？」 「うわ！？」":
        "「呜哇！？」 「呜哇！？」",
    "「あー」 「あー」 「あー」":
        "「啊—」 「啊—」 「啊—」",
    "「ほぅ」 「ほぅ」 「ほぅ」":
        "「嚯—」 「嚯—」 「嚯—」",
    "「……確かに」 「……確かに」":
        "「……确实如此」 「……确实如此」",
    "「え！？」 「え！？」":
        "「诶！？」 「诶！？」",
    "「っ！？」":
        "「！？」",
    "「はい……」 「はい……」 「はい……」":
        "「是……」 「是……」 「是……」",
}


def eval_int(expr_txt: str):
    toks = expr_txt.strip().split()
    st = []
    for tk in toks:
        if re.fullmatch(r"-?\d+", tk):
            st.append(int(tk))
        elif tk in ("+", "-", "*", "/") and len(st) >= 2:
            b, a = st.pop(), st.pop()
            st.append(a + b if tk == "+" else (a - b if tk == "-" else (a * b if tk == "*" else int(a / (b or 1)))))
        else:
            return None
    return st[-1] if len(st) == 1 else None


def eval_float(expr_txt: str):
    toks = expr_txt.strip().split()
    st = []
    for tk in toks:
        if tk.endswith("f"):
            try:
                st.append(float(tk[:-1]))
                continue
            except ValueError:
                return None
        if re.fullmatch(r"-?\d+", tk):
            st.append(float(tk))
        elif tk in ("+", "-", "*", "/") and len(st) >= 2:
            b, a = st.pop(), st.pop()
            st.append(a + b if tk == "+" else (a - b if tk == "-" else (a * b if tk == "*" else a / (b or 1.0))))
        else:
            return None
    return st[-1] if len(st) == 1 else None


def clean_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\\n", " ").replace("\\wc", "").replace("\\ws", "")
    # Remove CMVS ruby/wait tags if any like \w[..] or \r[..] and separator "\ \"
    s = re.sub(r"\\[a-zA-Z]+\d*", "", s)
    s = s.replace("\\ ", " ").replace("\\", "")
    s = s.replace("\t", " ")
    # Collapse newlines inside single dialogue box into spaces for clean Watch 5 wrapping
    lines = [x.strip() for x in s.split("\n") if x.strip()]
    out = " ".join(lines)
    if out in JP_LINE_TRANS:
        out = JP_LINE_TRANS[out]
    # Remove untranslated parenthetical translator notes & ruby braces containing kana
    out = re.sub(r"（译注：[^）]*）", "", out)
    out = out.replace("{我的表情/脸}", "我的表情").replace("{表情/かお}", "表情")
    # Normalize any stray Japanese kana marks (ー -> —, っ/ッ -> '')
    out = out.replace("ー", "—").replace("っ", "").replace("ッ", "")
    return out.strip()


def clean_speaker(s: str) -> str:
    raw = s.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", "").replace("\t", " ").strip()
    raw = SPEAKER_MAP.get(raw, raw)
    return clean_text(raw).strip()


def pc_to_watch_coords(asset: str, kind: str, wx: float, wy: float, wz: float, cam_wx: float, cam_wy: float, cam_wz: float):
    w, h = get_sprite_size(asset, kind)
    wz_rel = max(20.0, min(48.0, 36.0 + (wz - cam_wz)))
    px_per_unit = 293.327 / wz_rel
    raw_cx = 216.0 + (wx - cam_wx) * px_per_unit
    pc_x = max(80.0, min(1200.0, 640.0 + (wx - cam_wx) * (px_per_unit / 0.3375)))

    if w == 144 and h == 144:
        y = 48
    elif kind == "up":
        y = round(max(-32.0, min(18.0, -12.0 + (cam_wy - (wy - 23.5)) * 5.0)))
    else:
        y = round(max(-36.0, min(24.0, 0.0 + (cam_wy - (wy - 27.5)) * 5.0)))

    x = round(raw_cx - w / 2.0)
    return {
        "pcX": round(pc_x, 1),
        "pcWy": round(wy, 2),
        "pcWz": round(wz, 2),
        "rawCx": round(raw_cx, 1),
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    }


def layout_stage_sprites(active_sprites: dict):
    if not active_sprites:
        return {}
    out = {k: dict(v) for k, v in active_sprites.items()}
    ordered = sorted(out.keys(), key=lambda c: (out[c].get("rawCx", 216.0), int(c)))
    n = len(ordered)

    if n == 1:
        sp = out[ordered[0]]
        raw_cx = sp.get("rawCx", 216.0)
        cx = 216.0 if abs(raw_cx - 216.0) <= 26.0 else max(88.0, min(344.0, raw_cx))
        sp["x"] = round(max(-40.0, min(432.0 - sp["w"] + 40.0, cx - sp["w"] / 2.0)))
    elif n == 2:
        s0, s1 = out[ordered[0]], out[ordered[1]]
        c0 = max(78.0, min(354.0, s0.get("rawCx", 128.0)))
        c1 = max(78.0, min(354.0, s1.get("rawCx", 304.0)))
        if c1 - c0 < 168.0:
            mid = (c0 + c1) * 0.5
            if abs(mid - 216.0) <= 20.0:
                mid = 216.0
            mid = max(164.0, min(268.0, mid))
            c0, c1 = mid - 84.0, mid + 84.0
        s0["x"] = round(max(-32.0, min(432.0 - s0["w"] + 32.0, c0 - s0["w"] / 2.0)))
        s1["x"] = round(max(-32.0, min(432.0 - s1["w"] + 32.0, c1 - s1["w"] / 2.0)))
    else:
        ideals = [76.0, 216.0, 356.0] if n == 3 else [68.0 + i * ((364.0 - 68.0) / (n - 1)) for i in range(n)]
        centers = []
        for idx, cid in enumerate(ordered):
            raw_c = max(64.0, min(368.0, out[cid].get("rawCx", ideals[idx])))
            c = 0.35 * raw_c + 0.65 * ideals[idx]
            if idx > 0 and c - centers[-1] < 122.0:
                c = centers[-1] + 122.0
            centers.append(c)
        if centers[-1] > 372.0:
            shift = centers[-1] - 372.0
            centers = [max(58.0, c - shift) for c in centers]
        for idx, cid in enumerate(ordered):
            sp = out[cid]
            sp["x"] = round(max(-44.0, min(432.0 - sp["w"] + 44.0, centers[idx] - sp["w"] / 2.0)))

    return out


def parse_script_events(ps3_path: Path):
    h, l, c, tx = parse_ps3_raw(ps3_path)
    ins = disasm(c, tx, h[8], len(c), 4 * len(l))
    stk = []
    last_expr = ""
    outfits = {cid: 0 for cid in range(12)}
    char_3d = {cid: {"wx": 0.0, "wy": 27.5, "wz": 36.0} for cid in range(12)}
    cam_wx, cam_wy, cam_wz = 0.0, 0.0, 36.0
    active_bg = "black"
    active_sprites = {}  # cid -> dict
    titles = []
    choices = []
    events = []  # list of dicts: {bg, sprites_snap, speaker, text, is_h}
    trial_skip = False

    # Detect trial/staff gate (`G[111] 0 ==` jump in ending scripts sn214/sn312/sn413/sn510/sn603)
    for idx, (o, t) in enumerate(ins):
        m = re.match(r"EXPR\(020[012]\): (.+)$", t)
        if m:
            last_expr = m.group(1)
            continue
        if t == "PUSH_REG0":
            stk.append(last_expr)
            continue
        if t.startswith("CALL "):
            fn = t[5:]
            if fn in ("L193", "L195") and stk:
                ttl = stk[-1].strip("'").strip("- ").strip(" -").strip()
                if ttl:
                    titles.append(ttl)
            elif fn == "L91" and len(stk) >= 4:
                wx_v = eval_float(stk[-1])
                wy_v = eval_float(stk[-2])
                wz_v = eval_float(stk[-3])
                if wx_v is not None:
                    cam_wx = wx_v
                if wy_v is not None:
                    cam_wy = wy_v
                if wz_v is not None:
                    cam_wz = wz_v
            elif fn == "L120" and len(stk) >= 2:
                cid = eval_int(stk[-1])
                mode = eval_int(stk[-2])
                if cid is not None and mode is not None:
                    outfits[cid] = mode
            elif fn in ("L167", "L171", "L172", "L173", "L182", "L183") and stk:
                bid = eval_int(stk[-1])
                if bid is not None and str(bid) in BG_MAP:
                    active_bg = Path(BG_MAP[str(bid)]).stem
                if fn in ("L172", "L182", "L183"):
                    active_sprites.clear()
            elif fn == "L170" and stk:
                bid = eval_int(stk[-1])
                if bid is not None and str(bid) in BG_MAP:
                    active_bg = Path(BG_MAP[str(bid)]).stem
                active_sprites.clear()
            elif fn == "L168" and stk:
                bid = eval_int(stk[-1])
                if bid in L168_MAP and L168_MAP[bid]:
                    active_bg = Path(L168_MAP[bid]).stem
            elif fn == "L18" and stk:
                eid = eval_int(stk[-1])
                if eid is not None:
                    active_bg = f"eyecatch{eid:02d}"
                    active_sprites.clear()
            elif fn in ("L139", "L114", "L140", "L115", "L141", "L117") and len(stk) >= 5:
                cid = eval_int(stk[-1])
                eid = eval_int(stk[-2])
                wx_v = eval_float(stk[-3])
                wy_v = eval_float(stk[-4])
                wz_v = eval_float(stk[-5])
                if cid is not None and eid is not None and str(cid) in SP_MAP:
                    kind = "up" if fn in ("L114", "L115", "L117") else "st"
                    cm = SP_MAP[str(cid)]
                    outf = cm["outfits"].get(str(outfits.get(cid, 0)), cm["outfits"].get("0", ""))
                    ex = cm["exprs"].get(str(eid), "")
                    if outf and ex:
                        if wx_v is None:
                            wx_v = char_3d.get(cid, {}).get("wx", cam_wx)
                        if wy_v is None:
                            wy_v = 23.5 if kind == "up" else 27.5
                        if wz_v is None:
                            wz_v = 36.0
                        char_3d[cid] = {"wx": wx_v, "wy": wy_v, "wz": wz_v}
                        asset = f"{kind}-{outf}{ex}"
                        coords = pc_to_watch_coords(asset, kind, wx_v, wy_v, wz_v, cam_wx, cam_wy, cam_wz)
                        active_sprites[cid] = {
                            "cid": cid,
                            "kind": kind,
                            "asset": asset,
                            "base": f"{kind}-{outf}",
                            "wx": wx_v,
                            "wy": wy_v,
                            "wz": wz_v,
                            **coords,
                        }
            elif fn in ("L12", "L13", "L155", "L156") and len(stk) >= 2:
                cid = eval_int(stk[-1])
                eid = eval_int(stk[-2])
                if cid is not None and eid is not None and str(cid) in SP_MAP:
                    prev = active_sprites.get(cid)
                    kind = "up" if fn in ("L13", "L156") else ("st" if fn in ("L12", "L155") else (prev["kind"] if prev else "st"))
                    cm = SP_MAP[str(cid)]
                    outf = cm["outfits"].get(str(outfits.get(cid, 0)), cm["outfits"].get("0", ""))
                    ex = cm["exprs"].get(str(eid), "")
                    if outf and ex:
                        p3 = char_3d.get(cid, {"wx": cam_wx, "wy": (23.5 if kind == "up" else 27.5), "wz": 36.0})
                        asset = f"{kind}-{outf}{ex}"
                        coords = pc_to_watch_coords(asset, kind, p3["wx"], p3["wy"], p3["wz"], cam_wx, cam_wy, cam_wz)
                        active_sprites[cid] = {
                            "cid": cid,
                            "kind": kind,
                            "asset": asset,
                            "base": f"{kind}-{outf}",
                            "wx": p3["wx"],
                            "wy": p3["wy"],
                            "wz": p3["wz"],
                            **coords,
                        }
            elif fn in ("L143", "L153") and stk:
                cid = eval_int(stk[-1])
                if cid is not None:
                    active_sprites.pop(cid, None)
            elif fn in ("L2", "L190", "L191", "L192", "L1"):
                if fn == "L2":
                    active_sprites.clear()
            elif fn in ("L77", "L78", "L11", "L5"):
                nargs = 6 if fn == "L5" else 7
                if len(stk) >= nargs:
                    args = stk[-nargs:]
                    txt = clean_text(args[0].strip("'"))
                    spk = clean_speaker(args[2].strip("'"))
                    if txt:
                        events.append({
                            "bg": active_bg,
                            "sprites": layout_stage_sprites(active_sprites),
                            "speaker": spk,
                            "text": txt,
                            "is_h": active_bg.startswith("h_"),
                        })
            elif fn == "L186" and stk:
                opts = [clean_text(s.strip("'")) for s in stk[-5:] if s.startswith("'") and clean_text(s.strip("'"))]
                if opts:
                    choices.append(opts)
            stk.clear()
        elif t.startswith("SYS "):
            stk.clear()

    return {
        "stem": ps3_path.stem,
        "titles": titles,
        "events": events,
        "choices": choices,
    }


def split_adult_segments(stem: str, events: list):
    """Split script events into alternating non-adult and adult segments whenever h_* CGs appear."""
    if stem.startswith("snh"):
        return [{"sub": "", "adult": True, "events": events}]

    # Mark each event as H-segment if inside active h_* span (bridging brief <= 8 black/white transition lines between H-CGs)
    is_h = [e["is_h"] for e in events]
    if not any(is_h):
        return [{"sub": "", "adult": False, "events": events}]

    # Expand brief black/white/solid transition lines strictly between two h_* lines
    last_h = -1
    for i, flag in enumerate(is_h):
        if flag:
            if last_h >= 0 and i - last_h <= 12 and all(events[k]["bg"] in ("black", "white", "bg000a", "bg000b") for k in range(last_h + 1, i)):
                for k in range(last_h + 1, i):
                    is_h[k] = True
            last_h = i

    # Include leading fade-to-black line if immediately followed by h_* (max 2 lines)
    segs = []
    cur_flag = is_h[0]
    cur_ev = [events[0]]
    for i in range(1, len(events)):
        if is_h[i] != cur_flag:
            segs.append((cur_flag, cur_ev))
            cur_flag = is_h[i]
            cur_ev = [events[i]]
        else:
            cur_ev.append(events[i])
    segs.append((cur_flag, cur_ev))

    # Merge tiny non-H slivers (< 15 lines) except final normal ending transitions
    merged = []
    for flag, ev in segs:
        if merged and not flag and len(ev) < 12 and merged[-1][0]:
            merged[-1][1].extend(ev)
        elif merged and flag == merged[-1][0]:
            merged[-1][1].extend(ev)
        else:
            merged.append([flag, ev])

    out = []
    h_idx = 0
    n_idx = 0
    for idx, (flag, ev) in enumerate(merged):
        if len(merged) == 1:
            sub = ""
        elif flag:
            h_idx += 1
            sub = f"_h{h_idx}" if sum(1 for f, _ in merged if f) > 1 else "_h"
        else:
            n_idx += 1
            sub = "" if idx == 0 else f"_p{n_idx}"
        out.append({"sub": sub, "adult": flag, "events": ev})
    return out


def encode_chunk_lines(events: list, max_bytes: int = 23500):
    """Encode events into <= 24 KiB UTF-8 chunks with full initial state snapshot per chunk."""
    chunks = []
    cur_lines = []
    cur_bytes = 0
    prev_bg = None
    prev_sp = {}

    def flush():
        nonlocal cur_lines, cur_bytes
        if cur_lines:
            chunks.append("\n".join(cur_lines))
            cur_lines = []
            cur_bytes = 0

    def emit(line: str):
        nonlocal cur_bytes
        cur_lines.append(line)
        cur_bytes += len(line.encode("utf-8")) + 1

    def write_snapshot(ev):
        nonlocal prev_bg, prev_sp
        emit(f"@bg\t{ev['bg']}")
        prev_bg = ev["bg"]
        for cid, sp in sorted(ev["sprites"].items()):
            emit(f"@sp\t{cid}\t{sp['kind']}\t{sp['asset']}\t{sp['x']}\t{sp['y']}\t{sp['w']}\t{sp['h']}")
        prev_sp = {k: dict(v) for k, v in ev["sprites"].items()}

    for i, ev in enumerate(events):
        # Predict size needed for this event
        pending = []
        if i == 0 or not cur_lines:
            pass  # snapshot written below
        else:
            if ev["bg"] != prev_bg:
                pending.append(f"@bg\t{ev['bg']}")
            removed = set(prev_sp.keys()) - set(ev["sprites"].keys())
            if removed and not ev["sprites"]:
                pending.append("@sp0")
            else:
                for cid in sorted(removed):
                    pending.append(f"@sp-\t{cid}")
                for cid, sp in sorted(ev["sprites"].items()):
                    old = prev_sp.get(cid)
                    if not old or (old["asset"], old["x"], old["y"], old["w"], old["h"]) != (sp["asset"], sp["x"], sp["y"], sp["w"], sp["h"]):
                        pending.append(f"@sp\t{cid}\t{sp['kind']}\t{sp['asset']}\t{sp['x']}\t{sp['y']}\t{sp['w']}\t{sp['h']}")
        dl = f"{ev['speaker']}\t{ev['text']}" if ev["speaker"] else f"\t{ev['text']}"
        pending.append(dl)
        need_bytes = sum(len(x.encode("utf-8")) + 1 for x in pending)

        if cur_lines and cur_bytes + need_bytes > max_bytes:
            flush()
        if not cur_lines:
            write_snapshot(ev)
            emit(dl)
        else:
            for p in pending:
                emit(p)
        prev_bg = ev["bg"]
        prev_sp = {k: dict(v) for k, v in ev["sprites"].items()}

    flush()
    return chunks


def main():
    OUT_STORY_DIR.mkdir(parents=True, exist_ok=True)
    # Clean old story/*.txt if re-running
    for old in OUT_STORY_DIR.glob("*.txt"):
        old.unlink()

    nodes = []
    node_map = {}
    used_bgs = set()
    used_sprites = {}  # asset -> {kind, base, char}
    coord_samples = []

    script_subnodes = {}
    for route, stems in ROUTE_CHAINS:
        for stem in stems:
            p = CODE_DIR / f"{stem}.ps3"
            parsed = parse_script_events(p)
            segs = split_adult_segments(stem, parsed["events"])
            sub_ids = []
            base_title = TITLE_OVERRIDES.get(stem, parsed["titles"][0] if parsed["titles"] else stem)
            base_title = base_title.replace("メアリー", "玛丽").replace("Ｔｒｕｅ", "真结局")
            # Collect unique assets & coord samples
            for ev in parsed["events"]:
                used_bgs.add(ev["bg"])
                for cid, sp in ev["sprites"].items():
                    used_sprites[sp["asset"]] = {"kind": sp["kind"], "base": sp["base"], "cid": cid}
                    if len(coord_samples) < 40:
                        coord_samples.append({"script": stem, **sp})

            for sidx, seg in enumerate(segs):
                nid = f"{stem}{seg['sub']}"
                sub_ids.append(nid)
                chunk_texts = encode_chunk_lines(seg["events"])
                chunk_names = []
                for cidx, ctxt in enumerate(chunk_texts):
                    cname = f"{nid}_{cidx}" if len(chunk_texts) > 1 else nid
                    (OUT_STORY_DIR / f"{cname}.txt").write_text(ctxt, encoding="utf-8")
                    chunk_names.append(cname)

                title = f"{base_title}{' [H]' if seg['adult'] and not stem.startswith('snh') else ''}"
                node = {
                    "id": nid,
                    "script": stem,
                    "route": route,
                    "routeLabel": ROUTE_CN[route],
                    "title": title,
                    "adult": bool(seg["adult"]),
                    "lineCount": len(seg["events"]),
                    "chunks": chunk_names,
                    "next": None,
                    "nonAdultNext": None,
                    "choices": [],
                    "unlocks": UNLOCK_RULES.get(stem, []) if sidx == len(segs) - 1 else [],
                }
                nodes.append(node)
                node_map[nid] = node
            script_subnodes[stem] = sub_ids

    # Link edges within each script and across routes
    for route, stems in ROUTE_CHAINS:
        for idx, stem in enumerate(stems):
            sids = script_subnodes[stem]
            next_script = stems[idx + 1] if idx + 1 < len(stems) and route != "hscene" else None
            next_first = script_subnodes[next_script][0] if next_script else None

            for si, nid in enumerate(sids):
                node = node_map[nid]
                if si + 1 < len(sids):
                    node["next"] = sids[si + 1]
                else:
                    node["next"] = next_first

            # Add choices at sn108 and sn603
            last_nid = sids[-1]
            if stem == "sn108":
                node_map[last_nid]["choices"] = [
                    {"label": "理沙线", "next": script_subnodes["sn201"][0]},
                    {"label": "小夜线", "next": script_subnodes["sn301"][0]},
                    {"label": "玛丽线", "next": script_subnodes["sn401"][0]},
                ]
                node_map[last_nid]["next"] = None
            elif stem == "sn603":
                node_map[last_nid]["choices"] = [
                    {"label": "『喜欢这个世界』", "next": script_subnodes["sn604"][0]},
                ]
                node_map[last_nid]["next"] = script_subnodes["sn604"][0]

    # Compute nonAdultNext for every node (follow next pointers skipping adult nodes)
    for node in nodes:
        cur = node["next"]
        visited = set()
        while cur and cur not in visited and node_map[cur]["adult"]:
            visited.add(cur)
            cur = node_map[cur]["next"]
        node["nonAdultNext"] = cur if cur != node["next"] else node["next"]

    # Build gallery.json from OMAKE_GROUPS (include all CG variations in BG_MAP)
    # Build sorted list of intcode BG IDs so each group pulls exact contiguous IDs
    int_ids = sorted(int(k) for k in BG_MAP)
    gallery_groups = []
    for idx, g in enumerate(OMAKE_GROUPS):
        b_id = g["baseId"]
        cnt = g["count"]
        base_fn = g["baseFile"]
        stem0 = Path(base_fn).stem
        # Find contiguous entries in BG_MAP starting at b_id up to next group or matching prefix
        pos = int_ids.index(b_id) if b_id in int_ids else -1
        items = []
        if pos >= 0:
            for k in int_ids[pos : pos + cnt + 15]:
                fn = Path(BG_MAP[str(k)]).stem
                if len(items) < cnt and (fn.startswith(stem0[:6]) or len(items) == 0):
                    if fn not in items:
                        items.append(fn)
                        used_bgs.add(fn)
        if not items:
            items = [stem0]
            used_bgs.add(stem0)
        is_h = stem0.startswith("h_")
        hero = (
            "玛丽" if "_mr" in stem0 or "rm" in stem0 else
            "小夜" if "_sy" in stem0 else
            "明里" if "_ak" in stem0 else
            "理沙" if "_rs" in stem0 else
            "无垢" if "_mk" in stem0 else
            "由佳里" if "_yk" in stem0 else "其他"
        )
        gallery_groups.append({
            "index": idx,
            "base": stem0,
            "hero": hero,
            "adult": is_h,
            "items": items,
        })

    graph = {
        "title": "アオイトリ",
        "startNode": "sn101",
        "trueRouteStartNode": "sn501",
        "nodes": nodes,
        "totalLines": sum(n["lineCount"] for n in nodes),
        "totalChunks": sum(len(n["chunks"]) for n in nodes),
        "adultNodesCount": sum(1 for n in nodes if n["adult"]),
        "hSceneIds": [s for s in dict(ROUTE_CHAINS)["hscene"]],
    }
    OUT_GRAPH_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_GRAPH_JSON.write_text(json.dumps(graph, indent=2, ensure_ascii=False), "utf-8")
    OUT_GALLERY_JSON.write_text(json.dumps(gallery_groups, indent=2, ensure_ascii=False), "utf-8")

    asset_req = {
        "bgs": sorted(used_bgs),
        "sprites": used_sprites,
        "bgCount": len(used_bgs),
        "spriteCount": len(used_sprites),
    }
    OUT_ASSETS_JSON.write_text(json.dumps(asset_req, indent=2, ensure_ascii=False), "utf-8")

    # Emit sprite-coords.json documenting PC -> 432x514 rules + samples
    coords_doc = {
        "pcStage": {"width": 1280, "height": 720},
        "watchScreen": {"width": 432, "height": 514},
        "watchArtStage": {"width": 432, "height": 243, "scaleFromPc": 432.0 / 1280.0},
        "poseTypes": {
            "st": {
                "pcRawHeight": 1536,
                "pcRawWidthRange": [472, 1240],
                "stdlibWrapper": ["L138", "L139", "L12", "L140", "L141"],
                "intcodeG704": 0,
                "watchUniformScale": 0.234375,
                "watchCroppedHeight": 296,
                "usage": "Standing view preserving native aspect ratio; wy around 27.5"
            },
            "up": {
                "pcRawHeight": 1280,
                "pcRawWidthRange": [736, 1832],
                "stdlibWrapper": ["L112", "L114", "L13", "L115", "L117"],
                "intcodeG704": 1,
                "watchUniformScale": 0.20,
                "watchHeight": 256,
                "usage": "Close-up upper-body view preserving native aspect ratio; wy around 21.5..23.5"
            },
            "st_square": {
                "pcRawSize": [512, 512],
                "watchBox": [144, 144],
                "usage": "Phone/insert props (st-td_*) preserving 1:1 square aspect ratio"
            }
        },
        "conversionFormula": {
            "pxPerWorldUnit": "293.327 / clamp(36 + (sprite_wz - cam_wz), 20, 48)",
            "rawStageCenterX": "216 + (sprite_wx - cam_wx) * pxPerWorldUnit",
            "multiCharSolver": "1-char centered/clamped [88..344]; 2-char min separation 168px; 3+ char balanced [76, 216, 356] with >=122px gap",
            "watchTopY_st": "clamp(round(0 + (cam_wy - (wy - 27.5)) * 5), -36, 24)",
            "watchTopY_up": "clamp(round(-12 + (cam_wy - (wy - 23.5)) * 5), -32, 18)",
            "stateMachineKey": "characterId (cid 0..6), strictly <= 1 sprite element per character slot"
        },
        "samples": coord_samples[:20],
    }
    OUT_COORDS_JSON.write_text(json.dumps(coords_doc, indent=2, ensure_ascii=False), "utf-8")

    print(f"Wrote {OUT_GRAPH_JSON}: {len(nodes)} nodes ({graph['adultNodesCount']} adult), {graph['totalLines']} lines, {graph['totalChunks']} chunks")
    print(f"Wrote {OUT_GALLERY_JSON}: {len(gallery_groups)} CG groups, total gallery items={sum(len(g['items']) for g in gallery_groups)}")
    print(f"Wrote {OUT_ASSETS_JSON}: {len(used_bgs)} BGs/CGs, {len(used_sprites)} sprites")
    print(f"Wrote {OUT_COORDS_JSON}")


if __name__ == "__main__":
    main()
