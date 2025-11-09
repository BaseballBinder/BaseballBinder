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
                   card_id: Optional[int] = None) -> Dict:
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

        Returns:
            dict: Search results with pricing information

        Raises:
            eBayOAuthError: If search fails
        """
        # Build comprehensive search query
        query_parts = [year, brand, player_name]
        if card_number:
            query_parts.append(f"#{card_number}")
        if variety:
            query_parts.append(variety)
        if parallel:
            query_parts.append(parallel)
        if autograph:
            query_parts.append("autograph")
        if graded:
            query_parts.append(graded)

        # Extract print run from numbered (e.g., "05/49" -> "/49")
        print_run = None
        if numbered:
            # Check if numbered contains a pattern like "05/49" or "105/200"
            match = re.search(r'/(\d+)$', numbered)
            if match:
                # Extract just the "/49" part for search
                print_run = f"/{match.group(1)}"
                query_parts.append(print_run)
            else:
                # If it's already in format "/49" or doesn't match pattern, use as-is
                query_parts.append(numbered)

        query = " ".join(query_parts)
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

            if not items:
                logger.info(f"No results found for: {query}")

                # Progressive search broadening: try broader searches if no results
                broader_result = None

                # Strategy 1: Remove print run specification (most restrictive)
                if numbered and not broader_result:
                    logger.info(f"Retrying without print run specification: {numbered}")
                    broader_result = self.search_card(
                        year=year, brand=brand, player_name=player_name,
                        card_number=card_number, variety=variety, parallel=parallel,
                        autograph=autograph, graded=graded, numbered=None, card_id=card_id
                    )
                    if broader_result.get('total_results', 0) > 0:
                        broader_result['search_query'] += f" (broadened: removed print run)"
                        return broader_result

                # Strategy 2: Remove variety and parallel
                if (variety or parallel) and not broader_result:
                    logger.info(f"Retrying without variety/parallel specifications")
                    broader_result = self.search_card(
                        year=year, brand=brand, player_name=player_name,
                        card_number=card_number, variety=None, parallel=None,
                        autograph=autograph, graded=graded, numbered=None, card_id=card_id
                    )
                    if broader_result.get('total_results', 0) > 0:
                        broader_result['search_query'] += f" (broadened: removed variety/parallel)"
                        return broader_result

                # Strategy 3: Remove card number (keep only essentials)
                if card_number and not broader_result:
                    logger.info(f"Retrying without card number specification")
                    broader_result = self.search_card(
                        year=year, brand=brand, player_name=player_name,
                        card_number=None, variety=None, parallel=None,
                        autograph=autograph, graded=graded, numbered=None, card_id=card_id
                    )
                    if broader_result.get('total_results', 0) > 0:
                        broader_result['search_query'] += f" (broadened: removed card #)"
                        return broader_result

                # No results even with broadening - return empty result
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
        Calculate pricing statistics from search results.
        Uses top 20 listings for average to reduce outlier impact.

        Args:
            items: List of item summaries from Browse API

        Returns:
            dict: Pricing statistics (min, max, average, median)
        """
        all_prices = []

        # Collect all prices for min/max
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

        # Use only top 20 listings for average calculation (better sample)
        top_prices = all_prices[:20]

        # Calculate median (more resistant to outliers)
        sorted_prices = sorted(all_prices)
        n = len(sorted_prices)
        if n % 2 == 0:
            median = (sorted_prices[n//2 - 1] + sorted_prices[n//2]) / 2
        else:
            median = sorted_prices[n//2]

        return {
            'min_price': round(min(all_prices), 2),
            'max_price': round(max(all_prices), 2),
            'avg_price': round(sum(top_prices) / len(top_prices), 2),
            'median_price': round(median, 2),
            'count': len(all_prices),
            'sample_size': len(top_prices)  # How many used for average
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
