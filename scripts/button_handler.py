#!/usr/bin/env python3
import re
import subprocess
import threading
import time

from gpiozero import Button

BUTTON_PIN = 17  # BCM numbering
BOUNCE_SECONDS = 0.05
DOUBLE_PRESS_WINDOW = 0.4
HOLD_SECONDS = 2.0
FADE_SECONDS = 5
FADE_STEPS = 50
BASE_VOLUME = 100
MPD_PORTS = (6601, 6602)


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
        trigger_shutdown()

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
                trigger_next_crossfade()
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
        handle_single_press()


def run_mpc(port, *args, check=True):
    cmd = ["mpc", "-p", str(port), *args]
    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )
    return result.stdout.strip()


def get_volume(port):
    status = run_mpc(port, "status")
    match = re.search(r"volume:\s*(\d+)%", status)
    if not match:
        return 0
    return int(match.group(1))


def set_volume(port, volume):
    volume = max(0, min(BASE_VOLUME, int(round(volume))))
    run_mpc(port, "volume", str(volume))


def pause_if_playing(port):
    run_mpc(port, "pause-if-playing", check=False)


def resume_playback(port):
    run_mpc(port, "play")


def fade_all(target_volume):
    step_time = FADE_SECONDS / FADE_STEPS
    start_volumes = [get_volume(p) for p in MPD_PORTS]
    for step in range(FADE_STEPS + 1):
        t = step / FADE_STEPS
        for port, start in zip(MPD_PORTS, start_volumes):
            vol = start + (target_volume - start) * t
            set_volume(port, vol)
        time.sleep(step_time)
    print(f"fade complete: target={target_volume}%")


def handle_single_press():
    try:
        volumes = [get_volume(p) for p in MPD_PORTS]
        if max(volumes) > 0:
            print("fading down and pausing")
            fade_all(0)
            for port in MPD_PORTS:
                pause_if_playing(port)
            print("playback paused")
            return

        print("resuming and fading up")
        for port in MPD_PORTS:
            resume_playback(port)
        fade_all(BASE_VOLUME)
        print("playback resumed")
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.strip() if exc.stderr else "unknown error"
        print(f"mpc error: {err}")


def trigger_next_crossfade():
    volumes = [get_volume(p) for p in MPD_PORTS]
    if max(volumes) <= 0:
        print("double press ignored (volume is 0)")
        return
    result = subprocess.run(
        ["sudo", "systemctl", "kill", "-s", "USR1", "crossfade-controller.service"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        print("requested immediate crossfade (watch journalctl -u crossfade-controller -f for completion)")
    else:
        err = result.stderr.strip() or "unknown error"
        print(f"crossfade signal error: {err}")


def trigger_shutdown():
    result = subprocess.run(
        ["sudo", "systemctl", "poweroff"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        print("shutdown requested")
    else:
        err = result.stderr.strip() or "unknown error"
        print(f"shutdown error: {err}")


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
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting on Ctrl+C")


if __name__ == "__main__":
    main()
