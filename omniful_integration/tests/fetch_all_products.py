#!/usr/bin/env python3
"""
Salla Platform - Fetch All Products Script
Script to fetch all products from Salla platform and save to JSON file
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
        logging.FileHandler('salla_fetch_all.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
_logger = logging.getLogger(__name__)

class SallaProductFetcher:
    """
    Salla API Client for fetching all products
    """
    
    def __init__(self, access_token, base_url="https://api.salla.dev"):
        """
        Initialize Salla API fetcher
        
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
        
    def get_products_page(self, page=1, per_page=50):
        """
        Get products from a specific page
        
        Args:
            page (int): Page number
            per_page (int): Items per page (max 50)
            
        Returns:
            dict: Products data and pagination info
        """
        try:
            url = f"{self.base_url}/admin/v2/products"
            
            params = {
                'page': page,
                'per_page': min(per_page, 50)  # Salla max is 50
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'products': data.get('data', []),
                    'pagination': data.get('pagination', {})
                }
            else:
                _logger.error(f"❌ Failed to get products page {page}. Status: {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"❌ Request failed for page {page}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def fetch_all_products(self, filename=None):
        """
        Fetch all products from Salla store with pagination
        
        Args:
            filename (str): Custom filename for JSON file
            
        Returns:
            dict: Result with success status and file info
        """
        try:
            all_products = []
            page = 1
            per_page = 50  # Maximum allowed by Salla API
            total_pages = None
            total_count = 0
            
            _logger.info("🚀 Starting to fetch all products from Salla...")
            
            while True:
                _logger.info(f"📄 Fetching page {page}...")
                
                result = self.get_products_page(page=page, per_page=per_page)
                
                if not result.get('success'):
                    _logger.error(f"❌ Failed to fetch page {page}: {result.get('error')}")
                    if page == 1:  # If first page fails, return error
                        return result
                    else:  # If later page fails, continue with what we have
                        break
                
                products = result.get('products', [])
                pagination = result.get('pagination', {})
                
                if not products:
                    _logger.info("✅ No more products found")
                    break
                
                all_products.extend(products)
                
                # Get pagination info from first successful request
                if total_pages is None:
                    total_pages = pagination.get('last_page', 1)
                    total_count = pagination.get('total', 0)
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
            
            _logger.info(f"🎉 Successfully fetched {len(all_products)} products!")
            
            # Prepare the complete data structure
            complete_data = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_products': len(all_products),
                    'total_pages': total_pages or page,
                    'api_base_url': self.base_url,
                    'fetch_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'script_version': '1.0'
                },
                'products': all_products
            }
            
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'salla_all_products_{timestamp}.json'
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Save to file in the same directory as the script
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, ensure_ascii=False, indent=2)
            
            file_size = os.path.getsize(filepath)
            _logger.info(f"💾 All products saved to: {filepath}")
            _logger.info(f"📁 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            return {
                'success': True,
                'total_products': len(all_products),
                'filepath': filepath,
                'file_size': file_size,
                'metadata': complete_data['metadata']
            }
            
        except Exception as e:
            _logger.error(f"❌ Error fetching all products: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def print_summary(self, products, limit=10):
        """
        Print a summary of products
        
        Args:
            products (list): List of products
            limit (int): Number of products to show
        """
        if not products:
            print("\n❌ No products to display")
            return
        
        print(f"\n📋 Showing {min(len(products), limit)} of {len(products)} products:")
        print("=" * 80)
        
        for i, product in enumerate(products[:limit], 1):
            print(f"\n{i}. {product.get('name', 'N/A')}")
            print(f"   ID: {product.get('id', 'N/A')}")
            print(f"   SKU: {product.get('sku', 'N/A')}")
            print(f"   Price: {product.get('price', {}).get('amount', 'N/A')} {product.get('price', {}).get('currency', '')}")
            print(f"   Status: {product.get('status', 'N/A')}")
            print(f"   Stock: {product.get('quantity', 'N/A')}")
        
        if len(products) > limit:
            print(f"\n... and {len(products) - limit} more products")
        
        print("=" * 80)

def main():
    """
    Main function to fetch all products
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch all products from Salla store')
    parser.add_argument('--token', '-t', help='Salla access token')
    parser.add_argument('--filename', '-f', help='Custom filename for JSON file')
    parser.add_argument('--auto', '-a', action='store_true', help='Run automatically without confirmation')
    
    args = parser.parse_args()
    
    print("🚀 Salla Platform - Fetch All Products")
    print("=" * 50)
    
    # Get access token
    access_token = args.token or os.getenv('SALLA_ACCESS_TOKEN')
    
    if not access_token:
        try:
            access_token = input("Enter your Salla access token: ").strip()
        except EOFError:
            access_token = ""
    
    if not access_token:
        print("❌ Access token is required!")
        sys.exit(1)
    
    # Get custom filename
    filename = args.filename
    if not filename:
        try:
            custom_filename = input("Enter filename for JSON file (or press Enter for auto-generated): ").strip()
            filename = custom_filename if custom_filename else None
        except EOFError:
            filename = None
    
    # Initialize fetcher
    fetcher = SallaProductFetcher(access_token)
    
    # Warning and confirmation
    if not args.auto:
        print("\n⚠️ This will fetch ALL products from your Salla store.")
        print("⚠️ This may take several minutes depending on the number of products.")
        
        try:
            confirm = input("\nDo you want to continue? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ Operation cancelled.")
                sys.exit(0)
        except EOFError:
            print("❌ Operation cancelled (no input).")
            sys.exit(0)
    
    # Fetch all products
    print("\n🚀 Starting fetch process...")
    result = fetcher.fetch_all_products(filename=filename)
    
    if result.get('success'):
        total_products = result.get('total_products', 0)
        filepath = result.get('filepath')
        file_size = result.get('file_size', 0)
        
        print(f"\n🎉 SUCCESS! Fetched {total_products:,} products")
        print(f"📁 Saved to: {filepath}")
        print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
        # Ask if user wants to see a preview
        preview = input("\nShow preview of first 10 products? (y/N): ").strip().lower()
        if preview in ['y', 'yes']:
            # Load and show preview
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    products = data.get('products', [])
                    fetcher.print_summary(products, limit=10)
            except Exception as e:
                print(f"❌ Error loading preview: {e}")
        
    else:
        print(f"\n❌ FAILED: {result.get('error')}")
        sys.exit(1)
    
    print(f"\n✅ Process completed! Check 'salla_fetch_all.log' for detailed logs.")

if __name__ == "__main__":
    main()