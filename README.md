# musicpi

This repo tracks the Raspberry Pi MPD setup, scripts, and playlist tooling.

Change log (notes between commits):

v2
- Added `mpd2` instance on port 6602 with separate state/db/playlist paths.
- Added crossfade controller to overlap tracks by 15s using a shared playlist.
- Added shuffle script to generate `shuffled_playlist.txt` with relative paths.
- Switched MPD output to PipeWire/Pulse with ACLs for the `mpd` user.
- Updated backed-up configs under `config/` (mpd1/mpd2 service + config).

v3
- Added equal-power fade in/out during the 15s overlap.
- Added 5s incoming track seek (not applied to the first track).
- Improved crossfade controller logging and shutdown behavior.

v4
- Fixed boot-time Pulse/PipeWire auth for MPD by granting cookie access.
- Added boot-time wait for Pulse socket before starting MPD.
- Boot automation now starts audio reliably after reboot.

v5
- Added GPIO button handler with debounce and single/double/long press detection.

v6
- Added button-driven immediate crossfade signaling.
- Tuned immediate crossfade to 3s overlap.
- Improved crossfade logging/skip handling.
- Added GPIO button handler actions (fade/pause, immediate crossfade, shutdown).
- Added button-handler systemd service for boot automation.

v7
- Updated MPD runtime state after button handler rollout.

v8
- Made immediate crossfade response near-instant using interruptible waits.

v9
- Added Pulse readiness wait and output auto-enable in crossfade controller.
- Added MPD service auto-restart for better reliability.
- Added reflash/migration checklist to cheatsheet.

v10
- Cleaned up duplicate journal logging by preferring syslog over stdout.

v14
- Repointed all service/config/script paths to `/home/brispo/musicpi` after OS reflash.
- Installer now installs `acl` for MPD Pulse access and recreates MPD state/playlist dirs.
- Systemd units and MPD configs updated to match the new repo layout.

Backup MPD/system configs
- Added config backups for MPD and ALSA state under `config/`.

Initial commit
- Added `break-music` layout, MPD state, and music files.
