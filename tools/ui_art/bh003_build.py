"""bh-003 UI art build: tier emblems, guild banners/crests (+ PNG cloth textures), 13 new NPC portraits, evidence sheets.

Usage:  python tools/ui_art/bh003_build.py            (needs: pip install resvg-py fonttools pillow)

Writes only:
  game/assets/ui/tiers/tier_{unranked,e,d,c,b,a,s,ss,sss}.svg
  game/assets/ui/guilds/{swordfin,lantern}_{banner,crest}.svg, {swordfin,lantern}_banner.png (512x768)
  game/assets/ui/portraits/<13 new ids>.svg   (refuses to overwrite a portrait that existed before bh-003)
  work/lemondev/bh-003/evidence/ui_art/*.png + subset_check.txt
Evidence rasterisation uses resvg (not Godot/ThorVG - Godot is not run in this pipeline).
"""
from __future__ import annotations

import os
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
UI = os.path.join(ROOT, "game", "assets", "ui")
EVID = os.path.join(ROOT, "work", "lemondev", "bh-003", "evidence", "ui_art")

from bh003_render import render_svg, render_file, sheet, font  # noqa: E402
import bh003_tiers  # noqa: E402
import bh003_guilds  # noqa: E402
import bh003_portraits  # noqa: E402

PRE_BH003_PORTRAITS = {"blacksmith", "captain", "elder", "knight", "mage", "merchant", "mystic", "stranger"}
ALLOWED = {"svg", "defs", "linearGradient", "radialGradient", "stop", "g", "path", "circle", "ellipse", "rect"}


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def subset_problems(svg):
    tags = set(re.findall(r"<([a-zA-Z]+)[\s/>]", svg))
    bad = tags - ALLOWED
    probs = [f"disallowed element <{t}>" for t in sorted(bad)]
    for pat in ("filter=", "mask=", "clip-path=", "<text", "xlink:href", "style="):
        if pat in svg:
            probs.append(f"uses {pat}")
    return probs


def build():
    out = {"tiers": [], "guilds": [], "portraits": [], "png": []}
    for name, fn in bh003_tiers.TIERS.items():
        p = os.path.join(UI, "tiers", name + ".svg")
        write(p, fn().svg())
        out["tiers"].append(p)
    for name, fn in bh003_guilds.GUILDS.items():
        p = os.path.join(UI, "guilds", name + ".svg")
        write(p, fn().svg())
        out["guilds"].append(p)
    for name in ("swordfin_banner", "lantern_banner"):
        img = render_svg(bh003_guilds.banner_png_svg(name).svg(), 512)
        assert img.size == (512, 768), img.size
        p = os.path.join(UI, "guilds", name + ".png")
        img.save(p)
        out["png"].append(p)
    for name, fn in bh003_portraits.NEW_PORTRAITS.items():
        if name in PRE_BH003_PORTRAITS:
            raise SystemExit(f"refusing to overwrite existing portrait {name}")
        p = os.path.join(UI, "portraits", name + ".svg")
        write(p, fn().svg())
        out["portraits"].append(p)
    return out


def nm(p):
    return os.path.splitext(os.path.basename(p))[0]


