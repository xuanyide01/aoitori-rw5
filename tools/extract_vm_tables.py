import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\Antigravity\aoitori-rw5\tools")
from disasm_ps3 import parse_ps3_raw, disasm


def inspect_bgm():
    lines = Path(r"E:\Antigravity\aoitori-rw5\probe\disasm_stdlib.txt").read_text("utf-8").splitlines()
    in_l63 = False
    print("=== STDLIB L63 (BGM) ===")
    for ln in lines:
        if ln.startswith("-- L[63]"):
            in_l63 = True
        elif ln.startswith("-- L[") and in_l63:
            break
        if in_l63:
            if any(k in ln for k in ("jeq_reg", "'bgm", "CALL", "SYS", "-- L")):
                print(ln)


def inspect_sprite_and_bg_wrappers():
    lines = Path(r"E:\Antigravity\aoitori-rw5\probe\disasm_stdlib.txt").read_text("utf-8").splitlines()
    # Dump L102, L111, L118, L103, L112, L138, L108, L126, L167, L181, L182, L26, L28, L30, L31, L170, L171
    wanted = {
        "L[102]", "L[111]", "L[118]", "L[121]",
        "L[103]", "L[112]", "L[138]",
        "L[14]", "L[13]", "L[12]",
        "L[106]", "L[114]", "L[139]",
        "L[108]", "L[104]", "L[54]", "L[55]", "L[53]",
        "L[126]", "L[167]", "L[60]", "L[170]", "L[171]", "L[173]",
        "L[26]", "L[28]", "L[27]", "L[4]", "L[6]",
    }
    cur = None
    out = []
    for ln in lines:
        if ln.startswith("-- L["):
            m = re.search(r"L\[\d+\]", ln)
            lbls = re.findall(r"L\[?\d+\]?", ln)
            # parse labels list inside -- L[a, b] --
            inner = ln.split("[", 1)[1].split("]", 1)[0]
            names = [f"L[{x.strip()}]" for x in inner.split(",")]
            cur = ln if any(n in wanted for n in names) else None
            if cur:
                out.append(ln)
        elif cur:
            out.append(ln)
    Path(r"E:\Antigravity\aoitori-rw5\probe\stdlib_wrappers.txt").write_text("\n".join(out), "utf-8")
    print(f"Wrote stdlib_wrappers.txt ({len(out)} lines)")


def inspect_sn_calls():
    code_dir = Path(r"E:\Antigravity\aoitori-rw5\probe\longinus_named\code")
    call_counts = {}
    sys_counts = {}
    choice_scripts = []
    next_scripts = []
    for p in sorted(code_dir.glob("*.ps3")):
        hdr, labels, code_seg, text_seg = parse_ps3_raw(p)
        lbl_base = 4 * len(labels)
        insns = disasm(code_seg, text_seg, hdr[8], len(code_seg), lbl_base)
        has_choice = False
        for i, (off, txt) in enumerate(insns):
            if txt.startswith("CALL "):
                call_counts[txt] = call_counts.get(txt, 0) + 1
            elif txt.startswith("SYS "):
                sys_counts[txt] = sys_counts.get(txt, 0) + 1
                if "select_button" in txt:
                    has_choice = True
        if has_choice and p.stem.startswith("sn"):
            choice_scripts.append(p.stem)
    print("\nTop CALL targets across all 85 scripts:")
    for k, v in sorted(call_counts.items(), key=lambda kv: -kv[1])[:50]:
        print(f"  {k:12s}: {v}")
    print("\nStory scripts with select_button:", choice_scripts)


if __name__ == "__main__":
    inspect_bgm()
    inspect_sprite_and_bg_wrappers()
    inspect_sn_calls()
