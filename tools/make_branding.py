#!/usr/bin/env python3
"""Generate BingeTV's icons, banners and splash screens into overlay/.

These replace Kodi's own images. Kodi's logo and name are trademarks of the
XBMC Foundation, so BingeTV may not ship them. Every image is drawn from the
one design below: a TV screen with a play button on a violet-to-pink gradient,
plus the "BingeTV" wordmark. Run it again after changing the design, and
commit the files it writes:

    python3 tools/make_branding.py

Needs Pillow and the Roboto font (Apache 2.0); the build itself needs neither.
"""

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "overlay")
FONT = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf"

INK = (11, 16, 32)            # page background
VIOLET = (124, 58, 237)
PINK = (236, 72, 153)
WHITE = (255, 255, 255)

# The mark, on a 256 x 256 grid (also the adaptive icon's vector viewport).
SCREEN_OUTER = (48, 60, 208, 180, 26)   # x0, y0, x1, y1, corner radius
SCREEN_INNER = (64, 76, 192, 164, 14)
PLAY = ((110, 96), (110, 144), (152, 120))
STAND = (100, 190, 156, 200, 5)


def gradient(size, start=VIOLET, end=PINK):
    """A diagonal gradient from top left to bottom right."""
    w, h = size
    small = Image.new("RGB", (64, 64))
    px = small.load()
    for y in range(64):
        for x in range(64):
            t = (x + y) / 126
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(start, end))
    return small.resize((w, h), Image.BICUBIC)


def mark_mask(size, scale=1.0):
    """The mark in white on transparent, `size` square, the 256 grid scaled to fit
    `scale` of it, centred."""
    s = size / 256 * scale
    off = size * (1 - scale) / 2
    big = 4  # draw large and shrink: smooth edges
    img = Image.new("L", (size * big, size * big), 0)
    d = ImageDraw.Draw(img)

    def box(x0, y0, x1, y1, r):
        return [(off + x0 * s) * big, (off + y0 * s) * big, (off + x1 * s) * big, (off + y1 * s) * big], r * s * big

    rect, r = box(*SCREEN_OUTER)
    d.rounded_rectangle(rect, r, fill=255)
    rect, r = box(*SCREEN_INNER)
    d.rounded_rectangle(rect, r, fill=0)
    d.polygon([((off + x * s) * big, (off + y * s) * big) for x, y in PLAY], fill=255)
    rect, r = box(*STAND)
    d.rounded_rectangle(rect, r, fill=255)
    return img.resize((size, size), Image.LANCZOS)


def icon(size, rounded=True):
    """Gradient square (rounded for launchers) with the white mark."""
    img = gradient((size, size)).convert("RGBA")
    img.paste(WHITE, (0, 0), mark_mask(size, 0.92))
    if rounded:
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1], size * 4 * 0.22, fill=255)
        img.putalpha(mask.resize((size, size), Image.LANCZOS))
    return img


def wordmark(draw, xy, height, anchor="lm"):
    """ "Binge" in white and "TV" in pink, `height` pixels tall."""
    font = ImageFont.truetype(FONT, height)
    x, y = xy
    binge_w = draw.textlength("Binge", font=font)
    total = binge_w + draw.textlength("TV", font=font)
    if anchor == "mm":
        x -= total / 2
    draw.text((x, y), "Binge", font=font, fill=WHITE, anchor="lm")
    draw.text((x + binge_w, y), "TV", font=font, fill=PINK, anchor="lm")
    return total


