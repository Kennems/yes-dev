"""兼容层（Phase 1）：实现已迁移到 src/yesdev/yesdev/relay/cdp_multiplex.py。

保留同名文件是为了让旧的按路径启动、打包脚本和测试继续工作。
Phase 3 改造完成后删除。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from yesdev.relay.cdp_multiplex import *  # noqa: F401,F403,E402
from yesdev.relay import cdp_multiplex as _impl  # noqa: E402

sys.modules[__name__].__dict__.update(
    {k: v for k, v in _impl.__dict__.items() if not k.startswith("__")}
)
