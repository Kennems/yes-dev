"""Write a portable runtime check without starting the tray or approving prompts."""
import ctypes
import importlib.util
from importlib.metadata import version
import json
from pathlib import Path
import ssl
import sys
import traceback


EXPECTED_DEPENDENCIES = {"pystray": "0.19.5", "pillow": "12.2.0", "six": "1.17.0", "websockets": "15.0.1"}


def dependency_versions():
    versions = {name: version(name) for name in EXPECTED_DEPENDENCIES}
    for name, expected in EXPECTED_DEPENDENCIES.items():
        if versions[name] != expected:
            raise RuntimeError(f"Expected {name} {expected}; found {versions[name]}")
    return versions


def main():
    root = Path(__file__).resolve().parents[1]
    report = {"passed": False, "python": sys.version, "executable": sys.executable}
    try:
        import pystray
        from PIL import Image, ImageTk
        import tkinter
        from yesdev.ui import puffs
        from yesdev.platforms import windows as windows_runtime
        from yesdev.relay import supervisor as watcher_supervisor
        from yesdev.relay import cdp_relay
        from yesdev.relay import cdp_multiplex
        from yesdev.relay import relay_windows
        from websockets.asyncio.client import connect
        from websockets.asyncio.server import serve
        dependencies = dependency_versions()
        runtime = root / "runtime"
        for path in sys.path:
            assert Path(path).resolve().is_relative_to(root), path
        assert Path(sys.executable).resolve().is_relative_to(runtime)
        image = Image.new("RGBA", (16, 16), (0, 100, 200, 255))
        assert image.getpixel((0, 0)) == (0, 100, 200, 255)
        tcl = tkinter.Tcl()
        report["tcl"] = tcl.call("info", "patchlevel")
        for path in sorted((root / "app" / "yesdev").rglob("*.py")):
            compile(path.read_text(encoding="utf-8-sig"), str(path.relative_to(root / "app")), "exec")
        report.update(passed=True, dependencies=dependencies,
                      sys_path=sys.path, isolated=bool(sys.flags.isolated), openssl=ssl.OPENSSL_VERSION)
    except BaseException:
        report["error"] = traceback.format_exc()
    (root / "runtime-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
