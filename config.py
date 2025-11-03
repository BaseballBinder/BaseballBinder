"""
Configuration management for the Baseball Card Collection application.
Loads environment variables from .env file.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration from environment variables"""

    # eBay API Credentials
    EBAY_APP_ID = os.getenv('EBAY_APP_ID')
    EBAY_DEV_ID = os.getenv('EBAY_DEV_ID')
    EBAY_CERT_ID = os.getenv('EBAY_CERT_ID')
    EBAY_ENVIRONMENT = os.getenv('EBAY_ENVIRONMENT', 'production')

    @classmethod
    def validate_ebay_credentials(cls) -> tuple[bool, str]:
        """
        Validate that all required eBay API credentials are present.

        Returns:
            tuple: (is_valid, error_message)
        """
        missing = []

        if not cls.EBAY_APP_ID:
            missing.append('EBAY_APP_ID')
        if not cls.EBAY_DEV_ID:
            missing.append('EBAY_DEV_ID')
        if not cls.EBAY_CERT_ID:
            missing.append('EBAY_CERT_ID')

        if missing:
            error_msg = f"Missing required eBay API credentials: {', '.join(missing)}"
            return False, error_msg

        return True, "All eBay credentials are present"

    @classmethod
    def get_ebay_credentials(cls) -> dict:
        """
        Get eBay API credentials as a dictionary.

        Returns:
            dict: Dictionary containing eBay credentials

        Raises:
            ValueError: If any required credentials are missing
        """
        is_valid, error_msg = cls.validate_ebay_credentials()
        if not is_valid:
            raise ValueError(error_msg)

        return {
            'app_id': cls.EBAY_APP_ID,
            'dev_id': cls.EBAY_DEV_ID,
            'cert_id': cls.EBAY_CERT_ID,
            'environment': cls.EBAY_ENVIRONMENT
        }

# Validate credentials on module import (optional - can comment out for testing)
# is_valid, message = Config.validate_ebay_credentials()
# if not is_valid:
#     print(f"WARNING: {message}")
