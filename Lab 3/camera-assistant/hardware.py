"""Opt-in adapters; do not enable the TFT while piscreen.service owns it."""
import threading
import subprocess


class Hardware:
    def __init__(self, trigger, state, button_address=None, display=False, on_error=None):
        self.trigger, self.state = trigger, state
        self.on_error = on_error
        self.button = None
        self.display = None
        self.stop = threading.Event()
        if button_address is not None:
            import qwiic_button
            self.button = qwiic_button.QwiicButton(address=button_address)
            if not self.button.begin():
                raise RuntimeError("Qwiic button not found at configured address")
        if display:
            if subprocess.run(["systemctl", "is-active", "--quiet", "piscreen.service"],
                              check=False).returncode == 0:
                raise RuntimeError("piscreen.service owns the TFT; arrange a temporary handover first")
            import board
            import digitalio
            from adafruit_rgb_display import st7789
            self.display = st7789.ST7789(board.SPI(),
                cs=digitalio.DigitalInOut(board.D5),
                dc=digitalio.DigitalInOut(board.D25),
                rst=None, baudrate=24000000, width=135, height=240,
                x_offset=53, y_offset=40, rotation=90)
            self.backlight = digitalio.DigitalInOut(board.D22)
            self.backlight.switch_to_output(value=True)

    def run(self):
        pressed_before, previous_state = False, None
        try:
            while not self.stop.wait(0.05):
                state = self.state()
                if self.button:
                    pressed = self.button.is_button_pressed()
                    if pressed and not pressed_before:
                        self.trigger()
                    pressed_before = pressed
                if state != previous_state:
                    if self.button:
                        if state == "LISTENING":
                            self.button.LED_config(100, 0, 0)
                        else:
                            self.button.LED_off()
                    if self.display:
                        from PIL import Image, ImageDraw, ImageFont
                        canvas = Image.new("RGB", (240, 135), "black")
                        draw = ImageDraw.Draw(canvas)
                        for size in range(64, 11, -1):
                            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
                            left, top, right, bottom = draw.textbbox((0, 0), state, font=font)
                            if right - left <= 220 and bottom - top <= 115:
                                break
                        position = ((240 - (right - left)) // 2 - left,
                                    (135 - (bottom - top)) // 2 - top)
                        draw.text(position, state, font=font, fill="lime")
                        self.display.image(canvas)
                    previous_state = state
        except Exception as exc:
            if self.on_error:
                self.on_error(f"Hardware adapter stopped: {type(exc).__name__}: {exc}")
            else:
                raise
        finally:
            if self.button:
                try:
                    self.button.LED_off()
                except OSError:
                    pass
