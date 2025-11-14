# 🧾 BaseballBinder Dashboard Enhancement Plan

## Overview
This document outlines the **comprehensive dashboard enhancement** for BaseballBinder, building upon the existing React + Vision UI Dashboard implementation with FastAPI backend.

**Goal:** Transform the current 4-stat dashboard into a comprehensive analytics hub featuring collection insights, pricing trends, activity tracking, and visual analytics.

### Current State
- ✅ Backend: FastAPI (`backend/main.py`) with extensive eBay integration and admin analytics
- ✅ Frontend: React + Vision UI Dashboard with 4 StatCards
- ✅ Database: SQLite with Card, CardPriceHistory, CardSearchHistory, EbayApiCallLog, EbaySearchCache tables
- ✅ eBay Integration: OAuth-based price checking, image search, rate limiting, caching

### What's Being Added
- 📊 10+ new stats endpoints for comprehensive analytics
- 📈 ApexCharts integration for data visualization (donut, bar, line, heatmap)
- 🎯 Enhanced dashboard with 4 major sections (Core Stats, Composition, Activity, Analytics)
- 🎨 Reusable chart components following Vision UI design patterns

---

## ✅ IMPLEMENTATION STATUS (Updated 2025-11-08)

### 🎉 COMPLETED - Phase 1: Backend Foundation

**Database Enhancements:**
- ✅ Added index to `Card.year` in models.py
- ✅ Added index to `Card.team` in models.py

**New API Endpoints Created & Tested:**
1. ✅ `GET /stats/enhanced` - Enhanced stats with 7-day trends, tracked count, unique sets
2. ✅ `GET /stats/top-tracked-cards?limit=3` - Top tracked cards by value with preview images
3. ✅ `GET /stats/card-types` - Card distribution (Graded/Autograph/Numbered/Parallel/Base)
4. ✅ `GET /stats/team-distribution?limit=10` - Top teams by card count
5. ✅ `GET /stats/player-distribution?limit=10` - Top players by card count
6. ✅ `GET /stats/set-breakdown?limit=10` - Top sets by card count
7. ✅ `GET /stats/recent-additions?limit=10` - Recently added cards with preview images
8. ✅ `GET /stats/milestones` - Collector milestones and progress tracking
9. ✅ `GET /stats/monthly-snapshot` - Last 30 days vs previous 30 days comparison
10. ✅ `GET /stats/year-distribution` - Cards by year
11. ✅ `GET /stats/growth-over-time?period=monthly&months=12` - Collection growth charts
12. ✅ `GET /stats/value-trends?period=monthly&months=12` - Value trends from CardPriceHistory
13. ✅ `GET /stats/activity-heatmap?days=365` - Daily addition activity for heatmap

**Endpoint Testing:**
- ✅ All endpoints tested with curl and return valid JSON
- ✅ Timezone-aware datetime handling fixed
- ✅ Empty state handling implemented
- ✅ Tested with real collection data (216 cards)

### 🎉 COMPLETED - Phase 2: Frontend Chart Components

**New React Components Created:**
1. ✅ `frontend/src/components/ChartContainer.jsx` - Reusable wrapper with Vision UI styling
2. ✅ `frontend/src/components/DonutChart.jsx` - Donut chart for card type distribution
3. ✅ `frontend/src/components/BarChart.jsx` - Horizontal bar chart for distributions
4. ✅ `frontend/src/components/LineChart.jsx` - Line chart for growth trends
5. ✅ `frontend/src/components/StatCardWithSparkline.jsx` - Enhanced stat card with mini trend chart

**Chart Features:**
- ✅ ApexCharts dark theme configuration matching Vision UI
- ✅ Responsive design with proper breakpoints
- ✅ Empty state handling for all charts
- ✅ Custom tooltips with proper formatting
- ✅ Gradient backgrounds and hover effects

### 🎉 COMPLETED - Phase 3: Dashboard Enhancement (Partial)

**Dashboard Updates (`frontend/src/layouts/dashboard/index.js`):**
- ✅ Enhanced from 4 stats to 6 StatCards (added Tracked Cards, Unique Sets)
- ✅ Added 7-day sparkline trend to Total Cards stat
- ✅ Integrated Card Types donut chart
- ✅ Integrated Top 5 Teams bar chart
- ✅ Integrated Top 5 Players bar chart
- ✅ Integrated Collection Growth line chart (6 months)
- ✅ Parallel API fetching for optimal performance
- ✅ Responsive grid layout with proper spacing

