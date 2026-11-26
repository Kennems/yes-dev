<p align="center">
  <img src="docs/assets/logo.svg" alt="Yes, Dev" width="360">
</p>

替你点掉 Chrome / Edge 的「是否允许远程调试?」，Playwright、MCP 服务、自己的脚本不用停下来等你点。

> 开着的时候，**任何**本地程序都会被放行。不能接受就别开。

## 安装

**macOS** — 从 [Releases](https://github.com/Kennems/yes-dev/releases/latest) 下载 `.dmg`，把 **YesDev** 拖进 Applications，打开一次，在「系统设置 › 隐私与安全性 › 辅助功能」里勾上。首次打开可能要右键 → 打开。

**Windows** — 下载 ZIP，解压整个目录，运行 `YesDev.exe`。

## 使用

所有开关都在菜单栏 / 托盘图标里：

| 项 | 含义 |
|---|---|
| **自动批准** | 总开关 |
| **包含 Microsoft Edge** | Edge 的弹窗也点 |
| **仅观察** | 只记日志，不点 |
| **检查间隔** | 默认 250 ms，调大省 CPU 但反应慢 |

配置和日志在 `~/Library/Application Support/YesDev/`（macOS）或 `%LOCALAPPDATA%\YesDev`（Windows），升级不会丢。**替换前先退出程序**，跑着的旧进程会继续执行旧代码。

## 不点了怎么办

先看图标在不在、**自动批准**有没有勾上、是不是开了「仅观察」或定时关闭。然后读上面目录里的 `yes-dev.log`。

- 管得了：`chrome://inspect/#remote-debugging` 那个开关出来的授权框，包括锁屏状态下（macOS 1.7.1+）
- 管不了：命令行 `--remote-debugging-port` 那条路，以及弹窗文案不同的浏览器版本

## 文档

[macOS](docs/macos.md) · [Windows](docs/windows.md) · [中继](docs/concurrent-relay.md) · [排错](docs/troubleshooting.md) · [更新日志](CHANGELOG.md) · [English](README.md)

## 许可

[MIT](LICENSE)
