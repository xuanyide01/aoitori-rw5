import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
for stem in ["sn101", "sn102", "sn201"]:
    p = code_dir / f"{stem}.ps3"
    h, l, c, tx = parse_ps3_raw(p)
    ins = disasm(c, tx, h[8], len(c), 4 * len(l))
    stk = []
    last = ""
    cam = (0.0, 0.0, 36.0)
    print(f"=== {stem} camera + sprite placement ===")
    cnt = 0
    for o, t in ins:
        m = re.match(r"EXPR\(020[012]\): (.+)$", t)
        if m:
            last = m.group(1)
        elif t == "PUSH_REG0":
            stk.append(last)
        elif t.startswith("CALL "):
            fn = t[5:]
            if fn == "L91" and len(stk) >= 4:
                cam = (stk[-4], stk[-3], stk[-2])
                print(f"  0x{o:05x} CAM  wx={cam[0]} wy={cam[1]} wz={cam[2]}")
            elif fn in ("L139", "L114", "L140", "L115") and len(stk) >= 5:
                print(f"  0x{o:05x} {fn:4s} char={stk[-1]} expr={stk[-2]} wx={stk[-3]} wy={stk[-4]} wz={stk[-5]} (cam_wx={cam[0]})")
                cnt += 1
            elif fn == "L129" and len(stk) >= 3:
                print(f"  0x{o:05x} L129 char={stk[-1]} x={stk[-2]} y={stk[-3]}")
            stk.clear()
            if cnt >= 15:
                break
        elif t.startswith("SYS "):
            stk.clear()