**Current Dashboard Sections:**
1. ✅ **Collection Overview** - 6 enhanced stat cards
2. ✅ **Collection Composition** - Card types donut, teams bar, players bar
3. ✅ **Collection Growth** - Growth trends line chart

### 🔄 IN PROGRESS / TODO

**Phase 3 Remaining:**
- ⏳ Add Recent Additions section (timeline/list view)
- ⏳ Add Milestones section with progress bars
- ⏳ Add Monthly Snapshot comparison cards
- ⏳ Add Year Distribution bar chart
- ⏳ Add Activity Heatmap (calendar view)
- ⏳ Add Set Breakdown visualization

**Phase 4: Testing & Polish:**
- ⏳ Test dashboard on mobile, tablet, desktop
- ⏳ Add loading skeletons for better UX
- ⏳ Test with empty collection (0 cards)
- ⏳ Test with large collection (1000+ cards)
- ⏳ Performance optimization if needed
- ⏳ Accessibility audit (ARIA labels, keyboard nav)

**Phase 5: Deployment:**
- ⏳ Update API URLs from test port (8001) to production (8000)
- ⏳ Re-enable static file mounting in backend/main.py
- ⏳ Build production frontend
- ⏳ Final integration testing

### 📊 Testing Results

**Sample Data from Current Collection:**
- Total Cards: 216 (progressing to 250 milestone at 86%)
- Unique Players: 62 (progressing to 100 milestone at 62%)
- Unique Sets: 35
- Card Types: 128 Base, 50 Numbered, 20 Parallel, 10 Autograph, 8 Graded
- Top Players: Derek Jeter (33), Bryce Harper (30), Josh Hamilton (12)
- Top Teams: New York Yankees (37), Philadelphia Phillies (34)

**Performance:**
- ✅ All endpoints respond in <100ms
- ✅ Parallel API fetching reduces dashboard load time
- ✅ Charts render smoothly without lag

---

## 📋 Current State Inventory (Before Starting)

### Existing Tech Stack
- **Frontend:** React + Vision UI Dashboard + Material-UI + ApexCharts
- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Icons:** React Icons (IoWallet, IoCard, IoTrendingUp, etc.)
- **Routing:** React Router DOM
- **API Client:** Axios

### Existing Database Schema (models.py)

#### Card Table
```python
id, set_name, card_number, player, team, year, variety, parallel,
autograph, numbered, graded, price_paid, current_value, sold_price,
location, notes, quantity, tracked_for_pricing, last_price_check,
ebay_avg_price, preview_image_url, preview_fit, preview_focus,
preview_zoom, created_at, updated_at
```

#### CardPriceHistory Table
```python
id, card_id, price, source, checked_at, metadata_json
```

#### CardSearchHistory Table
```python
id, card_id, player, year, set_name, card_number, search_query,
selected_ebay_item_id, selected_ebay_title, selected_ebay_image_url,
selected_ebay_price, all_results, total_results, user_confirmed,
needs_refinement, refinement_notes, searched_at, selected_at
```

#### EbayApiCallLog & EbaySearchCache Tables
```python
# Tracking API usage, caching, and rate limiting - already implemented
```

### Existing API Endpoints (backend/main.py)

✅ **Already Implemented:**

**Core Collection:**
- `GET /stats/` - Collection stats (total_cards, total_value, total_invested, profit_loss, has_ebay_data)
- `GET /cards/` - List all cards with filtering (set_name, player)
- `GET /cards/{id}` - Get single card
- `POST /cards/` - Create new card
- `PUT /cards/{id}` - Update card
- `DELETE /cards/{id}` - Delete card
- `DELETE /cards/` - Delete all cards
- `POST /cards/bulk-import` - Bulk import cards from CSV

**Price Tracking:**
- `GET /cards/tracked/` - Get all tracked cards
- `POST /cards/update-tracking` - Update tracked card list
- `POST /cards/{id}/preview` - Update/clear card preview image
- `POST /cards/bulk-update-values` - Bulk update card values from eBay

**eBay Integration:**
- `GET /ebay/test-connection` - Test eBay API credentials
- `POST /cards/{card_id}/check-ebay-price` - Check single card price
- `POST /cards/check-tracked-prices` - Check all tracked cards (max 20)
- `GET /ebay/rate-limit-stats` - Get API rate limit status
- `POST /ebay/reset-rate-limit` - Reset rate limiter
- `GET /cards/{card_id}/price` - OAuth-based price check
- `GET /ebay/oauth/test-connection` - Test OAuth credentials
- `GET /cards/{card_id}/search-with-images` - Enhanced search with image results
- `POST /cards/{card_id}/confirm-selection` - Confirm user-selected eBay listing

