# 🧭 Vision UI Migration Plan — BaseballBinder

## Overview
You currently have two local environments:
- **Old (Working) Frontend:** `127.0.0.1:5500`  
  - Fully functional checklist requests, approvals, and data logic.  
  - Built using basic frontend structure.  
  - Correct functionality but outdated layout.

- **New Vision UI Frontend:** `localhost:3000`  
  - Proper modern design and dashboard layout (Vision UI).  
  - Contains “Coming Soon” placeholders, broken imports, and incomplete data binding.  
  - Uses `@mui` and Chakra/Emotion theming.

- **Backend:**  
  - Running at `127.0.0.1:8000` (FastAPI).  
  - Fully functional.  
  - Code files:
    - `checklist_api.py`  
    - `checklist_models.py`  
    - `models.py`  
    - `rate_limiter.py`  
    - `ebay_service.py`  
  - ✅ These files are **authoritative** and must **not be modified** during migration.

---

## 🧱 Migration Objective
Rebuild the full working logic from the **old frontend** into the **Vision UI dashboard** while:
- Maintaining **100% functional parity** (everything that worked before must work the same).  
- Applying **Vision UI’s styling** and layout.  
- Keeping code **modular**, **maintainable**, and **organized by feature**.  
- Ensuring **no backend changes** or endpoint rewrites.

---

## ⚙️ Rules for Claude Code
1. Use the old UI on port `5500` **only as a functional reference**.  
   - Observe how requests, approvals, and imports behave.  
   - Do not copy its HTML/CSS layout.  

2. Use the FastAPI backend **exactly as-is**.  
   - Reference endpoints in:
     - `/checklist/request` (POST)
     - `/checklist/requests` (GET)
     - `/checklist/requests/{id}/status` (PATCH)
     - `/checklist/summary` (GET)
     - `/checklist/rescan` (POST)
   - Validate all frontend API calls to ensure they match these routes.

3. Keep the **dark gradient Vision UI theme** consistent.  
   - No bright white tables or default MUI colors.  
   - Use `VuiBox`, `VuiTypography`, and other Vision UI wrappers wherever possible.

4. **Do not modify backend files.**  
   - Frontend only.

5. **Confirm successful completion of each stage before continuing.**

---

## ✅ Task Sequence (with Confirmation Required)

### Stage 1 – Request Checklist (User Form)
**Goal:** Create a React form allowing users to submit new checklist requests.

- Inputs: **Set Name**, **Year**, **Manufacturer**, **Email**, **Notes**  
- Endpoint: `POST /checklist/request`  
- Response: success alert, clear form  
- UI: Vision UI dark-themed card with proper field validation  

**Claude must:**
- Show code changes and affected files.  
- Provide testing instructions (`npm start`, backend checks).  
- Wait for confirmation before proceeding.  

---

### Stage 2 – Admin Dashboard
**Goal:** Build the admin panel for managing checklist requests.

- Endpoints:
  - `GET /checklist/requests`
  - `PATCH /checklist/requests/{id}/status`
- Features:
  - Display requests table
  - Approve/Reject/Complete buttons
  - Color-coded statuses

**Claude must:**  
- Report updated files and new components.  
- List example API requests.  
- Wait for confirmation before moving on.

---

### Stage 3 – Checklist Management
**Goal:** Manage and rescan checklists.

- Endpoints:
  - `GET /checklist/summary`
  - `POST /checklist/rescan`
- Features:
  - Show imported checklist summaries
  - Button to trigger rescan
  - Display import count and errors

**Claude must:**  
- Display implementation details.
- Confirm UI and data response work as expected before continuing.

---

### Stage 4 – Add Cards & View Collection
**Goal:** Migrate and restyle the working “Add Cards” and “View Collection” features.

- Retain logic from the previous build.
- Integrate with Vision UI components.

**Claude must:**  
- Confirm both routes function and display data.  
- Pause for review before final polish.

---

### Stage 5 – Final QA, Cleanup, & Integration
**Goal:** Finalize layout, imports, routing, and component structure.

- Remove unused placeholders and temp files.
- Fix ESLint, import errors, and color mismatches.
- Confirm all endpoints function.

**Claude must:**  
- Provide complete summary of structure.
- Only complete when confirmed by user.

---

## 🎨 Style Guide
| Component | Styling Rule |
|------------|--------------|
| Cards | Use gradient background: `linear-gradient(127.09deg, rgba(6,11,40,0.94) 19.41%, rgba(10,14,35,0.49) 76.65%)` |
| Tables | Background: `#1b1c2a`, Text: `white`, Header: semi-transparent |
| Buttons | Use Vision UI variants (`color="info"`, `variant="contained"`) |
| Typography | Use `VuiTypography`, avoid MUI defaults |
| Layout | Maintain spacing with `VuiBox` |
| Alerts | Soft gradient with `VuiBox` |

---

## 🛡 Safety Mechanisms
- Back up your current `frontend/` before any modification.  
- Only modify:  
  - `src/layouts/`  
  - `src/components/`  
  - `src/routes.js`
- Never overwrite `.env`, `.py`, or `package.json` without permission.  
- Keep the backend untouched.

---

## 🚦 Review Cycle
After each stage:
1. Claude must summarize changes.  
2. Show new/modified file paths.  
3. Provide testing instructions.  
4. Wait for explicit user confirmation before proceeding.

---

## 📁 Expected Structure After Migration
```
frontend/src/
├── components/
│   ├── RequestChecklistTable.jsx
│   ├── AdminRequestsTable.jsx
│   ├── ChecklistSummaryTable.jsx
│   └── Shared/
│       ├── StatusBadge.jsx
│       ├── RescanButton.jsx
│       └── Alerts/
├── layouts/
│   ├── request-checklist/
│   │   └── index.js
│   ├── admin-dashboard/
│   │   └── index.js
│   ├── checklist-management/
│   │   └── index.js
│   ├── add-cards/
│   │   └── index.js
│   └── view-collection/
│       └── index.js
└── routes.js
```
---

## ✅ Deliverable Summary
Claude Code should produce:
- A **working, styled Vision UI frontend** that fully integrates with the FastAPI backend.  
- No broken imports, white backgrounds, or missing routes.  
- A complete changelog and file list per stage.  
- A functioning, testable system confirmed after each phase.
