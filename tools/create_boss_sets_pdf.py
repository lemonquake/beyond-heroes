"""bh-022: the Boss Collections showcase PDF — every one of the fifteen sets as the game renders it, its pieces, and the
bonuses a hero is guaranteed for wearing it.

Inputs (all generated, see docs/BOSS_SETS.md):
  work/lemondev/bh-022/evidence/sets/<set>-front.png / -back.png   game/tests/tools/capture_boss_sets.tscn (--theme=)
  work/lemondev/bh-022/evidence/sets/all-15-front.png              the same capture, all sets
  game/assets/ui/icons/items3d/boss_<set>_<slot>.png                the item icons (tools/blender/items/boss_regalia.py)
Set data is read from game/src/data/data_boss_sets.gd so the PDF cannot drift from the game.

  python tools/create_boss_sets_pdf.py   ->  output/pdf/Beyond-Heroes-Boss-Collections.pdf
"""
from pathlib import Path
import re
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[1]
SETS_DIR = ROOT / "work/lemondev/bh-022/evidence/sets"
ICONS = ROOT / "game/assets/ui/icons/items3d"
OUT = ROOT / "output/pdf/Beyond-Heroes-Boss-Collections.pdf"

SRC = (ROOT / "game/src/data/data_boss_sets.gd").read_text(encoding="utf-8")
ROWS = re.findall(r'\["([a-z_]+)", "([^"]+)", "([a-z]+)", "([a-z]+)", Elements\.([A-Z]+), "([a-z_]+)", ([0-9.]+), "([^"]+)"\]', SRC)
assert len(ROWS) == 15, len(ROWS)
TWO_HANDED = {"bow", "crossbow", "staff", "spear", "greatsword"}
CLASS_NAMES = {"knight": "Knight", "ranger": "Ranger", "mage": "Mage", "shadowblade": "Shadowblade"}
THREE = {
    "knight": "+10% Defense and +8% maximum health",
    "ranger": "+12% projectile damage and +25 Accuracy",
    "mage": "+10% maximum Mana and +8% cast speed",
    "shadowblade": "+8% attack speed and +12% Evasion",
}
SLOT_LABELS = [("main_weapon", "Weapon"), ("sub_weapon", "Shield"), ("helm", "Crown"), ("inner_garment", "Vestment"),
               ("armor", "Armor"), ("gloves_1", "Left Gauntlet"), ("gloves_2", "Right Gauntlet"), ("boots_1", "Left Greave"),
               ("boots_2", "Right Greave"), ("accessory_1", "Signet"), ("accessory_2", "Seal"), ("accessory_3", "Pendant"),
               ("accessory_4", "Brooch")]
ACCENT = {  # the sets' glow colours (boss_regalia.SETS)
    "dragonforge": "#ff6a24", "truth_of_raikuru": "#6fe4ff", "crimson_glory": "#ffb060", "grievance_of_the_fairy": "#b8ff8a",
    "wailing_mistress": "#c490ff", "winter_court": "#8eeaff", "sunken_crown": "#62f0d8", "thunder_abbot": "#88c0ff",
    "ashfall_pilgrim": "#ff7040", "starfall_hunter": "#aebcff", "gale_nomad": "#8af4f4", "obsidian_oath": "#ec8ad0",
    "pale_requiem": "#90c0ff", "serpent_veil": "#a8f878", "eclipse_dancer": "#c49aff",
}
LORE = {
    "dragonforge": "Scale-forged plate from the furnaces under Emberhal, horned like the beast whose hide it copies.",
    "truth_of_raikuru": "A marksman's harness of white steel, crowned with the storm-halo of the Raikuru shrine.",
    "crimson_glory": "Crimson enamel and sunburst gold, worn by the champions who held the Dawn Gate.",
    "grievance_of_the_fairy": "Leaf-plate and a circlet of antler twigs; four jewelled wings still remember the wood.",
    "wailing_mistress": "A violet cowl under a silver halo, hung with tears that never finish falling.",
    "winter_court": "The frost-crown and fur mantle of the court that ruled the Rimeglass barrows.",
    "sunken_crown": "Verdigris plate from a drowned throne: trident crown, coral horns and fin guards.",
    "thunder_abbot": "The abbot's cowl, circled by twin rings and orbs that hum before every storm.",
    "ashfall_pilgrim": "A wide pilgrim's hat and ash-grey robes, an ember badge that never cools.",
    "starfall_hunter": "Midnight leather and blued plate studded with stars, for hunters who work by night.",
    "gale_nomad": "Desert wraps, a veil against the sand, feathered fittings that sing in the wind.",
    "obsidian_oath": "Black glass plate crowned with shards, its eye-slit burning rose.",
    "pale_requiem": "A pale hood with bone antlers; the mourner's harness of the Requiem.",
    "serpent_veil": "Scaled leather under a cobra's hood, a serpent coiled over the brow.",
    "eclipse_dancer": "Violet harness and silver crescents, an eclipse halo behind the dancer's head.",
}

