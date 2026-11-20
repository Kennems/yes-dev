"""First-run welcome window: what Yes, Dev does, what it needs, and one button.

The app is a menu-bar accessory with no Dock icon, so without this a new user
sees only a cloud and has no idea that an Accessibility grant is the difference
between working and silently doing nothing. The window states the single
permission the engine needs, asks for it, and watches the grant until it lands -
no restart, because AXIsProcessTrusted is re-read on every poll.

Same construction rules as settings_mac.py: plain NSView frames, one owner, no
Auto Layout, everything on the main thread. Text is Chinese because this build
is installed for a zh-CN user; the menu keeps upstream's English labels.
"""
from __future__ import annotations

import subprocess

from AppKit import (
    NSApplication, NSBackingStoreBuffered, NSBezelStyleRounded, NSBox, NSBoxSeparator,
    NSButton, NSColor, NSFont, NSImageView, NSImageScaleProportionallyUpOrDown,
    NSLineBreakByWordWrapping, NSMakeRect, NSTextField, NSView, NSWindow,
    NSWindowStyleMaskClosable, NSWindowStyleMaskTitled,
)
from Foundation import NSObject, NSTimer

from yesdev.platforms import mac as platform_mac
WELCOME_WIDTH = 560
WELCOME_HEIGHT = 620


class _YesDevWelcomeActions(NSObject):
    controller = None

    def grant_(self, sender):
        self.controller.grant()

    def later_(self, sender):
        self.controller.close()

    def tick_(self, timer):
        self.controller.poll()


