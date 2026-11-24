import json
import struct
import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IMG_DIR = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\image")
OUT_JSON = Path(r"E:\Antigravity\aoitori-rw5\reports\title.json")
PROBE_DIR = Path(r"E:\Antigravity\aoitori-rw5\probe")


def load_raw_bgra(path: Path, width: int) -> Image.Image:
    raw = path.read_bytes()
    assert len(raw) % (width * 4) == 0, (path.name, len(raw))
    height = len(raw) // (width * 4)
    # Raw Longinus BGRA stored upside-down? Let's check top vs bottom half by saving both or checking standard BGRA
    img = Image.frombytes("RGBA", (width, height), raw, "raw", "BGRA")
    return img


def main():
    previews = []
    for name in ("title01_chip.pb3", "title02_chip.pb3", "title03_chip.pb3"):
        p = IMG_DIR / name
        im = load_raw_bgra(p, 1280)
        # In title01/02/03_chip.pb3, menu.ps3 crops (0,0,1280,720) for the title BG!
        # Let's check top 720 vs bottom 720 (check opacity / brightness of (0,0,1280,720))
        bg_top = im.crop((0, 0, 1280, 720))
        bg_bot = im.crop((0, im.height - 720, 1280, im.height))
        top_out = PROBE_DIR / f"{p.stem}_top720.png"
        bot_out = PROBE_DIR / f"{p.stem}_bot720_flip.png"
        bg_top.convert("RGB").save(top_out)
        im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).crop((0, 0, 1280, 720)).convert("RGB").save(bot_out)
        previews.append({"file": name, "width": im.width, "height": im.height, "topOut": str(top_out), "flipOut": str(bot_out)})
        print(f"{name}: {im.width}x{im.height} saved previews")

    report = {
        "sourceScript": "menu.ps3 (L207 @ 0x3b534..0x3ec80) & sn103.ps3 & sn299/sn399/sn499 L186",
        "idleOpTimeoutMs": 30000,
        "idleOpScript": "op.ps3",
        "voiceGreetingOnEnter": {
            "variable": "G[46]",
            "pool": ["sys102.ogg", "sys202.ogg", "sys302.ogg", "sys402.ogg", "sys502.ogg", "sys602.ogg", "sys702.ogg"],
            "selection": "sys_rand(7) -> V0 % 7 (0..6)"
        },
        "titleStates": [
            {
                "stateId": 0,
                "variable": "V12 = 0",
                "condition": "Initial state (P[2147] == 0 && P[2156] == 0)",
                "conditionLabel": "初始标题",
                "chipTexture": "title01_chip.pb3",
                "bgRect": [0, 0, 1280, 720],
                "titleBgmId": 36,
                "titleBgmFile": "bgm36.ogg",
                "menuButtons": [
                    {"id": 1, "label": "开始游戏", "action": "sn101.ps3", "unlocked": "always"},
                    {"id": 2, "label": "继续/读取", "action": "LOAD_MENU (G[2192]=5, sys_int_call(48))", "unlocked": "always"},
                    {"id": 3, "label": "鉴赏/EXTRA", "action": "omake.ps3", "unlocked": "always in PC menu (button 3 always registered at V24=2; G[94]=0)"},
                    {"id": 4, "label": "系统设置", "action": "CONFIG_MENU (G[2192]=G[2193], sys_int_call(48))", "unlocked": "always"},
                    {"id": 5, "label": "退出游戏", "action": "sys_end", "unlocked": "always"}
                ]
            },
            {
                "stateId": 1,
                "variable": "V12 = 1",
                "condition": "P[2147] != 0 && P[2156] == 0",
                "conditionLabel": "共通线进度触发 (sn103.ps3 设置 P[2147]=1)",
                "chipTexture": "title02_chip.pb3",
                "bgRect": [0, 0, 1280, 720],
                "titleBgmId": 36,
                "titleBgmFile": "bgm36.ogg",
                "menuButtons": [
                    {"id": 1, "label": "开始游戏", "action": "sn101.ps3", "unlocked": "always"},
                    {"id": 2, "label": "继续/读取", "action": "LOAD_MENU", "unlocked": "always"},
                    {"id": 3, "label": "鉴赏/EXTRA", "action": "omake.ps3", "unlocked": "always"},
                    {"id": 4, "label": "系统设置", "action": "CONFIG_MENU", "unlocked": "always"},
                    {"id": 5, "label": "退出游戏", "action": "sys_end", "unlocked": "always"}
                ]
            },
            {
                "stateId": 2,
                "variable": "V12 = 2",
                "condition": "P[2156] != 0 (sn299/sn399/sn499 L186 当 P[2150]&&P[2151]&&P[2152] 均已达成时设置 P[2156]=1)",
                "conditionLabel": "三条个人线全通后解锁真结局线 (理沙 P[2150] + 小夜 P[2151] + 玛丽 P[2152])",
                "chipTexture": "title03_chip.pb3",
                "bgRect": [0, 0, 1280, 720],
                "titleBgmId": 33,
                "titleBgmFile": "bgm33.ogg",
                "menuButtons": [
                    {"id": 1, "label": "开始游戏", "action": "sn101.ps3", "unlocked": "always"},
                    {"id": 6, "label": "真相篇/After Story", "action": "sn501.ps3", "unlocked": "P[2156] != 0"},
                    {"id": 2, "label": "继续/读取", "action": "LOAD_MENU", "unlocked": "always"},
                    {"id": 3, "label": "鉴赏/EXTRA", "action": "omake.ps3", "unlocked": "always"},
                    {"id": 4, "label": "系统设置", "action": "CONFIG_MENU", "unlocked": "always"},
                    {"id": 5, "label": "退出游戏", "action": "sys_end", "unlocked": "always"}
                ]
            }
        ],
        "watch5Adaptation": {
            "screenStateAudioPolicy": "TITLE and TITLE_SUB share title BGM without restarting or stacking; GAME stops/fades out title BGM; returning to TITLE restarts title BGM.",
            "titleBgAndMenuRule": "Follows original V12 progression (title01 -> title02 when sn103/P[2147] reached -> title03 + sn501 button unlocked when sn299 & sn399 & sn499 cleared / P[2156]=1). For Watch 5 portability, also reflects clear flags persistently in settings/progress store.",
            "titleChipTextures": previews,
        }
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), "utf-8")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
