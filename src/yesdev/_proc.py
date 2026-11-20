"""Spawn the helpers that live inside this package.

The tray, the Accessibility engine, the focus guard, the CDP relay and the
overlay used to be sibling ``.py`` files started by path. Inside a package the
same job is done with ``-m``, which behaves the same from a source checkout
and from a packaged .app bundle.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

#: Directory that has to be on PYTHONPATH for ``-m yesdev.<x>`` to resolve.
#: In a checkout this is ``src/``; in the .app bundle it is ``Resources/app/``.
SRC_ROOT = Path(__file__).resolve().parent.parent


def child_env() -> dict:
    """Environment for a child process: our PYTHONPATH, extended."""
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join([str(SRC_ROOT)] + ([existing] if existing else []))
    return env


def module_args(module: str) -> list:
    """argv prefix that runs ``yesdev.<module>`` with the current interpreter."""
    return [sys.executable, "-m", module]
