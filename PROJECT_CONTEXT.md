# BaseballBinder - AI Context File

**Last Updated:** 2025-11-04 (Evening)
**Purpose:** Quick reference for AI assistants working on this project

---

## Project Overview
BaseballBinder is a baseball card collection manager built with FastAPI + SQLite + vanilla HTML/CSS/JS.
Users can track their card collections, import checklists from CSV files, and check current eBay market prices using OAuth integration.

**Stack:**
- Backend: FastAPI (Python 3.14)
- Database: SQLite with SQLAlchemy ORM
- Frontend: Single-page application (vanilla HTML/CSS/JS)
- Build: PyInstaller for Windows executable distribution
- CI/CD: GitHub Actions for automated releases

---

## Current Status

### ✅ Completed Features
- Basic card CRUD operations (add, view, edit, delete)
- CSV checklist import from /checklists folder
- Auto-import checklists on startup
- Request form for missing checklists
- Animated homepage with statistics dashboard
- Manual set entry for cards not in checklists
- eBay OAuth Integration (Client Credentials Grant)
  - Browse API for price checking
  - Token caching (2-hour expiration)
  - Rate limiting (5,000 calls/day)
  - Production environment ready
- Pricing page with smart search
  - Search by player name with live suggestions
  - Track up to 20 cards
  - Individual and bulk price updates
  - Real-time updates across app
- Auto-update system
  - Version checking on startup
  - Professional update notification modal
  - One-click download from GitHub Releases
- Build system
  - PyInstaller configuration for Windows executable
  - GitHub Actions automated build and release
  - Launcher script with auto-browser open
- Ko-fi donation button integration
- Admin Analytics Dashboard
  - API call logging with comprehensive metrics
  - 1-hour search result caching
  - Real-time analytics UI with summary stats
  - Cache performance monitoring
  - Recent API calls table with full details

### 🚧 In Progress
- None

### 📋 Upcoming
- User authentication system
- Per-user rate limiting
- Price history tracking over time
- Advanced search and filtering
- Export collection to CSV/PDF
- Mobile-responsive improvements

---

## Key Architecture Decisions

### eBay API Integration
- **Authentication:** Client Credentials Grant (NOT Authorization Code)
- **Token Type:** Application Access Token (NOT User Access Token)
- **Endpoint:** Browse API `https://api.ebay.com/buy/browse/v1/item_summary/search`
- **Rate Limit:** 5,000 calls/day (Production keys)
- **Token Caching:** 2-hour cache with automatic refresh (7200 seconds minus 5-minute safety margin)
- **Environment:** Production (NOT Sandbox)
- **Libraries:** `ebaysdk==2.2.0`, `pyyaml==6.0.3`
- **Configuration:** Credentials stored in `ebay-config.yaml` (gitignored)

### OAuth Implementation Details
- Token expires at 7200 seconds (2 hours)
- Cached tokens stored in memory with expiration timestamp
- Automatic refresh when token expires or is within 5 minutes of expiration
- Base64-encoded Basic Auth header for token requests
- Scope: `https://api.ebay.com/oauth/api_scope`

### Rate Limiting Strategy
- Daily limit: 5,000 API calls
- Tracked in `ebay_oauth_requests.json` file
- Request counter resets daily (date-based)
- Shows warning at 60% usage (3,000 calls)
- Blocks requests at 100% usage (5,000 calls)
- Visual progress bar on Pricing page

### Database Schema
**Cards Table:**
- `id` (Primary Key)
- `set_name`, `card_number`, `player`, `team`, `year`
- `variety`, `parallel`, `autograph`, `numbered`, `graded`
- `price_paid`, `current_value`, `sold_price`
- `location`, `notes`, `quantity`
- `tracked_for_pricing` (Boolean) - Max 20 cards
- `last_price_check` (DateTime) - Last eBay price update
- `ebay_avg_price` (Float) - Cached average price from eBay
- `created_at`, `updated_at` (Timestamps)

