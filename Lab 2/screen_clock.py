import argparse
import datetime
import time
from PIL import Image, ImageDraw, ImageFont


def period_for_minute(minute):
    """Map a local minute of day to a fixed prototype period."""
    if not 0 <= minute < 1440:
        raise ValueError("minute must be in [0, 1439]")
    if 300 <= minute < 660:
        return "MORNING", "A new day begins"
    if 660 <= minute < 1020:
        return "DAY", "Day in progress"
    if 1020 <= minute < 1260:
        return "EVENING", "Day winding down"
    return "NIGHT", "Time to rest"


def render_frame(image, font, now, simulated=False):
    """Render without touching GPIO, so every period can be checked in tests."""
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, image.width, image.height), outline=0, fill=400)
    period, message = period_for_minute(now.hour * 60 + now.minute)
    lines = [
        (10, 6, "SIMULATED" if simulated else "LIVE"),
        (10, 34, period),
        (10, 64, message),
        (10, 98, now.strftime("%H:%M:%S")),
    ]
    for x, y, text in lines:
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
    return lines


def test_time(value):
    try:
        return datetime.datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use HH:MM (00:00 to 23:59)") from exc


def main():
    parser = argparse.ArgumentParser(description="Local time-of-day clock")
    parser.add_argument("--test-time", type=test_time, help="fixed HH:MM, labeled SIMULATED")
    parser.add_argument("--frames", type=int, help="exit after this many one-second frames")
    parser.add_argument("--audio", action="store_true", help="enable USB period sound loops")
    args = parser.parse_args()
    if args.frames is not None and args.frames < 1:
        parser.error("--frames must be positive")

    import digitalio
    import board
    import adafruit_rgb_display.st7789 as st7789

    # Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
    cs_pin = digitalio.DigitalInOut(board.D5)
    dc_pin = digitalio.DigitalInOut(board.D25)
    reset_pin = None

    # Config for display baudrate (default max is 24mhz):
    BAUDRATE = 64000000

    # Setup SPI bus using hardware SPI:
    spi = board.SPI()

    # Create the ST7789 display:
    disp = st7789.ST7789(
        spi,
        cs=cs_pin,
        dc=dc_pin,
        rst=reset_pin,
        baudrate=BAUDRATE,
        width=135,
        height=240,
        x_offset=53,
        y_offset=40,
    )

    # Create blank image for drawing.
    # Make sure to create image with mode 'RGB' for full color.
    height = disp.width  # we swap height/width to rotate it to landscape!
    width = disp.height
    image = Image.new("RGB", (width, height))
    rotation = 90

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
    disp.image(image, rotation)
    # Draw some shapes.
    # First define some constants to allow easy resizing of shapes.
    padding = -2
    top = padding
    bottom = height - padding
    # Move left to right keeping track of the current x position for drawing shapes.
    x = 0

    # Alternatively load a TTF font.  Make sure the .ttf font file is in the
    # same directory as the python script!
    # Some other nice fonts to try: http://www.dafont.com/bitmap.php
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

    # Turn on the backlight
    backlight = digitalio.DigitalInOut(board.D22)
    backlight.switch_to_output()
    backlight.value = True

    audio = None
    if args.audio:
        from audio_output import AudioOutput
        audio = AudioOutput()

    frames = 0
    try:
        while True:
            # Read the Pi's local wall clock afresh on every live frame.
            now = datetime.datetime.now()
            if args.test_time is not None:
                now = datetime.datetime.combine(now.date(), args.test_time)
            render_frame(image, font, now, simulated=args.test_time is not None)
            disp.image(image, rotation)
            if audio is not None:
                audio.update(period_for_minute(now.hour * 60 + now.minute)[0])
            frames += 1
            if args.frames is not None and frames >= args.frames:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if audio is not None:
            audio.stop()
        backlight.deinit()
        cs_pin.deinit()
        dc_pin.deinit()
        spi.deinit()


if __name__ == "__main__":
    main()
