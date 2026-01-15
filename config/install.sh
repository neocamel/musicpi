#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo $ROOT_DIR/install.sh" >&2
  exit 1
fi

install -d /etc/mpd /etc/systemd/system /etc/sudoers.d
install -m 0644 "$ROOT_DIR/mpd/mpd1.conf" /etc/mpd/mpd1.conf
install -m 0644 "$ROOT_DIR/mpd/mpd2.conf" /etc/mpd/mpd2.conf

install -m 0644 "$ROOT_DIR/systemd/mpd1.service" /etc/systemd/system/mpd1.service
install -m 0644 "$ROOT_DIR/systemd/mpd2.service" /etc/systemd/system/mpd2.service
install -m 0644 "$ROOT_DIR/systemd/crossfade-controller.service" /etc/systemd/system/crossfade-controller.service
install -m 0644 "$ROOT_DIR/systemd/shuffle-playlist.service" /etc/systemd/system/shuffle-playlist.service
install -m 0644 "$ROOT_DIR/systemd/button-handler.service" /etc/systemd/system/button-handler.service

install -m 0440 "$ROOT_DIR/sudoers/musicpi-button" /etc/sudoers.d/musicpi-button
install -m 0440 "$ROOT_DIR/sudoers/musicpi-button-poweroff" /etc/sudoers.d/musicpi-button-poweroff

systemctl daemon-reload
systemctl enable --now mpd1 mpd2 shuffle-playlist crossfade-controller button-handler

echo "Install complete."
