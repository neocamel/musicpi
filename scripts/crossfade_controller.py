#!/usr/bin/env python3
import re
import subprocess
import time
from pathlib import Path

PLAYLIST_FILE = Path("/home/brispo/break-music/shuffled_playlist.txt")
MUSIC_DIR = Path("/home/brispo/break-music/music")
PORT1 = 6601
PORT2 = 6602
OVERLAP_SECONDS = 15


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
    play_track(active, tracks[index])

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
        play_track(standby, tracks[index])

        overlap = min(OVERLAP_SECONDS, total)
        log(f"[mpd{active}] overlapping for {overlap}s")
        time.sleep(overlap)
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