class WelcomeWindow:
    """One window, created once, reused by the menu item."""

    def __init__(self, owner):
        self.owner = owner
        self.actions = _YesDevWelcomeActions.alloc().init()
        self.actions.controller = self
        self._trusted = None
        self._timer = None

        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, WELCOME_WIDTH, WELCOME_HEIGHT),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered, False)
        self.window.setTitle_("Yes, Dev")
        self.window.setReleasedWhenClosed_(False)
        self.window.center()
        content = self.window.contentView()

        # --- header -------------------------------------------------------
        icon = NSImageView.alloc().initWithFrame_(NSMakeRect(32, 528, 64, 64))
        image = NSApplication.sharedApplication().applicationIconImage()
        if image is not None:
            icon.setImage_(image)
            icon.setImageScaling_(NSImageScaleProportionallyUpOrDown)
            content.addSubview_(icon)

        self.label(content, "Yes, Dev", 112, 562, 420, 32, size=26, bold=True)
        self.label(content, "自动批准 Chrome 的「要允许远程调试吗？」提示",
                   112, 532, 420, 22, size=13, secondary=True)
        self.separator(content, 32, 512, 496)

        # --- what it does -------------------------------------------------
        self.label(content, "它能做什么", 32, 484, 496, 22, size=13, bold=True)
        self.wrapped(content,
                     "Yes, Dev 常驻菜单栏，自动点掉 Chrome / Edge 的远程调试授权弹窗，"
                     "让你的自动化工具（Playwright、MCP、AI Agent）直接连上浏览器，"
                     "不用每次手动点「允许」。",
                     32, 428, 496, 50)
        self.label(content, "只匹配这一个特定弹窗，不会点击网页里的「允许」按钮。",
                   32, 400, 496, 22, size=12.5, secondary=True)
        self.label(content, "批准后默认显示云朵提示，可改成静音；随时可以一键关闭。",
                   32, 376, 496, 22, size=12.5, secondary=True)
        self.label(content, "每分钟超过 60 次会先询问，避免失控刷屏。",
                   32, 352, 496, 22, size=12.5, secondary=True)

        # --- permissions --------------------------------------------------
        self.label(content, "需要的权限", 32, 316, 496, 22, size=13, bold=True)
        self.label(content, "辅助功能（Accessibility）", 32, 288, 496, 22, size=13, bold=True)
        self.wrapped(content,
                     "用来读取并点击 Chrome 的授权对话框。除此之外不读网页内容、"
                     "不读键盘输入、不联网、不上传任何数据。",
                     32, 238, 496, 44)
        self.status = self.label(content, "未开启", 32, 202, 200, 24, size=13, bold=True)
        self.status.setTextColor_(NSColor.systemRedColor())

        # --- actions ------------------------------------------------------
        self.grant_button = self.button(content, "一键开启辅助功能", "grant:", 348, 148, 184, 36)
        self.grant_button.setKeyEquivalent_("\r")
        self.button(content, "稍后再说", "later:", 32, 148, 120, 36).setKeyEquivalent_("\x1b")

        self.hint = self.wrapped(
            content,
            "点击后 macOS 会请求授权并打开「系统设置 → 隐私与安全性 → 辅助功能」，"
            "把 Yes, Dev 的开关打开即可，这里会自动变成「已开启」。",
            32, 84, 496, 46, size=12.5, secondary=True)

        self.poll()

    # -- construction helpers ---------------------------------------------

    @staticmethod
    def label(parent, text, x, y, w, h, size=13, bold=False, secondary=False):
        field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
        field.setStringValue_(text)
        field.setEditable_(False)
        field.setSelectable_(False)
        field.setBordered_(False)
        field.setDrawsBackground_(False)
        field.setFont_(NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size))
        if secondary:
            field.setTextColor_(NSColor.secondaryLabelColor())
        parent.addSubview_(field)
        return field

    @staticmethod
    def wrapped(parent, text, x, y, w, h, size=13, secondary=False):
        field = WelcomeWindow.label(parent, text, x, y, w, h, size=size, secondary=secondary)
        try:
            field.setUsesSingleLineMode_(False)
            field.setLineBreakMode_(NSLineBreakByWordWrapping)
            field.cell().setWraps_(True)
        except Exception:
            pass
        return field

    def button(self, parent, title, action, x, y, w, h):
        button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
        button.setTitle_(title)
        button.setBezelStyle_(NSBezelStyleRounded)
        button.setTarget_(self.actions)
        button.setAction_(action)
        parent.addSubview_(button)
        return button

    @staticmethod
    def separator(parent, x, y, w):
        line = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, w, 1))
        line.setBoxType_(NSBoxSeparator)
        parent.addSubview_(line)

    # -- behavior ----------------------------------------------------------

    def show(self):
        self.poll()
        self.window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        if self._timer is None:
            self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.5, self.actions, "tick:", None, True)

    def close(self):
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None
        platform_mac.ensure_data_dir()
        try:
            (platform_mac.DATA_DIR / ".welcome-shown").touch()
        except Exception:
            pass
        self.window.orderOut_(None)

    def grant(self):
        """Ask for the grant and open the pane in one click.

        AXIsProcessTrustedWithOptions with the prompt option is what makes macOS
        itself show the request; without prompt=True this only reports the
        current state. The pane is opened too, because the request window and
        the checkbox live in different places on recent macOS.
        """
        already = platform_mac.is_trusted(prompt=True)
        if not already:
            try:
                subprocess.run(["open", platform_mac.accessibility_settings_url()], check=False)
            except Exception:
                pass
        self.poll()

    def poll(self):
        trusted = platform_mac.is_trusted()
        if trusted == self._trusted:
            return
        self._trusted = trusted
        if trusted:
            self.status.setStringValue_("已开启")
            self.status.setTextColor_(NSColor.systemGreenColor())
            self.grant_button.setTitle_("已完成")
            self.grant_button.setEnabled_(False)
            self.hint.setStringValue_(
                "授权已生效。关闭这个窗口，Yes, Dev 会立刻开始工作；"
                "菜单栏的 Accessibility 状态也会同步更新。")
        else:
            self.status.setStringValue_("未开启")
            self.status.setTextColor_(NSColor.systemRedColor())
            self.grant_button.setTitle_("一键开启辅助功能")
            self.grant_button.setEnabled_(True)
            self.hint.setStringValue_(
                "点击后 macOS 会请求授权并打开「系统设置 → 隐私与安全性 → 辅助功能」，"
                "把 Yes, Dev 的开关打开即可，这里会自动变成「已开启」。")
