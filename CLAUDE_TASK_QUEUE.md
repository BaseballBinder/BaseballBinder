# 🧰 CLAUDE_TASK_QUEUE.md
### BaseballBinder React + FastAPI Fix Workflow

> **Instruction to Claude:**  
> Work through these tasks **one at a time** and report back after each one.  
> After completing a task:  
> - Summarize what you fixed  
> - Show any relevant diffs or updated code  
> - Wait for confirmation before continuing to the next task  
>   
> **Goal:** Strip all demo data, restore stable UI layout, and re-link working FastAPI data.

---

## 🧹 PHASE 1 — Environment & Dependencies

### ✅ Task 1: Confirm environment stability
- Ensure `react-scripts` and `axios` are installed correctly.  
- If missing, install using:
  ```bash
  npm install --legacy-peer-deps
  ```
- Verify that `npm start` runs cleanly.

---

### ✅ Task 2: Normalize imports
- Fix any mismatched or case-sensitive imports such as:
  - `ChecklistTable` vs `CheckListTable`
- Ensure all default exports match the import syntax in their parent files.

---

### ✅ Task 3: Modernize dependencies
- Verify that `@mui/icons-material` version matches React 18+.  
- Replace deprecated `@mui/icons-material@5.1.1` if necessary.

---

## 🧱 PHASE 2 — Dashboard Layout Cleanup

### ✅ Task 4: Remove demo components
- Delete imports and JSX for:
  - `WelcomeMark`
  - `Projects`
  - `OrderOverview`
  - `SatisfactionRate`
  - `ReferralTracking`

---

### ✅ Task 5: Simplify dashboard layout
- Replace dashboard content with only:
  ```jsx
  <VuiTypography variant="h3" color="white" fontWeight="bold" mb={3}>
    BaseballBinder Dashboard
  </VuiTypography>
  <ChecklistTable />
  ```

---

### ✅ Task 6: Fix ESLint theme errors
- Resolve `light is not defined` in `examples/Tables/Table/index.js`.  
- Ensure proper theme destructuring:
  ```js
  const { palette: { light }, borders } = useTheme();
  ```

---

## 🧩 PHASE 3 — ChecklistTable Integration

### ✅ Task 7: Verify component export/import
- Confirm `ChecklistTable.jsx` has a **default export**:
  ```js
  export default function ChecklistTable() { ... }
  ```
- Ensure `Dashboard` imports it as:
  ```js
  import ChecklistTable from "../../ChecklistTable";
  ```

---

### ✅ Task 8: Verify FastAPI connection
- Test the endpoint `http://127.0.0.1:8000/api/checklist`.
- Add a console log:
  ```js
  console.log("📦 API response:", res.data);
  ```
- If data is empty, note whether backend returns an empty list or a 404.

---

### ✅ Task 9: Add basic load/error handling
Add to `ChecklistTable.jsx`:
```jsx
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  axios.get("http://127.0.0.1:8000/api/checklist")
    .then(res => setCards(res.data || []))
    .catch(err => setError(err))
    .finally(() => setLoading(false));
}, []);
```
Render conditions:
```jsx
if (loading) return <p>Loading...</p>;
if (error) return <p>Error loading data</p>;
```

---

## 🧭 PHASE 4 — Routing & Page Stability

### ✅ Task 10: Confirm routing
- Ensure the Dashboard is the only page loaded initially.
- Remove all demo routes or links if present.

---

### ✅ Task 11: Sidebar & Navbar verification
- Ensure the layout’s navbar/sidebar render without demo icons or fake stats.
- Remove imports if they reference non-existent components.

---

### ✅ Task 12: Footer cleanup
- Keep the footer base UI only.  
- Remove extra VisionUI demo widgets or links.

---

## 🧰 PHASE 5 — Sanity Checks

### ✅ Task 13: Run linter and build
```bash
npm run lint
npm run build
```
Confirm both succeed with zero blocking errors.

---

### ✅ Task 14: Test full stack integration
1. Start backend:  
   ```bash
   uvicorn main:app --reload
   ```
2. Start frontend:  
   ```bash
   npm start
   ```
3. Verify `/api/checklist` populates the React table.

---

### ✅ Task 15: Final cleanup
- Delete unused demo folders and files:
  - `src/layouts/dashboard/components`
  - `src/examples`
  - `src/assets/images` (optional)
- Keep only the base layout, theme, and your working components.

---

## 📋 Reporting Format (Claude should follow this after each fix)
```
✅ Task # (number): [short title]
🔧 Summary of fix:
[one or two sentences]
📄 Changed files:
- [list of files]

🧠 Next steps: [what to verify or test]
```

---

### ⚠️ Reminder
> Only work through **one task at a time**.  
> Wait for confirmation before continuing.  
> Keep explanations concise to preserve token usage.
