"""
Sky display for the Quiet Coyote Sleep Tracker: one flat-gradient scene per state
on the 240x135 Mini PiTFT.

    python sky_display.py --preview all                  # GIF + 4x PNG per state, no hardware
    python sky_display.py --preview night --out previews
    python sky_display.py --pi                           # cycle the states on the PiTFT

render() only uses Pillow, so every state can be checked on a laptop. SkyDisplay
talks to the screen and refuses to start while piscreen.service owns it.
"""
import argparse
import datetime
import math
import os
import random
import subprocess
import time

from PIL import Image, ImageDraw, ImageFont

W, H = 240, 135
HORIZON = 96          # where the hills meet the sky
NIGHT_CAP = 0.6       # overall brightness at night, 1.0 = full

# Sky colors (top to horizon) and hill colors, sampled from the Higgsfield mood board.
PALETTES = {
    "day": {"sky": [(61, 168, 253), (95, 192, 252), (141, 222, 249), (170, 239, 247)],
            "back": (124, 172, 122), "front": (97, 143, 99)},
    "sunset": {"sky": [(29, 19, 105), (80, 21, 120), (175, 31, 116), (224, 61, 79)],
               "back": (60, 24, 98), "front": (37, 10, 72)},
    "night": {"sky": [(1, 7, 25), (2, 9, 29), (4, 14, 39), (6, 19, 50)],
              "back": (5, 15, 42), "front": (2, 9, 29)},
    "sunrise": {"sky": [(132, 147, 221), (188, 162, 203), (251, 170, 140), (254, 184, 106)],
                "back": (214, 132, 132), "front": (109, 133, 114)},
}
SUN = {"day": (255, 232, 110), "sunset": (255, 122, 52), "sunrise": (255, 236, 140)}
MOON = (232, 224, 196)

# Minute of the day -> which palette, blended between neighbours (DORMANT follows the clock).
SKY_BY_MINUTE = [(0, "night"), (330, "night"), (390, "sunrise"), (480, "day"),
                 (1050, "day"), (1140, "sunset"), (1230, "night"), (1440, "night")]
SUNRISE_MIN, SUNSET_MIN = 390, 1140   # 6:30 and 19:00, fixed for now

FONTS = {
    False: ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"],
    True: ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"],
}
_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        for path in FONTS[bold]:
            if os.path.exists(path):
                _font_cache[key] = ImageFont.truetype(path, size)
                break
        else:
            _font_cache[key] = ImageFont.load_default(size)
    return _font_cache[key]


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def lerp(a, b, f):
    return tuple(round(x + (y - x) * f) for x, y in zip(a, b))


def mix(p, q, f):
    """Blend two palettes; f=0 is p, f=1 is q."""
    if isinstance(p, str):
        p = PALETTES[p]
    if isinstance(q, str):
        q = PALETTES[q]
    return {"sky": [lerp(a, b, f) for a, b in zip(p["sky"], q["sky"])],
            "back": lerp(p["back"], q["back"], f), "front": lerp(p["front"], q["front"], f)}


def palette_at(minute):
    for (m0, a), (m1, b) in zip(SKY_BY_MINUTE, SKY_BY_MINUTE[1:]):
        if m0 <= minute < m1:
            return mix(a, b, (minute - m0) / (m1 - m0))
    return mix("night", "night", 0)


def sky_color(pal, y):
    stops = pal["sky"]
    f = clamp(y / (HORIZON + 10)) * (len(stops) - 1)
    i = min(int(f), len(stops) - 2)
    return lerp(stops[i], stops[i + 1], f - i)


def draw_sky(img, pal):
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line((0, y, W, y), fill=sky_color(pal, y))


def draw_hills(img, pal):
    d = ImageDraw.Draw(img)
    back = [(x, HORIZON + 6 * math.sin(x / 38 + 1.0)) for x in range(0, W + 4, 4)]
    front = [(x, HORIZON + 13 + 5 * math.sin(x / 55 + 3.0)) for x in range(0, W + 4, 4)]
    d.polygon(back + [(W, H), (0, H)], fill=pal["back"])
    d.polygon(front + [(W, H), (0, H)], fill=pal["front"])


