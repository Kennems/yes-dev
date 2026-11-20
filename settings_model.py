"""兼容层（Phase 1）：实现已迁移到 src/yesdev/core/settings_model.py。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from yesdev.core.settings_model import *  # noqa: F401,F403,E402
from yesdev.core import settings_model as _impl  # noqa: E402

sys.modules[__name__].__dict__.update(
    {k: v for k, v in _impl.__dict__.items() if not k.startswith("__")}
)