for name, file in [("Body", "segoeui.ttf"), ("Bold", "segoeuib.ttf"), ("Serif", "georgia.ttf"), ("SerifBold", "georgiab.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / file)))

W, H = landscape(A4)
BG = colors.HexColor("#14171d")
PANEL = colors.HexColor("#1d222b")
GOLD = colors.HexColor("#e2c07a")
PARCH = colors.HexColor("#e8dcc0")
MUTED = colors.HexColor("#9aa3ad")


def para(text, font="Body", size=10.5, color=PARCH, leading=None):
    return Paragraph(text, ParagraphStyle("p", fontName=font, fontSize=size, leading=leading or size * 1.38, textColor=color))


def draw_para(c, text, x, y_top, w, **kw):
    p = para(text, **kw)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y_top - h)
    return h


def crop_figure(path, pad=24):
    """The capture's character and its plinth, trimmed of empty background and of the name label under it."""
    im = Image.open(path).convert("RGB")
    body = im.crop((0, 0, im.width, int(im.height * 0.86)))
    g = body.convert("L").point(lambda v: 255 if v > 40 else 0)
    l, t, r, b = g.getbbox() or (0, 0, im.width, im.height)
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(body.height, b + pad)))


def page_bg(c):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#3a3322"))
    c.setLineWidth(1.2)
    c.rect(14, 14, W - 28, H - 28, fill=0, stroke=1)


def footer(c, n):
    c.setFont("Body", 8)
    c.setFillColor(MUTED)
    c.drawString(28, 22, "Beyond Heroes · Boss Collections")
    c.drawRightString(W - 28, 22, str(n))


def cover(c):
    page_bg(c)
    c.setFont("SerifBold", 34)
    c.setFillColor(GOLD)
    c.drawString(40, H - 70, "The Fifteen Boss Collections")
    draw_para(c, "Every collection drops only from actual bosses of level 30 or higher (dungeon lords, their Usurpers and the named "
                 "Depth Guardians): one piece per victory, weighted toward the sets you have started and the pieces you are missing. "
                 "All pieces are <b>Master</b> rarity and require level 30 and 32 of the class's principal attribute.",
              40, H - 84, W - 80, size=11)
    lineup = SETS_DIR / "all-15-front.png"
    if lineup.exists():
        im = Image.open(lineup).convert("RGB")
        iw, ih = im.size
        tw = W - 80
        th = tw * ih / iw
        th = min(th, H - 200)
        tw = th * iw / ih
        c.drawImage(ImageReader(im), (W - tw) / 2, 50, tw, th)
    footer(c, 1)


