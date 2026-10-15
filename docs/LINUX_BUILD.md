# Native Linux build

This fork targets a genuine **Linux x86-64 Unity player**, using Mono and desktop
OpenGL. The output is an ELF executable with Unity's Linux runtime and the game's
data. Proton and Wine are not involved. Managed C# assemblies inside the player
are normal; a `.dll` extension alone does not indicate a Windows dependency.

**Status:** Linux build tooling and source changes are implemented. Unity
compilation, shader compilation and a Steam Deck gameplay test are still pending.
The automated portability checks are not a game build. There is no tested Linux
release binary yet.

## Requirements

- Unity **2017.4.40f1**, matching `ProjectSettings/ProjectVersion.txt`, activated on
  the build machine, with **Linux Build Support** installed. Windows or an Intel
  Mac can cross-build the Linux player; a compatible Linux build host also works.
- Git and Python 3.8+ for checks and packaging. Bash for the macOS/Linux wrapper.
- A complete checkout, including `Assets` and `ProjectSettings`.

Use the [official 2017.4.40f1 download page](https://unity.com/releases/editor/whats-new/2017.4.40f1)
for the editor and matching platform module. Do not accept an automatic upgrade
to a modern Unity release: the old NGUI, shaders and reconstructed scripts make
an engine upgrade a separate migration. Unity is needed on the build machine;
it does not need to be installed on the Steam Deck that plays the result.

## Build on macOS or Linux

Close the project in the Unity editor, then run from this repository:

```bash
export UNITY_EDITOR='/absolute/path/to/the/Unity/executable'
./scripts/build-linux.sh
```

For a Hub installation on an Intel Mac, the executable is commonly:

```bash
export UNITY_EDITOR='/Applications/Unity/Hub/Editor/2017.4.40f1/Unity.app/Contents/MacOS/Unity'
./scripts/build-linux.sh
```

Use the actual installed executable path. The wrapper performs static checks,
creates a fresh `Builds/linux-*` directory, starts Unity with `-buildTarget Linux64`
before it compiles scripts, and packages a successful build. Unity logs are written
to `Logs/linux-*.log`, with the exact path printed before the editor starts.

Output:

```text
dist/CardWars-Linux-x86_64.tar.gz
dist/CardWars-Linux-x86_64.tar.gz.sha256
```

The archive preserves executable permissions even when produced on Windows.
Keep the entire `CardWars_Data` directory and all other player files together.
The packager rejects Windows/incorrect-architecture executables, missing game data
and builds without the completion marker. Header checks establish the binary
format, not whether the game will run correctly.

The Unity CLI still needs a valid activation and host dependencies. If an older
Linux editor needs a display even in batch mode, use a normal desktop session or
an Xvfb-equipped build host. Do not treat that as a reason to run the game in Proton.

## Build in the editor, including Windows

1. Open the checkout with Unity 2017.4.40f1 and let asset import finish.
2. Select **Card Wars > Switch to Linux x86_64**. Wait for the platform reimport
   and script compilation to finish.
3. Select **Card Wars > Build Linux x86_64**.
4. Package the resulting directory from a terminal at the repository root:

   ```bash
   python3 scripts/package-linux.py Builds/Linux
   ```

   On Windows, use `py -3` instead of `python3` if needed.

The editor menu defaults to `Builds/Linux`; it must be empty or absent. Move a
previous output before rebuilding, or set `CARDWARS_BUILD_DIR` to a new empty
directory before starting Unity. The shell wrapper handles this automatically.
Build failures throw an exception so batch mode exits unsuccessfully. The builder
restores the player's settings in `finally`, while leaving the selected build
target as Linux. Company and product names remain `shishkabob` / `Card Wars`.

## Implementation and audit

| Area | Finding or change |
| --- | --- |
| Engine | Pinned to upstream's Unity 2017.4.40f1; no engine upgrade |
| Build | `Assets/Editor/LinuxBuild.cs`; `StandaloneLinux64`, Mono, OpenGL Core, 1280×800 fullscreen, no resolution dialog |
| Scenes | All 11 enabled scenes retained in their existing order; StartupScene first |
| Native plugins | None found in the source checkout; no Win32 calls found |
| Shader | Replaced GLES-only compiled `Unlit/Alpha With Fade 2` with equivalent texture × tint Cg source; preserved shader name and asset GUID |
| UI editor behavior | `UICamera` recognizes the Linux editor through `Application.isEditor` |
| Filesystem | No case-colliding asset paths found; existing active data loaders use Unity paths and `Path.Combine` |
| Saves | Existing `Application.persistentDataPath` behavior and save identity preserved |
| Controls | Existing mouse/gesture input retained; Steam Input maps Deck controls to it |

The apparent absolute-path bug in `TutorialDataManager` is in an unreferenced
legacy loader. The active `TutorialManager` reads `db_Tutorials.json` through
`SQUtils`; this port does not change either tutorial system. Existing server,
account and network behavior is unchanged and must be checked during gameplay.

## Validation

Run checks without Unity:

```bash
python3 scripts/check-linux.py
bash -n scripts/build-linux.sh scripts/linux/run.sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

GitHub Actions runs these same checks. Tests use clearly synthetic build fixtures
and a launcher probe; no test fixture is a game binary. They cover archive contents,
permissions, checksums, incomplete/wrong-target rejection, paths with spaces,
argument/environment forwarding and player exit status.

Before calling a release playable, complete Unity compilation and the checklist
in [STEAM_DECK.md](STEAM_DECK.md). In particular, fixed-function NGUI shaders,
audio, file loading, saves, network dependencies and suspend/resume need a real
graphical run. Native execution alone does not guarantee better performance than
the Windows build under Proton.

## API references

- [Unity 2017.4 BuildPipeline.BuildPlayer](https://docs.unity3d.com/2017.4/Documentation/ScriptReference/BuildPipeline.BuildPlayer.html)
  — the 2017 API returns an error string, unlike later BuildReport APIs.
- [Unity 2017.4 command-line arguments](https://docs.unity3d.com/2017.4/Documentation/Manual/CommandLineArguments.html)
  — `-buildTarget Linux64`, batch builds and standalone player options.
- [Unity graphics API selection](https://docs.unity3d.com/2017.4/Documentation/ScriptReference/PlayerSettings.SetGraphicsAPIs.html)
  — explicit OpenGL Core selection for the initial Linux build.
