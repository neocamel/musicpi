#!/usr/bin/env python3
import threading
import time

from gpiozero import Button

BUTTON_PIN = 17  # BCM numbering
BOUNCE_SECONDS = 0.05
DOUBLE_PRESS_WINDOW = 0.4
HOLD_SECONDS = 2.0


class PressDetector:
    def __init__(self, button):
        self.button = button
        self.pending_single = False
        self.single_timer = None
        self.press_start = 0.0
        self.long_press_active = False
        self.lock = threading.Lock()

        self.button.when_pressed = self.on_press
        self.button.when_released = self.on_release
        self.button.when_held = self.on_hold

    def on_press(self):
        with self.lock:
            self.press_start = time.monotonic()
            self.long_press_active = False

    def on_hold(self):
        with self.lock:
            self.long_press_active = True
            if self.single_timer:
                self.single_timer.cancel()
                self.single_timer = None
            self.pending_single = False
        print("long press")

    def on_release(self):
        if self.long_press_active:
            with self.lock:
                self.long_press_active = False
            return

        with self.lock:
            if self.pending_single:
                if self.single_timer:
                    self.single_timer.cancel()
                    self.single_timer = None
                self.pending_single = False
                print("double press")
                return
            self.pending_single = True
            self.single_timer = threading.Timer(
                DOUBLE_PRESS_WINDOW, self.emit_single
            )
            self.single_timer.start()

    def emit_single(self):
        with self.lock:
            if not self.pending_single:
                return
            self.pending_single = False
            self.single_timer = None
        print("single press")


def main():
    button = Button(
        BUTTON_PIN,
        pull_up=True,
        bounce_time=BOUNCE_SECONDS,
        hold_time=HOLD_SECONDS,
    )
    PressDetector(button)
    print(
        f"Listening on GPIO{BUTTON_PIN} (single/double/long). "
        f"hold={HOLD_SECONDS}s double_window={DOUBLE_PRESS_WINDOW}s"
    )
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