**Checklists Table:**
- Auto-imported from `/checklists/*.csv`
- Contains all cards in a set for tracking completion percentage
- Fields: `set_name`, `year`, `card_number`, `player_name`, etc.

**ChecklistRequests Table:**
- User-submitted requests for missing checklists
- Fields: `set_name`, `year`, `manufacturer`, `priority`, `status`, `notes`
- Status: pending, processing, completed, rejected

**Suggestions Table:**
- User-submitted feedback and feature requests
- Fields: `category`, `title`, `description`, `email`, `status`
- Status: new, reviewing, planned, completed, rejected

**EbayApiCallLog Table:**
- Comprehensive logging of all eBay API calls
- Fields: `endpoint`, `search_query`, `card_id`, `request_timestamp`
- Response tracking: `response_status`, `response_time_ms`, `items_returned`
- Cache tracking: `cache_hit` (boolean), `success` (boolean)
- Error tracking: `error_message`, `ip_address`
- Indexes on: `endpoint`, `card_id`, `request_timestamp`, `cache_hit`, `success`

**EbaySearchCache Table:**
- 1-hour TTL cache for eBay search results
- Fields: `search_query` (unique), `result_data` (JSON string)
- Cache metadata: `created_at`, `expires_at`, `hit_count`
- Automatic expiry cleanup on cache checks
- Significantly reduces API usage for repeated searches

### Frontend Architecture
- Single-page application with page routing
- No framework - vanilla JavaScript
- CSS custom properties for theming
- Modals for complex interactions
- Real-time API calls with fetch()
- Toast notifications for user feedback

---

## File Structure
```
card-collection/
├── main.py                   # FastAPI app entry point
├── models.py                 # SQLAlchemy database models (includes caching/logging tables)
├── config.py                 # Environment variable management
├── rate_limiter.py           # eBay API rate limiting
├── ebay_api.py               # Legacy Finding API (being replaced)
├── ebay_service.py           # OAuth Browse API service with caching & logging
├── checklist_api.py          # Checklist endpoints
├── launcher.py               # Application launcher script
├── test_ebay.py              # eBay OAuth integration test
├── index.html                # Single-page frontend app with admin analytics
├── checklists/               # CSV files for auto-import
├── ebay-config.yaml          # eBay OAuth credentials (GITIGNORED)
├── ebay_rate_limit.json      # Rate limit tracking (GITIGNORED)
├── ebay_oauth_requests.json  # OAuth request tracking (GITIGNORED)
├── version.json              # App version for auto-updates
├── .env                      # Environment variables (GITIGNORED)
├── .github/workflows/
│   └── release.yml           # Automated build and release
├── BaseballBinder.spec       # PyInstaller build configuration
├── build.bat                 # Windows build script
├── BUILD.md                  # Build and release documentation
├── PROJECT_CONTEXT.md        # This file - AI memory/context
└── requirements.txt          # Python dependencies
```

---

## API Endpoints

### Cards
- `GET /cards/` - List all cards (with filtering)
- `POST /cards/` - Create new card
- `GET /cards/{id}` - Get single card
- `PUT /cards/{id}` - Update card
- `DELETE /cards/{id}` - Delete card
- `GET /cards/tracked/` - Get cards marked for price tracking
- `POST /cards/update-tracking` - Update tracked card list
- `GET /cards/{id}/price` - Get eBay OAuth price for card (NEW)
- `POST /cards/{id}/check-ebay-price` - Check eBay price (legacy Finding API)
- `POST /cards/check-tracked-prices` - Bulk price check for tracked cards

### Statistics
- `GET /stats/` - Dashboard statistics
- `GET /stats/fun` - Fun statistics (top players, most valuable, etc.)

### Checklists
- `GET /checklists/summary` - List all imported checklists
- `GET /checklists/{set_name}` - Get checklist details
- `POST /checklists/request` - Submit checklist request
- `GET /checklists/requests` - List all requests (admin)
- `PUT /checklists/requests/{id}` - Update request status

