# Salla Platform API Test Script

This directory contains test scripts for integrating with the Salla e-commerce platform API to retrieve product data.

## Files Overview

- `test_salla_api.py` - Main test script for Salla API product operations
- `fetch_all_products.py` - Dedicated script to fetch ALL products and save to JSON
- `salla_config_template.py` - Configuration template (copy to `salla_config.py`)
- `requirements.txt` - Python dependencies
- `README.md` - This documentation file

## Prerequisites

1. **Salla Developer Account**: You need a Salla developer account and access to the Salla API
2. **Access Token**: Obtain an access token from your Salla app dashboard
3. **Python 3.7+**: Ensure you have Python 3.7 or higher installed

## Setup Instructions

### 1. Install Dependencies

```bash
cd /Users/vm/master/odoo18_saas_sh/extra/omniful_integration/tests
pip install -r requirements.txt
```

### 2. Configure Access Token

You have two options to provide your access token:

**Option A: Environment Variable (Recommended)**
```bash
export SALLA_ACCESS_TOKEN="your_access_token_here"
```

**Option B: Configuration File**
```bash
cp salla_config_template.py salla_config.py
# Edit salla_config.py and add your access token
```

**Option C: Interactive Input**
The script will prompt you for the token if not found in environment or config.

## Usage

### Basic API Testing

```bash
# Run the test script
python test_salla_api.py

# Or make it executable and run directly
chmod +x test_salla_api.py
./test_salla_api.py
```

### Fetch ALL Products to JSON

```bash
# Run the dedicated fetch script
python fetch_all_products.py

# Or make it executable and run directly
chmod +x fetch_all_products.py
./fetch_all_products.py
```

**Features of `fetch_all_products.py`:**
- Fetches ALL products from your Salla store (handles pagination automatically)
- Saves complete product data to JSON file with metadata
- Shows progress during fetch process
- Handles large datasets efficiently
- Includes error handling and retry logic
- Generates timestamped filenames automatically
- Provides file size and summary information

### Using the SallaAPITester Class

```python
from test_salla_api import SallaAPITester

# Initialize with your access token
api_tester = SallaAPITester(access_token="your_token_here")

# Test connection
result = api_tester.test_connection()
print(result)

# Get products
products = api_tester.get_products(page=1, per_page=10)
print(products)

# Get specific product
product = api_tester.get_product_by_id("product_id_here")
print(product)

# Search products
search_results = api_tester.search_products("search_term")
print(search_results)
```

## API Methods Available

### 1. test_connection()
Tests the API connection by fetching store information.

**Returns:**
```python
{
    'success': True/False,
    'status_code': 200,
    'data': {...}  # Store information
}
```

### 2. get_products(page=1, per_page=20, filters=None)
Retrieves products from the store with pagination.

**Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 50)
- `filters` (dict): Additional filters

**Returns:**
```python
{
    'success': True/False,
    'status_code': 200,
    'products': [...],  # List of products
    'pagination': {...},  # Pagination info
    'total_count': 10
}
```

### 3. get_product_by_id(product_id)
Retrieves a specific product by its ID.

**Parameters:**
- `product_id` (str/int): Product ID

**Returns:**
```python
{
    'success': True/False,
    'status_code': 200,
    'product': {...}  # Product details
}
```

### 4. search_products(query, page=1, per_page=20)
Searches products by name or SKU.

**Parameters:**
- `query` (str): Search term
- `page` (int): Page number
- `per_page` (int): Items per page

**Returns:**
Same format as `get_products()`

## Sample Product Data Structure

```python
{
    "id": 123456,
    "name": "Product Name",
    "sku": "PROD-001",
    "price": 99.99,
    "currency": "SAR",
    "status": "active",
    "quantity": 100,
    "description": "Product description",
    "images": [...],
    "categories": [...],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

## Error Handling

The script includes comprehensive error handling:

- **Connection Errors**: Network issues, timeouts
- **Authentication Errors**: Invalid or expired tokens
- **API Errors**: Rate limiting, invalid requests
- **Data Errors**: Malformed responses

All errors are logged to `salla_api_test.log` with timestamps.

## Logging

The script creates detailed logs in `salla_api_test.log` including:
- API requests and responses
- Error messages and stack traces
- Performance metrics
- Debug information

## Common Issues and Solutions

### 1. Authentication Failed (401)
- Check if your access token is valid
- Ensure the token has the required permissions
- Verify the token hasn't expired

### 2. Rate Limiting (429)
- The script includes automatic retry logic
- Consider adding delays between requests
- Check your API rate limits in Salla dashboard

### 3. No Products Found
- Verify your store has products
- Check if products are published/active
- Try different search terms

### 4. Connection Timeout
- Check your internet connection
- Verify Salla API status
- Increase timeout in configuration

## Integration with Odoo

This test script can be integrated into the existing Omniful integration module:

1. **Product Synchronization**: Use the product data to sync with Odoo products
2. **Inventory Updates**: Combine with inventory feeds
3. **Order Processing**: Extend for order management
4. **Webhook Integration**: Add webhook endpoints for real-time updates

## Security Notes

- Never commit access tokens to version control
- Use environment variables for sensitive data
- Rotate access tokens regularly
- Monitor API usage and logs

## Support

For Salla API documentation and support:
- [Salla Developer Documentation](https://docs.salla.dev/)
- [Salla API Reference](https://docs.salla.dev/api/)
- [Salla Developer Community](https://community.salla.dev/)

## License

This script is part of the Omniful Integration module and follows the same LGPL-3 license.