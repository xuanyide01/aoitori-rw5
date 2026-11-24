import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm

code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
bg_map = json.loads(Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_bg_map.json").read_text("utf-8"))
sp_map = json.loads(Path(r"E:\Antigravity\aoitori-rw5\probe\intcode_sprite_map.json").read_text("utf-8"))

# L168 video BG map
L168_MAP = {
    70: "bg070a.pb3", 220: "bg220a.pb3", 221: "bg220b.pb3", 222: "bg220c.pb3",
    260: "bg260a.pb3", 261: "bg260b.pb3", 262: "bg260c.pb3", 264: "bg260e.pb3",
    270: "bg280a.pb3", 272: "bg280c.pb3", 280: "bg280a.pb3", 282: "bg280c.pb3",
    290: "bg290a.pb3", 292: "bg290c.pb3", 580: "bg580a.pb3", 582: "bg580c.pb3",
    584: "bg580e.pb3", 731: "bg731e.pb3", 900: "mv01",
}

def eval_int(expr_txt: str):
    expr_txt = expr_txt.strip()
    if re.fullmatch(r"-?\d+", expr_txt):
        return int(expr_txt)
    m = re.fullmatch(r"(-?\d+)\s+(-?\d+)\s+([+\-*])", expr_txt)
    if m:
        a, b, op = int(m.group(1)), int(m.group(2)), m.group(3)
        return a + b if op == "+" else (a - b if op == "-" else a * b)
    return None

def eval_float(expr_txt: str):
    toks = expr_txt.strip().split()
    st = []
    for tk in toks:
        if tk.endswith("f"):
            try:
                st.append(float(tk[:-1]))
            except ValueError:
                return None
        elif re.fullmatch(r"-?\d+", tk):
            st.append(float(tk))
        elif tk in ("+", "-", "*", "/") and len(st) >= 2:
            b, a = st.pop(), st.pop()
            st.append(a + b if tk == "+" else (a - b if tk == "-" else (a * b if tk == "*" else a / (b or 1.0))))
        else:
            return None
    return st[-1] if len(st) == 1 else None

used_bgs = set()
used_sprites = set()
used_bgms = set()
h_scripts_detail = {}
titles_detail = {}

for p in sorted(code_dir.glob("sn*.ps3")):
    h, l, c, tx = parse_ps3_raw(p)
    ins = disasm(c, tx, h[8], len(c), 4 * len(l))
    stk = []
    last = ""
    outfits = {cid: 0 for cid in range(12)}
    titles = []
    line_idx = 0
    h_lines = []
    choices = []
    for o, t in ins:
        m = re.match(r"EXPR\(020[012]\): (.+)$", t)
        if m:
            last = m.group(1)
            continue
        if t == "PUSH_REG0":
            stk.append(last)
            continue
        if t.startswith("CALL "):
            fn = t[5:]
            if fn in ("L77", "L78", "L11", "L5"):
                line_idx += 1
            elif fn in ("L193", "L195") and stk:
                titles.append(stk[-1].strip("'"))
            elif fn == "L186" and len(stk) >= 1:
                opts = [s.strip("'") for s in stk[-5:] if s.startswith("'")]
                if any(opts):
                    choices.append((o, opts))
            elif fn == "L120" and len(stk) >= 2:
                cid = eval_int(stk[-1])
                mode = eval_int(stk[-2])
                if cid is not None and mode is not None:
                    outfits[cid] = mode
            elif fn in ("L167", "L170", "L171", "L172", "L173", "L182", "L183") and stk:
                bid = eval_int(stk[-1])
                if bid is not None and str(bid) in bg_map:
                    fn_bg = bg_map[str(bid)]
                    used_bgs.add(fn_bg)
                    if fn_bg.startswith("h_"):
                        h_lines.append((line_idx, fn_bg))
            elif fn == "L168" and stk:
                bid = eval_int(stk[-1])
                if bid in L168_MAP and L168_MAP[bid].endswith(".pb3"):
                    used_bgs.add(L168_MAP[bid])
            elif fn == "L18" and stk:
                eid = eval_int(stk[-1])
                if eid is not None:
                    used_bgs.add(f"eyecatch{eid:02d}.pb3")
            elif fn == "L62" and stk:
                mid = eval_int(stk[-1])
                if mid is not None:
                    used_bgms.add(mid)
            elif fn in ("L139", "L114", "L140", "L115", "L141", "L117", "L12", "L13") and len(stk) >= 2:
                cid = eval_int(stk[-1])
                eid = eval_int(stk[-2])
                pref = "up-" if fn in ("L114", "L115", "L117", "L13") else "st-"
                if cid is not None and eid is not None and str(cid) in sp_map:
                    cm = sp_map[str(cid)]
                    outf = cm["outfits"].get(str(outfits.get(cid, 0)), cm["outfits"].get("0", ""))
                    ex = cm["exprs"].get(str(eid), "")
                    if outf and ex:
                        used_sprites.add((pref, cid, outf, ex))
            stk.clear()
        elif t.startswith("SYS "):
            stk.clear()
    titles_detail[p.stem] = {"title": titles, "lines": line_idx, "choices": choices}
    if h_lines:
        h_scripts_detail[p.stem] = {
            "total_lines": line_idx,
            "first_h_line": h_lines[0][0],
            "last_h_line": h_lines[-1][0],
            "h_count": len(h_lines),
            "sample": h_lines[0][1],
        }

print(f"Total used BG/CGs: {len(used_bgs)}")
print(f"  bg*: {sum(1 for x in used_bgs if x.startswith('bg'))}")
print(f"  ev_*: {sum(1 for x in used_bgs if x.startswith('ev_'))}")
print(f"  h_*: {sum(1 for x in used_bgs if x.startswith('h_'))}")
print(f"  other: {sorted(x for x in used_bgs if not x.startswith(('bg','ev_','h_')))}")
print(f"Total used sprites: {len(used_sprites)} (st-: {sum(1 for x in used_sprites if x[0]=='st-')}, up-: {sum(1 for x in used_sprites if x[0]=='up-')})")
print(f"Total used (pref, char, outfit) bases: {len({(x[0], x[2]) for x in used_sprites})}")
print(f"Total used BGM IDs: {sorted(used_bgms)} ({len(used_bgms)})")
print("\nScripts with H-CGs:")
for k, v in h_scripts_detail.items():
    print(f"  {k:10s}: {v}")
print("\nScripts with choices:")
for k, v in titles_detail.items():
    if v["choices"]:
        print(f"  {k:10s}: {v['choices']}")
print("\nTotal story dialogue lines:", sum(v["lines"] for v in titles_detail.values()))
