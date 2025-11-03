# eBay API Integration Plan for BaseballBinder

## 🚨 Critical Update: API Deprecation

**The eBay Finding API is being DEPRECATED and will be decommissioned on February 5, 2025.**

eBay is migrating to newer RESTful APIs. We need to use the **Browse API** instead.

---

## 📋 Recommended API Strategy

### **1. Primary API: Browse API (Recommended)**

The Browse API is eBay's modern RESTful API that replaces the Finding API.

**Key Endpoints:**
- `search` - Search for active listings
- `searchByImage` - Search using images (useful for card identification)
- `getItem` - Get details for a specific listing
- `getItemByLegacyId` - Get item using old eBay item ID

**Advantages:**
- Modern RESTful architecture
- Better performance
- Will be supported long-term
- JSON responses (easier to parse)

**Limitations:**
- ❌ **Cannot access sold/completed listings** (major limitation)
- Only shows active listings

---

### **2. Secondary Option: Marketplace Insights API**

**This is what we actually need for sold prices, BUT:**

⚠️ **MAJOR RESTRICTION:** This API is only available to:
- Select developers approved by eBay business units
- eBay Partner Network members
- High-volume enterprise applications (like Terapeak)

**Not available to regular developers without special approval.**

---

## 🔍 Which eBay API Endpoints to Use

### **Option A: Browse API (For Active Listings Only)**

```
Base URL: https://api.ebay.com/buy/browse/v1

GET /item_summary/search
```

**Query Parameters:**
- `q` - Search query (e.g., "2023 Topps Chrome Mike Trout")
- `category_ids` - Sports Cards category (212)
- `filter` - Price ranges, conditions, etc.
- `sort` - Price, end time, etc.
- `limit` - Results per page (max 200)

**Example Search:**
```
GET /item_summary/search?q=2023+Topps+Chrome+Mike+Trout&category_ids=212&limit=50
```

---

### **Option B: Finding API (Deprecated - Use Until Feb 2025)**

**Available Endpoints:**

1. **findCompletedItems** - Get completed/sold listings ✅
   - Limited to last 90 days
   - **5,000 call limit per day**
   - Returns sold prices

2. **findItemsAdvanced** - Search active listings
   - More filtering options
   - Good for current market prices

3. **findItemsByKeywords** - Basic search
   - Simpler than advanced

**Example Query (findCompletedItems):**
```xml
POST https://svcs.ebay.com/services/search/FindingService/v1

<findCompletedItems>
  <keywords>2023 Topps Chrome Mike Trout PSA 10</keywords>
  <categoryId>212</categoryId>
  <sortOrder>EndTimeSoonest</sortOrder>
  <itemFilter>
    <name>SoldItemsOnly</name>
    <value>true</value>
  </itemFilter>
</findCompletedItems>
```

---

## 🎯 How to Search for Cards

### **Search Strategy for Sports Cards:**

Build search queries using:
1. **Year** - "2023"
2. **Manufacturer** - "Topps", "Panini", "Bowman"
3. **Set Name** - "Chrome", "Heritage", "Stadium Club"
4. **Player Name** - "Mike Trout", "Shohei Ohtani"
5. **Card Number** - "#150"
6. **Variety** - "Refractor", "Base", "Auto"
7. **Parallel** - "Red /5", "Blue /150"
8. **Grading** - "PSA 10", "BGS 9.5"

**Example Search Strings:**
```
"2023 Topps Chrome Mike Trout Refractor PSA 10"
"2022 Bowman Chrome Julio Rodriguez Auto"
"2021 Topps Heritage #150 Ronald Acuna"
```

**Category IDs:**
- Sports Cards: `212`
- Baseball: `213`
- Baseball Trading Cards: `212`

---

## 💰 How to Get Recent Sold Prices

### **Method 1: Finding API (Until Feb 2025)**

Use `findCompletedItems` with filters:

```javascript
const params = {
  'OPERATION-NAME': 'findCompletedItems',
  'keywords': '2023 Topps Chrome Mike Trout',
  'categoryId': '212',
  'itemFilter(0).name': 'SoldItemsOnly',
  'itemFilter(0).value': 'true',
  'itemFilter(1).name': 'ConditionFrom',
  'itemFilter(1).value': 'New',
  'sortOrder': 'EndTimeSoonest',
  'paginationInput.entriesPerPage': '100'
}
```

**Returns:**
- Sale price
- Sale date
- Listing title
- Item condition
- Shipping cost

---

### **Method 2: Alternative Solutions (Recommended)**

Since eBay restricts sold data access, consider:

1. **Web Scraping (with caution)**
   - Scrape eBay's "Sold Items" search results
   - Use tools like Puppeteer/Playwright
   - ⚠️ Against eBay's Terms of Service
   - ⚠️ IP may get blocked

2. **Third-Party Price APIs**
   - **130point.com** - Tracks eBay sold prices
   - **Terapeak** - eBay's official research tool (paid)
   - **CardLadder** - Sports card price tracking
   - **PWCC** - Auction house with price data
   - **Beckett** - Traditional price guides

3. **Manual Database**
   - Users enter their own sale prices
   - Community-sourced pricing
   - More sustainable long-term

---

## 🔐 Authentication Requirements

### **Browse API (OAuth 2.0)**

**Required Credentials:**
1. **Client ID** (App ID)
2. **Client Secret** (Cert ID)
3. **OAuth Token**

**Authentication Flow:**

