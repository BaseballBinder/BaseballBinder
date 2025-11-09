Date: 2025-11-08

Summary of safe, low-impact changes applied by Codex

- checklist_api.py
  - Added logging and module logger `logger = logging.getLogger(__name__)`.
  - Replaced several `print(...)` statements with `logger.info(...)` for consistent logs:
    - Scanning and force-reimport messages.
    - Replacement and removal notices during scan.
    - Rescan endpoint "existing cleared" message.
  - Added `ChecklistItem` Pydantic model and set `response_model=List[ChecklistItem]` for `GET /checklist/{year}/{set_name}` to ensure stable JSON serialization.

- No functional behavior was changed; endpoints and data formats remain backward compatible.

Notes / deferred items (not changed)

- Email notification helper still prints a few lines with non-ASCII characters in certain paths; left unchanged to avoid brittle edits. Functionality remains the same. Consider replacing those `print(...)` lines with `logger.warning/error(...)` in a future pass.
- The standalone verifier script at `checklists/checklist_verifier.py` contains malformed print strings and emoji artifacts. Left untouched to avoid risky text edits; fix is straightforward: replace the broken print line with a plain ASCII string.

Frontend table alignment changes (2025-11-08)

- frontend/src/components/CollectionTable.jsx
  - Wrapped the table in MUI `TableContainer` for consistent header/body scroll context.
  - Added a `columns` array and generated `<colgroup>` and header cells from it to enforce exact widths.
  - Updated loading/empty states to use `colSpan={columns.length}`.
  - Note: Body cells still rendered explicitly; can be converted to columns-driven rows in a later pass.

- frontend/src/components/RequestChecklistTable.jsx
  - Wrapped the table in `TableContainer`.

- frontend/src/components/ChecklistSummaryTable.jsx
  - Wrapped the table in `TableContainer`.
Phase 1 (Tracked Collection groundwork)

- models.py: added CardPriceHistory table for storing per-card price data.
- main.py: now records history on price updates and exposes GET /cards/{card_id}/history (daily/weekly/monthly/lifetime).
- View Collection: replaced ""Track Card"" action tied to /cards/update-tracking.
- Added Tracked Collection layout (/tracked-collection) with CSS-grid table, bulk Update All, per-card Update/Remove, and insights dialog (LineChart + percent change + preview image).
- routes.js: Collection menu now includes Tracked Collection.
Phase 2 (Tracked insights + UX)

- frontend/src/components/CollectionTable.jsx: cached tracked IDs client-side, added highlight/skeletons, and replaced the Track Card button with inline feedback.
- frontend/src/layouts/tracked-collection/index.js: themed the insights dialog, added skeleton loading rows, timezone-aware timestamps, and inline success toasts for updates/removals.
- Backend support already writing CardPriceHistory; insights view now consumes that data with percent change + preview fallback.
Phase 2 tweaks (UX fixes)

- Collection table: added tracked highlighting, skeleton loading, cached tracked IDs, and success/error toasts for the Track Card action.
- Tracked collection: themed insights dialog, added skeleton rows, timezone-aware timestamps, percent change stats, and fallback history data (plus instructions).
- Tabs now use scrollable styling consistent with the dark theme.
