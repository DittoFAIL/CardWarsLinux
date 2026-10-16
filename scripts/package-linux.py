#!/usr/bin/env python3
"""Package a completed Unity Linux build, preserving Linux executable permissions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "CardWars-Linux-x86_64"


def validate_build(source):
    required = (
        "CardWars.x86_64", "run.sh", "STEAM_DECK.md", "build-info.json",
        "CardWars_Data/Managed/Assembly-CSharp.dll",
        "CardWars_Data/StreamingAssets/server_settings.json",
        "CardWars_Data/StreamingAssets/global_settings.json",
        "CardWars_Data/StreamingAssets/Blueprints/db_Tutorials.json",
    )
    for name in required:
        if not (source / name).is_file():
            raise ValueError("Incomplete Linux build; missing " + name)
    with (source / "CardWars.x86_64").open("rb") as player:
        header = player.read(64)
    if (len(header) != 64 or header[:7] != b"\x7fELF\x02\x01\x01"
            or struct.unpack_from("<H", header, 18)[0] != 62
            or struct.unpack_from("<H", header, 16)[0] not in (2, 3)):
        raise ValueError("CardWars.x86_64 must be an x86-64 Linux ELF player, not a Windows executable.")
    info = json.loads((source / "build-info.json").read_text(encoding="utf-8"))
    if not isinstance(info, dict) or info.get("target") != "StandaloneLinux64" or info.get("unityVersion") != "2017.4.40f1":
        raise ValueError("Build metadata does not match the supported Unity Linux target.")
    for path in source.rglob("*"):
        if path.is_symlink():
            try:
                path.resolve(strict=True).relative_to(source)
            except (ValueError, FileNotFoundError, RuntimeError):
                raise ValueError("Build contains a broken or external symbolic link: " + str(path))


def archive_permissions(member):
    member.uid = member.gid = 0
    member.uname = member.gname = ""
    if member.isdir():
        member.mode = 0o755
    elif member.isfile():
        member.mode = 0o755 if member.name in (
            PACKAGE_NAME + "/run.sh", PACKAGE_NAME + "/CardWars.x86_64"
        ) else 0o644
    return member


def package(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    try:
        output.relative_to(source)
    except ValueError:
        pass
    else:
        raise ValueError("The archive must be outside the build directory.")
    validate_build(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".cardwars-", suffix=".tar.gz", dir=str(output.parent))
    os.close(fd)
    try:
        with tarfile.open(temporary, "w:gz", dereference=False) as archive:
            archive.add(str(source), arcname=PACKAGE_NAME, filter=archive_permissions)
        digest = hashlib.sha256()
        with open(temporary, "rb") as archive:
            for block in iter(lambda: archive.read(1024 * 1024), b""):
                digest.update(block)
        os.replace(temporary, str(output))
        checksum = output.with_name(output.name + ".sha256")
        checksum.write_text(digest.hexdigest() + "  " + output.name + "\n", encoding="utf-8")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_directory", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / (PACKAGE_NAME + ".tar.gz"))
    args = parser.parse_args()
    try:
        result = package(args.build_directory, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, "Packaging failed: " + str(error) + "\n")
    print("Packaged: " + str(result))
    print("Checksum: " + str(result) + ".sha256")
    print("Packaging checks passed. This does not establish gameplay or Steam Deck compatibility.")


if __name__ == "__main__":
    main()
