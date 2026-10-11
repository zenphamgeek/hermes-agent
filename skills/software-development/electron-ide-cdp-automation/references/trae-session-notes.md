# Trae CDP Session Notes

Verified pattern:

- Port `9339` exposed two targets: an `icubeProcessExplorer` utility page and the workspace page `● ref.md - VerticalRisk - TraeCode`.
- The utility page must be skipped.
- Workspace DOM exposed a visible `New Task (Ctrl+Alt+N)` control.
- Clicking that control returned `{ok:true}` and opened a new chat session.
- Earlier controller error: `TraeCDPController.__init__() got an unexpected keyword argument 'port'. Did you mean 'ports'?` Fixed with `TraeCDPController(ports=[9339])`.

Reproduction outline:

1. `TraeCDPController(ports=[9339]).get_all_active_pages()`.
2. Choose the workspace target, not the process-explorer target.
3. Evaluate visible button labels.
4. Click the button whose text contains `New Task`.
5. Re-query the workspace DOM to verify the new session.
