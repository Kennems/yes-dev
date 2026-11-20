# Windows portable release

Build from a full 64-bit Windows CPython 3.14 installation with Tcl/Tk and pip.
Use the Microsoft .NET Framework 4.x C# compiler installed with Windows. This
release was built with CPython 3.14.5; the manifest records the exact runtime.

```powershell
python packaging/build_windows.py --version 1.6.2 --output C:\builds\yesdev-1.6.2
python packaging/test_portable.py C:\builds\yesdev-1.6.2\YesDev-1.6.2-windows-x64.zip --extract-to "C:\builds\extracted with spaces"
```

Use an explicit real Python executable if `python` is a Windows Store alias.
The build requires a clean Git commit by default. `--allow-dirty` is for local
QA only; its manifest clearly records that the build contains uncommitted work.
The output directory must not exist, so an earlier build cannot be overwritten.

The app has editable Python files, the PowerShell worker, and a native launcher.
The private runtime copies the selected CPython install's interpreter, DLLs,
stdlib, Tcl/Tk, and original notices. It excludes its installed site-packages
and installs only the pinned app dependencies into a new target directory.
An isolated `python314._pth` blocks user/global Python imports and environment
path injection. Package and runtime licenses are included. This is a portable
distribution, not a single-file executable or an installer. The launcher is
unsigned. Build timestamps and native toolchain details can change archive
bytes; the manifest and checksum identify the exact published package.

Validate the extracted package's supervisor with real private browsers:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/run-supervisor-browser-tests.ps1 -Python "C:\builds\extracted with spaces\YesDev-1.6.2-windows-x64\runtime\python.exe" -SourcePath "C:\builds\extracted with spaces\YesDev-1.6.2-windows-x64\app\watcher.ps1" -ResultDirectory C:\builds\browser-results
```

These tests copy the worker/supervisor into private desktops, use fresh profiles,
and terminate only test-owned processes. They check all three speeds, Chinese
labels, exact ACTION persistence, forced-stall recovery, observe mode, and cleanup.
Do not test by closing an active user browser.

Create the final ZIP only after release commits are merged. Tag that exact commit
and publish the ZIP, `SHA256SUMS.txt`, and a source ZIP generated with `git archive`
from the same commit. Verify the downloaded asset checksum after publication.
The current runtime and user configuration must not be copied into the package.

The Windows relays use `relay/cdp_relay.py`, `relay/cdp_multiplex.py`, and the
`relay/relay_windows.py` host. The whole `src/yesdev` package and `websockets==15.0.1`
are included in new builds. The portable
runtime check imports all relay modules and the websockets asyncio client and
server APIs, then checks all dependency versions against the package pins. It
does not start the relay, tray, or a browser. The relay is off by default; the
portable README gives the opt-in steps and the Chrome/Edge User Data settings.

Run the non-native package checks before building:

```powershell
python -m unittest discover -s tests -p test_windows_relay_packaging.py
```

# macOS app bundle

Upstream ships macOS as bare Python source, so the process that asks for
Accessibility is the interpreter and TCC lists it as "python3.11". TCC keys the
grant to the process's code identity, so a launcher that `exec`s an interpreter
is still the interpreter to macOS. This packaging removes that layer:

```
YesDev.app/Contents/MacOS/YesDev          the CPython binary itself - the app's
                                          main executable, ad-hoc signed
YesDev.app/Contents/lib/python3.11/       stdlib, Tk, pip dependencies
YesDev.app/Contents/Resources/app/        the project's .py files
YesDev.app/Contents/Resources/YesDev.icns icon cut from docs/assets/logo.png
```

Because `Contents/MacOS/YesDev` is the bundle's main executable, macOS attributes
the process to the bundle: the Accessibility list shows the app, not an
interpreter. `Info.plist` sets `LSUIElement` (no Dock icon) and an
`LSEnvironment` marker; `sitecustomize.py` installed into site-packages starts
the tray only when that marker is present, because `sys.argv` is still empty at
that point. Helper processes are the same binary started with a script argument,
so `sys.executable` keeps working for the engine, overlay, guard, relay, and
burst dialog.

Building:

```bash
python3 packaging/build_macos_app.py \
  --python "$HOME/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin/python3.11" \
  --output dist
cp -R dist/YesDev.app /Applications/
```

The build pre-compiles all bytecode before sealing, and the bundle exports
`PYTHONDONTWRITEBYTECODE=1`. Both matter: if the app writes a new `__pycache__`
after signing, the added files invalidate the code signature and TCC stops
matching the grant (`errSecCSResourcesNotFound`). Keep that order.

The bundle is ad-hoc signed with the stable identifier `com.dev-newb.yesdev`.
TCC records a grant against the app's cdhash, so **rebuilding the app changes the
cdhash and needs a fresh grant**: remove the old YesDev entry in
System Settings > Privacy & Security > Accessibility before adding the new build,
or `tccutil reset Accessibility com.dev-newb.yesdev` first. Settings and logs
stay in `~/Library/Application Support/YesDev/`.
