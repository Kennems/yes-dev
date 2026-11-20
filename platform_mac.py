"""兼容层（Phase 1）：真实实现已迁移到 src/yesdev/platforms/mac.py。

保留这个文件是为了让旧的按路径启动方式、打包脚本和测试继续工作。
Phase 3 打包改造完成后可删除。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from yesdev.platforms.mac import *  # noqa: F401,F403,E402
from yesdev.platforms import mac as _impl  # noqa: E402

sys.modules[__name__].__dict__.update(
    {k: v for k, v in _impl.__dict__.items() if not k.startswith("__")}
)
