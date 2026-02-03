#!/usr/bin/env python3
"""
Salla API Configuration Template
Copy this file to 'salla_config.py' and fill in your credentials
"""

# Salla API Configuration
SALLA_CONFIG = {
    # Your Salla access token
    'access_token': 'your_access_token_here',
    
    # Salla API base URL (usually doesn't need to change)
    'base_url': 'https://api.salla.dev',
    
    # Optional: Store specific settings
    'store_id': 'your_store_id_here',  # If needed
    
    # Test settings
    'test_product_id': None,  # Specific product ID to test (optional)
    'default_per_page': 20,   # Default number of products per page
    'max_retries': 3,         # Max API retry attempts
    'timeout': 30,            # Request timeout in seconds
}

# Environment settings
ENVIRONMENT = 'sandbox'  # 'sandbox' or 'production'

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'log_file': 'salla_api_test.log',
    'console_output': True,
}