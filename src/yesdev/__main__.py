"""Entry point: ``python -m yesdev`` (and the ``yesdev`` console script)."""
from __future__ import annotations

import sys


def main() -> int:
    if sys.platform == "win32":
        from yesdev.platforms.windows_app import main as run
    else:
        from yesdev.app import main as run
    return run()


if __name__ == "__main__":
    sys.exit(main())
