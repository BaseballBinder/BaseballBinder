"""
Test script for eBay OAuth service.
Tests the Client Credentials flow and Browse API integration.
"""
import json
import sys
from ebay_service import eBayService, eBayOAuthError

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    """Test eBay OAuth service with a single search query"""
    print("=" * 60)
    print("eBay OAuth Service Test")
    print("=" * 60)
    print()

    try:
        # Initialize service
        print("1. Initializing eBay OAuth service...")
        service = eBayService()
        print("   ✓ Service initialized successfully")
        print()

        # Test connection
        print("2. Testing connection and authentication...")
        connection_test = service.test_connection()

        if connection_test['success']:
            print(f"   ✓ Connection successful")
            print(f"   Environment: {connection_test.get('environment')}")
            print(f"   Token expires: {connection_test.get('token_expires')}")
            print(f"   Test search results: {connection_test.get('test_search_results')} items")
        else:
            print(f"   ✗ Connection failed: {connection_test['message']}")
            return

        print()

        # Search for specific card
        print("3. Searching for: 1993 Topps Derek Jeter 98")
        result = service.search_card(
            year="1993",
            brand="Topps",
            player_name="Derek Jeter",
            card_number="98"
        )

        print(f"   Search query: {result['search_query']}")
        print(f"   Total results: {result['total_results']}")
        print()

        # Display pricing
        if result['pricing']:
            pricing = result['pricing']
            print("   Pricing Statistics:")
            print(f"   - Average price: ${pricing['avg_price']:.2f}")
            print(f"   - Min price: ${pricing['min_price']:.2f}")
            print(f"   - Max price: ${pricing['max_price']:.2f}")
            print(f"   - Sample size: {pricing['count']} listings")
        else:
            print("   No pricing data available")

        print()

        # Display sample items
        items = result.get('items', [])
        if items:
            print(f"   Sample Items (showing first 5 of {len(items)}):")
            for i, item in enumerate(items[:5], 1):
                title = item.get('title', 'N/A')
                price = item.get('price', {})
                price_value = price.get('value', 'N/A')
                currency = price.get('currency', 'USD')
                item_url = item.get('itemWebUrl', 'N/A')

                print(f"   {i}. {title}")
                print(f"      Price: {price_value} {currency}")
                print(f"      URL: {item_url[:80]}...")
                print()

        print()
        print("=" * 60)
        print("Test completed successfully!")
        print("=" * 60)

    except eBayOAuthError as e:
        print(f"   ✗ eBay OAuth Error: {e}")
    except Exception as e:
        print(f"   ✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