**Admin Analytics:**
- `GET /admin/api-usage/summary` - Today's API usage summary
- `GET /admin/api-usage/recent` - Recent API call logs
- `GET /admin/api-usage/trends` - API usage trends (last N days)
- `GET /admin/cache/stats` - Cache statistics

**Version Management:**
- `GET /version/current` - Get current app version
- `GET /version/check-update` - Check for GitHub updates

### Existing Dashboard (`frontend/src/layouts/dashboard/index.js`)

Current implementation shows:
- **4 StatCards:** Total Cards, Collection Value, Total Invested, Profit/Loss
- **Vision UI gradient card design** with hover effects
- **Custom StatCard component** with icons and color coding
- **Loading states** and error handling
- **Currency formatting** helper

### Vision UI Design Patterns Already in Use

```javascript
// Gradient background
background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)'

// Border glow
border: '1px solid rgba(255, 255, 255, 0.05)'

// Box shadow
boxShadow: '0 8px 26px rgba(0, 0, 0, 0.15), 0 0 20px rgba(0, 117, 255, 0.08)'

// Icon container gradient
background: 'linear-gradient(135deg, #0075ff, #3993fe)'

// Hover transform
'&:hover': { transform: 'translateY(-4px)' }
```

### Color Palette
- **Primary (Info):** `#0075ff` (blue)
- **Success:** `#01b574` (green)
- **Error:** `#e31a1a` (red)
- **Text:** `#a0aec0` (gray)
- **White:** `#ffffff`

---

## ⚙️ Step 1 — Planning Phase (Before Writing Code)

### 1. Data Availability Audit
Check which data points exist vs. which need to be computed:

**✅ Available Now:**
- Card counts by player, team, set_name, year
- Purchase prices (price_paid)
- Current values (current_value from eBay)
- eBay price history (CardPriceHistory table)
- Date added timestamps (created_at)
- Card attributes (variety, parallel, autograph, numbered, graded)
- Preview images (preview_image_url)
- Tracked card status

**❌ Not Available (Need to Add):**
- Set completion percentages (need checklist data)
- Card type categories (need to infer from variety/parallel/autograph)
- Player collection counts
- Team distribution counts

### 2. Required New Dashboard Endpoints (To Build)

**Section 1 - Enhanced Core Stats:**
- `GET /stats/enhanced` - Enhanced stats with trends (7-day value/card trends, tracked count, unique sets)
- `GET /stats/top-tracked-cards?limit=3` - Top 3 tracked cards with preview images

**Section 2 - Collection Composition:**
- `GET /stats/card-types` - Distribution by type (base, parallel, autograph, graded, numbered)
- `GET /stats/team-distribution?limit=10` - Top 10 teams by card count
- `GET /stats/player-distribution?limit=10` - Top 10 players by card count
- `GET /stats/set-breakdown?limit=10` - Top 10 sets by card count

**Section 3 - Activity & Highlights:**
- `GET /stats/recent-additions?limit=10` - Recently added cards with details
- `GET /stats/milestones` - Collector milestones and progress
- `GET /stats/monthly-snapshot` - Last 30 days vs previous 30 days comparison

**Section 4 - Analytics & Trends:**
- `GET /stats/growth-over-time?period=monthly&months=12` - Collection growth over time
- `GET /stats/value-trends?period=monthly&months=12` - Value growth using CardPriceHistory
- `GET /stats/year-distribution` - Card distribution by year
- `GET /stats/activity-heatmap?days=365` - Daily addition activity for heatmap

### 3. Database Performance Checks

**Indexes Already in Place (models.py):**
- `Card.id` (primary key, auto-indexed)
- `Card.set_name`, `Card.card_number`, `Card.player`
- `Card.tracked_for_pricing`, `Card.created_at`
- `CardPriceHistory.card_id`, `CardPriceHistory.checked_at`
- `CardSearchHistory.card_id`, `CardSearchHistory.searched_at`
- `EbayApiCallLog.endpoint`, `EbayApiCallLog.card_id`, `EbayApiCallLog.request_timestamp`
- `EbaySearchCache.search_query`, `EbaySearchCache.expires_at`

**Recommended to Add:**
- Index on `Card.year` for year distribution queries
- Index on `Card.team` for team distribution queries
- Composite index on `Card.created_at DESC` for recent additions

### 4. Vision UI Component Inventory