def bonus_page(c):
    page_bg(c)
    c.setFont("SerifBold", 24)
    c.setFillColor(GOLD)
    c.drawString(40, H - 60, "Guaranteed set bonuses")
    y = H - 80
    y -= draw_para(c, "Bonuses build up as you wear more distinct pieces of one collection. Duplicate copies of a piece never count "
                      "twice; removing a piece updates the bonuses at once. Individual pieces also roll their normal Master affixes, "
                      "and every piece can hold sockets and crystals.", 40, y, W - 80, size=11) + 14
    rows = [("3 pieces", "By the collection's class: " + "; ".join("<b>%s</b> %s" % (CLASS_NAMES[k], v) for k, v in THREE.items()) + "."),
            ("6 pieces", "+12% damage and +6% resistance for the collection's element."),
            ("Full collection", "The collection's own effect (13 pieces with a shield, 12 for two-handed collections): listed on each page.")]
    for head, text in rows:
        c.setFillColor(PANEL)
        h = para(text, size=10.5).wrap(W - 260, 1000)[1] + 14
        c.roundRect(40, y - h, W - 80, h, 6, fill=1, stroke=0)
        c.setFont("Bold", 12.5)
        c.setFillColor(GOLD)
        c.drawString(56, y - 18, head)
        draw_para(c, text, 200, y - 7, W - 260, size=10.5)
        y -= h + 6
    y -= 6
    c.setFont("Bold", 13)
    c.setFillColor(GOLD)
    c.drawString(40, y - 14, "Collection odds")
    draw_para(c, "Random set selection favours your class (2x) and any collection you own but have not finished (4x); within the set, "
                 "each missing piece is 6x as likely as one you already own. Every set stays possible for every hero; duplicates can "
                 "still happen. Ownership counts your bag, worn gear, bound Tempos, the Spirit Hall, pending recovery and the Hero's Vault.",
              40, y - 22, W - 80, size=11)
    # every full-set effect at a glance
    y = 32 + 5 * 37 + 16
    c.setFont("Bold", 13)
    c.setFillColor(GOLD)
    c.drawString(40, y, "Full-set effects at a glance")
    y -= 8
    colw = (W - 90) / 3
    for i, row in enumerate(ROWS):
        sid, name, cls, weapon, element, flag, value, effect = row
        cx = 40 + (i % 3) * (colw + 5)
        cy = y - (i // 3) * 37
        c.setFillColor(PANEL)
        c.roundRect(cx, cy - 34, colw, 33, 4, fill=1, stroke=0)
        c.setFont("Bold", 9.5)
        c.setFillColor(colors.HexColor(ACCENT[sid]))
        c.drawString(cx + 8, cy - 12, name)
        c.setFont("Body", 7.6)
        c.setFillColor(MUTED)
        c.drawRightString(cx + colw - 8, cy - 12, "%s · %s" % (CLASS_NAMES[cls], element.capitalize()))
        draw_para(c, escape(effect), cx + 8, cy - 15, colw - 16, size=7.9, leading=9.4)
    footer(c, 2)


def set_page(c, n, row):
    sid, name, cls, weapon, element, flag, value, effect = row
    accent = colors.HexColor(ACCENT[sid])
    page_bg(c)
    # the figure, front and back
    fx, fy, fw, fh = 34, 40, 380, H - 80
    c.setFillColor(colors.HexColor("#15191f"))   # the capture's own background
    c.roundRect(fx, fy, fw, fh, 8, fill=1, stroke=0)
    for i, side in enumerate(("front", "back")):
        p = SETS_DIR / ("%s-%s.png" % (sid, side))
        if not p.exists():
            continue
        im = crop_figure(p)
        iw, ih = im.size
        cw, ch = fw / 2 - 8, fh - 16
        s = min(cw / iw, ch / ih)
        c.drawImage(ImageReader(im), fx + 6 + i * (fw / 2) + (cw - iw * s) / 2, fy + 8 + (ch - ih * s) / 2, iw * s, ih * s)
    # the text column
    x = fx + fw + 26
    tw = W - x - 36
    c.setFont("SerifBold", 28)
    c.setFillColor(accent)
    c.drawString(x, H - 66, name)
    c.setFont("Bold", 11.5)
    c.setFillColor(GOLD)
    two = weapon in TWO_HANDED
    c.drawString(x, H - 86, "%s  ·  %s  ·  %s  ·  %d pieces" % (CLASS_NAMES[cls], weapon.capitalize(), element.capitalize(), 12 if two else 13))
    y = H - 98
    y -= draw_para(c, "<i>%s</i>" % escape(LORE[sid]), x, y, tw, size=10.5, color=MUTED) + 12
    # guaranteed effects
    effects = [("3 pieces", THREE[cls] + "."),
               ("6 pieces", "+12%% %s damage and +6%% %s resistance." % (element.capitalize(), element.capitalize())),
               ("Full set", effect)]
    for head, text in effects:
        h = para(escape(text), size=11).wrap(tw - 110, 1000)[1] + 16
        c.setFillColor(PANEL)
        c.roundRect(x, y - h, tw, h, 5, fill=1, stroke=0)
        c.setFillColor(accent if head == "Full set" else GOLD)
        c.setFont("Bold", 11.5)
        c.drawString(x + 12, y - 17, head)
        draw_para(c, escape(text), x + 100, y - 7, tw - 110, size=11, color=PARCH if head != "Full set" else colors.white)
        y -= h + 6
    # the pieces
    y -= 10
    c.setFont("Bold", 12)
    c.setFillColor(GOLD)
    c.drawString(x, y - 12, "The pieces")
    y -= 22
    slots = [s for s in SLOT_LABELS if not (two and s[0] == "sub_weapon")]
    cols = 7
    cell = min(64.0, (tw - (cols - 1) * 6) / cols)
    for i, (slot, label) in enumerate(slots):
        cx = x + (i % cols) * (cell + 6)
        cy = y - (i // cols) * (cell + 24) - cell
        c.setFillColor(colors.HexColor("#252b35"))
        c.roundRect(cx, cy, cell, cell, 4, fill=1, stroke=0)
        ic = ICONS / ("boss_%s_%s.png" % (sid, slot))
        if ic.exists():
            c.drawImage(ImageReader(str(ic)), cx + 2, cy + 2, cell - 4, cell - 4, mask="auto")
        c.setFont("Body", 7.4)
        c.setFillColor(MUTED)
        c.drawCentredString(cx + cell / 2, cy - 10, label)
    footer(c, n)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H))
    c.setTitle("Beyond Heroes: The Fifteen Boss Collections")
    c.setAuthor("Beyond Heroes")
    cover(c)
    c.showPage()
    bonus_page(c)
    c.showPage()
    for i, row in enumerate(ROWS):
        set_page(c, i + 3, row)
        c.showPage()
    c.save()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
