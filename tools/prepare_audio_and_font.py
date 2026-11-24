import json
import struct
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from fontTools import subset

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"E:\Antigravity\aoitori-rw5")
STEAM_DATA = Path(r"G:\SteamLibrary\steamapps\common\Aoi Tori\data")
FFMPEG = Path(r"D:\codex\2026-09-06\g\work\libs\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")
FONT_SRC = Path(r"D:\codex\移植项目\shinuyakata-rw5\研究\NotoSansCJKsc-Regular.otf")


def run_ffmpeg(inp: Path, out: Path, bitrate: str):
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(FFMPEG), "-y", "-i", str(inp),
        "-vn", "-c:a", "libopus", "-b:a", bitrate,
        "-ac", "1", "-ar", "24000", "-application", "audio",
        str(out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"ffmpeg failed: {res.stderr}"
    print(f"Encoded {out.name}: {out.stat().st_size:,} bytes ({bitrate})")


def extract_audio():
    # 1. Title BGM (bgm36 for initial/title02, bgm33 for true unlocked title03)
    run_ffmpeg(STEAM_DATA / "music/bgm36.ogg", ROOT / "src/common/title-bgm.opus", "32k")
    run_ffmpeg(STEAM_DATA / "music/bgm33.ogg", ROOT / "src/common/title-true-bgm.opus", "32k")

    # 2. Extract OggS OP audio from op.cmv entry 2915
    op_cmv = STEAM_DATA / "video/op.cmv"
    tmp_ogg = ROOT / "probe/op_audio.ogg"
    with open(op_cmv, "rb") as f:
        hdr = struct.unpack("<4s10I", f.read(44))
        assert hdr[0] == b"CMV6"
        res_off, _, _, max_seq = hdr[1], hdr[2], hdr[3], hdr[4]
        f.seek(44 + max_seq * 20)
        seq, csz, usz, rtype, foff = struct.unpack("<5I", f.read(20))
        f.seek(res_off + foff)
        ogg = f.read(csz)
        assert ogg[:4] == b"OggS", f"Unexpected OP audio magic: {ogg[:8]}"
        tmp_ogg.write_bytes(ogg)
    run_ffmpeg(tmp_ogg, ROOT / "src/common/opening-bgm.opus", "40k")


def build_font():
    chars = set()
    # Collect all story chunk characters
    for p in (ROOT / "src/common/story").glob("*.txt"):
        chars.update(p.read_text("utf-8"))
    # Collect graph/gallery strings
    for jp in (ROOT / "converted/graph.json", ROOT / "converted/gallery.json", ROOT / "reports/title.json"):
        if jp.exists():
            chars.update(jp.read_text("utf-8"))
    # Collect UI & JS strings
    for uip in (ROOT / "src/pages/index/index.ux", *sorted((ROOT / "src/common").glob("*.js"))):
        if uip.exists():
            chars.update(uip.read_text("utf-8"))
    # Add full UI / digits / ASCII / punctuation safety set
    ui_extra = (
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        "，。！？、；：“”‘’（）【】《》—…·～♂♀『』「」‹›"
        "アオイトリ开始游戏继续读取鉴赏系统设置退出真相篇幕间理沙小夜玛丽明里无垢由佳里"
        "自动播放跳过快进历史记录存档读档章节选择画廊回想成人模式开启关闭"
        "第章页条空删除确定取消返回菜单封面重播暂停播放音轨音乐鉴赏标题画面解锁条件"
        "已全部未触发分支选项当前进度提示确认覆盖是否"
    )
    chars.update(ui_extra)
    chars.discard("\n")
    chars.discard("\r")
    chars.discard("\t")

    out_otf = ROOT / "src/common/aoitori-text.otf"
    txt_file = ROOT / "probe/font_chars.txt"
    txt_file.write_text("".join(sorted(chars)), "utf-8")

    args = [
        str(FONT_SRC),
        f"--text-file={txt_file}",
        f"--output-file={out_otf}",
        "--desubroutinize",
        "--no-hinting",
        "--layout-features=*",
    ]
    subset.main(args)
    print(f"Built subset font {out_otf.name}: {out_otf.stat().st_size:,} bytes ({len(chars)} unique chars)")


def build_logo():
    # Build crisp 192x192 circular launcher icon from title03_chip_top720.png / title02_chip_top720.png
    src_img = Image.open(ROOT / "probe/title03_chip_top720.png").convert("RGBA")
    # Crop around Akari portrait + blue bird feather on right side (x=660..1240, y=40..620) or center
    w, h = src_img.size
    side = min(w, h)
    # Center-right crop framing hero portrait nicely
    x0 = max(0, w - side)
    crop = src_img.crop((x0, 0, x0 + side, side)).resize((192, 192), Image.Resampling.LANCZOS)
    mask = Image.new("L", (192, 192), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((2, 2, 189, 189), fill=255)
    out = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    out.paste(crop, (0, 0), mask)
    out_path = ROOT / "src/common/logo.png"
    out.save(out_path, "PNG")
    print(f"Built circular logo {out_path.name}: {out_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    if "--font-only" not in sys.argv:
        extract_audio()
    build_font()
    if "--font-only" not in sys.argv:
        build_logo()
