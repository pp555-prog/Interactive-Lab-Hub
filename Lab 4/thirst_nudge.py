import sys
import time
import qwiic_proximity
import pi_servo_hat

# Thirst Nudge
# A mug on the coaster is detected by a Qwiic proximity sensor looking up
# through a window under the mug. If the mug sits untouched for NUDGE_AFTER
# seconds, a servo slowly raises a "sip!" flag and wiggles it now and then.
# Lifting the mug drops the flag right away; putting it back restarts the timer.
#
# Usage: python thirst_nudge.py [seconds before the nudge]

SERVO_CH = 0
FLAG_DOWN = 0     # servo position with the flag lying flat
FLAG_UP = 90      # servo position with the flag raised
WIGGLE = 10       # how far the flag wiggles while nudging

# Measured through the cardboard window with my mug:
# empty ~49, mug resting ~12,100, mug lifted 5 cm 190-1,000.
MUG_THRESHOLD = 3000

READ_DELAY = 0.2          # seconds between proximity readings
CONFIRM_READS = 3         # readings in a row needed to change state
NUDGE_AFTER = 20.0        # seconds untouched before the flag rises (demo value)
WIGGLE_EVERY = 30.0       # seconds between reminder wiggles while nudging
RAISE_TIME = 1.5          # seconds for the slow flag raise

if len(sys.argv) > 1:
    NUDGE_AFTER = float(sys.argv[1])


# --- Set up proximity sensor ---
# begin() occasionally fails on our sensor (a rejected I2C write), so retry it.
proximity_sensor = qwiic_proximity.QwiicProximity()

if not proximity_sensor.connected:
    raise RuntimeError(
        "Qwiic proximity sensor not found. Check the Qwiic connection."
    )

for attempt in range(5):
    try:
        proximity_sensor.begin()
        break
    except OSError:
        time.sleep(0.2)
else:
    raise RuntimeError("Proximity sensor did not start after 5 tries.")


# --- Set up servo ---
servo = pi_servo_hat.PiServoHat()
servo.restart()
servo.move_servo_position(SERVO_CH, FLAG_DOWN)


def raise_flag():
    steps = 15
    for i in range(1, steps + 1):
        servo.move_servo_position(SERVO_CH, FLAG_DOWN + (FLAG_UP - FLAG_DOWN) * i / steps)
        time.sleep(RAISE_TIME / steps)


def wiggle_flag():
    for offset in (WIGGLE, -WIGGLE, WIGGLE, 0):
        servo.move_servo_position(SERVO_CH, FLAG_UP + offset)
        time.sleep(0.15)


print("Thirst Nudge ready!")
print(f"Place a mug on the coaster. Nudge after {NUDGE_AFTER:.0f} s untouched.")


state = "empty"        # empty -> resting -> nudging
streak = 0             # readings in a row that disagree with the current state
rested_since = 0.0
last_wiggle = 0.0
sips = 0

try:
    while True:
        proximity = proximity_sensor.get_proximity()
        mug_seen = proximity >= MUG_THRESHOLD
        now = time.monotonic()

        # Count readings that disagree with the state, so one odd reading
        # (like the spike when a mug is set down) does not flip it.
        if mug_seen == (state == "empty"):
            streak += 1
        else:
            streak = 0

        if state == "empty" and streak >= CONFIRM_READS:
            state, streak = "resting", 0
            rested_since = now
            print(f"\nMug placed (proximity {proximity}). Timer started.")

        elif state != "empty" and streak >= CONFIRM_READS:
            if state == "nudging":
                servo.move_servo_position(SERVO_CH, FLAG_DOWN)
            sips += 1
            state, streak = "empty", 0
            print(f"\nMug lifted (proximity {proximity}). Sips so far: {sips}")

        elif state == "resting" and now - rested_since >= NUDGE_AFTER:
            state = "nudging"
            print("\nUntouched too long: raising the flag.")
            raise_flag()
            last_wiggle = time.monotonic()

        elif state == "nudging" and now - last_wiggle >= WIGGLE_EVERY:
            wiggle_flag()
            last_wiggle = time.monotonic()

        print(f"Proximity: {proximity:6d}  state: {state:8s}", end="\r")
        time.sleep(READ_DELAY)

except KeyboardInterrupt:
    print("\nStopping Thirst Nudge.")
    servo.move_servo_position(SERVO_CH, FLAG_DOWN)
