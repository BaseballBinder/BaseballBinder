"""
eBay OAuth service using Client Credentials Grant flow.
Uses eBay Browse API for searching baseball card listings.
Includes 1-hour result caching and API call logging.
"""
import time
import json
import logging
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta, timezone
import requests
import base64
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database models for caching and logging
try:
    from models import SessionLocal, EbaySearchCache, EbayApiCallLog
    DB_AVAILABLE = True
except ImportError:
    logger.warning("Database models not available - caching and logging disabled")
    DB_AVAILABLE = False


class eBayOAuthError(Exception):
    """Custom exception for eBay OAuth errors"""
    pass


class eBayService:
    """
    eBay OAuth service client using Client Credentials Grant flow.
    Implements Application Access Token for read-only public data searches.
    """

    # eBay Production endpoints
    AUTH_ENDPOINT = "https://api.ebay.com/identity/v1/oauth2/token"
    BROWSE_API_ENDPOINT = "https://api.ebay.com/buy/browse/v1"

    # Token cache
    _token_cache = {
        'access_token': None,
        'expires_at': None
    }

    def __init__(self):
        """Initialize eBay OAuth service with credentials from config file"""
        try:
            self._load_credentials()
            logger.info("eBay OAuth service initialized (Production environment)")
        except Exception as e:
            logger.error(f"Failed to initialize eBay OAuth service: {e}")
            raise eBayOAuthError(f"Configuration error: {e}")

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        self.daily_limit = 5000
        self.request_count_file = Path("ebay_oauth_requests.json")

    INSERT_SYNONYMS = {
        "t-minus": ["T-Minus", "T-Minus 3 2 1", "T-Minus 3...2...1!", "T Minus 3 2 1"]
    }

    def _load_credentials(self):
        """Load eBay OAuth credentials from ebay-config.yaml"""
        try:
            import yaml
            config_path = Path("ebay-config.yaml")

            if not config_path.exists():
                raise FileNotFoundError("ebay-config.yaml not found")

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            ebay_config = config.get('api.ebay.com', {})
            self.app_id = ebay_config.get('appid')
            self.dev_id = ebay_config.get('devid')
            self.cert_id = ebay_config.get('certid')
            self.redirect_uri = ebay_config.get('redirecturi')

            if not all([self.app_id, self.cert_id]):
                raise ValueError("Missing required credentials in ebay-config.yaml")

        except ImportError:
            raise ImportError("PyYAML is required. Install with: pip install pyyaml")
        except Exception as e:
            raise ValueError(f"Error loading credentials: {e}")

    # =========================================================================
    # REMOVED DUPLICATE FUNCTION DEFINITIONS (previously lines 95-127)
    # These functions (_unique_terms, _build_brand_terms, _build_variety_terms)
    # are properly defined below starting around line 164
    # =========================================================================

    def _filter_items(self, items: List[Dict], card_number: Optional[str]) -> List[Dict]:
        if not items:
            return []
        filtered = []
        needle = (card_number or "").lower().replace("#", "")
        for item in items:
            title = (item.get("title") or "").lower()
            if any(term in title for term in ["pick your", "choose", "lot", "player list"]):
                if needle and needle not in title.replace("#", ""):
                    continue
            filtered.append(item)
        return filtered

    def _build_query_variants(self, base_terms: List[str], variety_terms: List[str], number_terms: List[str]) -> List[str]:
        variants = []
        combinations = [
            (True, True),
            (False, True),
            (False, False),
        ]
        for include_number, include_variety in combinations:
            terms = list(base_terms)
            if include_variety:
                terms.extend(variety_terms)
            if include_number:
                terms.extend(number_terms)
            variants.append(" ".join(self._unique_terms(terms)))
        unique_variants = []
        seen = set()
        for q in variants:
            if q and q not in seen:
                seen.add(q)
                unique_variants.append(q)
        return unique_variants

    def _unique_terms(self, terms: List[str]) -> List[str]:
        seen = set()
        ordered = []
        for term in terms:
            if term and term not in seen:
                seen.add(term)
                ordered.append(term)
        return ordered

    def _build_brand_terms(self, brand: Optional[str]) -> List[str]:
        """
        Build search term variations for card brands.
        Only adds 'Panini' prefix to actual Panini-manufactured brands.

        CRITICAL FIX: Previously added "Panini" to ALL non-Panini brands (Topps, Upper Deck, etc.)
        causing searches to match wrong manufacturers and incorrect pricing.
        """
        if not brand:
            return []
        terms = {brand}
        lower = brand.lower()

        # List of brands manufactured by Panini America
        PANINI_BRANDS = [
            "donruss", "prizm", "select", "chronicles", "optic",
            "prestige", "contenders", "mosaic", "absolute", "crown royale",
            "national treasures", "immaculate", "flawless", "noir",
            "encased", "limited", "spectra", "phoenix"
        ]

        # Only add Panini prefix to actual Panini brands
        is_panini_brand = any(pb in lower for pb in PANINI_BRANDS)
        if is_panini_brand and "panini" not in lower:
            terms.add(f"Panini {brand}")

        # Special case handling for brands with multiple naming conventions
        if "donruss optic" in lower:
            terms.add("Panini Donruss Optic")
            terms.add("Donruss Optic")
        if "topps chrome" in lower:
            terms.add("Topps Chrome")

        return list(terms)

    def _build_variety_terms(self, variety: Optional[str]) -> List[str]:
        if not variety:
            return []
        terms = {variety}
        lower = variety.lower()
        for key, synonyms in self.INSERT_SYNONYMS.items():
            if key in lower:
                terms.update(synonyms)
        return list(terms)

    def _score_result_relevance(self, item: Dict, year: str, brand: str,
                                player_name: str, card_number: Optional[str]) -> float:
        """
        Score how well a search result matches the input criteria.
        Returns 0.0 (no match) to 1.0 (perfect match).

        CRITICAL FIX: Previously no validation - accepted any result from eBay.
        This caused wrong players, wrong years, wrong brands to be included in pricing.

        Scoring breakdown:
        - Player name (40%): REQUIRED - reject if not found
        - Year (20%): REQUIRED - reject if not found
        - Brand (20%): REQUIRED - reject if not found
        - Card number (20%): OPTIONAL - bonus if found
        """
        title = item.get('title', '').lower()
        score = 0.0

        # Player name validation (40% weight) - REQUIRED
        player_lower = player_name.lower()
        if player_lower in title:
            score += 0.4
        else:
            # Check last name only as fallback
            last_name = player_lower.split()[-1] if player_lower else ""
            if last_name and last_name in title:
                score += 0.2  # Partial credit for last name match
            else:
                # Player not found = reject this result
                return 0.0

        # Year validation (20% weight) - REQUIRED
        if year and year in title:
            score += 0.2
        elif year:
            # Year required but missing = reject
            return 0.0
        else:
            # No year specified = automatic credit
            score += 0.2

        # Brand validation (20% weight) - REQUIRED
        brand_lower = brand.lower() if brand else ""
        if brand_lower and brand_lower in title:
            score += 0.2
        elif brand_lower:
            # Brand required but missing = reject
            return 0.0
        else:
            # No brand specified = automatic credit
            score += 0.2

        # Card number validation (20% weight) - OPTIONAL bonus
        if card_number:
            # Check multiple number formats
            if (card_number in title or
                f"#{card_number}" in title or
                f"no. {card_number}" in title or
                f"card {card_number}" in title):
                score += 0.2
            # Don't penalize if number not found - it's optional
        else:
            # No card number specified = automatic credit
            score += 0.2

        return score

    def _filter_by_relevance(self, items: List[Dict], year: str, brand: str,
                            player_name: str, card_number: Optional[str],
                            min_score: float = 0.6) -> List[Dict]:
        """
        Filter eBay search results by relevance score.
        Only keeps results that match the search criteria.

        Args:
            items: Raw eBay search results
            year: Expected card year
            brand: Expected card brand
            player_name: Expected player name
            card_number: Expected card number (optional)
            min_score: Minimum relevance score to keep (0.0-1.0)

        Returns:
            Filtered list of items, sorted by relevance score (highest first)
        """
        scored_items = []

        for item in items:
            score = self._score_result_relevance(item, year, brand, player_name, card_number)

            if score >= min_score:
                item['_relevance_score'] = score
                scored_items.append(item)
            else:
                logger.debug(f"Rejected low-relevance result (score {score:.2f}): {item.get('title', '')[:80]}")

        # Sort by relevance score descending (best matches first)
        scored_items.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)

        logger.info(f"Relevance filtering: kept {len(scored_items)}/{len(items)} results (min_score={min_score})")

        return scored_items

    def _get_request_count(self) -> int:
        """Get today's request count"""
        try:
            if self.request_count_file.exists():
                with open(self.request_count_file, 'r') as f:
                    data = json.load(f)
                    date_str = datetime.now().strftime('%Y-%m-%d')
                    if data.get('date') == date_str:
                        return data.get('count', 0)
            return 0
        except Exception as e:
            logger.error(f"Error reading request count: {e}")
            return 0

    def _increment_request_count(self):
        """Increment today's request count"""
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            count = self._get_request_count() + 1

            with open(self.request_count_file, 'w') as f:
                json.dump({'date': date_str, 'count': count}, f)

        except Exception as e:
            logger.error(f"Error incrementing request count: {e}")

    def _can_make_request(self) -> tuple[bool, str]:
        """Check if we can make a request within rate limits"""
        count = self._get_request_count()

        if count >= self.daily_limit:
            return False, f"Daily rate limit reached ({self.daily_limit} calls/day)"

        if count >= self.daily_limit * 0.9:
            return True, f"Warning: Approaching daily limit ({count}/{self.daily_limit})"

        return True, f"OK ({count}/{self.daily_limit} calls today)"

    def _wait_for_rate_limit(self):
        """Ensure we respect rate limits by waiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _get_cached_result(self, query: str) -> Optional[Dict]:
        """
        Check if we have a cached result for this query.
        Returns cached data if found and not expired, None otherwise.
        """
        if not DB_AVAILABLE:
            return None

        try:
            db = SessionLocal()
            cache_entry = db.query(EbaySearchCache).filter(
                EbaySearchCache.search_query == query
            ).first()

            if cache_entry:
                # Check if expired
                now = datetime.now(timezone.utc)
                # Make expires_at timezone-aware if it isn't already
                expires_at = cache_entry.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if expires_at > now:
                    # Cache hit - increment counter
                    cache_entry.hit_count += 1
                    db.commit()
                    db.close()

                    logger.info(f"Cache HIT for query: {query}")
                    return json.loads(cache_entry.result_data)
                else:
                    # Expired - delete it
                    logger.info(f"Cache EXPIRED for query: {query}")
                    db.delete(cache_entry)
                    db.commit()
                    db.close()

            db.close()
            logger.info(f"Cache MISS for query: {query}")
            return None

        except Exception as e:
            logger.error(f"Error checking cache: {e}")
            return None

    def _cache_result(self, query: str, result: Dict):
        """Cache a search result for 1 hour"""
        if not DB_AVAILABLE:
            return

        try:
            db = SessionLocal()

            # Delete any existing cache for this query
            db.query(EbaySearchCache).filter(
                EbaySearchCache.search_query == query
            ).delete()

            # Create new cache entry
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=1)

            cache_entry = EbaySearchCache(
                search_query=query,
                result_data=json.dumps(result),
                created_at=now,
                expires_at=expires_at,
                hit_count=0
            )

            db.add(cache_entry)
            db.commit()
            db.close()

            logger.info(f"Cached result for query: {query} (expires: {expires_at.isoformat()})")

        except Exception as e:
            logger.error(f"Error caching result: {e}")

    def _log_api_call(self, endpoint: str, query: str, card_id: Optional[int],
                     response_status: int, response_time_ms: int,
                     items_returned: int, cache_hit: bool, success: bool,
                     error_message: Optional[str] = None):
        """Log an API call to the database"""
        if not DB_AVAILABLE:
            return

        try:
            db = SessionLocal()

            log_entry = EbayApiCallLog(
                endpoint=endpoint,
                search_query=query,
                card_id=card_id,
                response_status=response_status,
                response_time_ms=response_time_ms,
                items_returned=items_returned,
                cache_hit=cache_hit,
                success=success,
                error_message=error_message
            )

            db.add(log_entry)
            db.commit()
            db.close()

            logger.debug(f"Logged API call: {endpoint} - {query}")

        except Exception as e:
            logger.error(f"Error logging API call: {e}")

    def _get_access_token(self) -> str:
        """
        Get Application Access Token using Client Credentials Grant flow.
        Tokens are cached for 2 hours (7200 seconds).

        Returns:
            str: Access token

        Raises:
            eBayOAuthError: If token request fails
        """
        # Check if we have a valid cached token
        if self._token_cache['access_token'] and self._token_cache['expires_at']:
            if datetime.now() < self._token_cache['expires_at']:
                logger.debug("Using cached access token")
                return self._token_cache['access_token']

        logger.info("Requesting new Application Access Token")

        # Create Basic Auth header (Base64 encoded client_id:client_secret)
        credentials = f"{self.app_id}:{self.cert_id}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_credentials}'
        }

        data = {
            'grant_type': 'client_credentials',
            'scope': 'https://api.ebay.com/oauth/api_scope'
        }

        try:
            response = requests.post(
                self.AUTH_ENDPOINT,
                headers=headers,
                data=data,
                timeout=10
            )

            if response.status_code == 429:
                raise eBayOAuthError("Rate limit exceeded (HTTP 429)")

            response.raise_for_status()

            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 7200)  # Default 2 hours

            if not access_token:
                raise eBayOAuthError("No access token in response")

            # Cache the token (subtract 5 minutes for safety)
            expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            self._token_cache['access_token'] = access_token
            self._token_cache['expires_at'] = expires_at

            logger.info(f"New access token obtained, expires at {expires_at.isoformat()}")
            return access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Token request failed: {e}")
            raise eBayOAuthError(f"Failed to get access token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during token request: {e}")
            raise eBayOAuthError(f"Token request error: {e}")

    def search_card(self, year: str, brand: str, player_name: str,
                   card_number: Optional[str] = None,
                   variety: Optional[str] = None,
                   parallel: Optional[str] = None,
                   autograph: bool = False,
                   graded: Optional[str] = None,
                   numbered: Optional[str] = None,
                   card_id: Optional[int] = None,
                   manual_query: Optional[str] = None,
                   _is_broadening: bool = False) -> Dict:
        """
        Search for baseball cards using eBay Browse API with caching.

        Args:
            year: Card year (e.g., "1993")
            brand: Card brand/manufacturer (e.g., "Topps")
            player_name: Player name (e.g., "Derek Jeter")
            card_number: Optional card number (e.g., "98")
            variety: Optional card variety (e.g., "All-Star", "Rookie Card")
            parallel: Optional parallel version (e.g., "Refractor", "Chrome")
            autograph: Whether card is autographed
            graded: Optional grading info (e.g., "PSA 10", "BGS 9.5")
            numbered: Optional serial numbering (e.g., "/99", "/25")
            card_id: Optional card ID for logging purposes
            manual_query: Optional manual search query override
            _is_broadening: Internal flag to prevent recursive broadening

        Returns:
            dict: Search results with pricing information

        Raises:
            eBayOAuthError: If search fails
        """
        if manual_query:
            query = manual_query.strip()
        else:
            # Build comprehensive search query
            query_parts = [year, player_name]
            query_parts.extend(self._build_brand_terms(brand))
            if card_number:
                query_parts.append(f"#{card_number}")
                # Removed duplicate card_number append - single #number format is sufficient
            if variety:
                query_parts.extend(self._build_variety_terms(variety))
            if parallel:
                query_parts.append(parallel)
            if autograph:
                query_parts.append("autograph")
            if graded:
                query_parts.append(graded)

            # Extract print run from numbered (e.g., "05/49" -> "/49")
            print_run = None
            if numbered:
                match = re.search(r'/(\d+)$', numbered)
                if match:
                    print_run = f"/{match.group(1)}"
                    query_parts.append(print_run)
                else:
                    query_parts.append(numbered)

            query = " ".join(self._unique_terms(query_parts))
        start_time = time.time()

        logger.info(f"Searching eBay for: {query}")

        # Check cache first
        cached_result = self._get_cached_result(query)
        if cached_result:
            # Log cache hit
            self._log_api_call(
                endpoint="browse/item_summary/search",
                query=query,
                card_id=card_id,
                response_status=200,
                response_time_ms=int((time.time() - start_time) * 1000),
                items_returned=cached_result.get('total_results', 0),
                cache_hit=True,
                success=True
            )
            return cached_result

        # Check rate limits
        can_request, message = self._can_make_request()
        if not can_request:
            # Log failed attempt
            self._log_api_call(
                endpoint="browse/item_summary/search",
                query=query,
                card_id=card_id,
                response_status=429,
                response_time_ms=0,
                items_returned=0,
                cache_hit=False,
                success=False,
                error_message=message
            )
            raise eBayOAuthError(message)

        if "Warning" in message:
            logger.warning(message)

        # Get access token
        access_token = self._get_access_token()

        # Wait for rate limiting
        self._wait_for_rate_limit()

        # Make Browse API request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US',
            'X-EBAY-C-ENDUSERCTX': 'affiliateCampaignId=<ePNCampaignId>,affiliateReferenceId=<referenceId>'
        }

        params = {
            'q': query,
            'category_ids': '261328',  # Baseball Cards category
            'limit': 100,
            'filter': 'buyingOptions:{FIXED_PRICE},itemLocationCountry:US',
            'sort': 'price'
        }

        try:
            response = requests.get(
                f"{self.BROWSE_API_ENDPOINT}/item_summary/search",
                headers=headers,
                params=params,
                timeout=10
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            # Increment request counter
            self._increment_request_count()

            if response.status_code == 429:
                self._log_api_call(
                    endpoint="browse/item_summary/search",
                    query=query,
                    card_id=card_id,
                    response_status=429,
                    response_time_ms=response_time_ms,
                    items_returned=0,
                    cache_hit=False,
                    success=False,
                    error_message="Rate limit exceeded"
                )
                raise eBayOAuthError("Rate limit exceeded (HTTP 429)")

            response.raise_for_status()

            data = response.json()

            # Parse results
            items = data.get('itemSummaries', [])
            total = data.get('total', 0)

            # CRITICAL FIX: Filter results by relevance before processing
            # Rejects results that don't match player, year, or brand
            if items:
                original_count = len(items)
                items = self._filter_by_relevance(
                    items, year, brand, player_name, card_number, min_score=0.6
                )
                if len(items) < original_count:
                    logger.info(f"Relevance filter reduced results: {original_count} → {len(items)}")

            if not items:
                logger.info(f"No results found for: {query}")

                # Progressive search broadening: try broader searches if no results
                # CRITICAL FIX: Stop before removing card number to prevent matching wrong cards
                # Only broaden if this is not already a broadened search (prevent recursion)
                if not _is_broadening:
                    broader_result = None

                    # Strategy 1: Remove print run specification (most restrictive)
                    if numbered and not broader_result:
                        logger.info(f"Retrying without print run specification: {numbered}")
                        broader_result = self.search_card(
                            year=year, brand=brand, player_name=player_name,
                            card_number=card_number, variety=variety, parallel=parallel,
                            autograph=autograph, graded=graded, numbered=None, card_id=card_id,
                            _is_broadening=True
                        )
                        if broader_result.get('total_results', 0) > 0:
                            broader_result['search_query'] += f" (broadened: removed print run)"
                            return broader_result

                    # Strategy 2: Remove variety and parallel (keep card number!)
                    if (variety or parallel) and not broader_result:
                        logger.info(f"Retrying without variety/parallel specifications")
                        broader_result = self.search_card(
                            year=year, brand=brand, player_name=player_name,
                            card_number=card_number,  # KEEP CARD NUMBER
                            variety=None, parallel=None,
                            autograph=autograph, graded=graded, numbered=None, card_id=card_id,
                            _is_broadening=True
                        )
                        if broader_result.get('total_results', 0) > 0:
                            broader_result['search_query'] += f" (broadened: removed variety/parallel)"
                            return broader_result

                    # Strategy 3 REMOVED: Previously removed card number (too broad!)
                    # This was matching completely wrong cards and causing pricing errors.
                    # Example: Search for "#98 Refractor /500" would match ANY card from that player/year
                    # Better to return NO results than WRONG results.

                # No results even with broadening - return empty result
                logger.warning(f"No results found after progressive broadening for: {query}")
                result = {
                    'search_query': query,
                    'total_results': 0,
                    'items': [],
                    'pricing': {
                        'avg_price': None,
                        'median_price': None,
                        'min_price': None,
                        'max_price': None,
                        'count': 0
                    },
                    'sample_images': []
                }

                # Log API call
                self._log_api_call(
                    endpoint="browse/item_summary/search",
                    query=query,
                    card_id=card_id,
                    response_status=response.status_code,
                    response_time_ms=response_time_ms,
                    items_returned=0,
                    cache_hit=False,
                    success=True
                )

                return result

            # Extract pricing information
            pricing = self._calculate_pricing(items)

            # Extract sample images from first 3 items
            sample_images = []
            for item in items[:3]:
                image_obj = item.get('image', {})
                image_url = image_obj.get('imageUrl')
                if image_url:
                    sample_images.append(image_url)

            result = {
                'search_query': query,
                'total_results': total,
                'items': items[:10],  # Return first 10 items
                'pricing': pricing,
                'sample_images': sample_images  # Add sample images for visual verification
            }

            # Cache the result
            self._cache_result(query, result)

            # Log API call
            self._log_api_call(
                endpoint="browse/item_summary/search",
                query=query,
                card_id=card_id,
                response_status=response.status_code,
                response_time_ms=response_time_ms,
                items_returned=total,
                cache_hit=False,
                success=True
            )

            logger.info(f"Found {total} results, avg price: ${pricing['avg_price']:.2f}")
            return result

        except requests.exceptions.RequestException as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            self._log_api_call(
                endpoint="browse/item_summary/search",
                query=query,
                card_id=card_id,
                response_status=0,
                response_time_ms=response_time_ms,
                items_returned=0,
                cache_hit=False,
                success=False,
                error_message=str(e)
            )
            logger.error(f"Browse API request failed: {e}")
            raise eBayOAuthError(f"Search failed: {e}")
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            self._log_api_call(
                endpoint="browse/item_summary/search",
                query=query,
                card_id=card_id,
                response_status=0,
                response_time_ms=response_time_ms,
                items_returned=0,
                cache_hit=False,
                success=False,
                error_message=str(e)
            )
            logger.error(f"Unexpected error during search: {e}")
            raise eBayOAuthError(f"Search error: {e}")

    def _calculate_pricing(self, items: List[Dict]) -> Dict:
        """
        Calculate pricing statistics from search results using IQR method.

        CRITICAL FIX: Previously used first 20 results which were the cheapest 20
        (eBay sorts by price ascending). This severely undervalued cards.

        Now uses interquartile range (IQR) method:
        - Removes bottom 25% (damaged/mispriced/fake cards)
        - Removes top 25% (overpriced/graded cards when searching raw)
        - Uses middle 50% for representative average

        Args:
            items: List of item summaries from Browse API

        Returns:
            dict: Pricing statistics (min, max, average, median)
        """
        all_prices = []

        # Collect all prices
        for item in items:
            try:
                price_obj = item.get('price', {})
                price_value = price_obj.get('value')

                if price_value:
                    all_prices.append(float(price_value))

            except (KeyError, ValueError, TypeError) as e:
                logger.debug(f"Error parsing price from item: {e}")
                continue

        if not all_prices:
            return {
                'min_price': None,
                'max_price': None,
                'avg_price': None,
                'median_price': None,
                'count': 0
            }

        # Sort prices for IQR calculation
        sorted_prices = sorted(all_prices)
        n = len(sorted_prices)

        # Use IQR method for representative sample (excludes extremes)
        if n < 4:
            # Too few results for IQR method - use all
            representative_prices = sorted_prices
        else:
            # Remove bottom 25% and top 25%, keep middle 50%
            q1_idx = n // 4
            q3_idx = 3 * n // 4
            representative_prices = sorted_prices[q1_idx:q3_idx]

            # Safety check: ensure we have a reasonable sample size
            if len(representative_prices) < min(10, n // 2):
                # If IQR gave us too few prices, use middle 50-70%
                start_idx = n // 6  # Start at ~17%
                end_idx = 5 * n // 6  # End at ~83%
                representative_prices = sorted_prices[start_idx:end_idx]

        # Calculate median (more resistant to outliers)
        if n % 2 == 0:
            median = (sorted_prices[n//2 - 1] + sorted_prices[n//2]) / 2
        else:
            median = sorted_prices[n//2]

        return {
            'min_price': round(min(all_prices), 2),
            'max_price': round(max(all_prices), 2),
            'avg_price': round(sum(representative_prices) / len(representative_prices), 2),
            'median_price': round(median, 2),
            'count': len(all_prices),
            'sample_size': len(representative_prices),  # How many used for average
            'excluded_low': len(all_prices) - len(sorted_prices) + (sorted_prices.index(representative_prices[0]) if representative_prices else 0),
            'excluded_high': len(sorted_prices) - (sorted_prices.index(representative_prices[-1]) + 1 if representative_prices else 0)
        }

    def get_average_price(self, year: str, brand: str, player_name: str,
                         card_number: Optional[str] = None, card_id: Optional[int] = None) -> Dict:
        """
        Get average price for a baseball card.

        Args:
            year: Card year
            brand: Card brand
            player_name: Player name
            card_number: Optional card number
            card_id: Optional card ID for logging

        Returns:
            dict: {
                'avg_price': float or None,
                'min_price': float or None,
                'max_price': float or None,
                'count': int
            }
        """
        try:
            result = self.search_card(year, brand, player_name, card_number, card_id)
            return result.get('pricing', {
                'min_price': None,
                'max_price': None,
                'avg_price': None,
                'count': 0
            })
        except eBayOAuthError as e:
            logger.error(f"Error getting average price: {e}")
            return {
                'min_price': None,
                'max_price': None,
                'avg_price': None,
                'count': 0,
                'error': str(e)
            }

    def test_connection(self) -> Dict:
        """
        Test eBay OAuth connection and credentials.

        Returns:
            dict: Connection test results
        """
        try:
            # Try to get an access token
            token = self._get_access_token()

            # Make a simple test search
            result = self.search_card("1993", "Topps", "Derek Jeter", "98")

            return {
                'success': True,
                'message': 'eBay OAuth connection successful',
                'timestamp': datetime.now().isoformat(),
                'environment': 'Production',
                'token_expires': self._token_cache['expires_at'].isoformat() if self._token_cache['expires_at'] else None,
                'test_search_results': result.get('total_results', 0)
            }

        except eBayOAuthError as e:
            return {
                'success': False,
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
