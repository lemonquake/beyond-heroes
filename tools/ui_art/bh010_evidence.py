"""bh-010 evidence: contact sheets of the new UI art rendered from game/assets/ui through Godot's ThorVG
(bh010_render / render_evidence, throwaway headless project - never the game project).

Writes into work/lemondev/bh-010/evidence/ui_art/:
  skills_<class>_128.png / skills_<class>_48.png   (grouped actives / auras / passives)
  skills_all_48.png, talents_128.png, talents_48.png, status_128.png, status_48.png,
  classes_portraits_256.png (new + existing knight/mage for style reference), tree_backdrops.png, tree_bg_*_full.png
Usage: python tools/ui_art/bh010_evidence.py
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_all import UI, ROOT  # noqa: E402
from bh010_render import render_many, sheet  # noqa: E402
from render_evidence import font, BG  # noqa: E402
import bh010_check as CK  # noqa: E402
import icons_skills_bh010 as SK  # noqa: E402

EVID = os.path.join(ROOT, "work", "lemondev", "bh-010", "evidence", "ui_art")
FAMILY = {"active": "actives (square bezel)", "aura_off": "auras - offensive (hex bezel, warm halo)",
          "aura_def": "auras - defensive (hex bezel, cool halo)", "passive": "passives (round medallion)"}


def P(sub, n):
    return os.path.abspath(os.path.join(UI, sub, n + ".svg"))


def main():
    os.makedirs(EVID, exist_ok=True)
    skills = {n: P("icons/skills", n) for n in CK.SKILLS}
    talents = {n: P("icons/talents", n) for n in CK.TALENTS}
    status = {n: P("icons/status", n) for n in CK.STATUS}
    big = {f"{s}/{n}": P(s, n) for s in ("icons/classes", "portraits") for n in ("ranger", "shadowblade", "knight", "mage")}
    small = list(skills.values()) + list(talents.values()) + list(status.values())
    ims, log, rc = render_many(small, [128, 48])
    ims2, log2, rc2 = render_many(list(big.values()), [256])
    ims.update(ims2)
    print((log.strip().splitlines() or [""])[-1], "|", (log2.strip().splitlines() or [""])[-1], "rc", rc, rc2)
    out = []

    def ents(d, names, px):
        return [(n, ims[(d[n], px)]) for n in names if (d[n], px) in ims]

    all48 = []
    for cls in ("knight", "mage", "ranger", "shadowblade"):
        for px in (128, 48):
            groups = []
            for fam in ("active", "aura_off", "aura_def", "passive"):
                names = [n for n in CK.SKILLS if SK.KINDS.get(n) == (cls, fam)]
                if names:
                    groups.append((FAMILY[fam], ents(skills, names, px)))
            out.append(sheet(None, f"bh-010 {cls} skill icons @ {px}px", os.path.join(EVID, f"skills_{cls}_{px}.png"),
                             cols=11, groups=groups, min_cell=108 if px == 48 else None))
            if px == 48:
                all48.append((f"{cls}", [e for _, g in groups for e in g]))
    out.append(sheet(None, "bh-010 all new skill icons @ 48px", os.path.join(EVID, "skills_all_48.png"), cols=19, groups=all48, min_cell=96))
    for px in (128, 48):
        out.append(sheet(None, f"bh-010 talent icons @ {px}px", os.path.join(EVID, f"talents_{px}.png"), cols=11, min_cell=108 if px == 48 else None,
                         groups=[("ranger", ents(talents, CK.TALENTS[:11], px)), ("shadowblade", ents(talents, CK.TALENTS[11:], px))]))
        out.append(sheet(None, f"bh-010 status icons @ {px}px", os.path.join(EVID, f"status_{px}.png"), cols=9, min_cell=108 if px == 48 else None,
                         groups=[("new statuses", ents(status, CK.STATUS[:6], px)), ("aura buffs", ents(status, CK.STATUS[6:14], px)),
                                 ("enemy/other", ents(status, CK.STATUS[14:], px))]))
    g = [("class crests: new ranger / shadowblade, existing knight / mage for reference", ents(big, [k for k in big if k.startswith("icons/classes")], 256)),
         ("portraits: new ranger / shadowblade, existing knight / mage for reference", ents(big, [k for k in big if k.startswith("portraits")], 256))]
    out.append(sheet(None, "bh-010 class crests + hero portraits @ 256px", os.path.join(EVID, "classes_portraits_256.png"), cols=4, groups=g))
    # tree backdrops: 2x2 at 800x450 (new + existing), and full-size copies of the new ones
    tw, th, pad = 800, 450, 14
    img = Image.new("RGB", (2 * tw + 3 * pad, 2 * (th + 22) + pad + 34), BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 8), "bh-010 tree backdrops (1600x900 shown at 50%): new ranger / shadowblade, existing knight / mage", fill=(230, 214, 180), font=font(16))
    for i, k in enumerate(("ranger", "shadowblade", "knight", "mage")):
        src = os.path.join(UI, "tree", f"tree_bg_{k}.png")
        im = Image.open(src).convert("RGB")
        if k in ("ranger", "shadowblade"):
            p = os.path.join(EVID, f"tree_bg_{k}_full.png")
            im.save(p)
            out.append(p)
        x, y = pad + (i % 2) * (tw + pad), 34 + (i // 2) * (th + 22)
        dr.text((x, y), f"tree_bg_{k}.png" + ("  (new)" if k in ("ranger", "shadowblade") else "  (existing)"), fill=(200, 196, 210), font=font(12))
        img.paste(im.resize((tw, th), Image.LANCZOS), (x, y + 18))
    p = os.path.join(EVID, "tree_backdrops.png")
    img.save(p)
    out.append(p)
    for p in out:
        print(os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