**Available Components:**
- `VuiBox` - Container with sx prop
- `VuiTypography` - Text with variants
- `VuiButton` - Buttons with colors
- `VuiAlert` - Alerts
- `Grid` (from MUI) - Layout grid
- `Card` (from MUI) - Card containers

**Chart Library:**
- ApexCharts (already imported in package.json)
- Need to install: `npm install react-apexcharts apexcharts`

### 5. Pre-Development Checklist

**Backend Preparation:**
- [ ] Review existing `/stats/` endpoint in `backend/main.py`
- [ ] Plan data aggregation queries for new stats endpoints
- [ ] Consider adding indexes to `Card.year` and `Card.team` in `models.py`
- [ ] Test queries with current database to ensure performance

**Frontend Preparation:**
- [ ] Install ApexCharts: `cd frontend && npm install react-apexcharts apexcharts`
- [ ] Review Vision UI theme colors and patterns in current dashboard
- [ ] Plan responsive grid layout (Grid from @mui/material)
- [ ] Identify reusable components to create (ChartContainer, StatCardWithSparkline, etc.)

**Development Environment:**
- [ ] Ensure backend running on `http://127.0.0.1:8000`
- [ ] Ensure frontend running on `http://localhost:3000`
- [ ] Test current `/stats/` endpoint returns valid data
- [ ] Review existing StatCard component in `frontend/src/layouts/dashboard/index.js`

---

## 🧱 Step 2 — Section Breakdown & Enhanced Tasks

### 🏁 Section 1: Enhanced Core Overview

**Goal:** Expand the existing 4-card dashboard with more insights

**Current State:**
- ✅ 4 StatCards already implemented
- ✅ GET /stats/ endpoint working

**Enhancements:**
1. Add **5th card:** "Tracked Cards" count
2. Add **6th card:** "Sets Collected" count
3. Add **carousel/grid:** Top 3 tracked cards with preview images
4. Add **sparkline charts** to existing cards showing trends

**New Components:**
- `TopTrackedCardsGrid` - 3-column grid with card previews
- `StatCardWithSparkline` - Enhanced StatCard with mini trend chart

**New Endpoints:**
```python
GET /stats/enhanced
{
  "total_cards": 1234,
  "total_value": 5000.00,
  "total_invested": 3000.00,
  "profit_loss": 2000.00,
  "tracked_count": 15,
  "unique_sets": 45,
  "value_trend_7d": [100, 120, 115, 130, 125, 140, 150],  # Last 7 days
  "cards_added_trend_7d": [2, 0, 3, 1, 5, 2, 1]
}

GET /stats/top-tracked-cards?limit=3
[
  {
    "id": 1,
    "player": "Derek Jeter",
    "year": "1993",
    "set_name": "Topps",
    "card_number": "98",
    "current_value": 500.00,
    "preview_image_url": "https://...",
    "value_change_percent": 15.5
  }
]
```

**Tasks:**
- [ ] Enhance GET /stats/ to include trends and counts
- [ ] Build GET /stats/top-tracked-cards
- [ ] Create StatCardWithSparkline component
- [ ] Create TopTrackedCardsGrid with preview images
- [ ] Add fade-in animations with CSS transitions

---

### 📊 Section 2: Collection Composition & Structure

**Goal:** Visualize what types of cards and how the collection is structured

**Widgets:**
1. `CardTypeDistribution` - Donut chart (Base, Parallel, Auto, Graded, Numbered)
2. `TeamDistribution` - Horizontal bar chart (top 10 teams)
3. `PlayerTopTen` - Leaderboard list (top 10 most collected players)
4. `SetTopTen` - Leaderboard list (top 10 sets by card count)

**Backend Logic:**

**Inferring Card Types:**
```python
def get_card_type(card):
    if card.graded:
        return 'Graded'
    if card.autograph:
        return 'Autograph'
    if card.numbered:
        return 'Numbered'
    if card.parallel:
        return 'Parallel'
    return 'Base'
```

**New Endpoints:**
```python
GET /stats/card-types
{
  "Base": 450,
  "Parallel": 125,
  "Autograph": 45,
  "Numbered": 78,
  "Graded": 12
}

GET /stats/team-distribution?limit=10
[
  {"team": "Yankees", "count": 234},
  {"team": "Red Sox", "count": 156},
  ...
]

GET /stats/player-distribution?limit=10
[
  {"player": "Derek Jeter", "count": 45},
  {"player": "Mike Trout", "count": 32},
  ...
]

GET /stats/set-breakdown?limit=10
[
  {"set_name": "Topps", "year": "2023", "count": 234},
  {"set_name": "Bowman Chrome", "year": "2022", "count": 156},
  ...
]
```

