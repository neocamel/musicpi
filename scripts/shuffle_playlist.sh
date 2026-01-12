#!/usr/bin/env bash
set -euo pipefail

music_dir="/home/brispo/break-music/music"
output_file="/home/brispo/break-music/shuffled_playlist.txt"

find "$music_dir" -maxdepth 1 -type f -name "*.mp3" -printf "%f\n" | shuf > "$output_file"
