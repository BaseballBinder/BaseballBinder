"""
Rate limiter for eBay API calls.
Tracks daily API usage and enforces limits.
"""
import json
import os
from datetime import datetime, date
from pathlib import Path

RATE_LIMIT_FILE = Path(__file__).parent / 'ebay_rate_limit.json'
DEFAULT_DAILY_LIMIT = 5000  # Conservative estimate
WARNING_THRESHOLD = 0.8  # Warn at 80% of limit

class RateLimiter:
    """Track and limit eBay API calls per day"""

    def __init__(self, daily_limit: int = DEFAULT_DAILY_LIMIT):
        self.daily_limit = daily_limit
        self.data = self._load_data()

    def _load_data(self) -> dict:
        """Load rate limit data from file"""
        if RATE_LIMIT_FILE.exists():
            try:
                with open(RATE_LIMIT_FILE, 'r') as f:
                    data = json.load(f)
                    # Reset if it's a new day
                    if data.get('date') != str(date.today()):
                        return self._create_new_data()
                    return data
            except Exception:
                return self._create_new_data()
        return self._create_new_data()

    def _create_new_data(self) -> dict:
        """Create new rate limit data for today"""
        return {
            'date': str(date.today()),
            'count': 0,
            'calls': []
        }

    def _save_data(self):
        """Save rate limit data to file"""
        with open(RATE_LIMIT_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    def can_make_request(self) -> tuple[bool, str]:
        """
        Check if a request can be made.

        Returns:
            tuple: (can_make_request, message)
        """
        if self.data['count'] >= self.daily_limit:
            return False, f"Daily limit of {self.daily_limit} API calls reached"

        # Warning threshold
        if self.data['count'] >= int(self.daily_limit * WARNING_THRESHOLD):
            remaining = self.daily_limit - self.data['count']
            return True, f"Warning: Only {remaining} API calls remaining today"

        return True, "OK"

    def record_request(self, endpoint: str = ""):
        """Record an API request"""
        self.data['count'] += 1
        self.data['calls'].append({
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint
        })
        self._save_data()

    def get_stats(self) -> dict:
        """Get current rate limit statistics"""
        return {
            'date': self.data['date'],
            'count': self.data['count'],
            'limit': self.daily_limit,
            'remaining': self.daily_limit - self.data['count'],
            'percentage_used': (self.data['count'] / self.daily_limit * 100) if self.daily_limit > 0 else 0
        }

    def reset(self):
        """Manually reset the counter (admin function)"""
        self.data = self._create_new_data()
        self._save_data()

# Global instance
rate_limiter = RateLimiter()
