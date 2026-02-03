#!/usr/bin/env python3
"""
Salla Platform API Test Script
Test script for getting product data from Salla platform using access token
"""

import requests
import json
import logging
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('salla_api_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
_logger = logging.getLogger(__name__)

class SallaAPITester:
    """
    Salla API Test Client for product data retrieval
    """
    
    def __init__(self, access_token, base_url="https://api.salla.dev"):
        """
        Initialize Salla API tester
        
        Args:
            access_token (str): Salla API access token
            base_url (str): Salla API base URL
        """
        self.access_token = access_token
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def test_connection(self):
        """
        Test API connection by getting store info
        
        Returns:
            dict: API response or error info
        """
        try:
            url = f"{self.base_url}/admin/v2/products"
            _logger.info(f"Testing connection to: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                _logger.info("✅ Connection successful!")
                
                # Handle different response structures
                store_info = data
                if isinstance(data, dict) and 'data' in data:
                    store_info = data.get('data', {})
                
                if isinstance(store_info, dict):
                    store_name = store_info.get('name', 'N/A')
                    _logger.info(f"Store Name: {store_name}")
                else:
                    _logger.info("Store info retrieved successfully")
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'data': data
                }
            else:
                _logger.error(f"❌ Connection failed with status: {response.status_code}")
                _logger.error(f"Response: {response.text}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"❌ Request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_products(self, page=1, per_page=20, filters=None):
        """
        Get products from Salla store
        
        Args:
            page (int): Page number (default: 1)
            per_page (int): Items per page (default: 20, max: 50)
            filters (dict): Additional filters
            
        Returns:
            dict: Products data or error info
        """
        try:
            url = f"{self.base_url}/admin/v2/products"
            
            params = {
                'page': page,
                'per_page': min(per_page, 50)  # Salla max is 50
            }
            
            # Add filters if provided
            if filters:
                params.update(filters)
            
            _logger.info(f"Fetching products from: {url}")
            _logger.info(f"Parameters: {params}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('data', [])
                pagination = data.get('pagination', {})
                
                _logger.info(f"✅ Successfully retrieved {len(products)} products")
                _logger.info(f"Total products: {pagination.get('total', 'N/A')}")
                _logger.info(f"Current page: {pagination.get('current_page', 'N/A')}")
                _logger.info(f"Total pages: {pagination.get('last_page', 'N/A')}")
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'products': products,
                    'pagination': pagination,
                    'total_count': len(products)
                }
            else:
                _logger.error(f"❌ Failed to get products. Status: {response.status_code}")
                _logger.error(f"Response: {response.text}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"❌ Request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_product_by_id(self, product_id):
        """
        Get specific product by ID
        
        Args:
            product_id (str/int): Product ID
            
        Returns:
            dict: Product data or error info
        """
        try:
            url = f"{self.base_url}/admin/v2/products/{product_id}"
            _logger.info(f"Fetching product {product_id} from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                product = data.get('data', {})
                
                _logger.info(f"✅ Successfully retrieved product: {product.get('name', 'N/A')}")
                _logger.info(f"SKU: {product.get('sku', 'N/A')}")
                _logger.info(f"Price: {product.get('price', 'N/A')}")
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'product': product
                }
            else:
                _logger.error(f"❌ Failed to get product {product_id}. Status: {response.status_code}")
                _logger.error(f"Response: {response.text}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"❌ Request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_products(self, query, page=1, per_page=20):
        """
        Search products by name or SKU
        
        Args:
            query (str): Search query
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            dict: Search results or error info
        """
        filters = {
            'search': query
        }
        
        _logger.info(f"Searching products with query: '{query}'")
        return self.get_products(page=page, per_page=per_page, filters=filters)
    
    def get_all_products(self, save_to_file=True, filename=None):
        """
        Get all products from Salla store with pagination
        
        Args:
            save_to_file (bool): Whether to save data to JSON file
            filename (str): Custom filename for JSON file
            
        Returns:
            dict: All products data or error info
        """
        try:
            all_products = []
            page = 1
            per_page = 50  # Maximum allowed by Salla API
            total_pages = None
            
            _logger.info("🚀 Starting to fetch all products...")
            
            while True:
                _logger.info(f"📄 Fetching page {page}...")
                
                result = self.get_products(page=page, per_page=per_page)
                
                if not result.get('success'):
                    _logger.error(f"❌ Failed to fetch page {page}: {result.get('error')}")
                    break
                
                products = result.get('products', [])
                pagination = result.get('pagination', {})
                
                if not products:
                    _logger.info("✅ No more products found")
                    break
                
                all_products.extend(products)
                
                # Get pagination info
                if total_pages is None:
                    total_pages = pagination.get('last_page', 1)
                    total_count = pagination.get('total', len(all_products))
                    _logger.info(f"📊 Total products to fetch: {total_count} across {total_pages} pages")
                
                current_count = len(all_products)
                
                # Calculate progress based on products fetched vs total expected
                if total_count > 0:
                    progress = (current_count / total_count) * 100
                    _logger.info(f"✅ Page {page} completed. Products fetched: {current_count}/{total_count} ({progress:.1f}%)")
                else:
                    _logger.info(f"✅ Page {page} completed. Products fetched: {current_count}")
                
                # Check if we've fetched all expected products or if we got less than per_page (indicating last page)
                if len(products) < per_page:
                    _logger.info(f"📄 Received {len(products)} products (less than {per_page}), assuming this is the last page")
                    break
                
                # Also check if we've reached the expected total count
                if total_count > 0 and current_count >= total_count:
                    _logger.info(f"📊 Reached expected total count of {total_count} products")
                    break
                    
                page += 1
            
            _logger.info(f"🎉 Successfully fetched all {len(all_products)} products!")
            
            # Prepare the complete data structure
            complete_data = {
                'timestamp': datetime.now().isoformat(),
                'total_products': len(all_products),
                'total_pages': total_pages,
                'api_base_url': self.base_url,
                'products': all_products
            }
            
            # Save to JSON file if requested
            if save_to_file:
                if filename is None:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'salla_products_{timestamp}.json'
                
                filepath = os.path.join(os.path.dirname(__file__), filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(complete_data, f, ensure_ascii=False, indent=2)
                
                _logger.info(f"💾 All products saved to: {filepath}")
                _logger.info(f"📁 File size: {os.path.getsize(filepath)} bytes")
            
            return {
                'success': True,
                'total_products': len(all_products),
                'products': all_products,
                'complete_data': complete_data,
                'saved_file': filepath if save_to_file else None
            }
            
        except Exception as e:
            _logger.error(f"❌ Error fetching all products: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def print_product_summary(self, products):
        """
        Print a formatted summary of products
        
        Args:
            products (list): List of product data
        """
        print("\n" + "="*80)
        print(f"{'PRODUCT SUMMARY':^80}")
        print("="*80)
        
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.get('name', 'N/A')}")
            print(f"   ID: {product.get('id', 'N/A')}")
            print(f"   SKU: {product.get('sku', 'N/A')}")
            print(f"   Price: {product.get('price', 'N/A')} {product.get('currency', '')}")
            print(f"   Status: {product.get('status', 'N/A')}")
            print(f"   Stock: {product.get('quantity', 'N/A')}")
            print(f"   Created: {product.get('created_at', 'N/A')}")
            print("-" * 50)

def main():
    """
    Main test function
    """
    print("🚀 Salla API Product Test Script")
    print("=" * 50)
    
    # Get access token from environment or prompt
    access_token = os.getenv('SALLA_ACCESS_TOKEN')
    
    if not access_token:
        access_token = input("Enter your Salla access token: ").strip()
    
    if not access_token:
        print("❌ Access token is required!")
        sys.exit(1)
    
    # Initialize API tester
    api_tester = SallaAPITester(access_token)
    
    # Test connection
    print("\n1. Testing API connection...")
    connection_result = api_tester.test_connection()
    
    if not connection_result.get('success'):
        print("❌ Connection test failed. Please check your access token.")
        return
    
    # Get products
    print("\n2. Fetching products...")
    products_result = api_tester.get_products(page=1, per_page=10)
    
    if products_result.get('success'):
        products = products_result.get('products', [])
        if products:
            api_tester.print_product_summary(products)
            
            # Test getting specific product
            first_product_id = products[0].get('id')
            if first_product_id:
                print(f"\n3. Testing single product fetch (ID: {first_product_id})...")
                single_product_result = api_tester.get_product_by_id(first_product_id)
                
                if single_product_result.get('success'):
                    product = single_product_result.get('product', {})
                    print(f"✅ Single product fetch successful: {product.get('name', 'N/A')}")
        else:
            print("ℹ️ No products found in the store.")
    else:
        print("❌ Failed to fetch products.")
    
    # Test search functionality
    print("\n4. Testing product search...")
    search_query = input("Enter search term (or press Enter to skip): ").strip()
    
    if search_query:
        search_result = api_tester.search_products(search_query, per_page=5)
        if search_result.get('success'):
            search_products = search_result.get('products', [])
            if search_products:
                print(f"\n🔍 Search results for '{search_query}':")
                api_tester.print_product_summary(search_products)
            else:
                print(f"ℹ️ No products found for '{search_query}'.")
    
    # Option to fetch all products and save to JSON
    print("\n5. Fetch all products and save to JSON file?")
    fetch_all = input("Do you want to fetch ALL products and save to JSON? (y/N): ").strip().lower()
    
    if fetch_all in ['y', 'yes']:
        print("\n🚀 Starting to fetch all products...")
        print("⚠️ This may take several minutes depending on the number of products.")
        
        # Ask for custom filename
        custom_filename = input("Enter custom filename (or press Enter for auto-generated): ").strip()
        filename = custom_filename if custom_filename else None
        
        all_products_result = api_tester.get_all_products(save_to_file=True, filename=filename)
        
        if all_products_result.get('success'):
            total_products = all_products_result.get('total_products', 0)
            saved_file = all_products_result.get('saved_file')
            
            print(f"\n🎉 Successfully fetched and saved {total_products} products!")
            print(f"📁 File saved as: {saved_file}")
            
            # Show sample of products
            products = all_products_result.get('products', [])
            if products:
                print(f"\n📋 Sample of first 5 products:")
                api_tester.print_product_summary(products[:5])
        else:
            print(f"❌ Failed to fetch all products: {all_products_result.get('error')}")
    
    print("\n✅ Test completed! Check 'salla_api_test.log' for detailed logs.")

if __name__ == "__main__":
    main()