def evidence(out):
    os.makedirs(EVID, exist_ok=True)
    log = []
    for group in ("tiers", "guilds", "portraits"):
        for p in out[group]:
            s = open(p, encoding="utf-8").read()
            pr = subset_problems(s)
            log.append(f"{os.path.relpath(p, ROOT)}  {len(s)} bytes  {'OK' if not pr else '; '.join(pr)}")
    write(os.path.join(EVID, "subset_check.txt"), "ThorVG-safe subset check (elements limited to " + ", ".join(sorted(ALLOWED)) + ")\n" + "\n".join(log) + "\n")

    tiers = out["tiers"]
    # native 28 px on dark and on a light background, plus 4x nearest-neighbour zoom of the 28 px render
    for px in (28, 48, 128):
        sheet([(nm(p)[5:], render_file(p, px)) for p in tiers], f"tier emblems @ {px}px (resvg)", os.path.join(EVID, f"tiers_{px}.png"), cols=9)
    sheet([(nm(p)[5:], render_file(p, 28)) for p in tiers], "tier emblems @ 28px on a light background", os.path.join(EVID, "tiers_28_light.png"),
          cols=9, bg=(200, 196, 188), cell_bg=(228, 224, 214))
    sheet([(nm(p)[5:], render_file(p, 28).resize((112, 112), Image.NEAREST)) for p in tiers], "tier emblems: 28px render, 4x nearest zoom",
          os.path.join(EVID, "tiers_28_zoom4x.png"), cols=9)
    hud_mock(tiers, os.path.join(EVID, "tiers_hud_mock.png"))

    g = out["guilds"]
    banners = [p for p in g if "banner" in p]
    crests = [p for p in g if "crest" in p]
    ents = [(nm(p) + ".svg", render_file(p, 256)) for p in banners]
    ents += [(nm(p) + ".png (50%)", Image.open(p).convert("RGBA").resize((256, 384), Image.LANCZOS)) for p in out["png"]]
    sheet(ents, "guild banners: SVG @256w and the 512x768 PNG cloth textures (shown at 50%)", os.path.join(EVID, "guild_banners.png"), cols=4)
    for p in banners:
        im = render_file(p, 512)
        bg = Image.new("RGBA", im.size, (34, 28, 42, 255))
        bg.alpha_composite(im)
        bg.convert("RGB").save(os.path.join(EVID, f"{nm(p)}_512.png"))
    sheet([(f"{nm(p)} {px}", render_file(p, px)) for p in crests for px in (28, 48, 128)], "guild crests @ 28 / 48 / 128 px",
          os.path.join(EVID, "guild_crests.png"), cols=6)

    por = out["portraits"]
    for px in (64, 128):
        sheet([(nm(p), render_file(p, px)) for p in por], f"bh-003 portraits @ {px}px", os.path.join(EVID, f"portraits_{px}.png"), cols=7 if px == 128 else 13)
    sheet([(nm(p), render_file(p, 256)) for p in por[:7]], "bh-003 portraits @ 256px (1/2)", os.path.join(EVID, "portraits_256_a.png"), cols=4)
    sheet([(nm(p), render_file(p, 256)) for p in por[7:]], "bh-003 portraits @ 256px (2/2)", os.path.join(EVID, "portraits_256_b.png"), cols=3)
    old = [os.path.join(UI, "portraits", n + ".svg") for n in sorted(PRE_BH003_PORTRAITS)]
    sheet([(nm(p) + (" *" if nm(p) in PRE_BH003_PORTRAITS else ""), render_file(p, 128)) for p in old + por],
          "all portraits @128 (* = pre-existing, for style comparison)", os.path.join(EVID, "portraits_all_128.png"), cols=7)


def hud_mock(tiers, path):
    """Emblem at 28 px beside a level number, the way the HUD shows it."""
    W, H = 9 * 96 + 20, 70
    img = Image.new("RGB", (W, H), (22, 18, 28))
    dr = ImageDraw.Draw(img)
    dr.text((10, 4), "HUD mock: [emblem 28px] Lv", fill=(230, 214, 180), font=font(12))
    for i, p in enumerate(tiers):
        x = 10 + i * 96
        dr.rounded_rectangle([x, 24, x + 88, 60], 6, fill=(40, 32, 48), outline=(120, 96, 60))
        im = render_file(p, 28)
        img.paste(im, (x + 5, 28), im)
        dr.text((x + 38, 32), f"Lv {1 + i * 5}", fill=(240, 232, 214), font=font(14))
    img.save(path)


if __name__ == "__main__":
    o = build()
    evidence(o)
    for k, v in o.items():
        print(k, len(v))
