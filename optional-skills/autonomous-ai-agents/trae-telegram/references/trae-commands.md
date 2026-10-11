# Trae Bridge — Telegram Command Reference

Reference for the agent when dispatching Trae IDE commands received via
Telegram. All commands route through two scripts in the user-local skill
directory.

## Script Locations

```
BRIDGE = ~/.hermes/skills/software-development/trae-screen-analyst/trae_bridge.py
RUNNER = ~/.hermes/skills/software-development/trae-screen-analyst/runner.py
```

## Command Dispatch Table

| Telegram Input | Script | Flags | Notes |
|---|---|---|---|
| `trae: <text>` | BRIDGE | `--send '<text>' --target dell` | CDP first, AT-SPI fallback |
| `trae screenshot` | RUNNER | `--target dell` | Captures + sends to TG |
| `trae screenshot samsung` | RUNNER | `--target samsung` | HDMI-1 monitor |
| `trae screenshot laptop` | RUNNER | `--target laptop` | eDP-1 monitor |
| `trae continue` | BRIDGE | `--continue-click --target dell` | Vision-guided |
| `trae click` | BRIDGE | `--continue-click --target dell` | Alias |
| `trae force click` | BRIDGE | `--force-click --target dell` | No vision check |
| `trae approve` | BRIDGE | `--continue-click --target dell` | Alias |
| `trae autopilot on` | BRIDGE | `--autopilot on` | BLOCKED — extension owns |
| `trae autopilot off` | BRIDGE | `--autopilot off` | Persists to JSON |
| `trae autopilot status` | BRIDGE | `--autopilot status` | Prints ON/OFF |
| `trae status` | BRIDGE | `--autopilot status` | Shorthand |
| `trae autopilot daemon` | BRIDGE | `--autopilot daemon -i 300` | BLOCKED — extension owns loop |
| `trae daemon` | BRIDGE | `--autopilot daemon -i 300` | BLOCKED — extension owns loop |
| `trae report` | BRIDGE | `--report-completion --target dell` | Screenshot + diff |
| `trae completion` | BRIDGE | `--report-completion --target dell` | Alias |
| `trae diff` | BRIDGE | `--git-diff` | Text only |

## Target Monitor Mapping

| User says | `--target` value | Physical output |
|---|---|---|
| `dell`, `dp`, `dp-1`, (default) | `dell` | Dell DP-1 (2560×1080 logical) |
| `samsung`, `hdmi`, `hdmi-1` | `samsung` | Samsung HDMI-1 (1920×1080 logical) |
| `laptop`, `edp`, `edp-1` | `laptop` | Laptop eDP-1 (2560×1440 logical) |

## CDP Injection Details

The bridge connects to Trae's Electron process via Chrome DevTools Protocol:

1. Probes `localhost:9339` then `localhost:9222` for debug targets
2. Finds the first `page` type target
3. Opens a WebSocket to the debugger URL
4. Executes JavaScript to:
   - Find the Lexical chat editor (`chat-input-v2-input-box-editable`)
   - Focus and select all existing text
   - Insert the new prompt via `document.execCommand('insertText')`
   - Click the send button after 150ms delay

This is **zero-focus** — no mouse movement, no window switching, works even
when Trae is not the active window.

## Autopilot State File (Extension-owned)

`~/.hermes/autopilot.json` is owned by the Trae Autopilot Extension
(trae-controller). Hermes must never read or write it — doing so would
override the extension and cause conflicts.

## Vision AI Button Detection

The bridge captures a screenshot, sends it to the local LM Studio vision
model (`10.123.214.1:1234`), and asks it to locate:

1. **Approval buttons**: Continue, Always Continue, Run in Terminal, Run,
   Allow, Confirm, Accept, Apply
2. **Error banners**: "Model request failed" red/warning bar

For approval buttons, it returns normalized coordinates and the bridge
translates them to absolute screen position for `xdotool` click.

For error banners, it auto-injects a retry prompt into the chat.

## Telegram Report Formats

### Autopilot Action Report (Extension sends this, not Hermes)
```
⚡ Autopilot Action Thành Công!
• Thao tác: Đã tự động bấm nút [Continue]
• Màn hình: Dell (DP-1)
• Trạng thái: Xác nhận Trae IDE đang tiếp tục chạy ổn định 🚀
⏰ 2026-08-23 08:30:00
```

### Completion Report
```
🎉 Trae IDE Đã Hoàn Tất Tác Vụ! (Dell (DP-1))
⏰ 2026-08-23 08:30:00

📁 Thay đổi mã nguồn (Git Changes):
  3 files changed, 47 insertions(+), 2 deletions(-)

📸 Ảnh chụp màn hình kết quả đính kèm.
```

### Error Recovery Report
```
⚠️ Phát Hiện Lỗi: Model Request Failed!
• Tự động xử lý: Đã gửi 'Tiếp tục công việc' vào ô chat Trae
• Màn hình: Dell (DP-1)
• Trạng thái: Đã kích hoạt Trae tiếp tục công việc ổn định 🚀
⏰ 2026-08-23 08:30:00
```
