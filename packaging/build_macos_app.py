#!/usr/bin/env python3
"""Build the macOS app bundle for Yes, Dev - as an app, not a Python script.

Upstream's macOS release is bare Python source, so the process that asks for
Accessibility is the interpreter, and TCC lists it as "python3.11". TCC keys the
grant to the process's code identity, so a launcher that execs an interpreter is
still the interpreter to macOS. This build removes that layer:

    YesDev.app/Contents/MacOS/YesDev        the CPython binary itself (the app's
                                           main executable, ad-hoc signed)
    YesDev.app/Contents/lib/python3.11/     stdlib, Tk, and the pip dependencies
    YesDev.app/Contents/Resources/app/      the project's .py files
    YesDev.app/Contents/Resources/YesDev.icns

Because Contents/MacOS/YesDev is the main executable of the bundle, macOS treats
the bundle as the client: the Accessibility list shows "Yes, Dev", and the grant
survives rebuilds when the identifier stays put (codesign --identifier).

Bootstrap: the interpreter has no script argument when LaunchServices starts it,
so `sitecustomize.py` (installed into site-packages) starts the tray. Helper
processes are the same binary with a script argument, which is how the bootstrap
tells them apart - so sys.executable keeps working for engines and overlays.

    python3 build_macos_app.py --python /path/to/runtime/python3.11 --output dist

Then: cp -R dist/YesDev.app /Applications/ and grant Accessibility to YesDev.app
once. Removing an older grant entry for python3.11 is expected.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ICON_SOURCE = BASE / "docs" / "assets" / "logo.png"
BUNDLE_ID = "com.dev-newb.yesdev"
VERSION = "1.7.1"
RUNTIME_MINOR = "python3.11"   # the directory name under Contents/lib

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key><string>zh_CN</string>
  <key>CFBundleExecutable</key><string>YesDev</string>
  <key>CFBundleIconFile</key><string>YesDev</string>
  <key>CFBundleIdentifier</key><string>{bundle_id}</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>CFBundleName</key><string>Yes, Dev</string>
  <key>CFBundleDisplayName</key><string>Yes, Dev</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleSignature</key><string>????</string>
  <key>CFBundleShortVersionString</key><string>{version}</string>
  <key>CFBundleVersion</key><string>{version}</string>
  <key>LSMinimumSystemVersion</key><string>12.0</string>
  <key>LSUIElement</key><true/>
  <key>LSEnvironment</key>
  <dict>
    <key>YESDEV_LAUNCHED_AS_APP</key><string>1</string>
    <key>PYTHONDONTWRITEBYTECODE</key><string>1</string>
  </dict>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSPrincipalClass</key><string>NSApplication</string>
</dict>
</plist>
"""

# Installed into site-packages, so it runs on every start of the bundled
# interpreter. LaunchServices marks an app launch with LSEnvironment; helper
# processes (the same binary with a script argument) inherit the marker, so it
# is popped on first read and the helpers never bootstrap the tray.
SITECUSTOMIZE = '''"""Start the Yes, Dev tray when the bundle is launched as an app.

The bundle's main executable is the interpreter, and LaunchServices marks an app
launch with LSEnvironment. sys.argv is still empty while sitecustomize runs, so
the marker is the only reliable signal. The marker is popped so the helper
processes this app starts do not bootstrap themselves.
"""
import os
import sys
from pathlib import Path


def _start_tray() -> None:
    if os.environ.pop("YESDEV_LAUNCHED_AS_APP", None) != "1":
        return
    app_dir = Path(sys.prefix) / "Resources" / "app"
    if not app_dir.is_dir():
        return
    sys.path.insert(0, str(app_dir))
    from yesdev.app import main
    os._exit(main())


_start_tray()
'''


def run(cmd: list[str], **kwargs) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, **kwargs)


