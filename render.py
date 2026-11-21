#!/usr/bin/env python3
"""Render the Azmara passport spread for make.fun.

Draws one 1024x1024 invented passport spread: the data page of
Amira Zahra Benali, caravan master of the Republic of Azmara
(an oasis nation in the Great Erg), and its visas page with a
consistent travel history. Pure Pillow + system fonts, run locally;
the finished PNG is what main.py ships (the grader has no Pillow
and no fonts), so this file is the generator kept in the repo.
"""
import base64
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PORTRAIT = os.path.join(HERE, "portrait.png")
OUT = os.path.join(HERE, "entry.png")


def ensure_portrait():
    """Rebuild portrait.png from its base64 text when it is absent."""
    if os.path.isfile(PORTRAIT):
        return
    b64_path = os.path.join(HERE, "portrait.png.b64")
    with open(b64_path, "r", encoding="ascii") as handle:
        raw = base64.b64decode("".join(handle.read().split()))
    with open(PORTRAIT, "wb") as handle:
        handle.write(raw)

W, H = 1024, 1024

PAPER = (248, 244, 231)
PAPER2 = (243, 237, 219)
INK = (32, 30, 26)
SOFT = (74, 70, 60)
MUTED = (122, 114, 96)
TEAL = (15, 76, 74)
TEAL_DK = (9, 50, 49)
GOLD = (172, 120, 24)
RED = (172, 42, 36)
BLUE = (32, 84, 150)
GREEN = (46, 110, 66)
GUILL = (214, 203, 172)
FRAME = (26, 38, 36)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def tw(draw, s, fnt):
    return draw.textlength(s, font=fnt)


def wrap(draw, s, fnt, width):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tw(draw, trial, fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, x, y, fnt, fill, leading=None):
    if leading is None:
        leading = fnt.size + 2
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += leading
    return y


def centred(draw, cx, y, s, fnt, fill):
    draw.text((cx - tw(draw, s, fnt) / 2, y), s, font=fnt, fill=fill)


def guilloche(draw, x0, y0, x1, y1, step=7, amp=5, color=GUILL):
    """Faint wavy security lines across a rectangle."""
    for yy in range(y0, y1, step):
        pts = []
        for xx in range(x0, x1 + 1, 6):
            pts.append((xx, yy + amp * math.sin((xx - x0) / 47.0 + yy / 31.0)))
        draw.line(pts, fill=color, width=1)


def mrz_check(s):
    vals = {}
    for i in range(10):
        vals[str(i)] = i
    for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        vals[ch] = 10 + i
    vals["<"] = 0
    total = 0
    for i, ch in enumerate(s):
        total += vals[ch] * (7, 3, 1)[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = "P<AZMBENALI<<AMIRA<ZAHRA"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "AZM041827"
    doc_c = mrz_check(doc)
    nat = "AZM"
    dob = "810312"
    dob_c = mrz_check(dob)
    sex = "F"
    exp = "350508"
    exp_c = mrz_check(exp)
    personal = "<" * 14
    personal_c = mrz_check(personal)
    line2_body = doc + doc_c + nat + dob + dob_c + sex + exp + exp_c + personal + personal_c
    overall = mrz_check(line2_body)
    line2 = line2_body + overall
    assert len(line1) == 44 and len(line2) == 44, (len(line1), len(line2))
    return line1, line2


def emblem(draw, cx, cy, r, color=TEAL):
    """Sun over a well, ringed: the arms of Azmara."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
    draw.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6],
                 outline=color, width=1)
    # sun disc: outline only, so the emblem stays legible at small size
    sr = r * 0.24
    draw.ellipse([cx - sr, cy - r * 0.52, cx + sr, cy - r * 0.52 + 2 * sr],
                 outline=color, width=2)
    for k in range(8):
        a = math.pi * k / 4
        x0 = cx + (sr + 3) * math.cos(a)
        y0 = cy - r * 0.22 + (sr + 3) * math.sin(a)
        x1 = cx + (sr + 8) * math.cos(a)
        y1 = cy - r * 0.22 + (sr + 8) * math.sin(a)
        draw.line([x0, y0, x1, y1], fill=color, width=2)
    # dunes / well water: three wavy lines under the sun
    for j, yy in enumerate((-2, 6, 14)):
        pts = []
        for xx in range(-r + 10, r - 9, 4):
            pts.append((cx + xx,
                        cy + yy + 3 * math.sin(xx / 11.0 + j)))
        draw.line(pts, fill=color, width=2)


def stamp(draw_img, box, color, place, kind, port, date, angle):
    """One rectangular entry/exit stamp, slightly rotated."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=10,
                        outline=color + (255,), width=3)
    d.rounded_rectangle([25, 25, 15 + w, 15 + h], radius=8,
                        outline=color + (255,), width=1)
    cx = 20 + w // 2
    centred(d, cx, 20 + 10, place, font(SANS_B, 17), color + (255,))
    centred(d, cx, 20 + 32, kind, font(SANS_B, 15), color + (255,))
    centred(d, cx, 20 + 52, port, font(SANS, 11), color + (255,))
    centred(d, cx, 20 + 68, date, font(SANS_B, 14), color + (255,))
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=False)
    draw_img.paste(layer, (x0 - 20, y0 - 20), layer)


