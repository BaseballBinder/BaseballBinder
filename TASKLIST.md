# BaseballBinder UI Rebuild - Task List

## Phase 1: Navigation & Structure ✅ Priority
### Task 1.1: Left Sidebar Navigation
- [ ] Create clean left sidebar with these items:
  - Dashboard (home icon)
  - Import Checklists (upload icon)
  - Add Cards (plus icon)
  - View Collection (cards icon)
  - Manage Checklists (list icon) - NEW
  - Request Checklist (message icon)
- [ ] Add BaseballBinder logo at top of sidebar
- [ ] Add user profile section at bottom (placeholder for now)
- [ ] Active page highlighting
- [ ] Smooth hover effects
- Note: Settings removed - already have cog icon in navbar

### Task 1.2: Checklists Page (NEW)
- [ ] Remove checklist table from Dashboard
- [ ] Create dedicated "Manage Checklists" page showing:
  - Table: Set Name | Year | Card Count | Last Updated
  - "Rescan Folder" button at top
  - Search/filter functionality
  - Clean, organized layout
- [ ] Show imported checklists from /checklists folder structure
- [ ] Display folder organization (by year)

### Task 1.3: Clean Up Current Template
- [ ] Remove "Free Download", "View Documentation", "Star" buttons
- [ ] Disable/remove Share and Tweet links
- [ ] Simplify "Need Help?" section - just keep minimal text
- [ ] Remove all template placeholder text

---

## Phase 2: Design System ✅ Priority
### Task 2.1: Implement Color Palette
- [ ] Reference DESIGN.md for all colors
- [ ] Apply consistently across all pages
- [ ] Update all buttons, cards, backgrounds
- [ ] Ensure good contrast and readability

### Task 2.2: Typography
- [ ] Use design system fonts
- [ ] Consistent heading sizes
- [ ] Proper text hierarchy
- [ ] Readable body text

### Task 2.3: Component Styling
- [ ] Cards: consistent shadows, borders, spacing
- [ ] Buttons: primary, secondary, danger styles
- [ ] Tables: clean rows, hover effects
- [ ] Forms: consistent input styling

---

## Phase 3: Dashboard Redesign ✅ Priority
### Task 3.1: Statistics Cards
Create engaging stat cards showing:
- [ ] Total Cards in Collection
- [ ] Total Collection Value
- [ ] Total Cards Available (across all checklists)
- [ ] Total BaseballBinder Users (placeholder: "1 Happy Collector!")
- [ ] Cards Tracked for Pricing (count)
- [ ] Last Price Check Date
- [ ] Most Valuable Card
- [ ] Newest Addition

### Task 3.2: Quick Actions
- [ ] Import Checklists button
- [ ] Add New Card button
- [ ] Check Tracked Prices button
- [ ] View Full Collection button

### Task 3.3: Recent Activity
- [ ] Show last 5 cards added
- [ ] Show recent price checks
- [ ] Show requested checklists status

---

## Phase 4: Feature Integration
### Task 4.1: Existing Features
- [ ] Card CRUD operations
- [ ] CSV checklist import (auto-import from folder)
- [ ] Checklist request form
- [ ] Price tracking (20 card limit)
- [ ] Search and filter
- [ ] Collection statistics

### Task 4.2: eBay Integration
- [ ] Price check button per card
- [ ] Bulk price check for tracked cards
- [ ] Display eBay results
- [ ] Update card values
- [ ] Rate limit tracking

### Task 4.3: Admin Features
- [ ] View checklist requests
- [ ] Clear all cards (testing)
- [ ] API usage stats
- [ ] System status

---

## Testing Checklist
- [ ] All navigation links work
- [ ] Pages load correctly
- [ ] Forms submit properly
- [ ] Buttons are functional
- [ ] Responsive on mobile
- [ ] No console errors
- [ ] Database operations work
- [ ] File uploads work
