# Card Wars on Steam Deck — native Linux

These instructions apply to a **compiled Linux build**, not a source-code ZIP or
the upstream Windows download. Build and gameplay verification are still pending;
this document describes the intended install and acceptance test.

## Install

1. In Desktop Mode, copy `CardWars-Linux-x86_64.tar.gz` to the Deck.
2. Extract it into a writable location, for example `/home/deck/Games/`. Keep all
   files inside the extracted `CardWars-Linux-x86_64` folder together.
3. In Steam, add the extracted `run.sh` as a **Non-Steam Game**. In the file picker,
   show all files if shell scripts are hidden. Name the shortcut **Card Wars**.
4. Check the shortcut properties. With the example location:

   - Target: `"/home/deck/Games/CardWars-Linux-x86_64/run.sh"`
   - Start In: `"/home/deck/Games/CardWars-Linux-x86_64"`
   - Compatibility: leave **Force the use of a specific Steam Play compatibility
     tool** unchecked for the first test. Do not select Proton.

5. Launch once in Desktop Mode, then test the same shortcut in Gaming Mode.

`run.sh` starts `CardWars.x86_64` directly and retains Steam's environment. It does
not invoke Wine, Proton, a Windows executable or the Unity editor. A Steam Linux
Runtime, if needed for older native dependencies, is still native Linux execution.

If permissions were lost during a transfer, run in the extracted folder:

```bash
chmod +x run.sh CardWars.x86_64
./run.sh
```

## Controls

The existing game uses mouse clicks and mouse-driven gestures. For the initial
Deck test, configure Steam Input as follows:

| Deck control | Binding |
| --- | --- |
| Right trackpad | Mouse |
| R2 | Left mouse button — hold while moving to drag |
| A | Left mouse button (optional alternative) |
| L2 | Right mouse button |
| Left trackpad | Mouse wheel for scrolling/gesture zoom where supported |
| Menu button | Escape — opens the existing quit dialog in the main menu |

Full controller navigation and controller button prompts have not been added.
Touchscreen behavior should be tested separately; trackpad mouse input is the
baseline. Use Steam's on-screen keyboard when a text field needs input.

## Saves and logs

The build keeps the upstream company/product identity. The expected native Linux
save directory is:

```text
~/.config/unity3d/shishkabob/Card Wars/
```

Unity may instead use `$XDG_CONFIG_HOME/unity3d/shishkabob/Card Wars/` when that
environment variable is set. Back up the entire directory before testing an update.
Native and Proton saves occupy different OS-specific directories; this port does
not automatically migrate a Proton save. Close both versions before manually
copying save files, retain backups, and verify progress before deleting anything.

To get an explicit log without depending on Unity's default log location, run:

```bash
./run.sh -logFile "$HOME/cardwars-linux-player.log"
```

The build defaults to 1280×800 fullscreen. For a windowed desktop diagnostic run:

```bash
./run.sh -screen-width 1280 -screen-height 800 -screen-fullscreen 0 \
  -logFile "$HOME/cardwars-linux-player.log"
```

Pink surfaces indicate a shader problem; collect the log and identify the affected
scene. If a system-library error appears before the log is created, run from Konsole
to capture stderr and try Steam's native Linux runtime. Do not disable SteamOS's
read-only filesystem or install random system packages to troubleshoot this build.

## Before marking the Linux release playable

- [ ] `file CardWars.x86_64` identifies an x86-64 ELF executable.
- [ ] Startup reaches the main menu in both Desktop and Gaming Mode.
- [ ] Fresh-profile tutorial and a complete battle work, including timing-ring taps.
- [ ] Card dragging, flooping, deck editing, scrolling and text entry work.
- [ ] UI fits at 1280×800; there are no pink shaders or missing textures.
- [ ] Music and sound effects play correctly.
- [ ] Progress survives a normal quit/relaunch; backup/restore works.
- [ ] Suspend/resume works without lost input, broken audio or lost progress.
- [ ] Connected and disconnected network behavior is recorded; inherited server
      dependencies are identified rather than assumed to work offline.
- [ ] Player log has been reviewed for exceptions and missing files.
- [ ] Frame pacing and power use have been measured on actual hardware.

Record the commit, Unity version, SteamOS version, Deck model and test results with
the first release. A passing tooling workflow does not replace these checks.
