"""Render the AI Canon OG image (1200x630) to a clean PNG.

Mirrors og-image/og.html: photo (cover, biased high) + navy scrim + headline,
subhead, URL, EU flag and AI-MODIFIED disclosure badge. Run: python render_og.py
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

HERE = Path(__file__).parent
F = HERE / "fonts"
W, H = 1200, 630
NAVY = (5, 28, 44)
CREAM = (244, 238, 226)
SUB = (231, 226, 214)
ORANGE = (240, 160, 92)      # text orange on dark
ORANGE2 = (232, 119, 34)     # accent bar
TAG = (159, 178, 196)
WHITE = (255, 255, 255)

serif = lambda s: ImageFont.truetype(str(F / "DMSerifDisplay-Regular.ttf"), s)
mono = lambda s: ImageFont.truetype(str(F / "DMMono-Medium.ttf"), s)
def sans(size, wght=400, opsz=14):
    f = ImageFont.truetype(str(F / "DMSans-VF.ttf"), size)
    try: f.set_variation_by_axes([opsz, wght])
    except Exception: pass
    return f

# 1. photo, cover at 50% / 28%
img = Image.new("RGB", (W, H), NAVY)
photo = Image.open(HERE / "photo.png").convert("RGB")
pw, ph = photo.size
scale = max(W / pw, H / ph)
rw, rh = round(pw * scale), round(ph * scale)
photo = photo.resize((rw, rh), Image.LANCZOS)
ox = round((rw - W) * 0.50)
oy = round((rh - H) * 0.28)
img.paste(photo.crop((ox, oy, ox + W, oy + H)), (0, 0))

# 2. scrim: vertical (bottom) + horizontal (left), composited via screen()
def vgrad():
    g = Image.new("L", (1, H), 0)
    px = g.load()
    for y in range(H):
        t = y / H
        if t < 0.38: a = 0
        elif t < 0.68: a = 0.55 * (t - 0.38) / 0.30
        else: a = 0.55 + (0.94 - 0.55) * (t - 0.68) / 0.32
        px[0, y] = int(a * 255)
    return g.resize((W, H))
def hgrad():
    g = Image.new("L", (W, 1), 0)
    px = g.load()
    for x in range(W):
        t = x / W
        a = 0.65 * (1 - t / 0.46) if t < 0.46 else 0
        px[x, 0] = int(max(a, 0) * 255)
    return g.resize((W, H))
alpha = ImageChops.screen(vgrad(), hgrad())
scrim = Image.new("RGBA", (W, H), NAVY + (0,))
scrim.putalpha(alpha)
img = Image.alpha_composite(img.convert("RGBA"), scrim)
d = ImageDraw.Draw(img)

def spaced(x, y, text, font, fill, sp):
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + sp
    return x
def runs(x, y, segs):
    for text, font, fill in segs:
        d.text((x, y), text, font=font, fill=fill)
        x += d.textlength(text, font=font)
    return x

LEFT = 64
# 3. text block (bottom-left)
spaced(LEFT, 300, "AN APPARENS PUBLIC RESEARCH INITIATIVE", mono(18), ORANGE, 5)
d.text((LEFT - 2, 322), "The AI Canon", font=serif(96), fill=CREAM)
s = sans(30, 500)
runs(LEFT, 438, [("A reference library you can ", s, SUB), ("check", s, ORANGE), (".", s, SUB)])
runs(LEFT, 480, [("It ranks ", s, SUB), ("texts, not people", s, ORANGE), (".", s, SUB)])
# accent bar + url
d.rectangle([LEFT, 542, LEFT + 54, 546], fill=ORANGE2)
d.text((LEFT + 72, 528), "ai-canon.apparens.nl", font=sans(26, 600), fill=ORANGE)
# bottom-right tag
tg = mono(16)
for i, line in enumerate(["PILOT v0.1", "Nothing is for sale."]):
    w = d.textlength(line, font=tg)
    d.text((W - 64 - w, 540 + i * 22), line, font=tg, fill=TAG)

# 4. upper-right: EU flag + AI MODIFIED badge
# badge
bx2 = W - 26
btxt_ai, btxt_mod = "AI", "MODIFIED"
fa, fm = sans(15, 800), sans(13, 500)
def spaced_len(text, font, sp): return sum(d.textlength(c, font=font) + sp for c in text) - sp
wm = spaced_len(btxt_mod, fm, 1.5)
wa = d.textlength(btxt_ai, font=fa)
padx, gap = 14, 7
bw = padx + wa + gap + wm + padx
bh = 28
bx1 = bx2 - bw
by1 = 24
d.rounded_rectangle([bx1, by1, bx2, by1 + bh], radius=14, fill=(0, 0, 0))
d.text((bx1 + padx, by1 + 5), btxt_ai, font=fa, fill=WHITE)
spaced(bx1 + padx + wa + gap, by1 + 7, btxt_mod, fm, WHITE, 1.5)
# flag to the left of badge
fw, fh = 46, 31
fx = bx1 - 10 - fw
fy = 24
d.rounded_rectangle([fx, fy, fx + fw, fy + fh], radius=4, fill=(0, 51, 153))
cx, cy, R = fx + fw / 2, fy + fh / 2, 9.2
def star(cx, cy, r):
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * 0.382
        a = math.radians(-90 + i * 36)
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts
for i in range(12):
    a = math.radians(-90 + i * 30)
    d.polygon(star(cx + R * math.cos(a), cy + R * math.sin(a), 2.05), fill=(255, 204, 0))

out = HERE / "og-card.png"
img.convert("RGB").save(out, "PNG")
print("wrote", out, img.size)