**ApexCharts Configuration (Donut):**
```javascript
const donutOptions = {
  chart: { type: 'donut', background: 'transparent' },
  labels: ['Base', 'Parallel', 'Autograph', 'Numbered', 'Graded'],
  colors: ['#0075ff', '#01b574', '#e31a1a', '#f6ad55', '#9f7aea'],
  theme: { mode: 'dark' },
  legend: { labels: { colors: '#a0aec0' } }
};
```

**Tasks:**
- [ ] Build GET /stats/card-types endpoint
- [ ] Build GET /stats/team-distribution endpoint
- [ ] Build GET /stats/player-distribution endpoint
- [ ] Build GET /stats/set-breakdown endpoint
- [ ] Create DonutChart component with Vision UI styling
- [ ] Create BarChart component with Vision UI styling
- [ ] Create Leaderboard component with player/set lists
- [ ] Test with datasets of varying sizes (10-1000 cards)

---

### 🧮 Section 3: Activity, Highlights & Milestones

**Goal:** Show recent activity and celebrate milestones

**Widgets:**
1. `RecentAdditions` - Timeline/feed of last 10 cards added
2. `CollectorMilestones` - Badge panel (100 cards, 500 cards, $1000 invested, etc.)
3. `MonthlySnapshot` - Stats for last 30 days vs. previous 30

**New Endpoints:**
```python
GET /stats/recent-additions?limit=10
[
  {
    "id": 123,
    "player": "Shohei Ohtani",
    "year": "2023",
    "set_name": "Topps Chrome",
    "card_number": "1",
    "preview_image_url": "https://...",
    "created_at": "2025-11-07T10:30:00Z",
    "days_ago": 1
  }
]

GET /stats/milestones
{
  "total_cards_milestones": [100, 500, 1000],  # Achieved milestones
  "total_cards_next": 1500,
  "total_cards_progress": 0.65,  # 65% to next milestone

  "total_value_milestones": [1000, 5000],
  "total_value_next": 10000,
  "total_value_progress": 0.72,

  "unique_players_milestones": [10, 25, 50],
  "unique_players_next": 100,
  "unique_players_progress": 0.45
}

GET /stats/monthly-snapshot
{
  "last_30_days": {
    "cards_added": 45,
    "value_added": 500.00,
    "unique_sets_added": 5
  },
  "previous_30_days": {
    "cards_added": 32,
    "value_added": 350.00,
    "unique_sets_added": 3
  },
  "change": {
    "cards_added_percent": 40.6,
    "value_added_percent": 42.9,
    "unique_sets_added_percent": 66.7
  }
}
```

**Tasks:**
- [ ] Build GET /stats/recent-additions endpoint
- [ ] Build GET /stats/milestones endpoint
- [ ] Build GET /stats/monthly-snapshot endpoint
- [ ] Create RecentAdditionsTimeline component
- [ ] Create MilestoneBadges component with progress bars
- [ ] Create MonthlySnapshotCards with comparison arrows
- [ ] Add smooth scroll animations for timeline

---

### 📈 Section 4: Analytics, Trends & Historical Data

**Goal:** Leverage CardPriceHistory and created_at timestamps for insights

**Widgets:**
1. `CollectionGrowthChart` - Line chart of total cards over time
2. `ValueGrowthChart` - Line chart of collection value over time (from CardPriceHistory)
3. `YearDistribution` - Bar chart of cards by year
4. `ActivityHeatmap` - Calendar heatmap of daily adds
5. `TopSetsTimeline` - Sparkline for each top set showing growth

**New Endpoints:**
```python
GET /stats/growth-over-time?period=monthly&months=12
{
  "card_count": [
    {"date": "2024-12-01", "count": 850},
    {"date": "2025-01-01", "count": 920},
    {"date": "2025-02-01", "count": 1015},
    ...
  ],
  "total_value": [
    {"date": "2024-12-01", "value": 3500.00},
    {"date": "2025-01-01", "value": 4200.00},
    ...
  ]
}

GET /stats/year-distribution
[
  {"year": "2023", "count": 234},
  {"year": "2022", "count": 189},
  {"year": "2021", "count": 145},
  ...
]

GET /stats/activity-heatmap?days=365
[
  {"date": "2024-11-08", "count": 5},
  {"date": "2024-11-07", "count": 2},
  {"date": "2024-11-06", "count": 0},
  ...
]
```

