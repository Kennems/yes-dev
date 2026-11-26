<p align="center">
  <img src="docs/assets/logo.svg" alt="Yes, Dev" width="360">
</p>

Clicks **Allow remote debugging?** for you, so Playwright, an MCP server or your own script connects without waiting on a human.

> It answers **any** local request while approval is on. Don't run it where that's unacceptable.

## Install

**macOS** — download the `.dmg` from [Releases](https://github.com/Kennems/yes-dev/releases/latest), drag **YesDev** into Applications, open it once, grant **Accessibility**. First launch may need right-click → Open.

**Windows** — download the ZIP, extract the whole folder, run `YesDev.exe`.

## Use

Everything lives in the menu bar / tray icon:

| Item | Meaning |
|---|---|
| **Auto-approve** | master switch |
| **Include Microsoft Edge** | answer Edge as well |
| **Observe only** | log what would be approved, approve nothing |
| **Interval** | 250 ms default; higher is lighter on CPU, slower to react |

Settings and logs live in `~/Library/Application Support/YesDev/` (macOS) or `%LOCALAPPDATA%\YesDev` (Windows) and survive updates. **Quit the app before replacing it** — a running copy keeps executing the old code.

## When it stops approving

Check the icon is there, **Auto-approve** is on, and neither Observe-only nor a timer is active. Then read `yes-dev.log` in the folder above.

- Handled: the consent sheet behind `chrome://inspect/#remote-debugging`, including while the screen is locked (macOS 1.7.1+)
- Not handled: command-line `--remote-debugging-port`, or browser builds whose dialog text differs

## Docs

[macOS](docs/macos.md) · [Windows](docs/windows.md) · [Relay](docs/concurrent-relay.md) · [Troubleshooting](docs/troubleshooting.md) · [Changelog](CHANGELOG.md) · [中文](README.zh-CN.md)

## License

[MIT](LICENSE)