def banner(size):
    """Android TV launcher banner: mark and wordmark on dark ink."""
    w, h = size
    img = Image.new("RGB", size, INK)
    mark = icon(int(h * 0.5))
    margin = int(w * 0.07)
    img.paste(mark, (margin, (h - mark.height) // 2), mark)
    draw = ImageDraw.Draw(img)
    left = margin + mark.width + int(h * 0.08)
    # The largest wordmark that fits beside the mark (at most 30% of the height).
    room = w - left - margin
    height = int(h * 0.30)
    while draw.textlength("BingeTV", font=ImageFont.truetype(FONT, height)) > room:
        height -= 1
    wordmark(draw, (left, h // 2), height)
    return img


def splash(size):
    """Full-screen splash: dark, with a soft glow, the mark and the wordmark."""
    w, h = size
    img = Image.new("RGB", size, INK)
    glow = gradient((w, h)).resize((w // 8, h // 8))
    fade = Image.new("L", glow.size, 0)
    ImageDraw.Draw(fade).ellipse([glow.width * 0.25, glow.height * 0.1, glow.width * 0.75, glow.height * 0.9], fill=70)
    from PIL import ImageFilter
    fade = fade.filter(ImageFilter.GaussianBlur(glow.width / 10))
    img.paste(glow.resize(size, Image.BICUBIC), (0, 0), fade.resize(size, Image.BICUBIC))
    mark = icon(int(h * 0.22))
    img.paste(mark, ((w - mark.width) // 2, int(h * 0.30)), mark)
    wordmark(ImageDraw.Draw(img), (w // 2, int(h * 0.64)), int(h * 0.09), anchor="mm")
    return img


def silhouette(size):
    """White mark on transparent (notification icon: Android tints it)."""
    img = Image.new("RGBA", (size, size), WHITE + (0,))
    img.putalpha(mark_mask(size, 1.0))
    return img


def vector(fill_attrs):
    """The mark as an Android vector drawable (adaptive icon foreground)."""
    def rrect(x0, y0, x1, y1, r):
        return (f"M{x0 + r},{y0}H{x1 - r}A{r},{r} 0,0 1,{x1},{y0 + r}V{y1 - r}"
                f"A{r},{r} 0,0 1,{x1 - r},{y1}H{x0 + r}A{r},{r} 0,0 1,{x0},{y1 - r}V{y0 + r}"
                f"A{r},{r} 0,0 1,{x0 + r},{y0}Z")
    play = "M{},{}L{},{}L{},{}Z".format(*[c for p in PLAY for c in p])
    data = rrect(*SCREEN_OUTER) + rrect(*SCREEN_INNER) + play + rrect(*STAND)
    # The adaptive icon's visible area is the middle 66%: shrink the mark into it.
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!-- BingeTV mark (generated by tools/make_branding.py) -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="256"
    android:viewportHeight="256">
  <group android:scaleX="0.6" android:scaleY="0.6" android:translateX="51.2" android:translateY="51.2">
    <path android:pathData="{data}" android:fillType="evenOdd" {fill_attrs}/>
  </group>
</vector>
"""


def save(img, *parts):
    path = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith(".jpg"):
        img.convert("RGB").save(path, quality=90, optimize=True)
    else:
        img.save(path, optimize=True)
    print(os.path.relpath(path, ROOT))


def write(text, *parts):
    path = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(os.path.relpath(path, ROOT))


def main():
    android = ("tools", "android", "packaging")
    for folder, size in (("ldpi", 36), ("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        save(icon(size), *android, "media", f"mipmap-{folder}", "ic_launcher.png")
    save(banner((320, 180)), *android, "media", "mipmap-xhdpi", "banner.png")
    save(icon(512, rounded=False), *android, "media", "playstore.png")
    drawable = (*android, "xbmc", "res", "drawable")
    write(vector('android:fillColor="#FFFFFFFF"'), *drawable, "ic_launcher_foreground.xml")
    write(vector('android:fillColor="#FFFFFFFF"'), *drawable, "ic_monochrome_foreground.xml")
    write(f"""<?xml version="1.0" encoding="utf-8"?>
<!-- BingeTV icon background (generated by tools/make_branding.py) -->
<shape xmlns:android="http://schemas.android.com/apk/res/android">
  <gradient android:angle="315"
      android:startColor="#FF{VIOLET[0]:02X}{VIOLET[1]:02X}{VIOLET[2]:02X}"
      android:endColor="#FF{PINK[0]:02X}{PINK[1]:02X}{PINK[2]:02X}"/>
</shape>
""", *drawable, "ic_launcher_background.xml")
    save(silhouette(36), *drawable, "notif_icon.png")
    save(icon(80), *drawable, "ic_recommendation_80dp.png")

    # Kodi's own media/: splash screens, window icons and the "vendor" images skins show.
    save(splash((1920, 1080)), "media", "applaunch_screen.png")
    save(splash((1920, 1080)), "media", "splash.jpg")
    save(banner((320, 180)), "media", "banner.png")
    for size in (16, 32, 48, 80, 120, 256):
        save(icon(size, rounded=False).convert("RGB"), "media", f"icon{size}x{size}.png")
    save(silhouette(128), "media", "vendor_icon.png")
    logo = Image.new("RGBA", (465, 128), (0, 0, 0, 0))
    logo.paste(icon(108), (0, 10), icon(108))
    wordmark(ImageDraw.Draw(logo), (126, 64), 74)
    save(logo, "media", "vendor_logo.png")


if __name__ == "__main__":
    main()
