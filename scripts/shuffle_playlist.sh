#!/usr/bin/env bash
set -euo pipefail

music_dir="/home/brispo/musicpi/music"
output_file="/home/brispo/musicpi/shuffled_playlist.txt"

find "$music_dir" -maxdepth 1 -type f -name "*.mp3" -printf "%f\n" | shuf > "$output_file"
