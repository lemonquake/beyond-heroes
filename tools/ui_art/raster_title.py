"""Hand-built vector letterforms for the BEYOND HEROES wordmark (Trajan-inspired capitals, no fonts).

Glyph units: cap height 1000, y down, baseline y=1000. Each glyph = dict(w=advance width, add=[polygons],
sub=[polygons], strokes=[(pts, widths)]). Rendered as SDF -> chiselled metal in raster_menu.title_logo.
"""
from __future__ import annotations

import math

from rast import bez3, bez2


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def serif(xs, y, side, top, length=48, t=26, br=48):
    """Bracketed serif on a stem edge at xs. side=-1 extends left, +1 right. top=True for cap-line serifs."""
    sgn = 1 if top else -1          # direction into the letter (down for top serifs)
    y_out = y                       # outer (cap or baseline)
    y_in = y + sgn * t              # inner face of the slab
    xe = xs + side * length
    pts = [(xs, y_out), (xe, y_out), (xe, y_in)]
    # concave bracket from the slab end back into the stem
    curve = bez2((xe, y_in), (xs, y_in), (xs, y_in + sgn * br), 10)
    pts += curve[1:]
    return pts


def bracket(xs, y_face, side, down=True, w=34, h=46):
    """Concave fillet between a slab face (y_face) and a stem edge at xs, extending `side` along the slab."""
    sgn = 1 if down else -1
    return [(xs, y_face), (xs + side * w, y_face)] + bez2((xs + side * w, y_face), (xs, y_face), (xs, y_face + sgn * h), 10)[1:]


def ell(cx, cy, rx, ry, rot=0.0, n=72):
    ca, sa = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


def G_B():
    top_o = [(135, 0), (400, 0)] + bez3((400, 0), (545, 0), (578, 110), (578, 232))[1:] + \
        bez3((578, 232), (578, 372), (470, 480), (340, 480))[1:] + [(135, 480)]
    top_c = [(210, 52), (378, 52)] + bez3((378, 52), (452, 52), (470, 150), (470, 238))[1:] + \
        bez3((470, 238), (470, 340), (430, 428), (360, 428))[1:] + [(210, 428)]
    bot_o = [(135, 468), (385, 468)] + bez3((385, 468), (565, 468), (628, 580), (628, 732))[1:] + \
        bez3((628, 732), (628, 900), (520, 1000), (362, 1000))[1:] + [(135, 1000)]
    bot_c = [(210, 520), (392, 520)] + bez3((392, 520), (478, 520), (516, 610), (516, 736))[1:] + \
        bez3((516, 736), (516, 882), (450, 948), (380, 948))[1:] + [(210, 948)]
    return dict(w=660, add=[rect(60, 0, 210, 1000), top_o, bot_o, serif(60, 0, -1, True), serif(60, 1000, -1, False)],
                sub=[top_c, bot_c])


def G_E():
    add = [rect(60, 0, 210, 1000), rect(150, 0, 500, 50), rect(150, 470, 420, 518), rect(150, 950, 540, 1000),
           [(462, 0), (505, 0), (516, 170), (500, 170), (470, 60)],                          # top beak
           [(405, 395), (425, 395), (430, 590), (410, 590), (400, 518)],                     # mid serif
           [(470, 950), (510, 810), (528, 810), (545, 1000), (480, 1000)],                   # bottom beak
           serif(60, 0, -1, True), serif(60, 1000, -1, False)]
    return dict(w=590, add=add, sub=[])


def G_Y():
    add = [[(40, 0), (192, 0), (398, 540), (246, 540)],
           [(548, 0), (606, 0), (396, 556), (338, 556)],
           rect(248, 520, 398, 1000),
           rect(0, 0, 232, 26), bracket(40, 26, -1), bracket(192, 26, 1, w=20, h=26),
           rect(500, 0, 650, 26),
           rect(178, 974, 468, 1000), bracket(248, 974, -1, False), bracket(398, 974, 1, False)]
    return dict(w=660, add=add, sub=[])


def G_O():
    return dict(w=800, add=[ell(400, 500, 372, 512)], sub=[ell(404, 500, 248, 452, rot=-0.16)])


def G_N():
    add = [[(52, 0), (198, 0), (668, 1012), (526, 1012)],
           rect(60, 20, 104, 1000), rect(620, 0, 664, 1000),
           rect(10, 0, 150, 26), rect(14, 974, 150, 1000), bracket(60, 974, -1, False, 30, 40), bracket(104, 974, 1, False, 30, 40),
           rect(570, 0, 712, 26), bracket(620, 26, -1, True, 30, 40), bracket(664, 26, 1, True, 30, 40)]
    return dict(w=730, add=add, sub=[])


def G_D():
    out = [(135, 0), (385, 0)] + bez3((385, 0), (622, 0), (725, 220), (725, 500))[1:] + \
        bez3((725, 500), (725, 780), (622, 1000), (385, 1000))[1:] + [(135, 1000)]
    cnt = [(210, 52), (372, 52)] + bez3((372, 52), (534, 52), (605, 250), (605, 500))[1:] + \
        bez3((605, 500), (605, 750), (534, 948), (372, 948))[1:] + [(210, 948)]
    return dict(w=780, add=[rect(60, 0, 210, 1000), out, serif(60, 0, -1, True), serif(60, 1000, -1, False)], sub=[cnt])


def G_H():
    add = [rect(60, 0, 210, 1000), rect(550, 0, 700, 1000), rect(210, 468, 550, 516)]
    for x0, x1 in ((60, 210), (550, 700)):
        add += [serif(x0, 0, -1, True), serif(x1, 0, 1, True), serif(x0, 1000, -1, False), serif(x1, 1000, 1, False)]
    return dict(w=760, add=add, sub=[])


def G_R():
    top_o = [(135, 0), (400, 0)] + bez3((400, 0), (552, 0), (590, 120), (590, 250))[1:] + \
        bez3((590, 250), (590, 400), (475, 510), (340, 510))[1:] + [(135, 510)]
    top_c = [(210, 52), (380, 52)] + bez3((380, 52), (458, 52), (480, 160), (480, 255))[1:] + \
        bez3((480, 255), (480, 370), (440, 460), (365, 460))[1:] + [(210, 460)]
    leg = [(318, 500), (446, 488)] + bez3((446, 488), (520, 700), (600, 900), (700, 985))[1:] + [(706, 1000), (560, 1000)] + \
        bez3((560, 1000), (500, 860), (430, 660), (318, 500))[1:-1]
    add = [rect(60, 0, 210, 1000), top_o, leg, serif(60, 0, -1, True), serif(60, 1000, -1, False), serif(210, 1000, 1, False)]
    return dict(w=720, add=add, sub=[top_c])


def G_S():
    spine = [(462, 128), (412, 42), (282, 22), (150, 62), (96, 190), (150, 330), (290, 440), (410, 540), (470, 690),
             (430, 880), (290, 978), (140, 962), (58, 870)]
    widths = [26, 44, 50, 78, 118, 140, 146, 142, 130, 84, 50, 44, 26]
    add = [[(448, 70), (470, 70), (478, 230), (462, 230)],        # top-right beak
           [(46, 780), (62, 780), (70, 944), (50, 944)]]           # bottom-left beak
    return dict(w=560, add=add, sub=[], strokes=[(spine, widths)])


GLYPHS = {"B": G_B, "E": G_E, "Y": G_Y, "O": G_O, "N": G_N, "D": G_D, "H": G_H, "R": G_R, "S": G_S}
