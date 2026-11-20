"""First-run welcome window: what Yes, Dev does, what it needs, and one button.

The app is a menu-bar accessory with no Dock icon, so without this a new user
sees only a cloud and has no idea that an Accessibility grant is the difference
between working and silently doing nothing. The window states the single
permission the engine needs, asks for it, and watches the grant until it lands -
no restart, because AXIsProcessTrusted is re-read on every poll.

Same construction rules as settings_mac.py: plain NSView frames, one owner, no
Auto Layout, everything on the main thread. All text comes from core/i18n, so
the window follows the system language like every other surface.
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

from yesdev.core import i18n
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
        self.label(content, i18n.t("welcome.subtitle"),
                   112, 532, 420, 22, size=13, secondary=True)
        self.separator(content, 32, 512, 496)

        # --- what it does -------------------------------------------------
        self.label(content, i18n.t("welcome.what.title"), 32, 484, 496, 22, size=13, bold=True)
        self.wrapped(content, i18n.t("welcome.what.body"), 32, 428, 496, 50)
        self.label(content, i18n.t("welcome.what.only_dialog"),
                   32, 400, 496, 22, size=12.5, secondary=True)
        self.label(content, i18n.t("welcome.what.notice"),
                   32, 376, 496, 22, size=12.5, secondary=True)
        self.label(content, i18n.t("welcome.what.burst"),
                   32, 352, 496, 22, size=12.5, secondary=True)

        # --- permissions --------------------------------------------------
        self.label(content, i18n.t("welcome.permission.title"), 32, 316, 496, 22, size=13, bold=True)
        self.label(content, i18n.t("welcome.permission.name"), 32, 288, 496, 22, size=13, bold=True)
        self.wrapped(content, i18n.t("welcome.permission.body"), 32, 238, 496, 44)
        self.status = self.label(content, i18n.t("welcome.status.off"),
                                 32, 202, 200, 24, size=13, bold=True)
        self.status.setTextColor_(NSColor.systemRedColor())

        # --- actions ------------------------------------------------------
        self.grant_button = self.button(content, i18n.t("welcome.grant"), "grant:",
                                        348, 148, 184, 36)
        self.grant_button.setKeyEquivalent_("\r")
        self.button(content, i18n.t("welcome.later"), "later:", 32, 148, 120, 36).setKeyEquivalent_("\x1b")

        self.hint = self.wrapped(content, i18n.t("welcome.hint.pending"),
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
            self.status.setStringValue_(i18n.t("welcome.status.on"))
            self.status.setTextColor_(NSColor.systemGreenColor())
            self.grant_button.setTitle_(i18n.t("welcome.done"))
            self.grant_button.setEnabled_(False)
            self.hint.setStringValue_(i18n.t("welcome.hint.granted"))
        else:
            self.status.setStringValue_(i18n.t("welcome.status.off"))
            self.status.setTextColor_(NSColor.systemRedColor())
            self.grant_button.setTitle_(i18n.t("welcome.grant"))
            self.grant_button.setEnabled_(True)
            self.hint.setStringValue_(i18n.t("welcome.hint.pending"))
