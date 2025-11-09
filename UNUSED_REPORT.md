Unused/Legacy Items (static scan; verify before removal)

Backend

- backend/main.py
  - Duplicates the main FastAPI app defined in root `main.py` and also mounts `frontend/build`.
  - Imports legacy `ebay_api.py` and `rate_limiter.py`.
  - If you start the server with `python main.py`, this file is likely unused.

- ebay_api.py and rate_limiter.py
  - Only referenced from `backend/main.py`.
  - The newer OAuth Browse API client in `ebay_service.py` is used from root `main.py`.
  - If `backend/main.py` is unused, these are effectively unused at runtime.

- backend/app/core/* (CSV files and duplicate verifier)
  - CSV assets are duplicated under `checklists/` and `backend/app/core/`.
  - `backend/app/core/checklist_verifier.py` is not imported anywhere; likely leftover.

- checklists/checklist_verifier.py
  - Standalone utility; not used by the API at runtime. Contains broken/garbled print strings.

Frontend

- frontend/api.js
  - A configured axios instance exists but most components import axios directly and hardcode base URLs.
  - Consider centralizing calls to this file and removing duplicate, hardcoded axios usage.

- Hardcoded API URLs
  - Found multiple `http://127.0.0.1:8000` references across components (tables, forms, dashboard stats).
  - Prefer a single source of truth via `frontend/api.js` and `REACT_APP_API_URL` env var.

General

- Two sets of requirements files (`requirements.txt` and `backend/requirements.txt`).
  - The backend one includes `ebaysdk` and `pyyaml` used by legacy and OAuth code respectively.
  - Consider consolidating to a single requirements file if you maintain one server entrypoint.

Important: This list is based on text search (no runtime tracing). Before removing, confirm your deployment/start command and build process to avoid deleting anything still in use.