def round_stamp(img, cx, cy, r, color, top, mid, bottom, date):
    """Circular tax/fee stamp, ring text around the full circle."""
    layer = Image.new("RGBA", (2 * r + 40, 2 * r + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cc = r + 20
    d.ellipse([20, 20, 20 + 2 * r, 20 + 2 * r], outline=color + (255,),
              width=3)
    d.ellipse([27, 27, 13 + 2 * r, 13 + 2 * r], outline=color + (255,),
              width=1)
    # ring text: one glyph per step around the circle, top pointing out
    R = r - 9
    f_ring = font(SANS_B, 10 if r >= 40 else 9)
    n = len(top)
    for i, ch in enumerate(top):
        a = math.radians(-90 + i * 360.0 / n)
        x = cc + R * math.cos(a)
        y = cc + R * math.sin(a)
        glyph = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glyph)
        bb = gd.textbbox((0, 0), ch, font=f_ring)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        gd.text((12 - w / 2 - bb[0], 12 - h / 2 - bb[1]), ch, font=f_ring,
                fill=color + (255,))
        glyph = glyph.rotate(-(math.degrees(a) + 90),
                             resample=Image.BICUBIC, center=(12, 12))
        layer.paste(glyph, (int(x) - 12, int(y) - 12), glyph)
    ms = max(11, int(r * 0.30))
    bs = max(10, int(r * 0.26))
    centred(d, cc, cc - int(r * 0.34), mid, font(SANS_B, ms), color + (255,))
    centred(d, cc, cc + int(r * 0.08), bottom, font(SANS_B, bs),
            color + (255,))
    centred(d, cc, cc + int(r * 0.42), date,
            font(SANS, 10 if r >= 40 else 9), color + (255,))
    layer = layer.rotate(-8, resample=Image.BICUBIC)
    img.paste(layer, (cx - r - 20, cy - r - 20), layer)


def field(draw, x, y, label, value, vsize=17, label_gap=13):
    draw.text((x, y), label, font=font(SANS, 9), fill=MUTED)
    draw.text((x, y + label_gap), value, font=font(SANS_B, vsize), fill=INK)
    return y + label_gap + vsize + 6


def draw_left_page(img, draw):
    x0, y0, x1, y1 = 10, 10, 508, 1014
    draw.rectangle([x0, y0, x1, y1], fill=PAPER)
    guilloche(draw, x0 + 14, y0 + 14, x1 - 14, y1 - 14)
    draw.rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], outline=TEAL, width=2)
    draw.rectangle([x0 + 12, y0 + 12, x1 - 12, y1 - 12], outline=TEAL, width=1)
    # faint watermark ring behind the fields
    draw.ellipse([330, 300, 560, 530], outline=(226, 216, 186), width=2)
    draw.ellipse([350, 320, 540, 510], outline=(226, 216, 186), width=1)

    draw.text((x1 - 100, 26), "AZM 041 827", font=font(SANS_B, 11), fill=TEAL_DK)
    emblem(draw, 259, 74, 30)
    centred(draw, 259, 112, "JUMHURIYAT AZMARA", font(SERIF_B, 25), TEAL_DK)
    centred(draw, 259, 142, "R E P U B L I C   O F   A Z M A R A",
            font(SANS, 12), INK)
    centred(draw, 259, 162, "JAWAZ SAFAR  ·  PASSPORT", font(SANS, 11), SOFT)
    draw.line([30, 184, 488, 184], fill=TEAL, width=2)

    # portrait
    photo = Image.open(PORTRAIT).convert("RGB")
    pw, ph = photo.size
    crop = photo.crop((int(pw * 0.09), int(ph * 0.02),
                       int(pw * 0.93), int(ph * 0.73)))
    crop = crop.resize((150, 190), Image.LANCZOS)
    img.paste(crop, (30, 200))
    draw.rectangle([30, 200, 180, 390], outline=TEAL, width=2)
    draw.text((30, 396), "PHOTOGRAPH / SURA", font=font(SANS, 8), fill=MUTED)

    # ghost portrait, faint, right of the signature block: true watermark,
    # guilloche shows through it
    ghost = crop.resize((104, 132), Image.LANCZOS).convert("RGBA")
    alpha = ghost.split()[3].point(lambda a: int(a * 0.16))
    ghost.putalpha(alpha)
    img.paste(ghost, (372, 452), ghost)

    # top row: type / code / number
    fx = 198
    draw.text((fx, 200), "TYPE / NAW", font=font(SANS, 9), fill=MUTED)
    draw.text((fx, 212), "P", font=font(SANS_B, 16), fill=INK)
    draw.text((fx + 62, 200), "CODE / RAMZ", font=font(SANS, 9), fill=MUTED)
    draw.text((fx + 62, 212), "AZM", font=font(SANS_B, 16), fill=INK)
    draw.text((fx + 140, 200), "PASSPORT No. / RAQM", font=font(SANS, 9),
              fill=MUTED)
    draw.text((fx + 140, 212), "AZM 041 827", font=font(SANS_B, 16), fill=INK)

    y = 244
    y = field(draw, fx, y, "SURNAME / LAQAB", "BENALI")
    y = field(draw, fx, y, "GIVEN NAMES / ISM", "AMIRA ZAHRA")
    y = field(draw, fx, y, "NATIONALITY / JINSIYA", "AZMARI")
    y = field(draw, fx, y, "DATE OF BIRTH / MILAD", "12 MAR 1981")
    y = field(draw, fx, y, "PLACE OF BIRTH / MAWLID", "QASR AZMAR")
    y = field(draw, fx, y, "SEX / JINS", "F")
    y = field(draw, fx, y, "DATE OF ISSUE / SUDUR", "09 MAY 2025")
    y = field(draw, fx, y, "DATE OF EXPIRY / INTIHA", "08 MAY 2035")
    y = field(draw, fx, y, "AUTHORITY / SULUTA",
              "OASIS REGISTRY, QASR AZMAR", vsize=15)

    # signature
    draw.text((30, 556), "Amira Zahra Benali", font=font(SERIF_I, 25),
              fill=(38, 44, 90))
    draw.line([30, 592, 300, 592], fill=INK, width=1)
    draw.text((30, 598), "HOLDER'S SIGNATURE / IMDA", font=font(SANS, 8),
              fill=MUTED)

    # observations
    draw.rectangle([30, 636, 488, 716], outline=TEAL, width=1)
    draw.text((40, 644), "OBSERVATIONS / MULAHADHAT", font=font(SANS_B, 10),
              fill=TEAL_DK)
    obs = ("Holder is a licensed caravan master, Oasis Guild No. 214. "
           "Authorised to cross the Erg by the northern well road.")
    draw_lines(draw, wrap(draw, obs, font(SANS, 12), 438), 40, 662,
               font(SANS, 12), INK, leading=16)

    centred(draw, 259, 782, "\u201cBy the salt and the sun.\u201d  —  bil-milh wash-shams",
            font(SERIF_I, 13), MUTED)

    # machine-readable zone
    draw.rectangle([30, 818, 488, 898], outline=TEAL, width=1)
    l1, l2 = mrz_lines()
    draw.text((42, 832), l1, font=font(MONO, 13), fill=INK)
    draw.text((42, 860), l2, font=font(MONO, 13), fill=INK)
    draw.text((30, 912), "32 pages  ·  Data page 2  ·  Visas page 3",
              font=font(SANS, 9), fill=MUTED)
    # registry seal, bottom right of the data page
    round_stamp(img, 440, 950, 34, TEAL, "OASIS REGISTRY",
                "QASR", "AZMAR", "")
    draw.text((30, 976), "2", font=font(SANS, 11), fill=MUTED)