### eBay
- `GET /ebay/test-connection` - Test Finding API connection
- `GET /ebay/rate-limit-stats` - Get current rate limit stats
- `POST /ebay/reset-rate-limit` - Reset rate limit counter
- `GET /ebay/oauth/test-connection` - Test OAuth connection (NEW)

### Version/Updates
- `GET /version/current` - Get current app version
- `GET /version/check-update` - Check for updates

### Suggestions
- `POST /suggestions/` - Submit user suggestion
- `GET /suggestions/` - List suggestions (admin)
- `PUT /suggestions/{id}` - Update suggestion status

### Admin Analytics (NEW)
- `GET /admin/api-usage/summary` - Today's API usage summary
- `GET /admin/api-usage/recent?limit=100` - Recent API call logs
- `GET /admin/api-usage/trends?days=30` - Daily usage trends
- `GET /admin/cache/stats` - Cache statistics and performance

---

## Environment Variables (.env)
```
# Not currently used - app runs without .env file
# All configuration is in code or ebay-config.yaml
```

---

## eBay OAuth Credentials (SENSITIVE)

**Location:** `ebay-config.yaml` (NEVER commit to git)

**Format:**
```yaml
api.ebay.com:
  appid: YOUR_EBAY_APP_ID
  devid: YOUR_EBAY_DEV_ID
  certid: YOUR_EBAY_CERT_ID
  redirecturi: YOUR_REDIRECT_URI
```

**Rate Limits:**
- 5,000 calls/day (current Production limit)
- Tracked daily in `ebay_oauth_requests.json`
- Visual progress bar on Pricing page
- Warnings at 60% usage, blocks at 100%

---

## Development Notes

### When Adding New Features:
1. Implement the feature with proper error handling
2. Test thoroughly (run main.py and test in browser)
3. Update PROJECT_CONTEXT.md with what changed
4. Update "Last Updated" date at top
5. Move items from "In Progress" to "Completed" as appropriate
6. Commit changes with descriptive message

### Before Committing:
- ✅ Check `.gitignore` includes all sensitive files
  - `ebay-config.yaml`
  - `ebay_rate_limit.json`
  - `ebay_oauth_requests.json`
  - `.env`
  - `*.db`
- ✅ No hardcoded credentials anywhere
- ✅ PROJECT_CONTEXT.md is updated
- ✅ requirements.txt is current

### Testing:
- Run `python main.py` to start server
- Open browser to `http://localhost:8000`
- Test all CRUD operations
- Test eBay price checking (sparingly - uses API calls)
- Check browser console for JavaScript errors

### Building Windows Executable:
```bash
build.bat
# Output: releases/BaseballBinder-v{version}-{date}/BaseballBinder.exe
```

### Creating a Release:
1. Update `version.json` with new version and release notes
2. Commit changes: `git commit -m "Release vX.X.X - Description"`
3. Create tag: `git tag vX.X.X`
4. Push: `git push origin main && git push origin vX.X.X`
5. GitHub Actions automatically builds and creates release

---

## Recent Changes

### 2025-11-04 (Evening): Admin Analytics Dashboard & API Caching
- ✅ Added comprehensive API call logging system
  - Created `EbayApiCallLog` database table
  - Tracks all eBay API requests with full metrics
  - Records: endpoint, query, card_id, timestamp, response status, response time
  - Cache hit tracking to measure effectiveness
  - Error logging with detailed messages
  - Proper indexes on frequently queried fields
- ✅ Implemented 1-hour search result caching
  - Created `EbaySearchCache` database table
  - Automatic cache expiry with TTL (1 hour)
  - Hit counter tracks cache effectiveness
  - Significantly reduces API usage for repeated searches
  - Graceful degradation if database unavailable
- ✅ Enhanced `ebay_service.py` with caching & logging
  - `_get_cached_result()` - Check cache before API calls
  - `_cache_result()` - Store successful results for 1 hour
  - `_log_api_call()` - Log every API interaction
  - Automatic cache cleanup on expiry
  - All search operations now cache-aware
