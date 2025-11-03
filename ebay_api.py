"""
eBay API integration for baseball card price checking.
Uses eBay Finding API to search for sold and active listings.
"""
import time
import logging
from typing import Optional, Dict, List
from datetime import datetime
import requests
from config import Config
from rate_limiter import rate_limiter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class eBayAPIError(Exception):
    """Custom exception for eBay API errors"""
    pass


class eBayAPI:
    """
    eBay API client for searching baseball card listings.
    Uses eBay Finding API to retrieve pricing data.
    """

    # eBay Finding API endpoints
    PRODUCTION_ENDPOINT = "https://svcs.ebay.com/services/search/FindingService/v1"
    SANDBOX_ENDPOINT = "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"

    def __init__(self):
        """Initialize eBay API client with credentials from config"""
        try:
            self.credentials = Config.get_ebay_credentials()
            self.app_id = self.credentials['app_id']
            self.environment = self.credentials['environment']

            # Set the appropriate endpoint
            if self.environment == 'production':
                self.endpoint = self.PRODUCTION_ENDPOINT
            else:
                self.endpoint = self.SANDBOX_ENDPOINT

            logger.info(f"eBay API initialized ({self.environment} environment)")

        except ValueError as e:
            logger.error(f"Failed to initialize eBay API: {e}")
            raise eBayAPIError(f"Configuration error: {e}")

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests

    def _wait_for_rate_limit(self):
        """Ensure we respect rate limits by waiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _build_search_keywords(self, player: str, year: Optional[str] = None,
                               set_name: Optional[str] = None,
                               card_number: Optional[str] = None) -> str:
        """
        Build search keywords from card information.

        Args:
            player: Player name
            year: Card year
            set_name: Set name
            card_number: Card number

        Returns:
            str: Search keyword string
        """
        keywords = []

        if player:
            keywords.append(player)
        if year:
            keywords.append(year)
        if set_name:
            keywords.append(set_name)
        if card_number:
            keywords.append(f"#{card_number}")

        return " ".join(keywords)

    def _make_request(self, operation: str, params: dict) -> dict:
        """
        Make a request to eBay Finding API.

        Args:
            operation: API operation name
            params: Request parameters

        Returns:
            dict: Response data

        Raises:
            eBayAPIError: If request fails
        """
        # Check rate limit before making request
        can_request, message = rate_limiter.can_make_request()
        if not can_request:
            logger.error(f"Rate limit exceeded: {message}")
            raise eBayAPIError(message)

        if "Warning" in message:
            logger.warning(message)

        self._wait_for_rate_limit()

        # Build request parameters
        request_params = {
            'OPERATION-NAME': operation,
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': self.app_id,
            'RESPONSE-DATA-FORMAT': 'JSON',
            **params
        }

        try:
            logger.info(f"Making eBay API request: {operation}")
            response = requests.get(self.endpoint, params=request_params, timeout=10)

            # Record successful request
            rate_limiter.record_request(operation)

            # Log response for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text[:500]}")  # First 500 chars

            response.raise_for_status()

            data = response.json()

            # Check for API errors
            if 'errorMessage' in data:
                errors = data['errorMessage'][0].get('error', [])
                if errors:
                    error_msg = errors[0].get('message', [None])[0]
                    error_id = errors[0].get('errorId', [None])[0]
                    logger.error(f"eBay API error {error_id}: {error_msg}")
                    raise eBayAPIError(f"eBay API error ({error_id}): {error_msg}")
                raise eBayAPIError("eBay API returned an error message")

            return data

        except requests.exceptions.Timeout:
            raise eBayAPIError("Request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise eBayAPIError(f"Request failed: {str(e)}")
        except eBayAPIError:
            raise  # Re-raise eBay errors
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise eBayAPIError(f"Unexpected error: {str(e)}")

    def search_sold_listings(self, player: str, year: Optional[str] = None,
                            set_name: Optional[str] = None,
                            card_number: Optional[str] = None) -> Dict:
        """
        Search for completed/sold listings on eBay.

        Args:
            player: Player name
            year: Card year
            set_name: Set name
            card_number: Card number

        Returns:
            dict: {
                'avg_price': float,
                'min_price': float,
                'max_price': float,
                'listing_count': int,
                'sample_urls': list,
                'search_keywords': str
            }
        """
        keywords = self._build_search_keywords(player, year, set_name, card_number)

        params = {
            'keywords': keywords,
            'categoryId': '261328',  # Sports Mem, Cards & Fan Shop > Sports Trading Cards > Baseball Cards
            'itemFilter(0).name': 'SoldItemsOnly',
            'itemFilter(0).value': 'true',
            'sortOrder': 'EndTimeSoonest',
            'paginationInput.entriesPerPage': '100'
        }

        try:
            data = self._make_request('findCompletedItems', params)

            # Parse response
            search_result = data.get('findCompletedItemsResponse', [{}])[0]
            ack = search_result.get('ack', [None])[0]

            if ack != 'Success':
                logger.warning(f"eBay API returned non-success ack: {ack}")
                return self._empty_result(keywords)

            # Get search results
            result_data = search_result.get('searchResult', [{}])[0]
            count = int(result_data.get('@count', 0))

            if count == 0:
                logger.info(f"No sold listings found for: {keywords}")
                return self._empty_result(keywords)

            items = result_data.get('item', [])

            # Calculate prices
            prices = []
            sample_urls = []

            for item in items:
                try:
                    price = float(item['sellingStatus'][0]['currentPrice'][0]['__value__'])
                    prices.append(price)

                    if len(sample_urls) < 3:  # Get up to 3 sample URLs
                        sample_urls.append(item['viewItemURL'][0])
                except (KeyError, ValueError, IndexError) as e:
                    logger.debug(f"Error parsing item: {e}")
                    continue

            if not prices:
                return self._empty_result(keywords)

            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)

            result = {
                'avg_price': round(avg_price, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'listing_count': len(prices),
                'sample_urls': sample_urls,
                'search_keywords': keywords
            }

            logger.info(f"Found {len(prices)} sold listings, avg price: ${avg_price:.2f}")
            return result

        except eBayAPIError as e:
            logger.error(f"Error searching sold listings: {e}")
            raise

    def search_active_listings(self, player: str, year: Optional[str] = None,
                               set_name: Optional[str] = None,
                               card_number: Optional[str] = None) -> Dict:
        """
        Search for active listings on eBay.

        Args:
            player: Player name
            year: Card year
            set_name: Set name
            card_number: Card number

        Returns:
            dict: {
                'min_price': float,
                'max_price': float,
                'listing_count': int,
                'sample_urls': list,
                'search_keywords': str
            }
        """
        keywords = self._build_search_keywords(player, year, set_name, card_number)

        params = {
            'keywords': keywords,
            'categoryId': '261328',  # Baseball Cards
            'itemFilter(0).name': 'ListingType',
            'itemFilter(0).value': 'FixedPrice',
            'sortOrder': 'PricePlusShippingLowest',
            'paginationInput.entriesPerPage': '100'
        }

        try:
            data = self._make_request('findItemsAdvanced', params)

            # Parse response
            search_result = data.get('findItemsAdvancedResponse', [{}])[0]
            ack = search_result.get('ack', [None])[0]

            if ack != 'Success':
                logger.warning(f"eBay API returned non-success ack: {ack}")
                return self._empty_active_result(keywords)

            # Get search results
            result_data = search_result.get('searchResult', [{}])[0]
            count = int(result_data.get('@count', 0))

            if count == 0:
                logger.info(f"No active listings found for: {keywords}")
                return self._empty_active_result(keywords)

            items = result_data.get('item', [])

            # Calculate prices
            prices = []
            sample_urls = []

            for item in items:
                try:
                    price = float(item['sellingStatus'][0]['currentPrice'][0]['__value__'])
                    prices.append(price)

                    if len(sample_urls) < 3:  # Get up to 3 sample URLs
                        sample_urls.append(item['viewItemURL'][0])
                except (KeyError, ValueError, IndexError) as e:
                    logger.debug(f"Error parsing item: {e}")
                    continue

            if not prices:
                return self._empty_active_result(keywords)

            min_price = min(prices)
            max_price = max(prices)

            result = {
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'listing_count': len(prices),
                'sample_urls': sample_urls,
                'search_keywords': keywords
            }

            logger.info(f"Found {len(prices)} active listings, range: ${min_price:.2f} - ${max_price:.2f}")
            return result

        except eBayAPIError as e:
            logger.error(f"Error searching active listings: {e}")
            raise

    def _empty_result(self, keywords: str) -> Dict:
        """Return empty result for sold listings"""
        return {
            'avg_price': None,
            'min_price': None,
            'max_price': None,
            'listing_count': 0,
            'sample_urls': [],
            'search_keywords': keywords
        }

    def _empty_active_result(self, keywords: str) -> Dict:
        """Return empty result for active listings"""
        return {
            'min_price': None,
            'max_price': None,
            'listing_count': 0,
            'sample_urls': [],
            'search_keywords': keywords
        }

    def test_connection(self) -> Dict:
        """
        Test eBay API connection and credentials.

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'timestamp': str
            }
        """
        try:
            # Make a simple test search
            params = {
                'keywords': 'baseball card',
                'paginationInput.entriesPerPage': '1'
            }

            data = self._make_request('findItemsAdvanced', params)

            search_result = data.get('findItemsAdvancedResponse', [{}])[0]
            ack = search_result.get('ack', [None])[0]

            if ack == 'Success':
                return {
                    'success': True,
                    'message': 'eBay API connection successful',
                    'timestamp': datetime.now().isoformat(),
                    'environment': self.environment
                }
            else:
                return {
                    'success': False,
                    'message': f'eBay API returned: {ack}',
                    'timestamp': datetime.now().isoformat()
                }

        except eBayAPIError as e:
            return {
                'success': False,
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
