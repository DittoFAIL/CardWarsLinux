#!/usr/bin/env bash
set -euo pipefail

game_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
player="$game_dir/CardWars.x86_64"
if [[ ! -f "$player" || ! -d "$game_dir/CardWars_Data" ]]; then
    printf '%s\n' 'Card Wars Linux player or CardWars_Data is missing. Extract the entire build archive.' >&2
    exit 1
fi
if [[ ! -x "$player" ]]; then
    printf '%s\n' 'CardWars.x86_64 is not executable. Run chmod +x CardWars.x86_64, or extract the tar.gz again on Linux.' >&2
    exit 1
fi

# Unity 2017 uses X11 (via Gamescope/XWayland on Steam Deck) and desktop OpenGL.
# Preserve the Steam runtime environment and pass all player options unchanged.
cd -- "$game_dir"
exec "$player" "$@"