def draw_disc(img, center, r, color, glow=0, crescent=False):
    """Sun (with a soft glow) or crescent moon, composited over the sky."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = center
    for i in range(glow, 0, -1):
        a = round(110 * (1 - i / (glow + 1)) ** 1.5)
        d.ellipse((x - r - i, y - r - i, x + r + i, y + r + i), fill=color + (a,))
    d.ellipse((x - r, y - r, x + r, y + r), fill=color + (255,))
    if crescent:
        o = r * 0.55
        d.ellipse((x - r + o, y - r - o * 0.4, x + r + o, y + r - o * 0.4), fill=(0, 0, 0, 0))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"))


def draw_stars(img, pal, alpha, t, n=34, seed=5):
    if alpha <= 0:
        return
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)              # same sky every frame; only the twinkle moves
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(HORIZON - 12)
        base, phase = rng.uniform(0.35, 1.0), rng.uniform(0, 2 * math.pi)
        b = alpha * base * (0.75 + 0.25 * math.sin(1.3 * t + phase))
        d.point((x, y), fill=lerp(sky_color(pal, y), (255, 255, 240), b))


def draw_text(img, xy, text, size, color=(255, 255, 255), bold=False, anchor="la", fade=1.0):
    d = ImageDraw.Draw(img)
    f = font(size, bold)
    x, y = xy
    under = img.getpixel((int(clamp(x, 0, W - 1)), int(clamp(y, 0, H - 1))))
    d.text((x + 1, y + 1), text, font=f, anchor=anchor, fill=lerp(under, (0, 0, 0), 0.5 * fade))
    d.text((x, y), text, font=f, anchor=anchor, fill=lerp(under, color, fade))


def dim(img, k):
    return img if k >= 1 else img.point(lambda v: int(v * k))


def arc(frac, height):
    """Position along a left-to-right arc over the hills; frac 0..1."""
    return 20 + frac * (W - 40), HORIZON + 2 - math.sin(math.pi * clamp(frac)) * height


def hhmm(t):
    return f"{t.hour}:{t.minute:02d}"


def render(state, ctx, now, p=1.0, t=0.0):
    """One 240x135 frame.

    state: dormant, goodnight, night, alarm or report.
    ctx:   bedtime, alarm (datetimes), events (list of datetimes), slept (timedelta or None),
           show_events (bool).
    p:     progress of a transition (goodnight sunset, alarm sunrise), 0..1.
    t:     seconds, only for the star twinkle.
    """
    img = Image.new("RGB", (W, H))
    state = state.lower()

    if state == "dormant":
        minute = now.hour * 60 + now.minute
        pal = palette_at(minute)
        draw_sky(img, pal)
        night = clamp((60 - sum(pal["sky"][0]) / 3) / 50)
        draw_stars(img, pal, night, t)
        if SUNRISE_MIN - 20 <= minute <= SUNSET_MIN + 20:
            frac = (minute - SUNRISE_MIN) / (SUNSET_MIN - SUNRISE_MIN)
            sun = SUN["day"] if 0.1 < frac < 0.9 else SUN["sunrise"]
            draw_disc(img, arc(frac, 70), 9, sun, glow=8)
        else:
            frac = ((minute - SUNSET_MIN) % 1440) / (1440 - SUNSET_MIN + SUNRISE_MIN)
            draw_disc(img, arc(frac, 60), 7, MOON, crescent=True)
        draw_hills(img, pal)
        draw_text(img, (6, 4), hhmm(now), 14)
        draw_text(img, (W - 6, H - 4), f"alarm {hhmm(ctx['alarm'])}", 11, anchor="rs")

    elif state == "goodnight":
        pal = mix("sunset", "night", p)
        draw_sky(img, pal)
        draw_stars(img, pal, p, t)
        draw_disc(img, (160, HORIZON - 4 + 30 * p), 10, lerp(SUN["sunset"], (120, 40, 60), p), glow=8)
        draw_hills(img, pal)
        draw_text(img, (W / 2, 46), "Good night", 22, bold=True, anchor="mm", fade=clamp(p * 1.6))
        img = dim(img, 1 - p * (1 - NIGHT_CAP))

    elif state == "night":
        pal = PALETTES["night"]
        span = (ctx["alarm"] - ctx["bedtime"]).total_seconds()
        q = clamp((now - ctx["bedtime"]).total_seconds() / span) if span > 0 else 0
        draw_sky(img, pal)
        draw_stars(img, pal, 1.0, t)
        draw_disc(img, arc(q, 62), 7, MOON, crescent=True)
        draw_hills(img, pal)
        if ctx.get("show_events"):
            d = ImageDraw.Draw(img)
            for e in ctx["events"]:
                if e <= now:
                    x = 20 + clamp((e - ctx["bedtime"]).total_seconds() / span) * (W - 40)
                    d.point([(x, H - 8), (x, H - 9)], fill=(40, 60, 95))
        img = dim(img, NIGHT_CAP)

    elif state == "alarm":
        pal = mix("night", "sunrise", p)
        draw_sky(img, pal)
        draw_stars(img, pal, 1 - p, t)
        draw_disc(img, (W / 2, HORIZON + 22 - 40 * p), 11, SUN["sunrise"], glow=round(4 + 8 * p))
        draw_hills(img, pal)
        if p >= 0.9:
            pulse = 0.85 + 0.15 * math.sin(4 * t)
            draw_text(img, (W / 2, 34), hhmm(ctx["alarm"]), 30, bold=True, anchor="mm",
                      fade=clamp((p - 0.9) * 10) * pulse)
        img = dim(img, NIGHT_CAP + (1 - NIGHT_CAP) * p)

    elif state == "report":
        pal = mix("sunrise", "day", 0.45)
        draw_sky(img, pal)
        draw_disc(img, (205, 26), 8, SUN["day"], glow=7)
        draw_hills(img, pal)
        if ctx.get("slept") is None:
            draw_text(img, (W / 2, 32), "No sleep data", 20, bold=True, anchor="mm")
            draw_text(img, (W / 2, 58), "The night was not tracked.", 12, anchor="mm")
        else:
            mins = round(ctx["slept"].total_seconds() / 60)
            draw_text(img, (W / 2, 14), "you slept", 12, anchor="mm")
            draw_text(img, (W / 2, 40), f"{mins // 60} h {mins % 60:02d} min", 26, bold=True, anchor="mm")
            draw_timeline(img, ctx)
    else:
        raise ValueError(f"unknown state: {state}")
    return img


def draw_timeline(img, ctx):
    """Bottom strip from bedtime to wake-up, one tick per logged event."""
    x0, x1, y0, y1 = 16, W - 16, H - 30, H - 22
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((x0 - 4, y0 - 3, x1 + 4, H - 4), 4, fill=(0, 0, 0, 120))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"))
    d = ImageDraw.Draw(img)
    d.rectangle((x0, y0, x1, y1), fill=(40, 52, 90))
    start, end = ctx["bedtime"], ctx.get("wake", ctx["alarm"])
    span = (end - start).total_seconds()
    for e in ctx["events"]:
        x = x0 + clamp((e - start).total_seconds() / span) * (x1 - x0)
        d.line((x, y0 - 1, x, y1 + 1), fill=(255, 200, 80), width=2)
    draw_text(img, (x0, H - 6), hhmm(start), 10, anchor="ls")
    draw_text(img, (x1, H - 6), hhmm(end), 10, anchor="rs")
    n = len(ctx["events"])
    draw_text(img, (W / 2, H - 6), f"{n} event{'s' if n != 1 else ''}", 10, anchor="ms")


def sample_ctx(day=None):
    """A made-up night for previews: 23:25 to 7:00, one visit at 2:47."""
    day = day or datetime.date(2026, 11, 1)
    bed = datetime.datetime.combine(day, datetime.time(23, 25))
    alarm = datetime.datetime.combine(day + datetime.timedelta(days=1), datetime.time(7, 0))
    return {"bedtime": bed, "alarm": alarm, "wake": alarm, "slept": alarm - bed,
            "events": [alarm.replace(hour=2, minute=47)], "show_events": False}


def preview_frames(state, ctx):
    """(frames, ms per frame, index of the frame to save as a still)."""
    bed, alarm = ctx["bedtime"], ctx["alarm"]
    if state == "dormant":
        start = datetime.datetime.combine(bed.date(), datetime.time(0, 0))
        frames = [render("dormant", ctx, start + datetime.timedelta(minutes=m), t=m / 20)
                  for m in range(0, 1440, 20)]
        return frames, 120, 33
    if state == "goodnight":
        frames = [render("goodnight", ctx, bed, p=i / 59, t=i * 0.1) for i in range(60)]
        return frames + frames[-1:] * 10, 100, 59
    if state == "night":
        span = alarm - bed
        frames = [render("night", ctx, bed + span * (i / 59), t=i * 0.4) for i in range(60)]
        return frames, 120, 30
    if state == "alarm":
        frames = [render("alarm", ctx, alarm, p=i / 39, t=i * 0.1) for i in range(40)]
        frames += [render("alarm", ctx, alarm, p=1.0, t=4 + i * 0.1) for i in range(20)]
        return frames, 100, 50
    if state == "report":
        return [render("report", ctx, alarm)], 1000, 0
    if state == "report-empty":
        return [render("report", dict(ctx, slept=None, events=[]), alarm)], 1000, 0
    raise ValueError(state)


STATES = ["dormant", "goodnight", "night", "alarm", "report", "report-empty"]


def write_preview(state, out):
    frames, ms, still = preview_frames(state, sample_ctx())
    os.makedirs(out, exist_ok=True)
    gif = os.path.join(out, f"sky-{state}.gif")
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=ms, loop=0)
    frames[still].resize((W * 4, H * 4), Image.NEAREST).save(os.path.join(out, f"sky-{state}-4x.png"))
    print(f"{gif}: {len(frames)} frames")


class SkyDisplay:
    """The Mini PiTFT, set up as in Lab 2's screen_clock.py."""

    def __init__(self):
        if subprocess.run(["systemctl", "is-active", "--quiet", "piscreen.service"]).returncode == 0:
            raise RuntimeError("piscreen.service owns the screen; stop it first (and restart it afterwards)")
        import board
        import digitalio
        import adafruit_rgb_display.st7789 as st7789
        self.cs = digitalio.DigitalInOut(board.D5)
        self.dc = digitalio.DigitalInOut(board.D25)
        self.spi = board.SPI()
        self.disp = st7789.ST7789(self.spi, cs=self.cs, dc=self.dc, rst=None, baudrate=64000000,
                                  width=135, height=240, x_offset=53, y_offset=40)
        self.backlight = digitalio.DigitalInOut(board.D22)
        self.backlight.switch_to_output(value=True)

    def show(self, img):
        self.disp.image(img, 90)

    def close(self):
        self.show(Image.new("RGB", (W, H)))
        for pin in (self.backlight, self.cs, self.dc, self.spi):
            pin.deinit()


def run_pi():
    """Cycle every state's preview frames on the screen and report the frame rate."""
    screen = SkyDisplay()
    try:
        for state in STATES:
            frames, ms, _ = preview_frames(state, sample_ctx())
            t0 = time.time()
            for f in frames:
                screen.show(f)
            pushed = time.time() - t0
            print(f"{state}: {len(frames)} frames, {len(frames) / pushed:.1f} fps max", flush=True)
            for f in frames:                          # again at the intended speed
                screen.show(f)
                time.sleep(ms / 1000)
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        screen.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", choices=STATES + ["all"], help="write GIF and PNG previews, no hardware")
    parser.add_argument("--out", default="sky_previews", help="folder for previews")
    parser.add_argument("--pi", action="store_true", help="cycle the states on the PiTFT")
    args = parser.parse_args()
    if args.preview:
        for s in STATES if args.preview == "all" else [args.preview]:
            write_preview(s, args.out)
    elif args.pi:
        run_pi()
    else:
        parser.print_help()
