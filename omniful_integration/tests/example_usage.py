#!/usr/bin/env python3
"""
Salla API Usage Examples
Demonstrates various ways to use the Salla API test script
"""

import os
import sys
from test_salla_api import SallaAPITester

def example_basic_usage():
    """
    Example 1: Basic API usage
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic API Usage")
    print("="*60)
    
    # Get access token (replace with your actual token)
    access_token = os.getenv('SALLA_ACCESS_TOKEN', 'your_token_here')
    
    if access_token == 'your_token_here':
        print("⚠️ Please set SALLA_ACCESS_TOKEN environment variable")
        return
    
    # Initialize API client
    api = SallaAPITester(access_token)
    
    # Test connection
    print("\n1. Testing connection...")
    connection = api.test_connection()
    if connection['success']:
        # Handle different response structures
        data = connection.get('data', {})
        store_info = data
        if isinstance(data, dict) and 'data' in data:
            store_info = data.get('data', {})
        
        if isinstance(store_info, dict):
            store_name = store_info.get('name', 'Unknown')
        else:
            store_name = 'Unknown'
        
        print(f"✅ Connected to store: {store_name}")
    else:
        print(f"❌ Connection failed: {connection.get('error', 'Unknown error')}")
        return
    
    # Get first page of products
    print("\n2. Fetching products...")
    products_result = api.get_products(page=1, per_page=5)
    if products_result['success']:
        products = products_result['products']
        print(f"✅ Found {len(products)} products")
        
        for product in products:
            print(f"  - {product.get('name', 'N/A')} (ID: {product.get('id', 'N/A')})")
    else:
        print(f"❌ Failed to get products: {products_result.get('error', 'Unknown error')}")

def example_product_details():
    """
    Example 2: Get detailed product information
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Product Details")
    print("="*60)
    
    access_token = os.getenv('SALLA_ACCESS_TOKEN', 'your_token_here')
    if access_token == 'your_token_here':
        print("⚠️ Please set SALLA_ACCESS_TOKEN environment variable")
        return
    
    api = SallaAPITester(access_token)
    
    # Get products to find a valid ID
    products_result = api.get_products(page=1, per_page=1)
    if not products_result['success'] or not products_result['products']:
        print("❌ No products available for testing")
        return
    
    # Get first product ID
    product_id = products_result['products'][0]['id']
    print(f"\nGetting details for product ID: {product_id}")
    
    # Get detailed product info
    product_result = api.get_product_by_id(product_id)
    if product_result['success']:
        product = product_result['product']
        print(f"\n📦 Product Details:")
        print(f"   Name: {product.get('name', 'N/A')}")
        print(f"   SKU: {product.get('sku', 'N/A')}")
        print(f"   Price: {product.get('price', 'N/A')} {product.get('currency', '')}")
        print(f"   Status: {product.get('status', 'N/A')}")
        print(f"   Stock: {product.get('quantity', 'N/A')}")
        print(f"   Description: {product.get('description', 'N/A')[:100]}...")
        
        # Show categories if available
        categories = product.get('categories', [])
        if categories:
            print(f"   Categories: {', '.join([cat.get('name', 'N/A') for cat in categories])}")
        
        # Show images if available
        images = product.get('images', [])
        if images:
            print(f"   Images: {len(images)} image(s)")
            for i, img in enumerate(images[:3], 1):  # Show first 3 images
                print(f"     {i}. {img.get('url', 'N/A')}")
    else:
        print(f"❌ Failed to get product details: {product_result.get('error', 'Unknown error')}")

