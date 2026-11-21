#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There (make.fun).

Renders a single 1024x1024 PNG: an open passport spread for the
invented Republic of the Kalden Isles, a small North Atlantic
archipelago.  The left leaf is the data page (vector portrait,
bilingual Kalden/English fields, machine-readable zone with genuine
ICAO check digits).  The right leaf is the visas leaf: entry/exit
stamps from neighbouring Nordic ports, a transit visa, and the
endorsement that gives the place away -- inter-island ferry tolls
are free for holders, and they travel visa-free around the North
Atlantic, provided they declare any fish they land abroad.

Written from scratch for this session.  Deterministic, no network,
no randomness; only Pillow and the system DejaVu / Liberation fonts.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
OUT = os.environ.get("ENTRY_OUT", "/output/entry.png")

DEJAVU = "/usr/share/fonts/truetype/dejavu"
LIBER = "/usr/share/fonts/truetype/liberation"


def load(path, size):
    """Load a TTF, falling back to Pillow's built-in bitmap font."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


# -- type scale -------------------------------------------------------------
F_BIG = load(f"{DEJAVU}/DejaVuSerif-Bold.ttf", 19)
F_MID = load(f"{DEJAVU}/DejaVuSerif-Bold.ttf", 15)
F_CAP = load(f"{DEJAVU}/DejaVuSans-Bold.ttf", 13)
F_LAB = load(f"{DEJAVU}/DejaVuSans.ttf", 11)
F_DAT = load(f"{DEJAVU}/DejaVuSans-Bold.ttf", 17)
F_DAT2 = load(f"{DEJAVU}/DejaVuSans-Bold.ttf", 15)
F_TXT = load(f"{DEJAVU}/DejaVuSans.ttf", 11)
F_MIN = load(f"{DEJAVU}/DejaVuSans.ttf", 9)
F_MRZ = load(f"{DEJAVU}/DejaVuSansMono.ttf", 17)
F_SIGN = load(f"{LIBER}/LiberationSerif-Italic.ttf", 25)
F_ST = load(f"{DEJAVU}/DejaVuSans-Bold.ttf", 13)
F_ST2 = load(f"{DEJAVU}/DejaVuSans-Bold.ttf", 10)
F_ST3 = load(f"{DEJAVU}/DejaVuSans.ttf", 9)
F_ST4 = load(f"{DEJAVU}/DejaVuSans.ttf", 8)

# -- palette ----------------------------------------------------------------
CREAM = (248, 243, 228)
CREAM_R = (243, 237, 217)
COVER = (56, 50, 42)
INK = (26, 40, 68)
NAVY = (20, 50, 90)
GILT = (168, 126, 54)
MUTE = (98, 94, 82)
RULE_C = (152, 142, 120)
SKY = (207, 215, 221)


def shade(c1, c2, t):
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def text_lines(draw, text, font, width):
    """Greedy word wrap, returns a list of lines fitting `width`."""
    out, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


# -- ICAO machine-readable zone ---------------------------------------------
def icao_check(field):
    """TD3 check digit: values A=10..Z=35, '<'=0, weights 7/3/1."""
    total = 0
    for i, ch in enumerate(field):
        if ch == "<":
            val = 0
        elif ch.isdigit():
            val = int(ch)
        else:
            val = ord(ch) - 55
        total += val * (7, 3, 1)[i % 3]
    return str(total % 10)


def mrz_pair():
    top = "P<KLDHALVORSEN<<INGRID<MARIE"
    top = top + "<" * (44 - len(top))
    doc = "0048217<<"                       # document number + filler
    dob, sex, exp = "940314", "F", "360601"  # 14 Mar 1994 / 01 Jun 2036
    optional = "<" * 14
    line2 = (doc + icao_check(doc) + "KLD" + dob + icao_check(dob)
             + sex + exp + icao_check(exp) + optional + icao_check(optional))
    # Composite check digit (ICAO 9303): over doc+cd, dob+cd, exp+cd,
    # optional+cd only -- nationality and sex are NOT part of it.
    composite = (doc + icao_check(doc) + dob + icao_check(dob)
                 + exp + icao_check(exp) + optional + icao_check(optional))
    bottom = line2 + icao_check(composite)
    assert len(top) == 44 and len(bottom) == 44
    return top, bottom


# -- coat of arms ------------------------------------------------------------
def crest(draw, cx, cy, s):
    """Shield with three sea-waves under a four-point north star."""
    pts = [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy + s * 0.45),
           (cx, cy + s * 1.2), (cx - s, cy + s * 0.45)]
    draw.polygon(pts, outline=GILT, width=3)
    inner = [(cx - s + 5, cy - s + 5), (cx + s - 5, cy - s + 5),
             (cx + s - 5, cy + s * 0.45 - 2), (cx, cy + s - 5),
             (cx - s + 5, cy + s * 0.45 - 2)]
    draw.polygon(inner, fill=(229, 233, 239))
    for k, wy in enumerate((-0.3, 0.05, 0.4)):
        wave = [(x, cy + s * wy + 3 * math.sin((x - cx) / 9.0 + k))
                for x in range(cx - s + 9, cx + s - 7, 4)]
        draw.line(wave, fill=NAVY, width=2)
    draw.polygon([(cx, cy - s), (cx + 3, cy - s * 0.66), (cx, cy - s * 0.48),
                  (cx - 3, cy - s * 0.66)], fill=GILT)


def guilloche(draw, x0, y0, x1, y1, colour, gap=7):
    """Faint wavy security print."""
    for yy in range(y0, y1, gap):
        pts = [(x, yy + 2 * math.sin((x - x0) / 44.0))
               for x in range(x0, x1 + 1, 8)]
        draw.line(pts, fill=colour, width=1)


# -- portrait ----------------------------------------------------------------
def photo(draw, x0, y0, x1, y1):
    """Flat vector passport portrait: woman, centre-parted dark hair,
    navy coat, plain grey-blue backdrop."""
    cx = (x0 + x1) // 2
    w, h = x1 - x0, y1 - y0
    for y in range(y0, y1):
        t = (y - y0) / max(1, h)
        draw.line([(x0, y), (x1, y)], fill=shade((216, 223, 228), (184, 194, 204), t))
    skin, skin_d, skin_l = (217, 173, 137), (199, 153, 119), (229, 189, 153)
    hair, hair_d = (90, 54, 36), (68, 40, 26)
    coat = (40, 54, 80)
    # coat and shoulders
    draw.pieslice([cx - 90, y1 - 120, cx + 90, y1 + 42], 180, 360, fill=coat)
    draw.rectangle([x0, y1 - 44, x1, y1], fill=coat)
    # white shirt V and collar
    draw.polygon([(cx - 27, y1 - 54), (cx + 27, y1 - 54), (cx, y1 - 6)],
                 fill=(241, 239, 231))
    draw.polygon([(cx - 31, y1 - 60), (cx - 9, y1 - 35), (cx - 2, y1 - 54)],
                 fill=(227, 225, 217))
    draw.polygon([(cx + 31, y1 - 60), (cx + 9, y1 - 35), (cx + 2, y1 - 54)],
                 fill=(227, 225, 217))
    # neck
    draw.rectangle([cx - 21, y1 - 110, cx + 21, y1 - 54], fill=skin_d)
    draw.rectangle([cx - 21, y1 - 110, cx + 21, y1 - 97], fill=(191, 145, 111))
    # head
    hx0, hy0, hx1, hy1 = cx - 53, y0 + 28, cx + 53, y0 + 150
    # hair mass behind the head, falling to the shoulders
    draw.pieslice([hx0 - 12, hy0 - 18, hx1 + 12, hy0 + 80], 180, 360, fill=hair)
    draw.rounded_rectangle([hx0 - 11, hy0 + 56, hx0 - 3, y0 + 168], radius=4, fill=hair)
    draw.rounded_rectangle([hx1 + 3, hy0 + 56, hx1 + 11, y0 + 168], radius=4, fill=hair)
    draw.ellipse([hx0, hy0, hx1, hy1], fill=skin)
    # cheek light
    draw.ellipse([hx0 + 7, hy0 + 64, hx0 + 35, hy0 + 98], fill=skin_l)
    draw.ellipse([hx1 - 35, hy0 + 64, hx1 - 7, hy0 + 98], fill=skin_l)
    # ears
    draw.ellipse([hx0 - 9, hy0 + 60, hx0 + 7, hy0 + 90], fill=skin)
    draw.ellipse([hx1 - 7, hy0 + 60, hx1 + 9, hy0 + 90], fill=skin)
    # fringe, swept to the sides from a centre part
    draw.pieslice([hx0 - 7, hy0 - 12, hx1 + 7, hy0 + 68], 180, 332, fill=hair)
    draw.pieslice([hx0 - 7, hy0 - 12, hx1 + 7, hy0 + 68], 196, 346, fill=hair_d)
    draw.line([(cx, hy0 + 2), (cx, hy0 + 28)], fill=hair_d, width=2)
    # brows
    draw.arc([cx - 35, hy0 + 58, cx - 9, hy0 + 74], 200, 340, fill=(72, 46, 32), width=3)
    draw.arc([cx + 9, hy0 + 58, cx + 35, hy0 + 74], 200, 340, fill=(72, 46, 32), width=3)
    # eyes: white, iris, pupil, highlight, and a short lash arc above
    for ex in (cx - 22, cx + 22):
        draw.ellipse([ex - 11, hy0 + 76, ex + 11, hy0 + 90], fill=(246, 243, 237))
        draw.ellipse([ex - 5, hy0 + 77, ex + 5, hy0 + 89], fill=(98, 68, 46))
        draw.ellipse([ex - 2, hy0 + 80, ex + 2, hy0 + 86], fill=(22, 18, 16))
        draw.ellipse([ex + 2, hy0 + 78, ex + 5, hy0 + 81], fill=(255, 255, 255))
        draw.arc([ex - 11, hy0 + 72, ex + 11, hy0 + 86], 200, 340,
                 fill=(72, 46, 32), width=2)
    # nose and mouth: one gentle closed-lip curve
    draw.line([(cx + 1, hy0 + 90), (cx - 2, hy0 + 110)], fill=skin_d, width=2)
    draw.arc([cx - 6, hy0 + 106, cx + 8, hy0 + 116], 0, 180, fill=skin_d, width=2)
    draw.arc([cx - 13, hy0 + 118, cx + 13, hy0 + 132], 0, 180, fill=(166, 98, 86), width=2)
    draw.arc([hx0 + 9, hy0 + 98, hx1 - 9, hy1 - 2], 20, 160, fill=skin_d, width=2)


# -- rubber stamps ------------------------------------------------------------
def round_stamp(img, cx, cy, r, ink, top, mid, bot, tilt=0):
    """Circular border-control stamp, drawn on a transparent layer and
    rotated so it sits slightly askew like a real hand stamp."""
    size = r * 2 + 26
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    col = ink + (212,)
    c = size // 2
    ld.ellipse([c - r, c - r, c + r, c + r], outline=col, width=3)
    ld.ellipse([c - r + 9, c - r + 9, c + r - 9, c + r - 9], outline=col, width=1)
    y = c - r + 20
    for lines, step in ((top, 13), (mid, 15), (bot, 13)):
        for txt, fnt in lines:
            use = fnt
            # Top lines sit near the circle's edge, where the chord is
            # narrow: shrink the font until the line fits inside it.
            if lines is top:
                dy = abs((y + 6) - c)
                chord = 2 * math.sqrt(max(1, r * r - dy * dy)) - 8
                for cand in (F_ST, F_ST2, F_ST3, F_ST4):
                    if ld.textlength(txt, font=cand) <= chord:
                        use = cand
                        break
                else:
                    use = F_ST4
            tw = ld.textlength(txt, font=use)
            ld.text((c - tw / 2, y), txt, font=use, fill=col)
            y += step
    layer = layer.rotate(tilt, resample=Image.BICUBIC, center=(c, c))
    img.paste(layer, (cx - size // 2, cy - size // 2), layer)


def box_stamp(img, x, y, w, h, ink, title, rows, tilt=0):
    layer = Image.new("RGBA", (w + 26, h + 26), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    col = ink + (212,)
    ld.rectangle([11, 11, 11 + w, 11 + h], outline=col, width=3)
    ld.line([(11, 35), (11 + w, 35)], fill=col, width=1)
    title_fnt = F_ST
    for cand in (F_ST, F_ST2, F_ST3):
        if ld.textlength(title, font=cand) <= w - 10:
            title_fnt = cand
            break
    tw = ld.textlength(title, font=title_fnt)
    ld.text((11 + (w - tw) / 2, 15), title, font=title_fnt, fill=col)
    yy = 43
    for row in rows:
        tw = ld.textlength(row, font=F_ST2)
        ld.text((11 + (w - tw) / 2, yy), row, font=F_ST2, fill=col)
        yy += 15
    layer = layer.rotate(tilt, resample=Image.BICUBIC)
    img.paste(layer, (x - 13, y - 13), layer)


# -- the spread ---------------------------------------------------------------
def build():
    img = Image.new("RGB", (SIZE, SIZE), COVER)
    d = ImageDraw.Draw(img)
    # two cream leaves, dark gutter between them
    d.rectangle([6, 6, 1018, 1018], fill=CREAM)
    d.rectangle([6, 6, 508, 1018], fill=CREAM)
    d.rectangle([516, 6, 1018, 1018], fill=CREAM_R)
    d.rectangle([508, 6, 516, 1018], fill=(122, 112, 94))
    d.line([(512, 6), (512, 1018)], fill=(92, 84, 68), width=1)

    # =============== LEFT LEAF: DATA PAGE ===============
    d.text((34, 26), "REPUBLIC OF THE KALDEN ISLES", font=F_BIG, fill=NAVY)
    d.text((34, 61), "VEGABRÉF  ·  PASSPORT  ·  PASSEPORT", font=F_MID, fill=GILT)
    d.line([(34, 89), (484, 89)], fill=RULE_C, width=2)
    crest(d, 462, 50, 18)

    # type / code / number
    for x, lab, val in ((34, "TYPE / TEGUND", "P"),
                        (150, "CODE / LAND", "KLD"),
                        (282, "PASSPORT No. / NÚMER", "0048217")):
        d.text((x, 101), lab, font=F_LAB, fill=MUTE)
        d.text((x, 115), val, font=F_DAT, fill=INK)

    # portrait
    photo(d, 34, 152, 206, 374)
    d.rectangle([34, 152, 206, 374], outline=INK, width=2)
    d.text((34, 380), "PHOTO / MYND", font=F_MIN, fill=MUTE)

    # faint ghost portrait behind the data fields
    ghost = Image.new("RGBA", (132, 132), (0, 0, 0, 0))
    photo(ImageDraw.Draw(ghost), 8, 0, 124, 132)
    ghost.putalpha(ghost.split()[3].point(lambda a: a // 18))
    img.paste(ghost, (346, 170), ghost)
    d = ImageDraw.Draw(img)

    # data fields
    fields = [
        ("SURNAME / EFTIRNAFN", "HALVORSEN"),
        ("GIVEN NAMES / FORNÖFN", "INGRID MARIE"),
        ("NATIONALITY / ÞJÓÐERNI", "KALDEN"),
        ("DATE OF BIRTH / FÆÐINGARDAGUR", "14 MAR 1994"),
        ("PLACE OF BIRTH / FÆÐINGARSTAÐUR", "NORHAVN"),
        ("SEX / KYN", "F"),
    ]
    y = 152
    for lab, val in fields:
        d.text((226, y), lab, font=F_LAB, fill=MUTE)
        d.text((226, y + 14), val, font=F_DAT, fill=INK)
        y += 40

    # holder's signature
    d.text((34, 398), "HOLDER'S SIGNATURE / UNDIRSKRIFT", font=F_LAB, fill=MUTE)
    d.text((34, 412), "Ingrid Halvorsen", font=F_SIGN, fill=(42, 42, 62))
    d.line([(34, 446), (302, 446)], fill=RULE_C, width=1)

    # issue / expiry / authority
    d.text((34, 464), "DATE OF ISSUE / ÚTGÁFUDAGUR", font=F_LAB, fill=MUTE)
    d.text((34, 478), "02 JUN 2026", font=F_DAT, fill=INK)
    d.text((236, 464), "DATE OF EXPIRY / GILDISTÍMI", font=F_LAB, fill=MUTE)
    d.text((236, 478), "01 JUN 2036", font=F_DAT, fill=INK)
    d.text((34, 508), "AUTHORITY / YFIRVALD", font=F_LAB, fill=MUTE)
    d.text((34, 522), "PASSPORT OFFICE — NORHAVN", font=F_DAT2, fill=INK)

    # authority round stamp, overlapping the note line
    round_stamp(img, 448, 548, 46, (32, 82, 162),
                [("PASSPORT OFFICE", F_ST3)],
                [("NORHAVN", F_ST), ("02 JUN 2026", F_ST2)],
                [("KALDEN ISLES", F_ST3)], tilt=-8)
    d = ImageDraw.Draw(img)
    d.text((34, 550), "The bearer is a citizen of the Republic of the", font=F_TXT, fill=INK)
    d.text((34, 566), "Kalden Isles and is entitled to its protection abroad.",
           font=F_TXT, fill=INK)

    # machine-readable zone
    d.rectangle([28, 598, 490, 670], fill=(239, 235, 221))
    l1, l2 = mrz_pair()
    d.text((36, 606), l1, font=F_MRZ, fill=INK)
    d.text((36, 634), l2, font=F_MRZ, fill=INK)
    d.text((34, 678), "P<KLD  ·  Machine-readable zone — please do not fold",
           font=F_MIN, fill=MUTE)
    guilloche(d, 28, 702, 490, 762, (201, 193, 169))
    d.text((470, 988), "2", font=F_TXT, fill=MUTE)

    # =============== RIGHT LEAF: VISAS & STAMPS ===============
    d.text((544, 26), "VISAS", font=F_BIG, fill=NAVY)
    d.text((544, 63), "VEGABRÉF — ENDORSEMENTS & ENTRY STAMPS", font=F_MID, fill=GILT)
    d.line([(544, 89), (994, 89)], fill=RULE_C, width=2)

    # faint crest watermark
    wm = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    crest(ImageDraw.Draw(wm), 150, 150, 92)
    wm.putalpha(wm.split()[3].point(lambda a: a // 14))
    img.paste(wm, (620, 382), wm)
    d = ImageDraw.Draw(img)

    # Travel history -- every stamp is dated after the 02 JUN 2026 issue.
    round_stamp(img, 662, 202, 74, (32, 82, 162),
                [("FAROE ISLANDS", F_ST)],
                [("TÓRSHAVN", F_ST), ("ENTRY", F_ST2)],
                [("18 JUL 2026", F_ST2)], tilt=-10)
    round_stamp(img, 882, 212, 74, (170, 46, 46),
                [("ICELAND", F_ST)],
                [("KEFLAVÍK", F_ST), ("ENTRY", F_ST2)],
                [("03 SEP 2026", F_ST2)], tilt=7)
    box_stamp(img, 580, 302, 202, 110, (38, 98, 68),
              "TRANSIT VISA — SVALBARD",
              ["Single entry · 30 days", "Valid 21 OCT – 20 NOV 2026",
               "Fee paid: 450 kr · No. SV-2214"], tilt=-3)
    round_stamp(img, 892, 382, 66, (32, 82, 162),
                [("NORWAY", F_ST)],
                [("BERGEN", F_ST), ("EXIT", F_ST2)],
                [("21 OCT 2026", F_ST2)], tilt=12)
    round_stamp(img, 662, 502, 66, (114, 64, 142),
                [("FERRY TOLL", F_ST2)],
                [("EXEMPT", F_ST)],
                [("KALDEN ISLES", F_ST3)], tilt=-6)
    box_stamp(img, 792, 472, 202, 98, (170, 46, 46),
              "SCOTLAND · ABERDEEN",
              ["ENTRY · 12 NOV 2026", "Leave to enter: 90 days"], tilt=5)

    # pencilled harbour note -- a small observed detail
    d.text((544, 584), "Harbour note, in pencil: met M. at the quay — cod, not haddock.",
           font=F_TXT, fill=MUTE)

    # endorsement -- the telling detail
    d.rectangle([544, 622, 994, 772], outline=RULE_C, width=1)
    d.rectangle([544, 622, 994, 650], fill=(233, 227, 207))
    d.text((556, 628), "ENDORSEMENT / ÁRITUN", font=F_CAP, fill=NAVY)
    body = ("The holder is exempt from inter-island ferry tolls within the "
            "Kalden Isles. Visa-free travel: Faroe Islands, Iceland, Norway. "
            "Holders must declare all catch landed at foreign ports on return.")
    yy = 662
    for ln in text_lines(d, body, F_TXT, 426):
        d.text((556, yy), ln, font=F_TXT, fill=INK)
        yy += 16
    d.text((556, yy + 8), "— Passport Office, Norhavn, 02 JUN 2026", font=F_TXT, fill=INK)

    # archipelago sketch
    d.text((544, 800), "THE KALDEN ISLES — NORTH ATLANTIC", font=F_CAP, fill=NAVY)
    d.line([(544, 820), (994, 820)], fill=RULE_C, width=1)
    for ix, iy, iw in ((580, 862, 52), (660, 838, 34), (722, 872, 62),
                       (802, 844, 30), (862, 872, 44), (922, 848, 28)):
        d.ellipse([ix, iy, ix + iw, iy + iw // 2],
                  fill=(191, 206, 216), outline=NAVY, width=1)
    d.ellipse([724, 874, 732, 880], fill=(170, 46, 46))
    d.text((722, 906), "Norhavn", font=F_TXT, fill=INK)
    d.text((544, 928), "Scale 1 : 2 400 000 — surveyed 2024, Hydrographic Office",
           font=F_MIN, fill=MUTE)
    d.text((962, 988), "3", font=F_TXT, fill=MUTE)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print("saved", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    build()
