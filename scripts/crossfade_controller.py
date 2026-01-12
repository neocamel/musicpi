#!/usr/bin/env python3
import math
import re
import subprocess
import time
from pathlib import Path

PLAYLIST_FILE = Path("/home/brispo/break-music/shuffled_playlist.txt")
MUSIC_DIR = Path("/home/brispo/break-music/music")
PORT1 = 6601
PORT2 = 6602
OVERLAP_SECONDS = 15
FADE_SECONDS = 5
FADE_STEPS = 50
BASE_VOLUME = 100
INCOMING_OFFSET_SECONDS = 5


def log(msg):
    print(msg, flush=True)


def run_mpc(port, *args):
    cmd = ["mpc", "-p", str(port), *args]
    return subprocess.check_output(cmd, text=True).strip()


def parse_duration(duration_str):
    # Expected format: M:SS or H:MM:SS
    if not duration_str:
        return 0
    parts = duration_str.split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return 0
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


def get_elapsed_total(port):
    status = run_mpc(port, "status")
    # Look for the "elapsed/total" segment in status output.
    match = re.search(r"(\d+:\d+(?::\d+)?)/(\d+:\d+(?::\d+)?)", status)
    if not match:
        return 0, 0
    elapsed = parse_duration(match.group(1))
    total = parse_duration(match.group(2))
    return elapsed, total


def play_track(port, rel_path):
    log(f"[mpd{port}] play: {rel_path}")
    run_mpc(port, "clear")
    run_mpc(port, "add", rel_path)
    run_mpc(port, "play")


def stop_track(port):
    log(f"[mpd{port}] stop")
    run_mpc(port, "stop")
    run_mpc(port, "clear")


def set_volume(port, volume):
    volume = max(0, min(BASE_VOLUME, int(round(volume))))
    run_mpc(port, "volume", str(volume))


def seek_if_needed(port, seconds):
    if seconds <= 0:
        return
    # Give MPD a moment to load the new track before seeking.
    time.sleep(0.1)
    run_mpc(port, "seek", str(seconds))


def load_playlist():
    if not PLAYLIST_FILE.exists():
        raise SystemExit(f"Playlist file not found: {PLAYLIST_FILE}")
    tracks = []
    for line in PLAYLIST_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        tracks.append(line)
    if not tracks:
        raise SystemExit("Playlist file is empty")
    return tracks


def main():
    tracks = load_playlist()
    index = 0
    active = PORT1
    standby = PORT2

    log(f"Loaded {len(tracks)} tracks from {PLAYLIST_FILE}")
    log("Initializing MPD instances")
    stop_track(PORT1)
    stop_track(PORT2)
    set_volume(active, BASE_VOLUME)
    play_track(active, tracks[index])
    first_track = False

    while True:
        elapsed, total = get_elapsed_total(active)
        if total <= 0:
            log(f"[mpd{active}] unknown track length; retrying")
            time.sleep(1)
            continue

        remaining = max(0, total - elapsed)
        until_overlap = max(0, remaining - OVERLAP_SECONDS)
        log(
            f"[mpd{active}] elapsed {elapsed}s / {total}s; "
            f"{until_overlap}s until overlap"
        )

        # Wait until we're OVERLAP_SECONDS from the end, recalculating
        # to avoid drift when a track started before we entered the loop.
        last_log = time.time()
        while remaining > OVERLAP_SECONDS:
            until_overlap = max(0, remaining - OVERLAP_SECONDS)
            wait = 1 if until_overlap <= 5 else min(5, until_overlap)
            time.sleep(wait)
            elapsed, total = get_elapsed_total(active)
            if total <= 0:
                break
            remaining = max(0, total - elapsed)
            until_overlap = max(0, remaining - OVERLAP_SECONDS)
            now = time.time()
            if until_overlap <= 5:
                log(f"[mpd{active}] {until_overlap}s to overlap")
                last_log = now
            elif now - last_log >= 10:
                log(f"[mpd{active}] {until_overlap}s to overlap")
                last_log = now

        index = (index + 1) % len(tracks)
        # Start incoming track muted, then fade in while outgoing fades out.
        set_volume(standby, 0)
        play_track(standby, tracks[index])
        if not first_track:
            seek_if_needed(standby, INCOMING_OFFSET_SECONDS)

        fade_step_time = FADE_SECONDS / FADE_STEPS
        log(f"[mpd{active}] fading out over {FADE_SECONDS}s")
        log(f"[mpd{standby}] fading in over {FADE_SECONDS}s")
        for step in range(FADE_STEPS + 1):
            theta = (step / FADE_STEPS) * (math.pi / 2.0)
            out_gain = math.cos(theta)
            in_gain = math.sin(theta)
            set_volume(active, BASE_VOLUME * out_gain)
            set_volume(standby, BASE_VOLUME * in_gain)
            time.sleep(fade_step_time)

        overlap = min(OVERLAP_SECONDS, total)
        log(f"[mpd{active}] overlapping for {overlap}s")
        time.sleep(max(0, overlap - FADE_SECONDS))
        stop_track(active)

        active, standby = standby, active


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Stopping playback on Ctrl+C")
        stop_track(PORT1)
        stop_track(PORT2)
        log("Exiting on Ctrl+C")
