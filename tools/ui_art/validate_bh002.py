"""Validate every bh-002 UI-art deliverable and write work/lemondev/bh-002/evidence/ui_art/validation.txt.

Raster: file exists, PNG RGBA, expected size class, alpha present (transparent pixels where the art needs them), manifest
entry with margins/use/scale, 9-slice margins fit the texture, panel centres tile seamlessly (seam metric), tileable noise
textures wrap, deterministic regeneration check (optional --determinism).
SVG: bh-001 rules via validate.check (XML, whitelist, no style/filter/mask/clip/href/text, refs resolve, background rule).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_all import UI, ROOT  # noqa: E402
import validate as v1  # noqa: E402

EVID = os.path.join(ROOT, "work", "lemondev", "bh-002", "evidence", "ui_art")

ST = ["normal", "hover", "pressed", "disabled", "focus"]
RASTER = {
    "frames": ["panel_main", "panel_inset", "panel_header", "panel_tooltip", "panel_dialogue", "panel_glass"]
    + [f"button_primary_{s}" for s in ST] + [f"button_{s}" for s in ST] + [f"button_menu_{s}" for s in ST]
    + ["tab_normal", "tab_hover", "tab_selected", "checkbox_off", "checkbox_on", "slider_track", "slider_fill", "slider_grabber",
       "slider_grabber_hover", "scroll_track", "scroll_grabber", "dropdown_arrow", "lineedit", "lineedit_focus", "separator_h",
       "close_x", "close_x_hover"],
    "slots": ["slot", "slot_hover", "slot_selected", "slot_disabled", "slot_locked", "equip_slot"]
    + [f"glyph_{g}" for g in ("main_weapon", "sub_weapon", "helm", "inner_garment", "armor", "gloves", "boots", "accessory")]
    + [f"rarity_{i}" for i in range(10)] + [f"rarity_glow_{i}" for i in range(5, 10)]
    + ["skill_slot", "skill_slot_empty", "cooldown_radial", "keybind_badge"],
    "hud": ["orb_frame_hp", "orb_frame_mana", "orb_glass", "orb_liquid_noise", "bar_frame_resource", "bar_frame_xp", "bar_fill",
            "bar_frame_boss", "bar_frame_target", "pip_empty", "pip_full", "minimap_frame", "minimap_mask", "buff_frame",
            "debuff_frame", "vignette_lowhp", "vignette_dark", "loot_beam", "mote", "spark", "ember", "cursor_default",
            "cursor_attack", "cursor_interact", "cursor_talk"],
    "tree": [f"node_{k}_{s}" for k in ("minor", "major", "keystone", "skill", "upgrade") for s in ("locked", "available", "allocated")]
    + ["connector", "tree_bg_knight", "tree_bg_mage"],
    "menu": ["title_logo", "menu_frame", "vignette_menu", "class_plinth_glow"],
}
EXTRA_RASTER = {"frames": ["panel_header_crest", "panel_dialogue_crest"]}
OPAQUE_OK = {"frames/panel_main", "frames/lineedit_focus", "tree/tree_bg_knight", "tree/tree_bg_mage", "hud/orb_liquid_noise", "slots/cooldown_radial", "hud/bar_fill"}

SVG = {
    "icons/items": ("0 0 128 128", "sword_2 sword_3 greatsword_2 greatsword_3 axe_2 axe_3 spear_2 spear_3 dagger_2 dagger_3 bow_2 bow_3 "
                    "staff_2 staff_3 wand_2 wand_3 shield_2 shield_3 helm_plate_2 helm_plate_3 helm_hood_2 helm_hood_3 armor_plate_2 "
                    "armor_plate_3 armor_robe_2 armor_robe_3 inner_chain inner_silk gloves_plate_2 gloves_cloth_2 boots_plate_2 "
                    "boots_cloth_2 ring_2 ring_3 amulet_2 amulet_3 charm_2 potion_health_large potion_mana_large elixir_rejuvenation "
                    "scroll_return antidote aether_shard frost_crystal storm_essence shadow_silk beast_hide quest_seal_key "
                    "quest_tablet quest_crown_fragment quest_letter set_guardian_helm set_guardian_armor set_guardian_gloves "
                    "set_guardian_boots set_guardian_shield set_sage_hood set_sage_robe set_sage_gloves set_sage_boots "
                    "set_sage_staff aether_sword aether_greatsword aether_staff aether_wand aether_ring aether_amulet"),
    "icons/status": ("0 0 128 128", "poisoned slowed silenced weakened armor_broken windswept empowered fortified overcharged "
                     "resolute badly_hurt"),
    "icons/ui": ("0 0 64 64", "gold aether level xp sort filter search lock favorite junk trash split compare settings save load "
                 "map teleport quest talk shop repair buyback back close plus minus check warning info skull crown"),
    "portraits": ("0 0 256 256", "knight mage blacksmith merchant elder mystic captain stranger"),
}


def seam_metric(arr, x0, y0, x1, y1):
    """Ratio of the wrap-around seam step to the mean neighbour step inside the centre patch (1.0 = invisible seam)."""
    c = arr[y0:y1, x0:x1, :3].astype(np.float32)
    inner = np.abs(np.diff(c, axis=1)).mean() + 1e-6
    seam = np.abs(c[:, 0] - c[:, -1]).mean()
    inner_y = np.abs(np.diff(c, axis=0)).mean() + 1e-6
    seam_y = np.abs(c[0] - c[-1]).mean()
    return seam / inner, seam_y / inner_y


def main(argv):
    lines = ["UI art validation for bh-002 (tools/ui_art/validate_bh002.py)", ""]
    bad = 0
    man_p = os.path.join(UI, "ui_art_manifest.json")
    man = json.load(open(man_p, encoding="utf-8")) if os.path.exists(man_p) else {}
    lines.append(f"manifest: {man_p} ({len(man) - 1 if man else 0} entries)")
    import raster_all
    regs = raster_all.builders()
    lines.append("")
    lines.append("== raster textures ==")
    total_r = 0
    for folder, names in RASTER.items():
        names = names + EXTRA_RASTER.get(folder, [])
        lines.append(f"[{folder}] expected {len(names)}")
        for n in names:
            rel = f"{folder}/{n}.png"
            p = os.path.join(UI, rel)
            errs = []
            if not os.path.exists(p):
                lines.append(f"  FAIL {rel} missing")
                bad += 1
                continue
            total_r += 1
            im = Image.open(p)
            if im.mode not in ("RGBA", "L"):
                errs.append(f"mode {im.mode}")
            a = np.asarray(im.convert("RGBA"))
            alpha = a[..., 3]
            transp = float((alpha < 8).mean())
            opaque = float((alpha > 247).mean())
            if im.mode == "RGBA" and transp < 0.005 and f"{folder}/{n}" not in OPAQUE_OK:
                errs.append("no transparent pixels")
            if (alpha == 0).all():
                errs.append("fully transparent")
            m = man.get(rel)
            extra = ""
            if m is None:
                errs.append("no manifest entry")
            else:
                for k in ("margins", "use", "scale"):
                    if k not in m:
                        errs.append(f"manifest missing '{k}'")
                mg = m.get("margins")
                if mg:
                    l, t, r, b = mg
                    if l + r >= im.width or t + b >= im.height and not (t + b == 0):
                        errs.append(f"margins {mg} do not fit {im.size}")
                    extra = f" margins={mg}"
                    if n.startswith("panel_") and l and t and m.get("stretch", "both") == "both":
                        sx, sy = seam_metric(a, l, t, im.width - r, im.height - b)
                        extra += f" centre-seam x={sx:.2f} y={sy:.2f}"
                        if sx > 3.0 or sy > 3.0:
                            errs.append(f"centre seam visible ({sx:.2f},{sy:.2f})")
                if m.get("hotspot"):
                    extra += f" hotspot={m['hotspot']}"
            if n in ("orb_liquid_noise", "connector"):
                g = a[..., :3].astype(np.float32) if n == "connector" else np.asarray(im).astype(np.float32)[..., None]
                sx = np.abs(g[:, 0] - g[:, -1]).mean() / (np.abs(np.diff(g, axis=1)).mean() + 1e-6)
                extra += f" wrap-x={sx:.2f}"
                if n == "orb_liquid_noise":
                    sy = np.abs(g[0] - g[-1]).mean() / (np.abs(np.diff(g, axis=0)).mean() + 1e-6)
                    extra += f" wrap-y={sy:.2f}"
                    if sy > 3.0:
                        errs.append("noise does not wrap vertically")
                if sx > 3.0:
                    errs.append("does not wrap horizontally")
            status = "OK  " if not errs else "FAIL"
            if errs:
                bad += 1
            lines.append(f"  {status} {rel:40s} {im.size[0]}x{im.size[1]} {im.mode} transparent={transp:.0%} opaque={opaque:.0%}{extra}"
                         + ("" if not errs else "  -> " + "; ".join(errs)))
    lines.append("")
    lines.append("== SVG (bh-001 rules: " + ",".join(sorted(v1.ALLOWED)) + "; no style/filter/mask/clip-path/href/class; refs resolve) ==")
    v1.VIEWBOX["icons/ui"] = {"0 0 64 64"}
    v1.VIEWBOX["portraits"] = {"0 0 256 256"}
    total_s = 0
    for sub, (vb, names) in SVG.items():
        want = names.split()
        lines.append(f"[{sub}] expected {len(want)} new files (viewBox {vb})")
        for n in want:
            p = os.path.join(UI, sub, n + ".svg")
            if not os.path.exists(p):
                lines.append(f"  FAIL {sub}/{n}.svg missing")
                bad += 1
                continue
            total_s += 1
            errs, got = v1.check(p, sub, n)
            txt = open(p, encoding="utf-8").read()
            if "<text" in txt or "<image" in txt or "<filter" in txt or "<mask" in txt:
                errs.append("forbidden tag text")
            if ("icons/items/" + n + ".svg") and man and f"{sub}/{n}.svg" not in man:
                errs.append("no manifest entry")
            status = "OK  " if not errs else "FAIL"
            if errs:
                bad += 1
            lines.append(f"  {status} {sub}/{n}.svg viewBox=\"{got}\" {os.path.getsize(p)} bytes" + ("" if not errs else "  -> " + "; ".join(sorted(set(errs)))))
    if "--determinism" in argv:
        lines.append("")
        lines.append("== determinism: re-render a sample and compare bytes ==")
        import build_raster
        sample = ["frames/panel_main", "slots/rarity_9", "hud/orb_frame_hp", "menu/title_logo", "tree/node_keystone_allocated"]
        before = {k: hashlib.sha1(open(os.path.join(UI, k + ".png"), "rb").read()).hexdigest() for k in sample}
        build_raster.build(sample, workers=5)
        for k in sample:
            h = hashlib.sha1(open(os.path.join(UI, k + ".png"), "rb").read()).hexdigest()
            same = h == before[k]
            if not same:
                bad += 1
            lines.append(f"  {'OK  ' if same else 'FAIL'} {k}.png sha1 {h[:12]} {'identical' if same else 'CHANGED'}")
    lines += ["", f"raster files checked: {total_r}; svg files checked: {total_s}; failures: {bad}", "RESULT: " + ("PASS" if bad == 0 else "FAIL")]
    os.makedirs(EVID, exist_ok=True)
    with open(os.path.join(EVID, "validation.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines if "FAIL" in l)[:4000])
    print("\n".join(lines[-2:]))
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