**ApexCharts Configuration (Line Chart):**
```javascript
const lineOptions = {
  chart: {
    type: 'line',
    background: 'transparent',
    toolbar: { show: false }
  },
  stroke: { curve: 'smooth', width: 3 },
  colors: ['#0075ff'],
  theme: { mode: 'dark' },
  grid: {
    borderColor: 'rgba(255, 255, 255, 0.1)',
    strokeDashArray: 4
  },
  xaxis: {
    type: 'datetime',
    labels: { style: { colors: '#a0aec0' } }
  },
  yaxis: {
    labels: { style: { colors: '#a0aec0' } }
  },
  tooltip: {
    theme: 'dark',
    x: { format: 'MMM yyyy' }
  }
};
```

**Tasks:**
- [ ] Build GET /stats/growth-over-time endpoint
- [ ] Build GET /stats/year-distribution endpoint
- [ ] Build GET /stats/activity-heatmap endpoint
- [ ] Create LineChart component for growth trends
- [ ] Create BarChart component for year distribution
- [ ] Create ActivityHeatmap component (calendar view)
- [ ] Optimize CardPriceHistory queries for performance
- [ ] Add date range filters (Last 30 days, 3 months, 1 year, All time)
- [ ] Implement lazy loading for historical data

---

### 🎨 Section 5: Layout & Design Finalization

**Goal:** Ensure consistent Vision UI styling and responsive layout

**Layout Structure:**
```
Dashboard
├── Section 1: Core Stats (2 rows)
│   ├── Row 1: 6 StatCards (Grid: xs=12 md=6 lg=4 xl=2)
│   └── Row 2: Top 3 Tracked Cards (Grid: xs=12 md=4)
├── Section 2: Composition (1 row)
│   ├── Card Type Donut (xs=12 md=6 lg=4)
│   ├── Team Distribution (xs=12 md=6 lg=4)
│   └── Player Top 10 (xs=12 md=6 lg=4)
├── Section 3: Activity (1 row)
│   ├── Recent Additions (xs=12 md=6)
│   ├── Milestones (xs=12 md=3)
│   └── Monthly Snapshot (xs=12 md=3)
└── Section 4: Analytics (2 rows)
    ├── Collection Growth Line (xs=12 lg=6)
    ├── Value Growth Line (xs=12 lg=6)
    ├── Year Distribution Bar (xs=12 md=6)
    └── Activity Heatmap (xs=12 md=6)
```

**Vision UI Container Pattern:**
```javascript
<VuiBox
  sx={{
    background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
    borderRadius: '15px',
    padding: '20px',
    boxShadow: '0 8px 26px rgba(0, 0, 0, 0.15)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
  }}
>
  {/* Chart content */}
</VuiBox>
```

**Tasks:**
- [ ] Create ChartContainer component (reusable wrapper)
- [ ] Implement responsive Grid breakpoints
- [ ] Add section headers with VuiTypography
- [ ] Apply consistent padding/margins (p={3}, mb={3})
- [ ] Add loading skeletons for all sections
- [ ] Add empty state placeholders
- [ ] Test on mobile, tablet, desktop viewports
- [ ] Add smooth scroll behavior for long dashboards
- [ ] Implement collapsible sections (optional)

---

## 🧩 Step 3 — Validation & Troubleshooting Phase

### Data Validation Checklist
- [ ] Run test queries on development database
- [ ] Verify date ranges work correctly with timezone-aware timestamps
- [ ] Check for NULL values in computed fields (current_value, price_paid)
- [ ] Ensure CardPriceHistory table has data for value trends
- [ ] Test with empty collection (0 cards)
- [ ] Test with small collection (1-10 cards)
- [ ] Test with large collection (1000+ cards)

### Performance Validation
- [ ] Profile all new endpoints with `EXPLAIN ANALYZE`
- [ ] Ensure all queries use indexes
- [ ] Add pagination for large result sets
- [ ] Implement caching for expensive queries (Redis or in-memory)
- [ ] Measure frontend render time with React DevTools
- [ ] Ensure ApexCharts don't block main thread

### Integration Testing
- [ ] Verify all endpoints return correct JSON format
- [ ] Test error handling (network failures, empty responses)
- [ ] Verify loading states display correctly
- [ ] Test filter/date range changes update charts
- [ ] Ensure tracked card updates refresh dashboard
- [ ] Test with different screen sizes

### Accessibility
- [ ] Add ARIA labels to charts
- [ ] Ensure proper heading hierarchy (h1 > h2 > h3)
- [ ] Test keyboard navigation
- [ ] Verify color contrast meets WCAG AA
- [ ] Add alt text for card preview images

---

