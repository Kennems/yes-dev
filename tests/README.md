# Tests

Three things live here: `test_*.py` suites that run anywhere Python runs,
macOS-specific suites under `mac/`, and a PowerShell harness for the Windows
desktop. The Python suites are what day-to-day work and CI use.

## Running

Install the package once, so `import yesdev` and the native dependencies
resolve without path tricks:

```bash
python3 -m pip install -e .
```

Then, on macOS:

```bash
python3 -m unittest discover -s tests -t tests -p "test_*.py"
python3 -m unittest discover -s tests/mac -p "test_*.py"
```

`-t tests` is required: `tests/` is not a package, so discovery needs the
top-level directory stated explicitly. `python3 -m pytest` runs the same
suites if pytest is installed.

A full run is 202 tests with 24 skipped on macOS: Windows-only suites skip
here, and the suites that touch macOS permission state skip when they cannot
reach the real AX API.

Everything runs against temporary data, fake loopback endpoints, and processes
it owns. No suite starts the installed app, reads a browser profile, or
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
are shims that `test_early_focus.py` imports; they are not standalone suites.
`hold_puppeteer_probe.mjs` and `traffic_puppeteer_client.mjs` are fixtures
those suites shell out to.

## Windows desktop harness

`run-windows-tests.ps1` is the only entry point for anything that needs a real
Windows session. Run it from Windows, not from CI on another OS:

```powershell
.\tests\run-windows-tests.ps1 -IncludeBrowsers
```

It drives the Python suites, then the helper scripts it depends on:
`concurrent-worker-log.ps1`, `watcher-regression.ps1`, `log-writer.ps1`,
`soak-log-reader.ps1`, `run-private-desktop.ps1` (with `legacy-native.ps1` and,
under `-IncludeBrowsers`, `browser-private.ps1`), plus `tray-launch.py` and
`tray-log.py`, which read the tray entry point and log reader out of the
source. `memory-soak.ps1` is the long-running soak that `soak-log-reader.ps1`
parses for its assertions.

Those scripts start real browsers on a private desktop and press real buttons.
Nothing in the Python suites proves a given Chrome or Windows build puts its
consent sheet where the matcher expects it; only this harness does.

## Limits

A passing suite says the code does what the fixtures assert. It does not say a
given Chrome or macOS build shows the consent sheet where the matcher expects
it. Version-specific behaviour is in [troubleshooting](../docs/troubleshooting.md)
and the [architecture notes](../docs/architecture.md#finding-the-dialog-on-macos).
