"""bh-022: socket sprites drawn on item cells and tooltips.

  game/assets/ui/slots/socket_empty.png          an open socket: antique bronze bezel around a dark pit
  game/assets/ui/slots/socket_<family>_<g>.png   the bezel holding one crystal (8 families x 4 grades):
      g0 Fragment     a rough chipped shard
      g1 Shard        a long hexagonal crystal
      g2 Crystalline  an octagonal step-cut stone
      g3 Orbital      a round brilliant with star facets and a halo

Painted at 4x and reduced (64 px), deterministic, no third-party art. Family colours = DataCrystals.FAMILIES.
Run: python tools/ui_art/bh022_sockets.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "game", "assets", "ui", "slots"))

FAMILIES = {
    "ember": (1.0, 0.45, 0.16),
    "aqua": (0.25, 0.62, 1.0),
    "nova": (1.0, 0.9, 0.55),
    "thundra": (1.0, 0.92, 0.3),
    "vipera": (0.45, 0.95, 0.3),
    "bloodrift": (0.85, 0.1, 0.16),
    "essencerift": (0.45, 0.45, 1.0),
    "aetherift": (0.7, 0.95, 1.0),
}
# thundra and nova share a hue family: thundra reads as electric (cooler highlight, violet shadow)
SHADOW_TINT = {"thundra": (0.35, 0.25, 0.55), "nova": (0.6, 0.42, 0.12)}

SS = 4
SIZE = 64
N = SIZE * SS
C = N / 2.0


def rgb(c, k=1.0, a=255):
    return (max(0, min(255, int(c[0] * 255 * k))), max(0, min(255, int(c[1] * 255 * k))),
            max(0, min(255, int(c[2] * 255 * k))), a)


def mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def radial(size, inner, outer, r0, r1, center=None):
    """RGBA radial gradient disc from inner colour (r0) to outer colour (r1), transparent outside r1."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    cx, cy = center or (size / 2.0, size / 2.0)
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d > r1:
                continue
            t = 0.0 if d <= r0 else (d - r0) / max(1e-6, r1 - r0)
            px[x, y] = tuple(int(inner[i] * (1 - t) + outer[i] * t) for i in range(4))
    return im


def bezel():
    """Antique bronze setting: bevelled ring, darker lip, four claw prongs."""
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ro = N * 0.47
    ri = N * 0.34
    # drop shadow
    sh = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([C - ro + SS * 2, C - ro + SS * 3, C + ro + SS * 2, C + ro + SS * 3], fill=(0, 0, 0, 170))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(SS * 2)))
    # ring body with a top-left light
    ring = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    rp = ring.load()
    for y in range(N):
        for x in range(N):
            dx, dy = x + 0.5 - C, y + 0.5 - C
            d = math.hypot(dx, dy)
            if ri <= d <= ro:
                t = (d - ri) / (ro - ri)                     # 0 inner .. 1 outer
                bevel = math.sin(t * math.pi)                # raised middle
                light = (-dx - dy) / (d * 1.414 + 1e-6)      # +1 top-left
                base = mix((0.30, 0.20, 0.10), (0.78, 0.58, 0.30), 0.35 + 0.45 * bevel + 0.25 * light * bevel)
                k = 0.75 + 0.35 * bevel
                rp[x, y] = rgb(base, k)
    im.alpha_composite(ring)
    d = ImageDraw.Draw(im)
    d.ellipse([C - ro, C - ro, C + ro, C + ro], outline=(26, 16, 8, 255), width=SS * 2)
    d.ellipse([C - ri, C - ri, C + ri, C + ri], outline=(22, 14, 8, 255), width=SS * 2)
    return im


def prongs():
    """Four claw prongs at the diagonals, gripping over the stone's edge."""
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ri = N * 0.34
    for k in range(4):
        a = math.pi * 0.25 + k * math.pi * 0.5
        px, py = C + math.cos(a) * (ri - SS * 1.0), C + math.sin(a) * (ri - SS * 1.0)
        w = SS * 3.2
        d.ellipse([px - w, py - w, px + w, py + w], fill=(150, 112, 58, 255), outline=(30, 18, 8, 255), width=SS)
        d.ellipse([px - w * 0.45 - SS, py - w * 0.45 - SS, px + w * 0.1, py + w * 0.1], fill=(235, 205, 140, 200))
    return im