def check_runtime(python: Path) -> None:
    if not python.exists():
        sys.exit(f"runtime interpreter not found: {python}")
    out = subprocess.run([str(python), "-c",
                          "import sys, tkinter; print(sys.version.split()[0], tkinter.TkVersion)"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"{python} cannot import tkinter (burst_dialog.py needs Tk):\n{out.stderr}")
    print(f"runtime: {python} ({out.stdout.strip()})")


def install_requirements(app_python: Path) -> None:
    for marker in (app_python.parent.parent / "lib").rglob("EXTERNALLY-MANAGED"):
        marker.unlink()
    run([str(app_python), "-m", "pip", "install", "--no-warn-script-location",
         "-r", str(BASE / "requirements.txt")])


def make_icns(resources: Path) -> None:
    from PIL import Image, ImageDraw

    im = Image.open(ICON_SOURCE).convert("RGBA")
    px = im.load()
    w, h = im.size
    # The mark is the green cloud with the check, right of the wordmark. The
    # "Dev" letters are green too, so start past them (492) and keep that edge.
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(492, w):
            r, g, b, a = px[x, y]
            if a > 120 and g > 130 and r < 140 and b < 140 and g - r > 30:
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    cloud = im.crop((minx - 8, miny - 8, maxx + 9, maxy + 9))

    size, margin, radius = 1024, 64, 232
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(canvas).rounded_rectangle(
        [margin, margin, size - margin, size - margin], radius=radius,
        fill=(20, 22, 28, 255))
    cloud = cloud.resize((600, int(cloud.height * (600 / cloud.width))), Image.LANCZOS)
    canvas.alpha_composite(cloud, ((size - cloud.width) // 2,
                                   (size - cloud.height) // 2))

    iconset = resources / "YesDev.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()
    for points in (16, 32, 128, 256, 512):
        for suffix, px_size in (("", points), ("@2x", points * 2)):
            canvas.resize((px_size, px_size), Image.LANCZOS).save(
                iconset / f"icon_{points}x{points}{suffix}.png")
    run(["iconutil", "-c", "icns", str(iconset), "-o", str(resources / "YesDev.icns")])
    shutil.rmtree(iconset)


SIGN_IDENTITY_ENV = "YESDEV_SIGN_IDENTITY"


def find_identity() -> str:
    """Return the codesigning identity to use, preferring a real certificate.

    Ad-hoc (`-`) has no certificate anchor, so macOS keys the Accessibility
    grant to the binary's cdhash. Any rebuild changes that hash and the grant is
    silently orphaned. A real certificate gives TCC a stable requirement
    (team + identifier), so the grant survives rebuilds.
    """
    override = os.environ.get(SIGN_IDENTITY_ENV)
    if override:
        return override
    proc = subprocess.run(["security", "find-identity", "-v", "-p", "codesigning"],
                          capture_output=True, text=True)
    for line in proc.stdout.splitlines():
        if "Apple Development" in line or "Developer ID Application" in line:
            return line.split('"')[1]
    return "-"


def code_sign(app: Path) -> None:
    """Sign the executable and the bundle with one stable identity."""
    identity = find_identity()
    print(f"   signing with: {identity if identity != '-' else 'ad-hoc (no certificate found)'}")
    binary = app / "Contents" / "MacOS" / "YesDev"
    run(["codesign", "--force", "--sign", identity, "--identifier", BUNDLE_ID, str(binary)])
    run(["codesign", "--force", "--sign", identity, "--identifier", BUNDLE_ID, str(app)])


def build(output_dir: Path, python: Path) -> Path:
    app = output_dir / "YesDev.app"
    if app.exists():
        shutil.rmtree(app)
    contents = app / "Contents"
    macros = contents / "MacOS"
    resources = contents / "Resources"
    lib = contents / "lib"
    app_sources = resources / "app"
    for d in (macros, resources):
        d.mkdir(parents=True)

    # The interpreter becomes the app's main executable; its prefix is computed
    # from that location, which makes Contents/lib the stdlib root.
    print("== app executable + runtime ==")
    shutil.copytree(python.parent.parent / "lib", lib, symlinks=True)
    shutil.copy2(python, macros / "YesDev")
    (macros / "YesDev").chmod(0o755)
    app_python = macros / "YesDev"

    prefix = subprocess.run([str(app_python), "-c", "import sys; print(sys.prefix)"],
                            capture_output=True, text=True).stdout.strip()
    if Path(prefix) != contents:
        sys.exit(f"unexpected sys.prefix {prefix!r}, expected {contents}; the runtime "
                 "is not relocatable into this layout")

    print("== dependencies ==")
    install_requirements(app_python)

    print("== sources ==")
    app_sources.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BASE / "src" / "yesdev", app_sources / "yesdev",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # Keep this out of the source tree: it must only exist inside the bundle, or
    # a developer running `python3 yes_dev_mac.py` would be hijacked by it.
    sitecustomize = lib / RUNTIME_MINOR / "site-packages" / "sitecustomize.py"
    sitecustomize.write_text(SITECUSTOMIZE, encoding="utf-8")

    # Compile everything before the seal. If the app compiles on first run, the
    # fresh __pycache__ entries are "files added" to the bundle and the code
    # signature becomes invalid - and TCC then refuses to match the grant. Doing
    # it here makes the bundle content stable for the lifetime of this build.
    print("== bytecode ==")
    run([str(app_python), "-m", "compileall", "-q", str(lib), str(app_sources)])

    print("== icon ==")
    make_icns(resources)

    print("== Info.plist ==")
    (contents / "Info.plist").write_text(
        INFO_PLIST.format(bundle_id=BUNDLE_ID, version=VERSION), encoding="utf-8")
    (contents / "PkgInfo").write_text("APPL????", encoding="ascii")

    # Sealing records the file set: any __pycache__ written afterwards is an
    # added file and invalidates the signature, which makes TCC stop matching the
    # grant. The runtime only needs read access, so freeze the tree.
    print("== freeze runtime tree ==")
    for tree in (lib, app_sources):
        for path in [tree, *tree.rglob("*")]:
            path.chmod(path.stat().st_mode & ~0o222)

    print("== codesign ==")
    code_sign(app)
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--python", required=True,
                        help="relocatable CPython with tkinter to use as the app executable")
    parser.add_argument("--output", default=str(BASE / "dist"),
                        help="directory to write YesDev.app into (default: ./dist)")
    opts = parser.parse_args()

    python = Path(opts.python).expanduser().resolve()
    check_runtime(python)
    app = build(Path(opts.output).expanduser().resolve(), python)
    print(f"\nbuilt: {app}")
    print("install: cp -R dist/YesDev.app /Applications/")
    print("grant:   System Settings > Privacy & Security > Accessibility > + > YesDev")
    return 0


if __name__ == "__main__":
    sys.exit(main())
