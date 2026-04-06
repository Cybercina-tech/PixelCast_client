# Template Editor Baseline Audit

## Scope
- Screen audited: `frontend/src/pages/templates/TemplateEditor.vue`
- Supporting shell/store/backend paths reviewed:
  - `frontend/src/components/layout/AppLayout.vue`
  - `frontend/src/stores/templates.js`
  - `BackEnd/templates/views.py`
  - `BackEnd/templates/tests.py`

## Confirmed Issues
- Canvas is space-constrained by wide side panels and full app sidebar.
- Editor had no compact panel controls and no tabbed inspector/layers split.
- `exportJSON` exported a Promise-like value because `saveTemplate()` was not awaited.
- Global keyboard shortcuts could interfere with active form fields in properties panel.
- `online`/`offline` listeners were not removed on unmount.
- Debug-heavy console/print statements existed in critical activation/sync paths.
- Editor-specific automated coverage was missing (frontend E2E + backend template tests).

## Acceptance Criteria Used
- Canvas receives visibly larger effective workspace without removing core navigation.
- Export always saves and downloads a concrete template payload.
- Keyboard shortcuts do not fire while editing form controls.
- Window event listeners are correctly cleaned up on editor unmount.
- Backend debug output is logging-based, not raw `print`.
- New tests cover activation/sync and core editor interaction regressions.