def example_search_products():
    """
    Example 3: Search products
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Product Search")
    print("="*60)
    
    access_token = os.getenv('SALLA_ACCESS_TOKEN', 'your_token_here')
    if access_token == 'your_token_here':
        print("⚠️ Please set SALLA_ACCESS_TOKEN environment variable")
        return
    
    api = SallaAPITester(access_token)
    
    # Search terms to try
    search_terms = ['shirt', 'phone', 'book', 'shoes']
    
    for term in search_terms:
        print(f"\n🔍 Searching for: '{term}'")
        search_result = api.search_products(term, per_page=3)
        
        if search_result['success']:
            products = search_result['products']
            if products:
                print(f"   Found {len(products)} products:")
                for product in products:
                    print(f"   - {product.get('name', 'N/A')} (${product.get('price', 'N/A')})")
            else:
                print(f"   No products found for '{term}'")
        else:
            print(f"   ❌ Search failed: {search_result.get('error', 'Unknown error')}")
        
        # Break after first successful search to avoid too much output
        if search_result['success'] and search_result['products']:
            break

def example_pagination():
    """
    Example 4: Handle pagination
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Pagination Handling")
    print("="*60)
    
    access_token = os.getenv('SALLA_ACCESS_TOKEN', 'your_token_here')
    if access_token == 'your_token_here':
        print("⚠️ Please set SALLA_ACCESS_TOKEN environment variable")
        return
    
    api = SallaAPITester(access_token)
    
    # Get first page to check pagination info
    print("\nAnalyzing pagination...")
    result = api.get_products(page=1, per_page=5)
    
    if result['success']:
        pagination = result['pagination']
        total_products = pagination.get('total', 0)
        per_page = pagination.get('per_page', 5)
        total_pages = pagination.get('last_page', 1)
        current_page = pagination.get('current_page', 1)
        
        print(f"📊 Pagination Info:")
        print(f"   Total Products: {total_products}")
        print(f"   Products per Page: {per_page}")
        print(f"   Total Pages: {total_pages}")
        print(f"   Current Page: {current_page}")
        
        # Fetch a few pages if available
        max_pages_to_fetch = min(3, total_pages)
        all_products = []
        
        for page in range(1, max_pages_to_fetch + 1):
            print(f"\n📄 Fetching page {page}...")
            page_result = api.get_products(page=page, per_page=5)
            
            if page_result['success']:
                products = page_result['products']
                all_products.extend(products)
                print(f"   Got {len(products)} products from page {page}")
                
                # Show first product from each page
                if products:
                    first_product = products[0]
                    print(f"   First product: {first_product.get('name', 'N/A')}")
            else:
                print(f"   ❌ Failed to fetch page {page}")
        
        print(f"\n✅ Total products fetched: {len(all_products)}")
    else:
        print(f"❌ Failed to get pagination info: {result.get('error', 'Unknown error')}")

def example_error_handling():
    """
    Example 5: Error handling
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Error Handling")
    print("="*60)
    
    # Test with invalid token
    print("\n1. Testing with invalid token...")
    invalid_api = SallaAPITester('invalid_token_12345')
    result = invalid_api.test_connection()
    
    if not result['success']:
        print(f"✅ Correctly handled invalid token: {result.get('status_code', 'N/A')}")
    else:
        print("⚠️ Unexpected success with invalid token")
    
    # Test with invalid product ID
    access_token = os.getenv('SALLA_ACCESS_TOKEN')
    if access_token and access_token != 'your_token_here':
        print("\n2. Testing with invalid product ID...")
        api = SallaAPITester(access_token)
        result = api.get_product_by_id('invalid_product_id_99999')
        
        if not result['success']:
            print(f"✅ Correctly handled invalid product ID: {result.get('status_code', 'N/A')}")
        else:
            print("⚠️ Unexpected success with invalid product ID")
    
    print("\n3. Testing with invalid base URL...")
    invalid_url_api = SallaAPITester('test_token', base_url='https://invalid-url-12345.com')
    result = invalid_url_api.test_connection()
    
    if not result['success']:
        print(f"✅ Correctly handled invalid URL: Connection error detected")
    else:
        print("⚠️ Unexpected success with invalid URL")

def main():
    """
    Run all examples
    """
    print("🚀 Salla API Usage Examples")
    print("=" * 80)
    
    # Check if access token is available
    access_token = os.getenv('SALLA_ACCESS_TOKEN')
    if not access_token:
        print("\n⚠️ SALLA_ACCESS_TOKEN environment variable not set.")
        print("   Set it with: export SALLA_ACCESS_TOKEN='your_token_here'")
        print("   Some examples will be skipped.\n")
    
    try:
        # Run examples
        example_basic_usage()
        example_product_details()
        example_search_products()
        example_pagination()
        example_error_handling()
        
        print("\n" + "="*80)
        print("✅ All examples completed!")
        print("📝 Check 'salla_api_test.log' for detailed logs.")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Examples interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()