def pit():
    """The empty hollow inside the bezel."""
    ri = N * 0.345
    im = radial(N, (6, 6, 9, 255), (40, 34, 30, 255), ri * 0.2, ri)
    # inner shadow from the top-left rim
    sh = Image.new("L", (N, N), 0)
    ImageDraw.Draw(sh).ellipse([C - ri, C - ri, C + ri, C + ri], fill=255)
    off = Image.new("L", (N, N), 0)
    ImageDraw.Draw(off).ellipse([C - ri + SS * 4, C - ri + SS * 4, C + ri + SS * 4, C + ri + SS * 4], fill=255)
    rim = ImageChops.subtract(sh, off).filter(ImageFilter.GaussianBlur(SS * 2))
    dark = Image.new("RGBA", (N, N), (0, 0, 0, 255))
    dark.putalpha(rim.point(lambda v: int(v * 0.8)))
    im.alpha_composite(dark)
    return im


def facet_poly(draw, pts, col):
    draw.polygon([(C + x, C + y) for x, y in pts], fill=col)


def gem(family, grade):
    """One crystal, faceted by grade; light from the top-left."""
    base = FAMILIES[family]
    dark = mix(base, SHADOW_TINT.get(family, (0.05, 0.05, 0.1)), 0.55)
    dark = tuple(v * 0.45 for v in dark)
    lite = mix(base, (1, 1, 1), 0.55)
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    R = N * (0.27 + 0.02 * grade)
    if grade == 0:
        # rough chipped shard: an irregular pentagon split into lit and shaded halves
        pts = [(-0.55, -0.85), (0.5, -0.7), (0.85, 0.2), (0.15, 0.9), (-0.8, 0.35)]
        pts = [(x * R, y * R) for x, y in pts]
        facet_poly(d, pts, rgb(dark))
        facet_poly(d, [pts[0], pts[1], (0.1 * R, 0.05 * R), pts[4]], rgb(base, 0.95))
        facet_poly(d, [pts[0], pts[1], (0.05 * R, -0.35 * R)], rgb(lite))
        facet_poly(d, [pts[2], pts[3], (0.1 * R, 0.05 * R)], rgb(dark, 0.8))
    elif grade == 1:
        # long hexagonal crystal, tilted
        ang = -0.5
        pts = []
        for x, y in [(0, -1.0), (0.42, -0.55), (0.42, 0.55), (0, 1.0), (-0.42, 0.55), (-0.42, -0.55)]:
            xr = x * math.cos(ang) - y * math.sin(ang)
            yr = x * math.sin(ang) + y * math.cos(ang)
            pts.append((xr * R, yr * R))
        facet_poly(d, pts, rgb(dark))
        mid_top = ((pts[0][0] + pts[3][0]) * 0.5, (pts[0][1] + pts[3][1]) * 0.5)
        facet_poly(d, [pts[0], pts[5], pts[4], pts[3]], rgb(base))
        facet_poly(d, [pts[0], pts[5], (pts[5][0] * 0.3 + mid_top[0] * 0.7, pts[5][1] * 0.3 + mid_top[1] * 0.7)], rgb(lite))
        facet_poly(d, [pts[1], pts[2], pts[3], pts[0]], rgb(base, 0.62))
    elif grade == 2:
        # octagonal step cut: outer ring of facets, flat table
        outer = [(math.cos(math.pi / 8 + k * math.pi / 4) * R, math.sin(math.pi / 8 + k * math.pi / 4) * R) for k in range(8)]
        inner = [(x * 0.55, y * 0.55) for x, y in outer]
        for k in range(8):
            a = math.pi / 8 + (k + 0.5) * math.pi / 4
            light = -(math.cos(a) + math.sin(a)) / 1.414        # top-left facets bright
            col = mix(dark, lite, 0.5 + 0.5 * light)
            facet_poly(d, [outer[k], outer[(k + 1) % 8], inner[(k + 1) % 8], inner[k]], rgb(col))
        facet_poly(d, inner, rgb(base, 1.05))
        facet_poly(d, [inner[4], inner[5], inner[6], (0, 0)], rgb(lite, 1.0, 150))
    else:
        # round brilliant with star facets and a soft halo
        n = 12
        rim = [(math.cos(k * math.tau / n) * R, math.sin(k * math.tau / n) * R) for k in range(n)]
        star = [(math.cos((k + 0.5) * math.tau / n) * R * 0.62, math.sin((k + 0.5) * math.tau / n) * R * 0.62) for k in range(n)]
        table = [(math.cos(k * math.tau / 6 + 0.26) * R * 0.38, math.sin(k * math.tau / 6 + 0.26) * R * 0.38) for k in range(6)]
        facet_poly(d, star, rgb(mix(dark, base, 0.75)))
        for k in range(n):
            a = (k + 0.5) * math.tau / n
            light = -(math.cos(a) + math.sin(a)) / 1.414
            col = mix(dark, lite, 0.45 + 0.55 * light)
            facet_poly(d, [rim[k], rim[(k + 1) % n], star[k]], rgb(col))
            col2 = mix(dark, base, 0.7 + 0.3 * light)
            facet_poly(d, [star[k], rim[(k + 1) % n], star[(k + 1) % n]], rgb(col2))
        facet_poly(d, [(x * 1.25, y * 1.25) for x, y in table], rgb(base, 0.85))
        facet_poly(d, table, rgb(mix(base, (1, 1, 1), 0.25)))
    # specular glint and a clean dark edge
    g = N * 0.05
    gx, gy = C - R * 0.35, C - R * 0.4
    d.ellipse([gx - g, gy - g * 0.6, gx + g, gy + g * 0.6], fill=(255, 255, 255, 230))
    return im


