#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${UNITY_EDITOR:-}" || ! -x "$UNITY_EDITOR" ]]; then
    printf '%s\n' 'Set UNITY_EDITOR to an activated Unity 2017.4.40f1 executable with Linux Build Support installed.' >&2
    exit 1
fi
python3 "$project_root/scripts/check-linux.py"
mkdir -p "$project_root/Builds" "$project_root/Logs"
# Each build starts in a fresh directory, including failed builds. No user files are removed.
export CARDWARS_BUILD_DIR
CARDWARS_BUILD_DIR="$(mktemp -d "$project_root/Builds/linux-XXXXXXXX")"
export CARDWARS_SOURCE_REVISION
CARDWARS_SOURCE_REVISION="$(git -C "$project_root" rev-parse HEAD)"
if [[ -n "$(git -C "$project_root" status --porcelain --untracked-files=normal)" ]]; then
    CARDWARS_SOURCE_REVISION="$CARDWARS_SOURCE_REVISION-dirty"
fi
build_log="$project_root/Logs/$(basename "$CARDWARS_BUILD_DIR").log"
printf 'Building Linux player in %s\nUnity log: %s\n' "$CARDWARS_BUILD_DIR" "$build_log"
if ! "$UNITY_EDITOR" -batchmode -nographics -quit \
    -projectPath "$project_root" -buildTarget Linux64 \
    -executeMethod LinuxBuild.Build -logFile "$build_log"; then
    printf 'Unity build failed. See %s\n' "$build_log" >&2
    exit 1
fi
python3 "$project_root/scripts/package-linux.py" "$CARDWARS_BUILD_DIR"
