# Tests

Two kinds of file live here: `test_*.py` suites that run anywhere, and
`verify_*` / `*_live.py` tools that need a real browser or a real desktop.
The suites are what day-to-day work and CI use.

## Running

Install the package once, so `import yesdev` resolves without path tricks:

```bash
python3 -m pip install -e .
```

Then, on macOS or Linux:

```bash
python3 -m unittest discover -s tests -t tests -p "test_*.py"
python3 -m unittest discover -s tests/mac -p "test_*.py"
python3 -m pytest                    # same suites, if pytest is installed
```

`-t tests` is required: `tests/` is not a package, so discovery needs the
top-level directory stated explicitly.

On Windows, use a full CPython installation rather than a venv redirector for
the suites that exercise the Explorer launch broker:

```powershell
python -m unittest discover -s tests -t tests -p "test_*.py" -v
```

Suites that touch macOS permission state skip elsewhere, and Windows-only
suites skip on macOS. A run of 202 tests with 24 skipped is expected on macOS.

Everything here uses temporary data, fake loopback endpoints, and processes it
owned. No suite starts the installed app, reads your browser profile, or
approves a real prompt.

## Suites at the root

Cross-platform and Windows. None of these need a browser.

| File | Covers |
|---|---|
| `test_settings_model.py` | Settings validation, defaults, atomic save |
| `test_cdp_relay.py` | Real TCP/WebSocket lifecycle, endpoint discovery |
| `test_cdp_relay_hold.py` | The held connection: one approved socket lent out and reclaimed |
| `test_cdp_relay_adversarial.py` | Malformed frames, early disconnects, hostile clients |
| `test_cdp_relay_resource_limits.py` | Per-client and total call caps, queue bounds |
| `test_cdp_multiplex.py` | Concurrent clients sharing one upstream transport |
| `test_launch_primer.py` | Opening the connection at launch instead of on first client |
| `test_relay_windows.py` | Windows helper lifecycle, parent identity, stop paths |
| `test_relay_windows_adversarial.py` | Fault injection, retry and recovery edges |
| `test_relay_windows_performance.py` | Work counts and recovery under load |
| `test_watcher_supervisor.py` | Stall detection and worker recovery |
| `test_windows_runtime.py` | Launch independence and exit diagnostics |
| `test_windows_relay_tray.py` | Tray integration with private settings |
| `test_windows_relay_packaging.py` | Package manifest and runtime check wiring |
| `test_speed_menu.py` | Tray speed actions without a tray |
| `test_watcher_mac_consent.py` | Consent-dialog matching in `dialogs/watcher.py` |
| `test_onboarding_mac.py` | First-run welcome window |

Menu text is resolved through `core/i18n`, so assertions match against
`i18n.t(...)` rather than a literal English string. That keeps the suites
language-independent.

## Suites under tests/mac

macOS-specific behaviour. These fake the native calls rather than driving them.

| File | Covers |
|---|---|
| `test_approve_no_raise.py` | The approval path presses the button and does nothing else |
| `test_attribute_reads.py` | Reading AX values cannot turn into an approval |
| `test_focus_guard.py` | Guard decisions: quiet, arm, cancel |
| `test_early_focus.py` | Early-focus request policy and its control channel |
| `test_early_focus_events.py` | Helper wake-up, run limits, single use |
| `test_parent_exit.py` | Helpers stop when the supervisor goes, even mid-start |
| `test_tray_settings.py` | Settings application and helper ownership |

`early_focus_client.py`, `early_focus_guard.py`, and `early_focus_protocol.py`
are small shims that `test_early_focus.py` imports; they are not standalone
suites.

## Live verification tools

These are not run by discovery. They were written against the old flat layout
and launch processes by file path, so several spawn calls no longer resolve
after the move to `src/yesdev`. Treat them as starting points to update before
use, not as a passing suite.

| File | What it drives |
|---|---|
| `mac/verify_hold_live.py` | The held CDP connection against real Chrome |
| `mac/verify_relay_live.py` | Real clients against a named desktop |
| `mac/verify_parent_exit_live.py` | Kills a real tray and watches helpers exit |
| `mac/verify_tray_lifecycle.py` | Tray settings and helper lifetimes |
| `mac/verify_focus_input.py` | Input after cancelling a live focus request |
| `mac/verify_attribute_reads.py` | Native AX reads against a disposable Chrome |
| `mac/native_input_checks.py` | Explicitly authorised native input |
| `mac/recon_cdp_live.py` | Records MCP/Playwright/Puppeteer traffic |
| `mac/record_cdp_traffic.py` | Consent-mode evidence capture |
| `mac/soak_everyday.py` | Bounded mixed-client soak with a real tray |
| `mac/focus_flasher.py` | Stand-in for Chrome's self-activation |
| `windows_relay_live.py` | Isolated headless Chrome through the relay |
| `windows_relay_consent.py` | Real Chrome consent on a private desktop |
| `windows_relay_adversarial_live.py` | Fault injection against a real host |
| `windows_relay_performance_live.py` | Idle and load checks on an owned relay |
| `windows_multiplex_live.py` | Private Chrome and Edge sharing |
| `windows_multiplex_mcp.py` | Four stdio MCP servers against two relays |
| `windows_multiplex_stress.py` | Concurrency stress on private browsers |
| `tray-launch.py` | The real tray launch method, parsed from source |
| `tray-log.py` | The real tray log reader, parsed from source |

Headless browser checks do not prove native consent. Only
`windows_relay_consent.py` and the macOS `verify_*` tools exercise the real
permission dialog, and those require a desktop you can dedicate to the run.

## Limits

A passing suite says the code does what the fixtures assert. It does not say a
given Chrome or macOS build shows the consent sheet where the matcher expects
it. Version-specific behaviour is in [troubleshooting](../docs/troubleshooting.md)
and the [architecture notes](../docs/architecture.md#finding-the-dialog-on-macos).