def draw_right_page(img, draw):
    x0, y0, x1, y1 = 516, 10, 1014, 1014
    draw.rectangle([x0, y0, x1, y1], fill=PAPER)
    guilloche(draw, x0 + 14, y0 + 14, x1 - 14, y1 - 14)
    draw.rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], outline=TEAL, width=2)
    draw.rectangle([x0 + 12, y0 + 12, x1 - 12, y1 - 12], outline=TEAL, width=1)

    draw.text((536, 30), "VISAS", font=font(SERIF_B, 26), fill=TEAL_DK)
    draw.text((640, 38), "/  TA'SHIRAT", font=font(SANS, 13), fill=SOFT)
    draw.text((972, 34), "3", font=font(SANS, 11), fill=MUTED)
    draw.line([536, 66, 994, 66], fill=TEAL, width=2)
    draw.text((536, 76), "ENTRY AND EXIT STAMPS — TRAVEL HISTORY",
              font=font(SANS, 10), fill=MUTED)

    stamps = [
        ("BIR TAMEL", "ARRIVAL", "NORTH WELL ROAD", "21 MAY 2025", BLUE, -2),
        ("BIR TAMEL", "DEPARTURE", "NORTH WELL ROAD", "28 MAY 2025", BLUE, 2),
        ("WADI NURA", "ARRIVAL", "PALM GATE", "09 JUN 2025", GREEN, 2),
        ("WADI NURA", "DEPARTURE", "PALM GATE", "17 JUN 2025", GREEN, -2),
        ("KHOR SALIM", "ARRIVAL", "SALT GATE", "02 SEP 2025", RED, -2),
        ("KHOR SALIM", "DEPARTURE", "SALT GATE", "11 SEP 2025", RED, 2),
        ("OASIS OF INARA", "ARRIVAL", "EAST WELL", "19 JAN 2026", BLUE, 2),
        ("OASIS OF INARA", "DEPARTURE", "EAST WELL", "27 JAN 2026", BLUE, -2),
    ]
    xs = [536, 780]
    ys = [100, 200, 300, 400]
    for i, (place, kind, port, date, color, ang) in enumerate(stamps):
        stamp(img, (xs[i % 2], ys[i // 2], xs[i % 2] + 214, ys[i // 2] + 88),
              color, place, kind, port, date, ang)

    # endorsement box
    draw.rectangle([536, 512, 994, 644], outline=TEAL, width=2)
    draw.rectangle([536, 512, 994, 538], fill=TEAL)
    draw.text((546, 519), "WATER MANIFEST ENDORSEMENT  ·  ERG CROSSING ACT §7",
              font=font(SANS_B, 11), fill=(255, 255, 255))
    body = ("The bearer may cross the Erg only with a licensed guide and "
            "a stamped water manifest. No crossing of the White Dune "
            "after nightfall. Present this passport at every well station.")
    draw_lines(draw, wrap(draw, body, font(SANS, 12), 438), 546, 548,
               font(SANS, 12), INK, leading=17)
    draw.text((546, 622), "Issued at Qasr Azmar, 09 May 2025  ·  No. AZM 041 827",
              font=font(SANS, 10), fill=MUTED)

    # round well-tax stamp overlapping the box corner
    round_stamp(img, 915, 600, 52, RED, "REPUBLIC OF AZMARA",
                "WELL TAX", "PAID · 12 AZM", "09 MAY 2025")

    # diagonal red notice stamp
    layer = Image.new("RGBA", (460, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([4, 4, 456, 56], outline=RED + (255,), width=3)
    d.text((230 - tw(d, "WATER MANIFEST REQUIRED", font(SANS_B, 16)) / 2, 8),
           "WATER MANIFEST REQUIRED", font=font(SANS_B, 16), fill=RED + (255,))
    d.text((230 - tw(d, "BEYOND THE WHITE DUNE", font(SANS_B, 13)) / 2, 32),
           "BEYOND THE WHITE DUNE", font=font(SANS_B, 13), fill=RED + (255,))
    layer = layer.rotate(-4, resample=Image.BICUBIC)
    img.paste(layer, (556, 700), layer)

    # conditions box
    draw.rectangle([536, 762, 994, 906], outline=TEAL, width=1)
    draw.text((546, 772), "CONDITIONS OF ISSUE / SHURUT", font=font(SANS_B, 11),
              fill=TEAL_DK)
    cond = ("The holder must report to the Oasis Registry within 48 hours "
            "of entering Azmara. The White Dune is closed during the sand "
            "season (June – August) without a guide's permit.")
    draw_lines(draw, wrap(draw, cond, font(SANS, 12), 438), 546, 794,
               font(SANS, 12), INK, leading=17)
    draw.text((546, 884), "No. 041827  ·  Fee paid at issue",
              font=font(SANS, 10), fill=MUTED)

    draw_lines(draw, wrap(draw, "This passport remains the property of the "
                                 "Republic of Azmara. If found, please return "
                                 "to any Azmari consulate or oasis registry.",
                           font(SERIF_I, 12), 458), 536, 926,
               font(SERIF_I, 12), MUTED, leading=16)
    draw.text((536, 976), "AZMARA  ·  VISAS  ·  PAGE 3", font=font(SANS, 9),
              fill=MUTED)


def main():
    ensure_portrait()
    img = Image.new("RGB", (W, H), FRAME)
    draw = ImageDraw.Draw(img)
    # spine shadow
    draw.rectangle([508, 10, 516, 1014], fill=(60, 66, 60))
    draw_left_page(img, draw)
    draw_right_page(img, draw)
    img.save(OUT, optimize=True)
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}: {size} bytes")
    assert size <= 1048576, "entry.png over 1 MiB"
    assert img.size[0] <= 1024 and img.size[1] <= 1024
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
