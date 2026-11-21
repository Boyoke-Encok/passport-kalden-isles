#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There (make.fun).

Draws one 1024x1024 PNG: an open passport spread of the invented
Republic of the Kalden Isles (a small North Atlantic archipelago).
Left page: data page with portrait, bilingual (Kalden/English) fields
and a machine-readable zone with real ICAO check digits.
Right page: visa/stamps page with a travel history that agrees with
the issue date, plus the telling endorsement: inter-island ferry toll
exemption and visa-free travel to the neighbouring Nordic states.

Own code, written fresh. Deterministic: fixed geometry, no randomness,
no network. Fonts: DejaVu / Liberation from the system font dir.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = "/output/entry.png"

FD = "/usr/share/fonts/truetype/dejavu"
FL = "/usr/share/fonts/truetype/liberation"


def font(path, size):
    return ImageFont.truetype(path, size)


F_TITLE = font(f"{FD}/DejaVuSerif-Bold.ttf", 20)
F_SUB = font(f"{FD}/DejaVuSerif-Bold.ttf", 15)
F_HEAD = font(f"{FD}/DejaVuSans-Bold.ttf", 13)
F_LBL = font(f"{FD}/DejaVuSans.ttf", 11)
F_VAL = font(f"{FD}/DejaVuSans-Bold.ttf", 17)
F_VAL_SM = font(f"{FD}/DejaVuSans-Bold.ttf", 15)
F_SMALL = font(f"{FD}/DejaVuSans.ttf", 11)
F_TINY = font(f"{FD}/DejaVuSans.ttf", 9)
F_MRZ = font(f"{FD}/DejaVuSansMono.ttf", 17)
F_SIG = font(f"{FL}/LiberationSerif-Italic.ttf", 24)
F_STAMP = font(f"{FD}/DejaVuSans-Bold.ttf", 13)
F_STAMP_SM = font(f"{FD}/DejaVuSans-Bold.ttf", 10)
F_STAMP_T = font(f"{FD}/DejaVuSans.ttf", 9)

PAPER = (247, 242, 226)
PAPER2 = (242, 236, 216)
INK = (24, 38, 66)
NAVY = (18, 48, 88)
GOLD = (166, 124, 52)
GREY = (96, 92, 80)
RULE = (150, 140, 118)
PHOTO_BG = (206, 214, 220)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rr(d, box, r, **kw):
    d.rounded_rectangle([int(v) for v in box], radius=int(r), **kw)


