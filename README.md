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

Backup MPD/system configs
- Added config backups for MPD and ALSA state under `config/`.

Initial commit
- Added `break-music` layout, MPD state, and music files.
