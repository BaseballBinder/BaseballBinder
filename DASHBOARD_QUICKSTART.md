# Dashboard Implementation - Quick Start Guide

## TL;DR for Codex

This is the condensed version of `dashboardupgrade.md`. Read this first, then refer to the full plan for details.

---

## Pre-Flight Checklist

**Before writing any code:**
- [ ] Read this entire document
- [ ] Read `dashboardupgrade.md` sections 1 & 2
- [ ] Run `test_data_generator.py` to populate test database
- [ ] Install ApexCharts: `npm install react-apexcharts apexcharts`
- [ ] Verify backend server is running on port 8000
- [ ] Verify frontend is running on port 3000

---

## Tech Stack (What You're Working With)

```
Backend: FastAPI + SQLAlchemy + SQLite
Frontend: React + Vision UI Dashboard + Material-UI
Charts: ApexCharts (NOT Recharts)
Icons: React Icons (IoWallet, IoCard, etc.)
API Client: Axios
```

---

## Database Schema (Field Names to Use)

```python
Card:
  id, set_name, card_number, player, team, year,
  variety, parallel, autograph, numbered, graded,
  price_paid, current_value, ebay_avg_price,
  tracked_for_pricing, last_price_check,
  preview_image_url, preview_fit, preview_focus, preview_zoom,
  created_at, updated_at

CardPriceHistory:
  id, card_id, price, source, timestamp
```

---

## What's Already Built (Don't Rebuild)

✅ `GET /stats/` - Returns total_cards, total_value, total_invested, profit_loss
✅ `frontend/src/layouts/dashboard/index.js` - Has 4 StatCards already
✅ Vision UI components (VuiBox, VuiTypography, VuiButton, etc.)
✅ StatCard component with gradient design
✅ Currency formatting helper

---

## What You Need to Build

### Phase 1: Backend Endpoints (Build These First)

```python
# main.py - Add these endpoints

GET /stats/top-tracked-cards?limit=3
GET /stats/card-types
GET /stats/team-distribution?limit=10
GET /stats/player-distribution?limit=10
GET /stats/set-breakdown?limit=10
GET /stats/recent-additions?limit=10
GET /stats/milestones
GET /stats/monthly-snapshot
GET /stats/growth-over-time?period=monthly&months=12
GET /stats/year-distribution
GET /stats/activity-heatmap?days=365
```

**Card Type Logic:**
```python
def get_card_type(card):
    if card.graded: return 'Graded'
    if card.autograph: return 'Autograph'
    if card.numbered: return 'Numbered'
    if card.parallel: return 'Parallel'
    return 'Base'
```

### Phase 2: Frontend Components (Build After Backend)

**File Structure:**
```
frontend/src/
├── components/
│   ├── charts/
│   │   ├── ChartContainer.jsx
│   │   ├── DonutChart.jsx
│   │   ├── BarChart.jsx
│   │   └── LineChart.jsx
│   └── dashboard/
│       ├── TopTrackedCardsGrid.jsx
│       ├── RecentAdditionsTimeline.jsx
│       ├── MilestoneBadges.jsx
│       └── MonthlySnapshotCards.jsx
└── utils/
    └── apexChartsTheme.js (already created)
```

---

## Vision UI Design Patterns (Copy These)

**Container:**
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
```

**Icon Container:**
```javascript
<VuiBox
  sx={{
    background: 'linear-gradient(135deg, #0075ff, #3993fe)',
    borderRadius: '12px',
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 4px 12px rgba(0, 117, 255, 0.4)',
  }}
>
  {icon}
</VuiBox>
```

**Colors:**
```javascript
info: '#0075ff'
success: '#01b574'
error: '#e31a1a'
text: '#a0aec0'
white: '#ffffff'
```

---

## ApexCharts Configuration (Use These)

**Already created in `frontend/src/utils/apexChartsTheme.js`:**
```javascript
import { visionUIChartTheme } from 'utils/apexChartsTheme';

// Use in your charts:
<Chart
  options={{ ...visionUIChartTheme, /* your specific options */ }}
  series={data}
  type="line"