def finish(im):
    return im.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    b = bezel()
    empty = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    empty.alpha_composite(b)
    empty.alpha_composite(pit())
    empty.alpha_composite(prongs())
    finish(empty).save(os.path.join(OUT, "socket_empty.png"))
    count = 1
    for fam in FAMILIES:
        for g in range(4):
            im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
            if g == 3:
                im.alpha_composite(radial(N, rgb(FAMILIES[fam], 1.0, 200), rgb(FAMILIES[fam], 1.0, 0), N * 0.3, N * 0.5))
            im.alpha_composite(b)
            im.alpha_composite(pit())
            im.alpha_composite(gem(fam, g))
            im.alpha_composite(prongs())
            if g == 3:
                # an Orbital lights its own setting: a coloured rim around the bezel
                rim = Image.new("RGBA", (N, N), (0, 0, 0, 0))
                ImageDraw.Draw(rim).ellipse([C - N * 0.47, C - N * 0.47, C + N * 0.47, C + N * 0.47],
                                            outline=rgb(FAMILIES[fam], 1.0, 230), width=SS * 3)
                im.alpha_composite(rim.filter(ImageFilter.GaussianBlur(SS)))
            finish(im).save(os.path.join(OUT, "socket_%s_%d.png" % (fam, g)))
            count += 1
    # preview sheet
    sheet = Image.new("RGBA", (SIZE * 9, SIZE * 4), (22, 20, 26, 255))
    for g in range(4):
        sheet.alpha_composite(Image.open(os.path.join(OUT, "socket_empty.png")), (0, g * SIZE))
        for i, fam in enumerate(FAMILIES):
            sheet.alpha_composite(Image.open(os.path.join(OUT, "socket_%s_%d.png" % (fam, g))), ((i + 1) * SIZE, g * SIZE))
    prev = os.environ.get("BH_SOCKET_PREVIEW")
    if prev:
        sheet.resize((SIZE * 9 * 3, SIZE * 4 * 3), Image.NEAREST).save(prev)
    print("sockets:", count)


if __name__ == "__main__":
    main()
