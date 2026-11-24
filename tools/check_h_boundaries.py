import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
bg_map = json.loads(Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_bg_map.json").read_text("utf-8"))

for stem in ["sn101", "sn104", "sn105", "sn209", "sn211", "sn304", "sn308", "sn404", "sn407", "sn409", "sn412", "sn501", "sn506", "sn507", "sn509", "sn602"]:
    p = code_dir / f"{stem}.ps3"
    h, l, c, tx = parse_ps3_raw(p)
    ins = disasm(c, tx, h[8], len(c), 4 * len(l))
    stk = []
    last = ""
    line = 0
    events = []
    for o, t in ins:
        m = re.match(r"EXPR\(020[012]\): (.+)$", t)
        if m:
            last = m.group(1)
        elif t == "PUSH_REG0":
            stk.append(last)
        elif t.startswith("CALL "):
            fn = t[5:]
            if fn in ("L77", "L78", "L11", "L5"):
                line += 1
            elif fn in ("L167", "L170", "L171", "L172", "L173", "L182", "L183") and stk:
                if re.fullmatch(r"\d+", stk[-1].strip()):
                    fn_bg = bg_map.get(stk[-1].strip(), "")
                    if fn_bg:
                        events.append((line, fn, fn_bg))
            elif "P[" in last:
                pass
            stk.clear()
        elif "P[" in last and "=" in last:
            events.append((line, "SET_P", last))
        elif t.startswith("SYS "):
            stk.clear()
    # Print transitions into/out of h_*
    h_ev = [(ln, fn, bg) for ln, fn, bg in events if bg.startswith("h_") or fn == "SET_P"]
    print(f"=== {stem} (total {line}) ===")
    if h_ev:
        first_ln = next((ln for ln, fn, bg in h_ev if bg.startswith("h_")), 0)
        # find non-h bg right before first_ln and right after last h_
        last_ln = max(ln for ln, fn, bg in h_ev if bg.startswith("h_"))
        prev_bg = [e for e in events if e[0] <= first_ln and not e[2].startswith("h_") and e[1] != "SET_P"][-1:]
        next_bg = [e for e in events if e[0] > last_ln and not e[2].startswith("h_") and e[1] != "SET_P"][:1]
        p_sets = [e for e in events if e[1] == "SET_P"]
        print(f"  prev_bg={prev_bg}, first_h={first_ln}, last_h={last_ln}, next_bg={next_bg}, p_sets={p_sets}")
        # Also show distinct h_ prefixes/groups in this file
        h_groups = []
        for ln, fn, bg in events:
            if bg.startswith("h_"):
                grp = bg[:8]
                if not h_groups or h_groups[-1][0] != grp:
                    h_groups.append((grp, ln))
        print(f"  h_spans={h_groups}")