1. **Get Application Token:**
```
POST https://api.ebay.com/identity/v1/oauth2/token

Headers:
  Content-Type: application/x-www-form-urlencoded
  Authorization: Basic <base64(client_id:client_secret)>

Body:
  grant_type=client_credentials
  scope=https://api.ebay.com/oauth/api_scope
```

2. **Use Token in API Calls:**
```
GET https://api.ebay.com/buy/browse/v1/item_summary/search

Headers:
  Authorization: Bearer <access_token>
```

**Token Expiry:** 7200 seconds (2 hours)

---

### **Finding API (Legacy Auth)**

**Required Credentials:**
1. **App ID** (Application Key)
2. **Dev ID** (Developer ID)
3. **Cert ID** (Certificate ID)

**Simple Header Authentication:**
```
X-EBAY-SOA-SECURITY-APPNAME: <Your App ID>
X-EBAY-SOA-OPERATION-NAME: findCompletedItems
X-EBAY-SOA-SERVICE-VERSION: 1.0.0
X-EBAY-SOA-GLOBAL-ID: EBAY-US
```

**No OAuth required** - simpler to implement!

---

## ⏱️ Rate Limits and Best Practices

### **Rate Limits:**

| API | Daily Limit | Short-term Limit |
|-----|-------------|------------------|
| Finding API | 5,000 calls/day | - |
| Browse API | 5,000 calls/day | Varies by method |
| OAuth Token | - | 25 requests/5 min |

**Application Growth Check:**
- Default: 5,000 calls/day
- After approval: Up to 50,000+ calls/day

---

### **Best Practices:**

1. **Caching Strategy**
   ```python
   # Cache search results for 1 hour
   cache_duration = 3600  # seconds

   # Store in database:
   # - Search query
   # - Results JSON
   # - Timestamp
   # - Expiry time
   ```

2. **Rate Limiting**
   ```python
   import time
   from datetime import datetime, timedelta

   class RateLimiter:
       def __init__(self, max_calls=5000, time_window=86400):
           self.max_calls = max_calls
           self.calls = []

       def allow_request(self):
           now = datetime.now()
           # Remove calls older than time window
           self.calls = [t for t in self.calls
                        if now - t < timedelta(seconds=86400)]

           if len(self.calls) < self.max_calls:
               self.calls.append(now)
               return True
           return False
   ```

3. **Batch Similar Requests**
   - Group searches for same player/set
   - Reduce redundant API calls

4. **Use Filters Effectively**
   - Narrow searches to reduce result size
   - Use category IDs to limit scope

5. **Error Handling**
   ```python
   try:
       response = api_call()
   except RateLimitError:
       # Wait and retry
       time.sleep(60)
   except AuthenticationError:
       # Refresh token
       refresh_oauth_token()
   except ConnectionError:
       # Retry with exponential backoff
       retry_with_backoff()
   ```

6. **Monitor Usage**
   ```python
   # Track API calls in database
   log_api_call(
       endpoint='findCompletedItems',
       timestamp=datetime.now(),
       status='success',
       response_time=0.5
   )
   ```

---

## 🎯 Recommended Implementation for BaseballBinder

### **Phase 1: Use Finding API (Short-term)**
- Implement `findCompletedItems` for sold prices
- Use until February 2025
- 5,000 calls/day should be sufficient for small app

### **Phase 2: Migrate to Browse API (Active Listings)**
- Implement Browse API for current market prices
- Use for "estimated value" feature
- More reliable long-term

### **Phase 3: Alternative Price Data**
- Partner with third-party price API
- Build manual price database
- Community-sourced pricing
- Web scraping (last resort, risky)

### **Phase 4: Premium Features**
- Apply for eBay Partner Network
- Get Marketplace Insights API access
- Requires proven track record + traffic

---

## 📝 Implementation Checklist

- [ ] Register eBay Developer Account
- [ ] Create App to get credentials (App ID, Dev ID, Cert ID)
- [ ] Test Finding API with `findCompletedItems`
- [ ] Implement OAuth 2.0 for Browse API
- [ ] Build rate limiting system
- [ ] Add caching layer (Redis or database)
- [ ] Create error handling and retry logic
- [ ] Set up API call logging/monitoring
- [ ] Build fallback to third-party APIs
- [ ] Plan migration from Finding API before Feb 2025

---

## 🔗 Useful Resources

- **eBay Developer Portal:** https://developer.ebay.com/
- **Browse API Docs:** https://developer.ebay.com/api-docs/buy/browse/overview.html
- **Finding API Docs:** https://developer.ebay.com/devzone/finding/concepts/FindingAPIGuide.html
- **OAuth Guide:** https://developer.ebay.com/api-docs/static/oauth-guide.html
- **Rate Limits:** https://developer.ebay.com/develop/get-started/api-call-limits
- **Sandbox Testing:** https://developer.ebay.com/sandbox

---

## ⚠️ Important Notes

1. **Finding API Deprecation:** Must migrate by Feb 5, 2025
2. **Sold Data Access:** Very limited - requires special approval
3. **Rate Limits:** Start at 5,000/day - plan accordingly
4. **Caching:** Essential to stay within limits
5. **Alternative Sources:** Consider third-party APIs for pricing
6. **Terms of Service:** Don't scrape eBay directly
7. **User Experience:** Set expectations - "estimated values" not "exact prices"

---

**Last Updated:** November 2024
**Status:** Research Complete - Ready for Implementation