- ✅ Created 4 admin analytics endpoints
  - `/admin/api-usage/summary` - Today's usage stats
  - `/admin/api-usage/recent` - Recent API calls with details
  - `/admin/api-usage/trends` - Historical usage over N days
  - `/admin/cache/stats` - Cache performance metrics
- ✅ Built complete admin analytics UI
  - New "API Analytics" tab in admin panel
  - 6 summary stat cards (Total Calls, Cache Hits, Real Calls, Cache Rate, Remaining Limit, Avg Response Time)
  - 3 cache stat cards (Total/Active/Expired entries)
  - Recent API calls table with 7 columns
  - Real-time data loading via JavaScript
  - Professional grid layout with visual indicators
- ✅ Fixed datetime deprecation warnings (Python 3.14)
  - Changed from `datetime.utcnow()` to `datetime.now(timezone.utc)`
  - All timestamps now timezone-aware throughout codebase
- ✅ Updated pricing endpoint to pass card_id for logging
- ✅ Updated PROJECT_CONTEXT.md with all changes

### 2025-11-04: eBay OAuth Integration & Pricing Page Redesign
- ✅ Implemented eBay OAuth service using Client Credentials Grant flow
- ✅ Created `ebay_service.py` with Browse API integration
- ✅ Added token caching (2-hour expiration with auto-refresh)
- ✅ Implemented conservative rate limiting (5,000 calls/day)
- ✅ Added `GET /cards/{id}/price` endpoint for OAuth pricing
- ✅ Created `ebay-config.yaml` for credential management
- ✅ Added `test_ebay.py` for OAuth testing (successfully tested)
- ✅ Installed `ebaysdk==2.2.0` and `pyyaml==6.0.3`
- ✅ Complete redesign of Pricing page UI/UX
  - Smart search with player name suggestions (no more full card list)
  - Display tracked cards directly on page (max 20)
  - Individual "Update Value" button per card
  - "Remove from Tracking" button per card
  - "Update All Values" bulk action button
  - Real-time updates across entire app
  - Clean, professional card display with pricing info
  - Instant add/remove from tracking (no "Save" button needed)
- ✅ Added Ko-fi donation button to header
- ✅ Fixed GitHub Actions workflow (replaced deprecated actions)

### 2025-01-10: Initial v0.3.0 Release
- eBay API Integration for price checking (Finding API)
- Auto-Update System with professional notifications
- Manual Set Entry for cards not in checklists
- Build system for Windows executable distribution
- Rate limiting and API management
- Improved dashboard and statistics

### 2025-01-08: Dashboard Stats Loading Fix
- Fixed dashboard stats not loading on initial page load
- Proper datetime handling (timezone-aware)

### 2025-01-07: Initial Release v0.2.0
- Basic card collection management
- CSV checklist import
- Request system for missing checklists
- User suggestions/feedback system
- Admin panel

---

## Known Issues / Technical Debt

1. **Legacy eBay Finding API**
   - Still present in `ebay_api.py`
   - Being replaced by OAuth Browse API in `ebay_service.py`
   - Can be removed once all features migrated

2. **No User Authentication**
   - Single-user application currently
   - All data shared across users
   - Rate limiting is global, not per-user

3. **Token Storage**
   - Tokens cached in memory only
   - Lost on server restart
   - Not a major issue (tokens refresh automatically)

4. **No Price History Tracking**
   - Cards track only last_price_check and current ebay_avg_price
   - No historical price data stored
   - Can't show price trends over time

---

## Dependencies (requirements.txt)
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy==2.0.35
pydantic==2.9.2
python-multipart==0.0.12
requests==2.32.3
python-dotenv==1.0.0
pyinstaller==6.3.0
ebaysdk==2.2.0
pyyaml==6.0.3
```

---

**END OF CONTEXT FILE**

*This file should be updated whenever significant changes are made to the project.*
*Always update "Last Updated" date and add entries to "Recent Changes" section.*
