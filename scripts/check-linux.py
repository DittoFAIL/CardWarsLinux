#!/usr/bin/env python3
"""Static portability checks. Does not compile Unity scripts or shaders."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def check(root):
    errors = []
    version = (root / "ProjectSettings/ProjectVersion.txt").read_text().strip()
    if version != "m_EditorVersion: 2017.4.40f1":
        errors.append("Editor version differs from the supported Unity 2017.4.40f1.")
    settings = (root / "ProjectSettings/EditorBuildSettings.asset").read_text()
    scenes = re.findall(r"- enabled: 1\s+path: (.+)", settings)
    if not scenes or scenes[0] != "Assets/Scene/Scenes/StartupScene.unity":
        errors.append("StartupScene must be the first enabled build scene.")
    for scene in scenes:
        if not (root / scene).is_file():
            errors.append("Missing build scene (check filename case): " + scene)

    paths = list((root / "Assets").rglob("*"))
    by_case = {}
    for path in paths:
        name = path.relative_to(root).as_posix()
        previous = by_case.setdefault(name.casefold(), name)
        if previous != name:
            errors.append("Case-colliding asset paths: " + previous + " and " + name)
        if path.suffix == ".shader" and re.search(r'\bSubProgram\s+"', path.read_text(encoding="utf-8-sig")):
            errors.append("Platform-specific compiled shader needs portable source: " + name)

    for name in ("server_settings.json", "global_settings.json", "Blueprints/db_Tutorials.json"):
        path = root / "Assets/StreamingAssets" / name
        try:
            contents = path.read_text(encoding="utf-8-sig")
            # Upstream MiniJSON accepts a trailing comma in global_settings.json.
            # Do not reject that existing file using Python's stricter JSON parser.
            if name != "global_settings.json":
                json.loads(contents)
        except (OSError, ValueError) as error:
            errors.append("Invalid or missing startup data " + name + ": " + str(error))
    for name in ("scripts/build-linux.sh", "scripts/linux/run.sh"):
        if b"\r" in (root / name).read_bytes():
            errors.append("Shell scripts require LF line endings: " + name)
    native = [p.relative_to(root).as_posix() for p in paths
              if p.suffix.lower() in (".dll", ".so", ".dylib", ".bundle", ".a", ".aar", ".jar")]
    return errors, scenes, native


if __name__ == "__main__":
    failures, build_scenes, plugins = check(ROOT)
    for failure in failures:
        print("ERROR: " + failure, file=sys.stderr)
    if plugins:
        print("Review platform compatibility of bundled plugins: " + ", ".join(plugins))
    if failures:
        sys.exit(1)
    print("Static checks passed: {} enabled scenes, no asset case collisions, no compiled-only shaders, startup data present and LF launchers.".format(len(build_scenes)))
    print("Bundled native/managed plugin files: {}. Unity compilation and gameplay still require separate testing.".format(len(plugins)))