/>
```

---

## Implementation Order (Follow This)

**Day 1-2: Backend**
1. Create all GET /stats/* endpoints in main.py
2. Test each endpoint with Postman/browser
3. Verify JSON responses match expected format

**Day 3-4: Reusable Components**
1. Create ChartContainer component
2. Create DonutChart with test data
3. Create BarChart with test data
4. Create LineChart with test data

**Day 5-6: Dashboard Sections**
1. Add TopTrackedCardsGrid to dashboard
2. Add CardTypeDistribution (donut chart)
3. Add TeamDistribution (bar chart)
4. Add PlayerTopTen (leaderboard)

**Day 7-8: Activity & Analytics**
1. Add RecentAdditions timeline
2. Add Milestones badges
3. Add MonthlySnapshot
4. Add growth charts

**Day 9-10: Polish**
1. Loading states
2. Empty states
3. Error handling
4. Responsive testing
5. Performance optimization

---

## Critical Rules (Don't Break These)

1. **Always use Vision UI components** (VuiBox, VuiTypography, etc.)
2. **Never use Tailwind classes** (this is a Material-UI project)
3. **Use ApexCharts, not Recharts**
4. **Follow the gradient background pattern** for all cards
5. **Test with test_data_generator.py data** before production
6. **Use exact field names** from database schema above
7. **Add loading states** to every component that fetches data
8. **Handle empty data** gracefully (show placeholder messages)

---

## Testing Checklist

Before marking any section complete:
- [ ] Endpoint returns correct JSON format
- [ ] Loading state displays during fetch
- [ ] Error state displays on failure
- [ ] Empty state displays when no data
- [ ] Component is responsive (test mobile, tablet, desktop)
- [ ] Matches Vision UI design language
- [ ] No console errors or warnings

---

## Common Pitfalls to Avoid

❌ **Don't:** Use `card_name` or `player_name` (wrong field names)
✅ **Do:** Use `player` and `set_name`

❌ **Don't:** Import Tailwind utilities
✅ **Do:** Use Material-UI Grid and Vision UI components

❌ **Don't:** Build charts without test data
✅ **Do:** Run test_data_generator.py first

❌ **Don't:** Use Recharts
✅ **Do:** Use ApexCharts with visionUIChartTheme

❌ **Don't:** Hardcode colors
✅ **Do:** Use Vision UI color palette

---

## Example: Complete Component Template

```javascript
import React, { useState, useEffect } from "react";
import axios from "axios";
import VuiBox from "components/VuiBox";
import VuiTypography from "components/VuiTypography";
import { CircularProgress } from "@mui/material";
import Chart from "react-apexcharts";
import { visionUIChartTheme } from "utils/apexChartsTheme";

function ExampleChart() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/stats/example")
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <VuiBox display="flex" justifyContent="center" p={3}>
        <CircularProgress sx={{ color: '#0075ff' }} />
      </VuiBox>
    );
  }

  if (error) {
    return (
      <VuiBox p={3}>
        <VuiTypography color="error">Error: {error}</VuiTypography>
      </VuiBox>
    );
  }

  if (!data || data.length === 0) {
    return (
      <VuiBox p={3}>
        <VuiTypography color="text">No data available</VuiTypography>
      </VuiBox>
    );
  }

  const chartOptions = {
    ...visionUIChartTheme,
    labels: data.map(d => d.label),
  };

  const chartSeries = data.map(d => d.value);

  return (
    <VuiBox
      sx={{
        background: 'linear-gradient(127.09deg, rgba(6, 11, 40, 0.94) 19.41%, rgba(10, 14, 35, 0.49) 76.65%)',
        borderRadius: '15px',
        padding: '20px',
        boxShadow: '0 8px 26px rgba(0, 0, 0, 0.15)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
      }}
    >
      <VuiTypography variant="h6" color="white" mb={2}>
        Example Chart
      </VuiTypography>
      <Chart
        options={chartOptions}
        series={chartSeries}
        type="donut"
        height="300"
      />
    </VuiBox>
  );
}

export default ExampleChart;
```

---

## When You Get Stuck

1. **Check existing code first** - Look at `frontend/src/layouts/dashboard/index.js` for patterns
2. **Verify field names** - Re-check database schema in this doc
3. **Test the endpoint** - Use browser or Postman to verify JSON response
4. **Check the full plan** - Refer to `dashboardupgrade.md` for detailed specs
5. **Verify imports** - Make sure you're importing from correct paths

---

## Success Criteria

You'll know you're done when:
- ✅ All 11 new endpoints working
- ✅ Dashboard has 5+ new sections with charts
- ✅ All charts use Vision UI styling
- ✅ Loading/error/empty states all handled
- ✅ Responsive on mobile, tablet, desktop
- ✅ No console errors
- ✅ Matches the Vision UI design language perfectly

---

**Questions? Check `dashboardupgrade.md` for full details.**
