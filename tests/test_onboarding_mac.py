"""Smoke tests for the first-run welcome window.

This is a native window, so the tests assert structure rather than pixels: the
window is the promised size, every control lands inside the content view, the
copy actually states what the app does and which permission it needs, and the
status/button pair reflects the real Accessibility grant.

They construct the window without showing it, so they do not steal focus. They
need the macOS pyobjc stack and a logged-in window server, which the app bundle
already provides.

    python3 -m unittest discover -s tests -p 'test_onboarding_mac.py' -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

if sys.platform != "darwin":
    raise unittest.SkipTest("the welcome window is macOS-only")

try:
    from AppKit import NSApplication
    import onboarding_mac
    import platform_mac
except Exception as exc:  # pyobjc / window server missing
    raise unittest.SkipTest(f"needs the macOS pyobjc stack: {exc!r}")

WIDTH, HEIGHT = onboarding_mac.WELCOME_WIDTH, onboarding_mac.WELCOME_HEIGHT


class WelcomeWindowStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        NSApplication.sharedApplication()
        cls.window = onboarding_mac.WelcomeWindow(None)
        cls.content = cls.window.window.contentView()

    def test_window_has_the_declared_size(self) -> None:
        # The window frame adds the title bar; the layout is in the content view.
        frame = self.content.frame()
        self.assertEqual((frame.size.width, frame.size.height), (WIDTH, HEIGHT))

    def test_every_control_is_inside_the_content_view(self) -> None:
        for view in self.content.subviews():
            frame = view.frame()
            with self.subTest(view=view.__class__.__name__):
                self.assertGreaterEqual(frame.origin.x, 0)
                self.assertGreaterEqual(frame.origin.y, 0)
                self.assertLessEqual(frame.origin.x + frame.size.width, WIDTH + 0.5)
                self.assertLessEqual(frame.origin.y + frame.size.height, HEIGHT + 0.5)

    def test_copy_states_what_the_app_does(self) -> None:
        texts = self._texts()
        joined = "\n".join(texts)
        self.assertIn("自动批准", joined)
        self.assertIn("远程调试", joined)
        self.assertIn("不会点击网页里的「允许」按钮", joined)

    def test_copy_states_the_permission_it_needs(self) -> None:
        joined = "\n".join(self._texts())
        self.assertIn("辅助功能", joined)
        self.assertIn("Accessibility", joined)
        # The privacy claim is part of the promise, not decoration.
        self.assertIn("不联网", joined)
        self.assertIn("不上传任何数据", joined)

    def test_there_is_exactly_one_grant_button(self) -> None:
        titles = [b.title() for b in self._buttons()]
        self.assertEqual(sum(1 for t in titles if "辅助功能" in t or t == "已完成"), 1)
        self.assertIn("稍后再说", titles)

    def test_status_matches_the_real_grant(self) -> None:
        trusted = platform_mac.is_trusted()
        if trusted:
            self.assertEqual(self.window.status.stringValue(), "已开启")
            self.assertFalse(bool(self.window.grant_button.isEnabled()))
        else:
            self.assertEqual(self.window.status.stringValue(), "未开启")
            self.assertTrue(bool(self.window.grant_button.isEnabled()))

    def _texts(self) -> list[str]:
        out = []
        for view in self.content.subviews():
            if view.__class__.__name__ != "NSTextField":
                continue
            try:
                value = str(view.stringValue() or "")
            except Exception:
                continue
            if value:
                out.append(value)
        return out

    def _buttons(self) -> list:
        return [v for v in self.content.subviews() if v.__class__.__name__ == "NSButton"]


if __name__ == "__main__":
    unittest.main()