def wrap(d, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        trial = f"{cur} {w}".strip()
        if d.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- ICAO MRZ
def check_digit(s):
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(s):
        if ch == "<":
            v = 0
        elif ch.isdigit():
            v = int(ch)
        else:
            v = ord(ch) - 55  # A=10 .. Z=35
        total += v * weights[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = "P<KLDHALVORSEN<<INGRID<MARIE"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "0048217<<"
    doc_cd = check_digit(doc)
    dob = "940314"
    dob_cd = check_digit(dob)
    exp = "360601"
    exp_cd = check_digit(exp)
    personal = "<" * 14
    personal_cd = check_digit(personal)
    body = doc + doc_cd + "KLD" + dob + dob_cd + "F" + exp + exp_cd + personal + personal_cd
    body_cd = check_digit(body)
    line2 = body + body_cd
    assert len(line1) == 44 and len(line2) == 44, (len(line1), len(line2))
    return line1, line2


# ---------------------------------------------------------------- portrait
def draw_portrait(d, x0, y0, x1, y1):
    """Front-facing passport portrait, flat shaded vector style."""
    cx = (x0 + x1) // 2
    pw, ph = x1 - x0, y1 - y0
    # photo background: soft vertical gradient
    for y in range(y0, y1):
        t = (y - y0) / max(1, ph)
        d.line([(x0, y), (x1, y)], fill=lerp((214, 221, 226), (186, 196, 205), t))
    skin = (216, 172, 136)
    skin_d = (198, 152, 118)
    skin_l = (228, 188, 152)
    hair_c = (88, 52, 34)
    hair_d = (66, 38, 24)
    coat = (38, 52, 78)
    # shoulders / coat
    d.pieslice([cx - 88, y1 - 118, cx + 88, y1 + 40], start=180, end=360, fill=coat)
    d.rectangle([x0, y1 - 42, x1, y1], fill=coat)
    # shirt V + collar
    d.polygon([(cx - 26, y1 - 52), (cx + 26, y1 - 52), (cx, y1 - 8)], fill=(240, 238, 230))
    d.polygon([(cx - 30, y1 - 58), (cx - 8, y1 - 34), (cx - 2, y1 - 52)], fill=(226, 224, 216))
    d.polygon([(cx + 30, y1 - 58), (cx + 8, y1 - 34), (cx + 2, y1 - 52)], fill=(226, 224, 216))
    # neck
    d.rectangle([cx - 20, y1 - 108, cx + 20, y1 - 52], fill=skin_d)
    d.rectangle([cx - 20, y1 - 108, cx + 20, y1 - 96], fill=(190, 144, 110))
    # head
    hx0, hy0, hx1, hy1 = cx - 52, y0 + 26, cx + 52, y0 + 148
    d.ellipse([hx0, hy0, hx1, hy1], fill=skin)
    # soft cheek shading
    d.ellipse([hx0 + 6, hy0 + 62, hx0 + 34, hy0 + 96], fill=skin_l)
    d.ellipse([hx1 - 34, hy0 + 62, hx1 - 6, hy0 + 96], fill=skin_l)
    # ears
    d.ellipse([hx0 - 8, hy0 + 58, hx0 + 6, hy0 + 88], fill=skin)
    d.ellipse([hx1 - 6, hy0 + 58, hx1 + 8, hy0 + 88], fill=skin)
    # hair: back mass behind head, then fringe
    d.pieslice([hx0 - 10, hy0 - 16, hx1 + 10, hy0 + 78], start=180, end=360, fill=hair_c)
    d.rounded_rectangle([hx0 - 8, hy0 + 52, hx0 + 8, y0 + 166], radius=8, fill=hair_c)
    d.rounded_rectangle([hx1 - 8, hy0 + 52, hx1 + 8, y0 + 166], radius=8, fill=hair_c)
    # fringe sweep
    d.pieslice([hx0 - 6, hy0 - 10, hx1 + 6, hy0 + 66], start=180, end=330, fill=hair_c)
    d.pieslice([hx0 - 6, hy0 - 10, hx1 + 6, hy0 + 66], start=195, end=345, fill=hair_d)
    # centre part line
    d.line([(cx, hy0 + 2), (cx, hy0 + 26)], fill=hair_d, width=2)
    # eyebrows
    d.arc([cx - 34, hy0 + 56, cx - 8, hy0 + 72], start=200, end=340, fill=(70, 44, 30), width=3)
    d.arc([cx + 8, hy0 + 56, cx + 34, hy0 + 72], start=200, end=340, fill=(70, 44, 30), width=3)
    # eyes
    for ex in (cx - 21, cx + 21):
        d.ellipse([ex - 11, hy0 + 74, ex + 11, hy0 + 88], fill=(245, 242, 236))
        d.ellipse([ex - 5, hy0 + 75, ex + 5, hy0 + 87], fill=(96, 66, 44))
        d.ellipse([ex - 2, hy0 + 78, ex + 2, hy0 + 84], fill=(20, 16, 14))
        d.ellipse([ex + 2, hy0 + 76, ex + 5, hy0 + 79], fill=(255, 255, 255))
        d.line([(ex - 11, hy0 + 76), (ex + 11, hy0 + 76)], fill=(70, 44, 30), width=2)
    # nose
    d.line([(cx + 1, hy0 + 88), (cx - 2, hy0 + 108)], fill=skin_d, width=2)
    d.arc([cx - 6, hy0 + 104, cx + 8, hy0 + 114], start=0, end=180, fill=skin_d, width=2)
    # lips: calm, closed
    d.arc([cx - 13, hy0 + 116, cx + 13, hy0 + 130], start=0, end=180, fill=(164, 96, 84), width=2)
    d.line([(cx - 12, hy0 + 123), (cx + 12, hy0 + 123)], fill=(150, 84, 74), width=2)
    # jaw shading
    d.arc([hx0 + 8, hy0 + 96, hx1 - 8, hy1 - 2], start=20, end=160, fill=skin_d, width=2)


# ---------------------------------------------------------------- stamps
def stamp_circle(d, cx, cy, r, ink, lines_top, lines_mid, lines_bot, rot=0):
    """Circular entry/exit stamp, drawn on its own layer for alpha + tilt."""
    size = int(r * 2 + 24)
    lay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    c = size // 2
    col = ink + (215,)
    ld.ellipse([c - r, c - r, c + r, c + r], outline=col, width=3)
    ld.ellipse([c - r + 9, c - r + 9, c + r - 9, c + r - 9], outline=col, width=1)
    y = c - r + 16
    for ln, fnt in lines_top:
        w = ld.textlength(ln, font=fnt)
        ld.text((c - w / 2, y), ln, font=fnt, fill=col)
        y += 13
    for ln, fnt in lines_mid:
        w = ld.textlength(ln, font=fnt)
        ld.text((c - w / 2, y), ln, font=fnt, fill=col)
        y += 15
    for ln, fnt in lines_bot:
        w = ld.textlength(ln, font=fnt)
        ld.text((c - w / 2, y), ln, font=fnt, fill=col)
        y += 13
    lay = lay.rotate(rot, resample=Image.BICUBIC, center=(c, c))
    return lay, (cx - size // 2, cy - size // 2)


def stamp_rect(d, x, y, w, h, ink, title, rows, rot=0):
    size_w, size_h = w + 24, h + 24
    lay = Image.new("RGBA", (size_w, size_h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    col = ink + (215,)
    ld.rectangle([10, 10, 10 + w, 10 + h], outline=col, width=3)
    ld.line([(10, 34), (10 + w, 34)], fill=col, width=1)
    tw = ld.textlength(title, font=F_STAMP)
    ld.text((10 + (w - tw) / 2, 14), title, font=F_STAMP, fill=col)
    yy = 42
    for ln in rows:
        tw = ld.textlength(ln, font=F_STAMP_SM)
        ld.text((10 + (w - tw) / 2, yy), ln, font=F_STAMP_SM, fill=col)
        yy += 15
    lay = lay.rotate(rot, resample=Image.BICUBIC)
    return lay, (x - 12, y - 12)


def guilloche(d, x0, y0, x1, y1, color, step=7):
    """Fine wavy security lines, very light."""
    for yy in range(y0, y1, step):
        pts = []
        for x in range(x0, x1 + 1, 8):
            pts.append((x, yy + 2 * math.sin((x - x0) / 46.0)))
        d.line(pts, fill=color, width=1)


def emblem(d, cx, cy, s):
    """Coat of arms: shield with three waves and a north star."""
    # shield
    d.polygon([(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy + s * 0.4),
               (cx, cy + s * 1.15), (cx - s, cy + s * 0.4)], outline=GOLD, width=3)
    d.polygon([(cx - s + 5, cy - s + 5), (cx + s - 5, cy - s + 5),
               (cx + s - 5, cy + s * 0.4 - 2), (cx, cy + s - 4),
               (cx - s + 5, cy + s * 0.4 - 2)], fill=(228, 232, 238))
    # waves
    for i, wy in enumerate((cy - s * 0.25, cy + s * 0.1, cy + s * 0.45)):
        pts = []
        for x in range(cx - s + 8, cx + s - 6, 4):
            pts.append((x, wy + 3 * math.sin((x - cx) / 9.0 + i)))
        d.line(pts, fill=NAVY, width=2)
    # north star
    d.polygon([(cx, cy - s * 0.95), (cx + 3, cy - s * 0.62), (cx, cy - s * 0.45),
               (cx - 3, cy - s * 0.62)], fill=GOLD)


# ---------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (W, H), (58, 52, 44))
    d = ImageDraw.Draw(img)
    # spread: two cream pages with a centre gutter
    d.rectangle([6, 6, 1018, 1018], fill=PAPER)
    d.rectangle([6, 6, 508, 1018], fill=PAPER)
    d.rectangle([516, 6, 1018, 1018], fill=PAPER2)
    d.rectangle([508, 6, 516, 1018], fill=(120, 110, 92))
    d.line([(512, 6), (512, 1018)], fill=(90, 82, 66), width=1)

    # ================= LEFT PAGE: data page =================
    # header
    d.text((34, 26), "REPUBLIC OF THE KALDEN ISLES", font=F_TITLE, fill=NAVY)
    d.text((34, 60), "VEGABRÉF  ·  PASSPORT  ·  PASSEPORT", font=F_SUB, fill=GOLD)
    d.line([(34, 88), (484, 88)], fill=RULE, width=2)
    emblem(d, 458, 50, 20)

    # type / code / number row
    d.text((34, 100), "TYPE / TEGUND", font=F_LBL, fill=GREY)
    d.text((34, 114), "P", font=F_VAL, fill=INK)
    d.text((150, 100), "CODE / LAND", font=F_LBL, fill=GREY)
    d.text((150, 114), "KLD", font=F_VAL, fill=INK)
    d.text((280, 100), "PASSPORT No. / NÚMER", font=F_LBL, fill=GREY)
    d.text((280, 114), "0048217", font=F_VAL, fill=INK)

    # portrait photo
    px0, py0, px1, py1 = 34, 150, 204, 372
    draw_portrait(d, px0, py0, px1, py1)
    d.rectangle([px0, py0, px1, py1], outline=INK, width=2)
    d.text((px0, py1 + 6), "PHOTO / MYND", font=F_TINY, fill=GREY)

    # ghost image watermark behind fields (very faint)
    ghost = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost)
    draw_portrait(gd, 8, 0, 122, 130)
    ghost.putalpha(ghost.split()[3].point(lambda a: a // 18))
    img.paste(ghost, (348, 168), ghost)
    d = ImageDraw.Draw(img)

    # data fields (right of portrait)
    fields = [
        ("SURNAME / EFTIRNAFN", "HALVORSEN"),
        ("GIVEN NAMES / FORNÖFN", "INGRID MARIE"),
        ("NATIONALITY / ÞJÓÐERNI", "KALDEN"),
        ("DATE OF BIRTH / FÆÐINGARDAGUR", "14 MAR 1994"),
        ("PLACE OF BIRTH / FÆÐINGARSTAÐUR", "NORHAVN"),
        ("SEX / KYN", "F"),
    ]
    y = 150
    for lbl, val in fields:
        d.text((224, y), lbl, font=F_LBL, fill=GREY)
        d.text((224, y + 14), val, font=F_VAL, fill=INK)
        y += 40
    # signature
    d.text((34, 396), "HOLDER'S SIGNATURE / UNDIRSKRIFT", font=F_LBL, fill=GREY)
    d.text((34, 410), "Ingrid Halvorsen", font=F_SIG, fill=(40, 40, 60))
    d.line([(34, 444), (300, 444)], fill=RULE, width=1)

    # issue / expiry / authority
    d.text((34, 462), "DATE OF ISSUE / ÚTGÁFUDAGUR", font=F_LBL, fill=GREY)
    d.text((34, 476), "02 JUN 2026", font=F_VAL, fill=INK)
    d.text((235, 462), "DATE OF EXPIRY / GILDISTÍMI", font=F_LBL, fill=GREY)
    d.text((235, 476), "01 JUN 2036", font=F_VAL, fill=INK)
    d.text((34, 506), "AUTHORITY / YFIRVALD", font=F_LBL, fill=GREY)
    d.text((34, 520), "PASSPORT OFFICE — NORHAVN", font=F_VAL_SM, fill=INK)

    # small authority stamp on data page
    lay, pos = stamp_circle(d, 448, 546, 46, (30, 80, 160),
                            [("PASSPORT OFFICE", F_STAMP_T)],
                            [("NORHAVN", F_STAMP), ("02 JUN 2026", F_STAMP_SM)],
                            [("KALDEN ISLES", F_STAMP_T)], rot=-8)
    img.paste(lay, pos, lay)
    d = ImageDraw.Draw(img)
    d.text((34, 548), "The bearer is a citizen of the Republic of the", font=F_SMALL, fill=INK)
    d.text((34, 564), "Kalden Isles and is entitled to its protection abroad.", font=F_SMALL, fill=INK)

    # MRZ
    d.rectangle([28, 596, 490, 668], fill=(238, 234, 220))
    l1, l2 = mrz_lines()
    d.text((36, 604), l1, font=F_MRZ, fill=INK)
    d.text((36, 632), l2, font=F_MRZ, fill=INK)
    d.text((34, 676), "P<KLD  ·  Machine-readable zone — please do not fold", font=F_TINY, fill=GREY)
    guilloche(d, 28, 700, 490, 760, (200, 192, 168))
    # page number
    d.text((470, 986), "2", font=F_SMALL, fill=GREY)

    # ================= RIGHT PAGE: visas & stamps =================
    d.text((544, 26), "VISAS", font=F_TITLE, fill=NAVY)
    d.text((544, 62), "VEGABRÉF — ENDORSEMENTS & ENTRY STAMPS", font=F_SUB, fill=GOLD)
    d.line([(544, 88), (994, 88)], fill=RULE, width=2)

    # faint watermark emblem
    wm = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    emblem(wd, 150, 150, 90)
    wm.putalpha(wm.split()[3].point(lambda a: a // 14))
    img.paste(wm, (620, 380), wm)
    d = ImageDraw.Draw(img)

    # stamps (all after the 02 JUN 2026 issue date)
    lay, pos = stamp_circle(d, 660, 200, 74, (30, 80, 160),
                            [("FAROE ISLANDS", F_STAMP)],
                            [("TÓRSHAVN", F_STAMP), ("ENTRY", F_STAMP_SM)],
                            [("18 JUL 2026", F_STAMP_SM)], rot=-10)
    img.paste(lay, pos, lay)
    lay, pos = stamp_circle(d, 880, 210, 74, (168, 44, 44),
                            [("ICELAND", F_STAMP)],
                            [("KEFLAVÍK", F_STAMP), ("ENTRY", F_STAMP_SM)],
                            [("03 SEP 2026", F_STAMP_SM)], rot=7)
    img.paste(lay, pos, lay)
    lay, pos = stamp_rect(d, 580, 300, 200, 108, (36, 96, 66),
                          "TRANSIT VISA — SVALBARD",
                          ["Single entry · 30 days", "Valid 21 OCT – 20 NOV 2026",
                           "Fee paid: 450 kr · No. SV-2214"], rot=-3)
    img.paste(lay, pos, lay)
    lay, pos = stamp_circle(d, 890, 380, 66, (30, 80, 160),
                            [("NORWAY", F_STAMP)],
                            [("BERGEN", F_STAMP), ("EXIT", F_STAMP_SM)],
                            [("21 OCT 2026", F_STAMP_SM)], rot=12)
    img.paste(lay, pos, lay)
    lay, pos = stamp_circle(d, 660, 500, 66, (112, 62, 140),
                            [("FERRY TOLL", F_STAMP_SM)],
                            [("EXEMPT", F_STAMP)],
                            [("KALDEN ISLES", F_STAMP_T)], rot=-6)
    img.paste(lay, pos, lay)
    lay, pos = stamp_rect(d, 790, 470, 200, 96, (168, 44, 44),
                          "SCOTLAND · ABERDEEN",
                          ["ENTRY · 12 NOV 2026", "Leave to enter: 90 days"], rot=5)
    img.paste(lay, pos, lay)

    # endorsement block — the telling detail
    d.rectangle([544, 620, 994, 800], outline=RULE, width=1)
    d.rectangle([544, 620, 994, 648], fill=(232, 226, 206))
    d.text((556, 626), "ENDORSEMENT / ÁRITUN", font=F_HEAD, fill=NAVY)
    end_lines = wrap(d, "The holder is exempt from inter-island ferry tolls "
                        "within the Kalden Isles. Visa-free travel: Faroe Islands, "
                        "Iceland, Norway. Holders must declare all catch landed "
                        "at foreign ports on return.", F_SMALL, 426)
    yy = 660
    for ln in end_lines:
        d.text((556, yy), ln, font=F_SMALL, fill=INK)
        yy += 16
    d.text((556, yy + 6), "— Passport Office, Norhavn, 02 JUN 2026", font=F_SMALL, fill=INK)

    # small archipelago sketch
    d.text((544, 822), "THE KALDEN ISLES — NORTH ATLANTIC", font=F_HEAD, fill=NAVY)
    d.line([(544, 842), (994, 842)], fill=RULE, width=1)
    for (ix, iy, iw) in [(580, 880, 46), (660, 856, 30), (720, 892, 56), (800, 862, 26),
                         (860, 890, 40), (920, 866, 24)]:
        d.ellipse([ix, iy, ix + iw, iy + iw // 2], fill=(190, 205, 215), outline=NAVY, width=1)
    d.ellipse([722, 894, 730, 900], fill=(168, 44, 44))
    d.text((736, 890), "Norhavn", font=F_SMALL, fill=INK)
    d.text((544, 940), "Scale 1 : 2 400 000 — surveyed 2024, Hydrographic Office", font=F_TINY, fill=GREY)
    d.text((960, 986), "3", font=F_SMALL, fill=GREY)

    os.makedirs("/output", exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print("saved", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    build()
