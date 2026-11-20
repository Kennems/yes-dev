"""Bilingual (English / Simplified Chinese) strings for the UI surfaces.

No third-party dependency on purpose: this is imported by the Tk dialog
processes and by the tray, and neither should need pyobjc just to pick a
language.

Resolution order, first match wins:

1. ``YESDEV_LANG`` environment variable (``zh``, ``zh-CN``, ``en``, ...)
2. macOS system language (``defaults read -g AppleLanguages``)
3. ``LC_ALL`` / ``LC_MESSAGES`` / ``LANG``
4. ``locale.getdefaultlocale()``

Anything that is not Chinese resolves to English, which matches the
behaviour the app had before this module existed.
"""
from __future__ import annotations

import locale
import os
import subprocess
import sys

EN = "en"
ZH = "zh"

LANGUAGE_NAMES = {EN: "English", ZH: "中文"}

_cached: str | None = None


def _match(tag: str) -> str | None:
    tag = tag.strip().strip('",()').lower()
    if not tag:
        return None
    if tag.startswith("zh"):
        return ZH
    if tag.startswith("en"):
        return EN
    return None


def _darwin_preferred() -> str | None:
    try:
        out = subprocess.run(
            ["defaults", "read", "-g", "AppleLanguages"],
            capture_output=True, text=True, timeout=3,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for token in out.replace("(", " ").replace(")", " ").split(","):
        hit = _match(token)
        if hit:
            return hit
    return None


def detect() -> str:
    """Return the language tag to use, without caching."""
    explicit = os.environ.get("YESDEV_LANG", "")
    hit = _match(explicit)
    if hit:
        return hit

    if sys.platform == "darwin":
        hit = _darwin_preferred()
        if hit:
            return hit

    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        hit = _match(os.environ.get(var, ""))
        if hit:
            return hit

    try:
        name = locale.getdefaultlocale()[0] or ""
    except (ValueError, TypeError):
        name = ""
    return _match(name) or EN


def language() -> str:
    """Cached language tag for this process."""
    global _cached
    if _cached is None:
        _cached = detect()
    return _cached


def is_chinese() -> bool:
    return language() == ZH


STRINGS: dict[str, dict[str, str]] = {
    # Burst guard
    "burst.title": {
        EN: "{count} approvals in the last minute",
        ZH: "最近一分钟已批准 {count} 次",
    },
    "burst.body": {
        EN: "{app} is approving Chrome debugging requests much faster than usual. "
            "If you were not expecting this many, something other than your own "
            "tools may be asking - stopping is recommended.",
        ZH: "{app} 批准 Chrome 调试请求的速度远高于正常水平。"
            "如果你并没有预期这么多次批准，可能是你的工具之外的程序在发请求 —— 建议停止。",
    },
    "burst.countdown": {
        EN: "Stopping automatically in {seconds}s",
        ZH: "{seconds} 秒后自动停止",
    },
    "burst.allow": {
        EN: "Allow for one hour",
        ZH: "允许一小时",
    },
    "burst.stop": {
        EN: "Stop {app}",
        ZH: "停止 {app}",
    },

    # Welcome window
    "welcome.subtitle": {
        EN: "Approves Chrome's \"Allow remote debugging?\" prompt",
        ZH: "自动批准 Chrome 的「要允许远程调试吗？」提示",
    },
    "welcome.what.title": {
        EN: "What it does",
        ZH: "它能做什么",
    },
    "welcome.what.body": {
        EN: "Yes, Dev sits in the menu bar and dismisses Chrome / Edge "
            "remote-debugging consent dialogs, so Playwright, MCP, and AI agents "
            "connect to the browser without you clicking Allow each time.",
        ZH: "Yes, Dev 常驻菜单栏，自动点掉 Chrome / Edge 的远程调试授权弹窗，"
            "让你的自动化工具（Playwright、MCP、AI Agent）直接连上浏览器，"
            "不用每次手动点「允许」。",
    },
    "welcome.what.only_dialog": {
        EN: "It matches that one dialog only. It never clicks an Allow button inside a page.",
        ZH: "只匹配这一个特定弹窗，不会点击网页里的「允许」按钮。",
    },
    "welcome.what.notice": {
        EN: "Cloud notice by default; you can silence it or switch off anytime.",
        ZH: "批准后默认显示云朵提示，可改成静音；随时可以一键关闭。",
    },
    "welcome.what.burst": {
        EN: "Above 60 a minute it asks first, so a runaway cannot flood the screen.",
        ZH: "每分钟超过 60 次会先询问，避免失控刷屏。",
    },
    "welcome.permission.title": {
        EN: "Permission required",
        ZH: "需要的权限",
    },
    "welcome.permission.name": {
        EN: "Accessibility",
        ZH: "辅助功能（Accessibility）",
    },
    "welcome.permission.body": {
        EN: "Used to read and click Chrome's consent dialog. Nothing else: no page "
            "contents, no keystrokes, no network, no uploads.",
        ZH: "用来读取并点击 Chrome 的授权对话框。除此之外不读网页内容、"
            "不读键盘输入、不联网、不上传任何数据。",
    },
    "welcome.status.off": {
        EN: "Not granted",
        ZH: "未开启",
    },
    "welcome.status.on": {
        EN: "Granted",
        ZH: "已开启",
    },
    "welcome.grant": {
        EN: "Grant Accessibility",
        ZH: "一键开启辅助功能",
    },
    "welcome.done": {
        EN: "Done",
        ZH: "已完成",
    },
    "welcome.later": {
        EN: "Later",
        ZH: "稍后再说",
    },
    "welcome.hint.pending": {
        EN: "macOS asks for the grant and opens System Settings > Privacy & "
            "Security > Accessibility. Switch Yes, Dev on there; this window "
            "updates by itself.",
        ZH: "点击后 macOS 会请求授权并打开「系统设置 → 隐私与安全性 → 辅助功能」，"
            "把 Yes, Dev 的开关打开即可，这里会自动变成「已开启」。",
    },
    "welcome.hint.granted": {
        EN: "The grant is active. Close this window and Yes, Dev starts working "
            "immediately; the menu bar status updates too.",
        ZH: "授权已生效。关闭这个窗口，Yes, Dev 会立刻开始工作；"
            "菜单栏的 Accessibility 状态也会同步更新。",
    },

    # Menu bar
    "menu.status.starting": {
        EN: "Status: starting",
        ZH: "状态：启动中",
    },
    "menu.status": {
        EN: "Status: {state}",
        ZH: "状态：{state}",
    },
    "menu.approved": {
        EN: "Approved: {count}",
        ZH: "已批准：{count} 次",
    },
    "menu.access.checking": {
        EN: "Accessibility: checking",
        ZH: "辅助功能：检查中",
    },
    "menu.access.granted": {
        EN: "Accessibility: granted",
        ZH: "辅助功能：已授权",
    },
    "menu.access.missing": {
        EN: "Accessibility: NOT granted - click to fix",
        ZH: "辅助功能：未授权 —— 点此修复",
    },
    "menu.on": {
        EN: "On",
        ZH: "已开启",
    },
    "menu.welcome": {
        EN: "Welcome…",
        ZH: "欢迎页…",
    },
    "menu.settings": {
        EN: "Settings…",
        ZH: "设置…",
    },
    "menu.open_log": {
        EN: "Open log",
        ZH: "打开日志",
    },
    "menu.open_relay_log": {
        EN: "Open relay log",
        ZH: "打开中继日志",
    },
    "menu.quit": {
        EN: "Quit",
        ZH: "退出",
    },
    "menu.resume_in": {
        EN: "back in {seconds}s",
        ZH: "{seconds} 秒后恢复",
    },
    "menu.minutes_left": {
        EN: "{minutes} min left",
        ZH: "剩余 {minutes} 分钟",
    },
    "menu.paused": {
        EN: "paused ({reason})",
        ZH: "已暂停（{reason}）",
    },
    "menu.relay.off": {
        EN: "Fast focus: off",
        ZH: "快速聚焦：关闭",
    },
    "menu.relay.blocked": {
        EN: "Fast focus: paused while approval is off or observing",
        ZH: "快速聚焦：批准关闭或观察模式下暂停",
    },
    "menu.relay.ready": {
        EN: "Fast focus: ready{held} · {count} connected",
        ZH: "快速聚焦：就绪{held} · 已连接 {count} 个",
    },
    "menu.relay.held_suffix": {
        EN: " · Chrome connection held",
        ZH: " · Chrome 连接保持中",
    },
    "menu.relay.starting": {
        EN: "Fast focus: starting — check the relay log if this persists",
        ZH: "快速聚焦：启动中 —— 若一直如此，请看中继日志",
    },
    "menu.relay.error": {
        EN: "Fast focus: {error}",
        ZH: "快速聚焦：{error}",
    },

    # Engine state words
    "state.on": {EN: "on", ZH: "运行中"},
    "state.off": {EN: "off", ZH: "已关闭"},
    "state.observing": {EN: "observing", ZH: "仅观察"},
    "state.paused": {EN: "paused", ZH: "已暂停"},

    # Why the engine paused itself
    "reason.timer_expired": {EN: "timer expired", ZH: "定时结束"},
    "reason.burst_guard": {EN: "burst guard", ZH: "突发保护"},
    "reason.stopped_after_burst": {EN: "stopped after a burst", ZH: "突发后停止"},

    # Settings window
    "settings.title": {EN: "Yes, Dev Settings", ZH: "Yes, Dev 设置"},
    "settings.subtitle": {
        EN: "Approvals, focus, and connections",
        ZH: "批准、聚焦与连接",
    },
    "settings.accessibility": {EN: "Accessibility…", ZH: "辅助功能…"},
    "settings.tab.general": {EN: "General", ZH: "通用"},
    "settings.tab.focus": {EN: "Focus & connection", ZH: "聚焦与连接"},

    "settings.enabled": {
        EN: "Automatically approve debugging requests",
        ZH: "自动批准调试请求",
    },
    "settings.observe_only": {
        EN: "Observe only — record requests without approving",
        ZH: "仅观察 —— 只记录请求，不批准",
    },
    "settings.include_edge": {
        EN: "Also approve Microsoft Edge requests",
        ZH: "同时批准 Microsoft Edge 的请求",
    },
    "settings.start_at_login": {
        EN: "Start Yes, Dev when I log in",
        ZH: "登录时自动启动 Yes, Dev",
    },
    "settings.notify_style": {EN: "Approval notice", ZH: "批准提示"},
    "settings.notify.puffs": {EN: "Floating puffs", ZH: "飘云动画"},
    "settings.notify.toast": {EN: "Toast card", ZH: "通知卡片"},
    "settings.notify.none": {EN: "Silent", ZH: "静音"},
    "settings.poll_ms": {EN: "Check interval", ZH: "检查间隔"},
    "settings.poll_ms.unit": {EN: "milliseconds", ZH: "毫秒"},
    "settings.arm_minutes": {EN: "Stay on for", ZH: "保持开启"},
    "settings.arm_minutes.unit": {
        EN: "minutes · 0 means until turned off",
        ZH: "分钟 · 0 表示一直开到手动关闭",
    },
    "settings.burst_limit": {EN: "Pause after", ZH: "暂停阈值"},
    "settings.burst_limit.unit": {
        EN: "approvals / minute · 0 disables",
        ZH: "次批准 / 分钟 · 0 表示关闭该保护",
    },
    "settings.burst_action": {EN: "When a burst occurs", ZH: "突发时"},
    "settings.burst_action.ask": {EN: "Ask me first (15 seconds)", ZH: "先询问我（15 秒）"},
    "settings.burst_action.stop": {EN: "Pause automatically", ZH: "自动暂停"},
    "settings.diagnostics": {
        EN: "Detailed diagnostic logging",
        ZH: "详细诊断日志",
    },

    "settings.focus_mode": {EN: "Focus behavior", ZH: "聚焦方式"},
    "settings.focus.off": {EN: "Off", ZH: "关闭"},
    "settings.focus.quiet": {EN: "Quiet focus", ZH: "安静聚焦"},
    "settings.focus.relay": {
        EN: "Fast focus via local relay (experimental)",
        ZH: "本地中继快速聚焦（实验性）",
    },
    "settings.focus.help": {
        EN: "Quiet focus returns you to your previous app after Chrome opens a prompt.\n"
            "Fast focus shortens the interruption for tools using the address below.",
        ZH: "安静聚焦会在 Chrome 弹出授权框后，把你带回原来的应用。\n"
            "快速聚焦则缩短打断时间，适用于使用下方地址的工具。",
    },
    "settings.profile.title": {EN: "Chrome data folder", ZH: "Chrome 数据目录"},
    "settings.profile.tooltip": {
        EN: "Chrome's data folder contains Local State and DevToolsActivePort, "
            "not the Default subfolder.",
        ZH: "Chrome 的数据目录里有 Local State 和 DevToolsActivePort，"
            "不是 Default 子目录。",
    },
    "settings.profile.choose": {EN: "Choose…", ZH: "选择…"},
    "settings.profile.hint": {
        EN: "Choose the folder containing Chrome's Local State file.",
        ZH: "请选择包含 Chrome「Local State」文件的那个目录。",
    },
    "settings.relay_port": {EN: "Local port", ZH: "本地端口"},
    "settings.relay_port.unit": {EN: "default: 9333", ZH: "默认：9333"},
    "settings.relay_hold": {
        EN: "Keep one Chrome connection open, so Chrome asks once per launch",
        ZH: "保持一条 Chrome 连接，每次启动只询问一次",
    },
    "settings.relay_hold.tooltip": {
        EN: "Chrome asks when you open it, while you are already in it, instead of "
            "when an agent first connects. Clients take turns on that connection; a "
            "second client at the same time gets its own connection and its own "
            "prompt. Chrome shows its automation banner for as long as the "
            "connection is held.",
        ZH: "Chrome 会在你打开它时就询问，而不是等 Agent 连接时才问。"
            "客户端轮流使用这条连接；同时来的第二个客户端会另开一条连接、"
            "再弹一次授权。连接保持期间，Chrome 会显示「正在被自动测试软件控制」的横幅。",
    },
    "settings.address.title": {EN: "Saved connection address", ZH: "连接地址"},
    "settings.address.copy": {EN: "Copy address", ZH: "复制地址"},
    "settings.cancel": {EN: "Cancel", ZH: "取消"},
    "settings.save": {EN: "Save", ZH: "保存"},
    "settings.permission.granted": {
        EN: "Accessibility: granted",
        ZH: "辅助功能：已授权",
    },
    "settings.permission.required": {
        EN: "Accessibility permission required",
        ZH: "需要辅助功能授权",
    },
    "settings.folder.prompt": {EN: "Choose folder", ZH: "选择目录"},
    "settings.folder.message": {
        EN: "Choose Chrome's data folder (the folder containing Local State).",
        ZH: "请选择 Chrome 的数据目录（包含 Local State 文件的那个）。",
    },

    # Windows tray menu. Labels here are resolved once when the module loads,
    # which is fine: the language does not change while a process runs.
    "windows.start_at_login": {EN: "Start at login", ZH: "登录时启动"},
    "windows.stay_on": {EN: "Stay on for", ZH: "保持开启"},
    "windows.speed": {EN: "Speed", ZH: "检查频率"},
    "windows.approve_notice": {EN: "Approve notice", ZH: "批准提示"},
    "windows.pause_on_burst": {EN: "Pause on burst", ZH: "突发时暂停"},
    "windows.options": {EN: "Options", ZH: "选项"},
    "windows.relay_chrome": {
        EN: "Keep one Chrome connection open",
        ZH: "保持一条 Chrome 连接",
    },
    "windows.relay_edge": {
        EN: "Keep one Edge connection open",
        ZH: "保持一条 Edge 连接",
    },
    "windows.observe_only": {
        EN: "Observe only (log, don't click)",
        ZH: "仅观察（只记录，不点击）",
    },
    "windows.include_edge": {
        EN: "Include Microsoft Edge",
        ZH: "同时处理 Microsoft Edge",
    },
    "windows.open_log": {EN: "Open log", ZH: "打开日志"},
    "windows.open_relay_log": {EN: "Open relay log", ZH: "打开 Chrome 中继日志"},
    "windows.open_edge_relay_log": {EN: "Open Edge relay log", ZH: "打开 Edge 中继日志"},
    "windows.open_lifecycle": {
        EN: "Open startup/exit records",
        ZH: "打开启动/退出记录",
    },
    "windows.open_config": {EN: "Open config", ZH: "打开配置"},
    "windows.quit": {EN: "Quit", ZH: "退出"},
    "windows.starting": {EN: "{app} - starting", ZH: "{app} - 启动中"},
    "windows.tray_title": {
        EN: "{app} - {state} - {count} approved",
        ZH: "{app} · {state} · 已批准 {count} 次",
    },

    "windows.arm.until_off": {EN: "Until I turn it off", ZH: "一直开启"},
    "windows.arm.15m": {EN: "15 minutes", ZH: "15 分钟"},
    "windows.arm.1h": {EN: "1 hour", ZH: "1 小时"},
    "windows.arm.4h": {EN: "4 hours", ZH: "4 小时"},

    "windows.poll.snappy": {EN: "Snappy (150ms)", ZH: "灵敏（150 毫秒）"},
    "windows.poll.normal": {EN: "Normal (250ms)", ZH: "正常（250 毫秒）"},
    "windows.poll.relaxed": {EN: "Relaxed (750ms)", ZH: "宽松（750 毫秒）"},

    "windows.burst.off": {EN: "Off", ZH: "关闭"},
    "windows.burst.30": {EN: "30 / min", ZH: "30 次/分"},
    "windows.burst.60": {EN: "60 / min", ZH: "60 次/分"},
    "windows.burst.120": {EN: "120 / min", ZH: "120 次/分"},

    "windows.burst_action.ask": {EN: "Ask me first (15s)", ZH: "先询问我（15 秒）"},
    "windows.burst_action.stop": {EN: "Stop silently", ZH: "静默停止"},

    # Notifications
    "notify.back_on": {
        EN: "{app} is back on",
        ZH: "{app} 已恢复运行",
    },
    "notify.disarmed": {
        EN: "Disarmed after {minutes} min",
        ZH: "定时结束，已自动关闭（{minutes} 分钟）",
    },
    "notify.burst_paused": {
        EN: "Paused: {count} approvals in under a minute. Resuming automatically in {seconds}s.",
        ZH: "已暂停：一分钟内批准了 {count} 次。{seconds} 秒后自动恢复。",
    },
    "notify.allow_hour": {
        EN: "{app} will keep approving for one hour",
        ZH: "{app} 将在一小时内继续批准",
    },
    "notify.stopped_menu": {
        EN: "{app} stopped. Turn it back on from the menu when ready.",
        ZH: "{app} 已停止。需要时从菜单重新开启。",
    },
    "notify.stopped_tray": {
        EN: "{app} stopped. Turn it back on from the tray when ready.",
        ZH: "{app} 已停止。需要时从托盘菜单重新开启。",
    },
    "notify.approved_one": {
        EN: "Approved {count} debugging request",
        ZH: "已批准 {count} 个调试请求",
    },
    "notify.approved_many": {
        EN: "Approved {count} debugging requests",
        ZH: "已批准 {count} 个调试请求",
    },

    # Validation messages shown inside the settings window
    "validation.poll_ms": {EN: "Check interval", ZH: "检查间隔"},
    "validation.burst_limit": {EN: "Approvals per minute", ZH: "每分钟批准次数"},
    "validation.arm_minutes": {EN: "Stay on for", ZH: "保持开启时长"},
    "validation.relay_port": {EN: "Relay port", ZH: "中继端口"},
    "error.bool": {
        EN: "{field} must be on or off.",
        ZH: "「{field}」必须是开或关。",
    },
    "error.number": {
        EN: "{field} must be a whole number from {low} to {high}.",
        ZH: "「{field}」必须是 {low} 到 {high} 之间的整数。",
    },
    "error.enum": {
        EN: "Choose a valid {field}.",
        ZH: "请为「{field}」选择一个有效值。",
    },
    "error.profile_missing": {
        EN: "Choose a Chrome data folder.",
        ZH: "请选择 Chrome 数据目录。",
    },
    "error.profile_missing_dir": {
        EN: "The Chrome data folder does not exist. Choose the folder containing Local State.",
        ZH: "Chrome 数据目录不存在。请选择包含 Local State 文件的目录。",
    },
    "error.fast_needs_quiet": {
        EN: "Fast focus requires Quiet focus.",
        ZH: "快速聚焦需要同时开启安静聚焦。",
    },
}


def t(key: str, **values: object) -> str:
    """Look up `key` in the current language and fill in placeholders."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    template = entry.get(language()) or entry[EN]
    if not values:
        return template
    try:
        return template.format(**values)
    except (KeyError, IndexError):
        return template
