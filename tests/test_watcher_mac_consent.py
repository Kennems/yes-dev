"""Unit tests for the consent-dialog matching in watcher_mac.py.

These cover the one thing that broke on a localised Chrome: the title the
browser puts on the "Allow remote debugging?" sheet, and the label of the
button that grants it. The English strings are the originals; the Simplified
Chinese strings are taken from Chrome itself, not from documentation:

    要允许远程调试吗？   Chrome 157 zh_CN,
                        Google Chrome Framework .../Resources/zh_CN.lproj/locale.pak
                        (one string in the consent paragraph, which the sheet
                        title reproduces verbatim)
    是否允许远程调试?    Chrome 152-153 zh_CN, as recorded in watcher.ps1

The negative cases matter as much as the positive ones: Chrome's Window menu
carries a menu item with a similar title, and the sheet has a "在“设置”中关闭"
button that turns the feature off. Matching either of those would be worse than
not matching at all, so both are pinned here.

Run with the repo's macOS interpreter (the pyobjc imports need it):

    python3 -m unittest discover -s tests -p 'test_watcher_mac_consent.py' -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

try:
    import watcher_mac as engine
except Exception as exc:  # pyobjc / GUI stack missing on this host
    raise unittest.SkipTest(f"watcher_mac needs the macOS pyobjc stack: {exc!r}")


class ConsentDialogTitles(unittest.TestCase):
    """DIALOG_PATTERN decides whether a sheet is the remote-debugging prompt."""

    def test_english_title_matches(self) -> None:
        self.assertTrue(engine.DIALOG_PATTERN.match("Allow remote debugging?"))

    def test_english_title_is_case_insensitive(self) -> None:
        self.assertTrue(engine.DIALOG_PATTERN.match("ALLOW REMOTE DEBUGGING?"))

    def test_chrome_157_simplified_chinese_title_matches(self) -> None:
        # Verbatim from Chrome 157 zh_CN locale.pak.
        self.assertTrue(engine.DIALOG_PATTERN.match("要允许远程调试吗？"))

    def test_chrome_152_simplified_chinese_title_matches(self) -> None:
        # The earlier zh-CN wording, half-width question mark.
        self.assertTrue(engine.DIALOG_PATTERN.match("是否允许远程调试?"))

    def test_other_consent_prompts_do_not_match(self) -> None:
        # The same Chrome dialog family, but a different permission.
        self.assertFalse(engine.DIALOG_PATTERN.match("要允许开发者工具修改文件吗？"))

    def test_titles_without_the_question_mark_do_not_match(self) -> None:
        # Anchored on purpose: no partial matches, no menu-item lookalikes.
        for title in ("Allow remote debugging", "要允许远程调试吗",
                      "是否允许远程调试", "远程调试"):
            with self.subTest(title=title):
                self.assertFalse(engine.DIALOG_PATTERN.match(title))

    def test_unrelated_titles_do_not_match(self) -> None:
        for title in ("GitHub", "Settings", "Allow", "允许"):
            with self.subTest(title=title):
                self.assertFalse(engine.DIALOG_PATTERN.match(title))

    def test_surrounding_whitespace_is_trimmed_by_the_caller(self) -> None:
        # _element_label() strips before matching; pin the contract here.
        self.assertTrue(engine.DIALOG_PATTERN.match(" 要允许远程调试吗？ ".strip()))


class ConsentHostDecision(unittest.TestCase):
    """_is_consent_host keeps title/heading/dialog-role decisions honest."""

    def test_chinese_title_on_a_sheet_is_a_consent_host(self) -> None:
        self.assertTrue(engine._is_consent_host("要允许远程调试吗？", False, True))

    def test_english_title_on_a_sheet_is_a_consent_host(self) -> None:
        self.assertTrue(engine._is_consent_host("Allow remote debugging?", False, True))

    def test_untitled_sheet_with_matching_heading_is_a_consent_host(self) -> None:
        # Chrome 153+ can leave the sheet title empty and put the text in a heading.
        self.assertTrue(engine._is_consent_host("", True, True))

    def test_non_dialog_elements_are_never_consent_hosts(self) -> None:
        for title, heading in (("要允许远程调试吗？", False),
                               ("Allow remote debugging?", False),
                               ("", True)):
            with self.subTest(title=title, heading=heading):
                self.assertFalse(engine._is_consent_host(title, heading, False))

    def test_untitled_non_dialog_is_not_a_consent_host(self) -> None:
        self.assertFalse(engine._is_consent_host("", False, True))


class ApproveButtonLabel(unittest.TestCase):
    """APPROVE_PATTERN picks the Allow button and nothing destructive."""

    def test_allow_labels_match(self) -> None:
        for label in ("Allow", "allow", "Approve", "approve", "允许"):
            with self.subTest(label=label):
                self.assertTrue(engine.APPROVE_PATTERN.match(label))

    def test_simplified_chinese_allow_matches(self) -> None:
        # Chrome 157 zh_CN sheet: ['在“设置”中关闭', '取消', '允许']
        self.assertTrue(engine.APPROVE_PATTERN.match("允许"))

    def test_turn_off_in_settings_never_matches(self) -> None:
        # Would disable the whole remote-debugging feature instead of approving.
        for label in ("在“设置”中关闭", '在"设置"中关闭', "Turn off in settings"):
            with self.subTest(label=label):
                self.assertFalse(engine.APPROVE_PATTERN.match(label))

    def test_cancel_never_matches(self) -> None:
        for label in ("取消", "Cancel"):
            with self.subTest(label=label):
                self.assertFalse(engine.APPROVE_PATTERN.match(label))

    def test_partial_labels_do_not_match(self) -> None:
        # Anchored, so a page button reading "Allow notifications" is out of reach.
        for label in ("Allow notifications", "允许通知", "Allow all"):
            with self.subTest(label=label):
                self.assertFalse(engine.APPROVE_PATTERN.match(label))


if __name__ == "__main__":
    unittest.main()