## 🚀 Step 4 — Implementation Order (Recommended)

### Phase 1: Backend Foundation (2-3 days)
1. Build all new GET /stats/* endpoints
2. Add database indexes if missing
3. Write unit tests for each endpoint
4. Document endpoint responses

### Phase 2: Core Enhancement (1-2 days)
1. Enhance existing dashboard StatCards
2. Add TopTrackedCardsGrid component
3. Test with real data

### Phase 3: Composition Charts (2-3 days)
1. Install ApexCharts
2. Build reusable ChartContainer component
3. Create DonutChart, BarChart components
4. Add card type and team distribution

### Phase 4: Activity & Milestones (1-2 days)
1. Build RecentAdditions component
2. Build Milestones badges
3. Build MonthlySnapshot comparison

### Phase 5: Analytics & Trends (3-4 days)
1. Build LineChart component
2. Add collection growth chart
3. Add value growth chart (using CardPriceHistory)
4. Add year distribution
5. Add activity heatmap (most complex)

### Phase 6: Polish & Testing (1-2 days)
1. Responsive layout testing
2. Loading states and error handling
3. Performance optimization
4. Accessibility audit
5. Final design polish

**Total Estimated Time:** 10-16 days

---

## ✅ Deliverables

**Backend:**
- [ ] 10+ new GET /stats/* endpoints
- [ ] Database indexes optimized
- [ ] All endpoints documented with sample responses
- [ ] Unit tests for all stat calculations

**Frontend:**
- [ ] Enhanced dashboard page (`layouts/dashboard/index.js`)
- [ ] Reusable chart components library
- [ ] ApexCharts integrated with Vision UI theme
- [ ] All sections responsive (mobile, tablet, desktop)
- [ ] Loading states and error handling for all sections

**Documentation:**
- [ ] API endpoint documentation
- [ ] Component usage guide
- [ ] Performance optimization notes
- [ ] Accessibility checklist completed

---

## 🎯 Key Differences from Original Plan

### Tech Stack Updates
- ~~Tailwind + shadcn/ui~~ → **Vision UI + Material-UI**
- ~~Recharts~~ → **ApexCharts**
- ~~React Icons~~ → **Already using React Icons (IoWallet, etc.)**

### Database Schema Corrections
- ~~`card_name, player_name`~~ → **`player, set_name, card_number`**
- ~~`card_type`~~ → **Inferred from `variety, parallel, autograph, numbered, graded`**
- ~~`purchase_price, estimated_value`~~ → **`price_paid, current_value, ebay_avg_price`**
- ~~`is_tracked`~~ → **`tracked_for_pricing`**

### New Capabilities Added
- ✅ CardPriceHistory table for historical value tracking
- ✅ Preview images with zoom/fit/focus controls
- ✅ eBay price integration with caching
- ✅ Tracked collection with price history charts

### Existing Foundation to Build On
- ✅ StatCard component pattern established
- ✅ Vision UI gradient backgrounds and styling
- ✅ GET /stats/ endpoint working
- ✅ Loading states and currency formatting

---

## 🧠 Development Prompt for Claude Code / AI Agent

**Project Context:**
You are enhancing an existing BaseballBinder card collection application. The app currently has:
- **Backend:** FastAPI running at `http://127.0.0.1:8000` (located in `backend/main.py`)
- **Frontend:** React + Vision UI Dashboard running at `http://localhost:3000`
- **Database:** SQLite with SQLAlchemy ORM (schema defined in `models.py`)
- **Current Dashboard:** 4 StatCards showing total_cards, total_value, total_invested, profit_loss

**Your Task:**
Transform the basic 4-stat dashboard into a comprehensive analytics hub with charts, trends, activity tracking, and collection insights.

### Step-by-Step Implementation Guide

#### Phase 1: Backend Development (Priority)
1. **Install dependencies** (if needed): Verify FastAPI, SQLAlchemy, and dependencies are installed
2. **Add database indexes** to `models.py`:
   - Add `index=True` to `Card.year` column
   - Add `index=True` to `Card.team` column
3. **Create new stats endpoints** in `backend/main.py`:
   - Start with `GET /stats/enhanced` (extends existing `/stats/`)
   - Add `GET /stats/top-tracked-cards?limit=3`
   - Add composition endpoints: `/stats/card-types`, `/stats/team-distribution`, `/stats/player-distribution`, `/stats/set-breakdown`
   - Add activity endpoints: `/stats/recent-additions`, `/stats/milestones`, `/stats/monthly-snapshot`
   - Add analytics endpoints: `/stats/growth-over-time`, `/stats/value-trends`, `/stats/year-distribution`, `/stats/activity-heatmap`
4. **Test each endpoint** with curl or Postman before moving to frontend

#### Phase 2: Frontend Setup
1. **Install ApexCharts**: Run `cd frontend && npm install react-apexcharts apexcharts`
2. **Create reusable components** in `frontend/src/components/`:
   - `ChartContainer.jsx` - Wrapper with Vision UI styling
   - `StatCardWithSparkline.jsx` - Enhanced StatCard with mini chart
   - `DonutChart.jsx` - For card type distribution
   - `BarChart.jsx` - For team/player/set distributions
   - `LineChart.jsx` - For growth trends
   - `ActivityHeatmap.jsx` - Calendar heatmap for additions

#### Phase 3: Dashboard Enhancement
1. **Update `frontend/src/layouts/dashboard/index.js`**:
   - Keep existing 4 StatCards
   - Add new sections below using Material-UI Grid layout
   - Fetch data from new `/stats/*` endpoints using axios
   - Add loading states and error handling
2. **Section Layout:**
   - Section 1: Enhanced Core Stats (6 StatCards + Top 3 Tracked Cards)
   - Section 2: Collection Composition (Donut chart, Team bars, Player list)
   - Section 3: Activity & Highlights (Recent additions, Milestones, Monthly snapshot)
   - Section 4: Analytics & Trends (Growth charts, Year distribution, Heatmap)

#### Phase 4: Styling & Polish
1. **Match Vision UI patterns:**
   - Use gradient backgrounds: `linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)`
   - Use border glow: `border: '1px solid rgba(255, 255, 255, 0.05)'`
   - Use box shadows: `boxShadow: '0 8px 26px rgba(0, 0, 0, 0.15)'`
   - Add hover transforms: `'&:hover': { transform: 'translateY(-4px)' }`
2. **Configure ApexCharts dark theme:**
   - Set `theme: { mode: 'dark' }`
   - Use colors: `#0075ff` (info), `#01b574` (success), `#e31a1a` (error)
   - Set grid color: `borderColor: 'rgba(255, 255, 255, 0.1)'`

### Key Technical Requirements

**Database Queries:**
- Use SQLAlchemy `func` for aggregations (count, sum, avg)
- Use `filter()` for date ranges and conditionally filtering
- Use `group_by()` for distributions
- Use `order_by()` with `desc()` or `asc()` for rankings

**Card Type Inference Logic:**
```python
def get_card_type(card):
    if card.graded:
        return 'Graded'
    if card.autograph:
        return 'Autograph'
    if card.numbered:
        return 'Numbered'
    if card.parallel:
        return 'Parallel'
    return 'Base'
```

**Frontend Data Fetching Pattern:**
```javascript
useEffect(() => {
  axios.get("http://127.0.0.1:8000/stats/enhanced")
    .then(res => setStats(res.data))
    .catch(err => console.error(err))
    .finally(() => setLoading(false));
}, []);
```

**Responsive Grid Pattern:**
```javascript
<Grid container spacing={3}>
  <Grid item xs={12} md={6} lg={4}>
    {/* Component */}
  </Grid>
