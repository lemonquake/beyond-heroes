"""Validate every UI SVG against the contract (bh-001 / ui_art.md) and write validation.txt.

Checks per file: parses as XML, root is <svg> with the expected viewBox, only ThorVG-safe elements are used,
no CSS/style/filter/mask/clip/text/image/external refs, every url(#id) resolves, and the full-bleed background rule
(skill/talent icons have one, item icons do not). Also checks that every contract file name exists.
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_all import UI, ROOT  # noqa: E402

EVID = os.path.join(ROOT, "work", "lemondev", "bh-001", "evidence", "ui_art")
NS = "{http://www.w3.org/2000/svg}"

EXPECTED = {
    "icons/skills": "cleave shield_bash leap_slam whirlwind war_cry judgment ground_fissure iron_bulwark firebolt frost_nova "
                    "chain_lightning blink meteor tidal_wave gale_burst arcane_surge shadow_curse radiant_ward stone_spear",
    "icons/talents": "crit fire_res sword_mastery block_mana crit_cooldown burning_spread frozen_impact armor vitality valor "
                     "heavy_hands bulwark counter momentum arcane_mind mana_flow elemental_focus conduit permafrost pyromancy "
                     "storm tides shadow radiance keystone_juggernaut keystone_unbreakable keystone_archmage "
                     "keystone_elemental_overload minor_str minor_agi minor_int minor_wis minor_spi minor_dex",
    "icons/items": "sword greatsword axe spear dagger bow staff wand shield helm_plate helm_hood inner_garment armor_plate "
                   "armor_robe gloves_plate gloves_cloth boots_plate boots_cloth ring amulet charm potion_health potion_mana "
                   "mat_iron_shard mat_arcane_dust mat_ember_core mat_bone_fragment gold",
    "icons/elements": "physical fire ice lightning earth wind water light dark",
    "icons/status": "burning chilled frozen shocked staggered wet cursed purged bleeding stunned valor arcane_charge guard "
                    "haste regen shielded",
    "icons/attributes": "strength agility intelligence wisdom spirit dexterity",
    "icons/classes": "knight mage",
    "emblem": "logo_emblem ornament_divider ornament_corner",
}
VIEWBOX = {"icons/classes": {"0 0 128 128", "0 0 256 256"}, "emblem/ornament_divider": {"0 0 512 32"},
           "emblem/ornament_corner": {"0 0 64 64"}, "emblem/logo_emblem": None}
ALLOWED = {"svg", "defs", "g", "path", "circle", "ellipse", "rect", "linearGradient", "radialGradient", "stop"}
FORBIDDEN_ATTR = {"style", "filter", "mask", "clip-path", "href", "{http://www.w3.org/1999/xlink}href", "class"}


def full_bleed(root):
    for el in root.iter():
        if el.tag == NS + "rect":
            try:
                if (float(el.get("x", 0)) <= 0 and float(el.get("y", 0)) <= 0 and float(el.get("width", 0)) >= 128
                        and float(el.get("height", 0)) >= 128 and el.get("fill", "none") != "none"):
                    return True
            except ValueError:
                pass
    return False


def check(path, sub, name):
    errs = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        return [f"XML parse error: {e}"], None
    root = tree.getroot()
    if root.tag != NS + "svg":
        errs.append(f"root is {root.tag}")
    vb = root.get("viewBox")
    if not vb:
        errs.append("missing viewBox")
    else:
        want = VIEWBOX.get(f"{sub}/{name}", VIEWBOX.get(sub, {"0 0 128 128"}))
        if want is not None and vb not in want:
            errs.append(f"viewBox {vb} not in {sorted(want)}")
    ids = {el.get("id") for el in root.iter() if el.get("id")}
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag not in ALLOWED:
            errs.append(f"forbidden element <{tag}>")
        for k, v in el.attrib.items():
            if k in FORBIDDEN_ATTR:
                errs.append(f"forbidden attribute {k} on <{tag}>")
            for ref in re.findall(r"url\(([^)]*)\)", v):
                if not ref.startswith("#") or ref[1:] not in ids:
                    errs.append(f"unresolved/external reference {ref}")
    if sub in ("icons/skills", "icons/talents") and not full_bleed(root):
        errs.append("skill/talent icon lacks a full-bleed background")
    if sub == "icons/items" and full_bleed(root):
        errs.append("item icon should have a transparent background")
    return errs, vb


def main():
    lines = ["UI art validation (tools/ui_art/validate.py)",
             "checks: XML parse, <svg> root, viewBox value, element whitelist " + ",".join(sorted(ALLOWED)) +
             ", no style/filter/mask/clip-path/href/class attributes, url(#id) refs resolve, background rule", ""]
    total = bad = 0
    for sub, names in EXPECTED.items():
        folder = os.path.join(UI, sub)
        present = sorted(x[:-4] for x in os.listdir(folder) if x.endswith(".svg")) if os.path.isdir(folder) else []
        want = names.split()
        missing = [n for n in want if n not in present]
        extra = [n for n in present if n not in want]
        lines.append(f"[{sub}] expected {len(want)}, present {len(present)}, missing {missing or 'none'}, extra {extra or 'none'}")
        if missing:
            bad += len(missing)
        for n in want:
            p = os.path.join(folder, n + ".svg")
            if not os.path.exists(p):
                continue
            total += 1
            errs, vb = check(p, sub, n)
            size = os.path.getsize(p)
            status = "OK  " if not errs else "FAIL"
            if errs:
                bad += 1
            lines.append(f"  {status} {n}.svg  viewBox=\"{vb}\"  {size} bytes" + ("" if not errs else "  -> " + "; ".join(sorted(set(errs)))))
    lines += ["", f"files checked: {total}; failures: {bad}", "RESULT: " + ("PASS" if bad == 0 else "FAIL")]
    os.makedirs(EVID, exist_ok=True)
    with open(os.path.join(EVID, "validation.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[-3:]))
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