</Grid>
```

### Success Criteria
- [ ] All new endpoints return valid JSON responses
- [ ] Dashboard renders without errors in browser console
- [ ] Charts display with proper Vision UI dark theme styling
- [ ] Responsive layout works on mobile (xs), tablet (md), desktop (lg)
- [ ] Loading states show while fetching data
- [ ] Empty states handle collections with 0 cards gracefully
- [ ] No performance issues with 100-1000 card collections

### Testing Checklist
- [ ] Test backend endpoints with `curl http://127.0.0.1:8000/stats/enhanced`
- [ ] Verify database queries use indexes (check with SQLite EXPLAIN QUERY PLAN)
- [ ] Test frontend with empty collection (0 cards)
- [ ] Test frontend with small collection (1-10 cards)
- [ ] Test frontend with large collection (100+ cards)
- [ ] Test responsive layout at different breakpoints
- [ ] Verify all charts render properly with ApexCharts

---

**Project Metadata:**
- **Author:** Jordan Hanratty
- **Version:** 3.0 (Enhanced Dashboard Implementation)
- **Last Updated:** 2025-11-08
- **Tech Stack:** React + Vision UI Dashboard + FastAPI + SQLAlchemy + SQLite
- **Backend Location:** `backend/main.py`
- **Frontend Location:** `frontend/src/layouts/dashboard/index.js`
- **Database Models:** `models.py`
