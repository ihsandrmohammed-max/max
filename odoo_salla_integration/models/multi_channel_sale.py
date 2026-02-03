# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, timezone
import requests
import json
from urllib.parse import urlencode, urljoin
import random, string
from .sallaAPI import SallaApi
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

auth_url = "https://accounts.salla.sa/oauth2/auth"
token_url = "https://accounts.salla.sa/oauth2/token"


class MultiChannelSale(models.Model):
    _inherit = 'multi.channel.sale'

    salla_client_id = fields.Char(string='Client id')
    salla_client_secret = fields.Char(string='Secret key')
    salla_redirect_url = fields.Char(
        string='Callback-Url', default=lambda self: self.get_redirect_url())
    refresh_token = fields.Char(string='Refresh Toekn', tracking=True)
    access_token = fields.Char(string='Access Toekn', tracking=True)
    salla_token_expiry = fields.Datetime(tracking=True)
    salla_verification_key = fields.Char(string="Verification Key", copy=False, default=lambda self: self.get_verification_key())

    def get_verification_key(self): # Generate 16 characters random string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    def get_redirect_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return  urljoin(base_url, 'salla/authenticate')
    
    def salla_available_configs(self):
        return [
                # Webhooks Add from extension when implemented
                # 'webhook_available', 
                # 'create_order_webhook',
                # 'update_order_webhook',

                # base
                # 'child_store_config', # Child for existing channel

                # Import Crons
                'cron_available',
                'import_order_cron',
                'order_created_after',
                # 'order_updated_after',
                # 'import_product_cron',
                # 'product_created_after',
                # 'product_updated_after',
                # 'import_partner_cron',
                # 'partner_created_after',
                # 'partner_updated_after',
                'import_category_cron',

                # realtime export
                'sync_order_invoice',
                'sync_order_shipment',
                'sync_order_cancel',
            ]
        
    @api.constrains('salla_verification_key')
    def validate_vefication_key(self):
        key = self.salla_verification_key
        if len(key) < 8:
            raise UserError('The verification key should be minimum 8 characters long')
        channel = self.search([('channel','=','salla'),('salla_verification_key','=',key)])
        if len(channel) > 1:
            channel = channel - self
            raise UserError(f'The verification key [ {key} ] is already exists in other channel [ID: {channel.id}]')


    def write(self, vals):
        for record in self:
            if record.channel == "salla" and (vals.get('salla_client_id') or vals.get('salla_client_secret')):
                vals.update({'refresh_token': False})
                # self.write({'refresh_token': False})
        return super(MultiChannelSale, self).write(vals)

    def get_core_feature_compatible_channels(self):
        channels = super(MultiChannelSale,
                         self).get_core_feature_compatible_channels()
        channels.append('salla')
        return channels

    def get_channel(self):
        channels = super(MultiChannelSale, self).get_channel()
        channels.append(('salla', 'Salla'))
        return channels

    @api.model
    def get_info_urls(self):
        urls = super(MultiChannelSale,self).get_info_urls()
        urls.update(
            salla = {
                'blog' : '#',
                'store': '#',
            },
        )
        return urls

    def get_sallaApi(self, **kw):
        with SallaApi(self.salla_client_id, self.salla_client_secret, self.access_token, self.refresh_token, channel=self, **kw) as api:
            return api

    def connect_to_salla(self):
        scope = '''offline_access products.read_write'''
        data = {
            'client_id': self.salla_client_id,
            'scope': scope,
            'response_type': 'code',
            # 'approval_prompt':'auto',
            'state': self.salla_verification_key
        }
        url = '?'.join([auth_url, urlencode(data)])
        response = requests.post(url)
        if response.status_code in [200, 201]:
            return {
                'type': 'ir.actions.act_url',
                'target': 'self',
                'url': url
            }
        else:
            return self.display_message("<span class='text-danger'>Authentication failed, Please verify the added Client Keys and Redirect URI</p>")
            

    def create_salla_connection(self, kwargs):
        code = kwargs['code']
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = urlencode({
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.salla_client_id,
            'client_secret': self.salla_client_secret,
        })
        response = requests.post(token_url, data, headers=headers)
        if response.status_code in [200, 201]:
            res = response.json()
            refresh_token = res.get('refresh_token', '')
            access_token = res.get('access_token', '')
            return self.write({
                'state': 'validate',
                'refresh_token': refresh_token,
                'access_token': access_token,
                'salla_token_expiry': datetime.now(),
            })
        else:
            _logger.error(
                'Authentication failed, please verify the added keys in the channel')
            _logger.info(response.content)
        return False

    def get_user_info(self):  # Call the api to check the tokens: valid or not
        api = self.get_sallaApi()
        endpoint = "https://api.salla.dev/admin/v2/oauth2/user/info"
        res = api.salla_response(endpoint)
        if res:
            return True
        return False

    def connect_salla(self):
        """
        Real connection test to Salla API.
        Performs actual API call to validate access token and connection.
        
        Returns:
            tuple: (bool, str) - (success, message)
        """
        self.ensure_one()
        
        _logger.info("=" * 80)
        _logger.info("SALLA CONNECTION TEST - Starting")
        _logger.info("Channel ID: %s | Channel Name: %s", self.id, self.name)
        _logger.info("=" * 80)
        
        # Check if access token exists (required for API call)
        if not self.access_token:
            _logger.error("Connection test failed: Access token is missing")
            _logger.info("=" * 80)
            _logger.info("SALLA CONNECTION TEST - FAILED")
            _logger.info("=" * 80)
            return False, "<p class='text-danger'>Access token is missing. Please authenticate with Salla first.</p>"
        
        _logger.info("Access token exists - Proceeding with connection test")
        _logger.debug("Access token (masked): %s...%s", 
                     self.access_token[:10] if len(self.access_token) > 10 else self.access_token[:5],
                     self.access_token[-5:] if len(self.access_token) > 10 else "")
        
        if self.refresh_token:
            _logger.info("Refresh token exists - Available for token refresh if needed")
        else:
            _logger.warning("Refresh token is missing - Will not be able to auto-refresh if token expires")
        
        # Perform real API call to validate connection
        try:
            api = self.get_sallaApi()
            endpoint = "https://api.salla.dev/admin/v2/oauth2/user/info"
            
            headers = api.get_headers()
            
            # Log request details
            _logger.info("-" * 80)
            _logger.info("REQUEST DETAILS:")
            _logger.info("  Method: GET")
            _logger.info("  URL: %s", endpoint)
            _logger.info("  Headers:")
            for key, value in headers.items():
                if key.lower() == 'authorization':
                    # Mask token in logs
                    masked_value = value[:20] + "..." + value[-10:] if len(value) > 30 else "***MASKED***"
                    _logger.info("    %s: %s", key, masked_value)
                else:
                    _logger.info("    %s: %s", key, value)
            _logger.info("  Timeout: 15 seconds")
            _logger.info("-" * 80)
            
            response = requests.get(endpoint, headers=headers, timeout=15)
            
            # Log response details
            _logger.info("-" * 80)
            _logger.info("RESPONSE DETAILS:")
            _logger.info("  Status Code: %s", response.status_code)
            _logger.info("  Status Text: %s", response.reason)
            _logger.info("  Response Headers:")
            for key, value in response.headers.items():
                _logger.info("    %s: %s", key, value)
            
            # Log response body
            try:
                response_text = response.text
                _logger.info("  Response Body (raw): %s", response_text[:1000] if len(response_text) > 1000 else response_text)
                
                if response_text:
                    try:
                        response_json = response.json()
                        _logger.info("  Response Body (JSON formatted):")
                        _logger.info("    %s", json.dumps(response_json, indent=2, ensure_ascii=False)[:2000])
                    except:
                        _logger.info("  Response Body (not JSON): %s", response_text[:500])
                else:
                    _logger.info("  Response Body: (empty)")
            except Exception as e:
                _logger.warning("  Could not log response body: %r", e)
            
            _logger.info("-" * 80)
            
            # Handle successful response
            if response.status_code == 200:
                _logger.info("SUCCESS: HTTP 200 - Connection test passed")
                try:
                    data = response.json()
                    _logger.info("Response JSON parsed successfully")
                    _logger.debug("Full response data: %s", data)
                    
                    # Extract store/merchant name if available
                    store_name = ""
                    if isinstance(data, dict):
                        if 'data' in data:
                            store_data = data.get('data', {})
                            store_name = store_data.get('name', store_data.get('merchant_name', ''))
                            _logger.info("Store data extracted: %s", store_data)
                        else:
                            store_name = data.get('name', data.get('merchant_name', ''))
                    
                    success_msg = "<p class='text-success'>Connection successful! Token is valid and API is accessible.</p>"
                    if store_name:
                        success_msg += f"<p class='text-info'>Connected to store: {store_name}</p>"
                        _logger.info("Store name found: %s", store_name)
                    
                    self.state = 'validate'
                    _logger.info("Channel state updated to: validate")
                    _logger.info("=" * 80)
                    _logger.info("SALLA CONNECTION TEST - SUCCESS")
                    _logger.info("=" * 80)
                    return True, success_msg
                    
                except (ValueError, KeyError) as e:
                    # Response is 200 but JSON parsing failed
                    _logger.warning("Connection test returned 200 but JSON parsing failed: %r", e)
                    _logger.warning("Response text: %s", response.text[:500])
                    self.state = 'validate'
                    _logger.info("Channel state updated to: validate (despite JSON parsing error)")
                    _logger.info("=" * 80)
                    _logger.info("SALLA CONNECTION TEST - SUCCESS (with warning)")
                    _logger.info("=" * 80)
                    return True, "<p class='text-success'>Connection successful! Token is valid.</p>"
            
            # Handle unauthorized - token expired or invalid
            elif response.status_code == 401:
                _logger.warning("UNAUTHORIZED: HTTP 401 - Token expired or invalid")
                error_data = {}
                try:
                    error_data = response.json()
                    _logger.info("Error response JSON: %s", error_data)
                except:
                    _logger.warning("Could not parse error response as JSON")
                    _logger.info("Error response text: %s", response.text[:500])
                
                error_message = error_data.get('message', 'Unauthorized')
                error_type = error_data.get('type', '')
                _logger.warning("Error message: %s | Error type: %s", error_message, error_type)
                
                # Try to refresh token if refresh_token exists
                if self.refresh_token:
                    _logger.info("Attempting to refresh access token...")
                    refresh_success, refresh_msg = self._refresh_salla_token()
                    if refresh_success:
                        _logger.info("Token refresh successful, retrying connection test...")
                        # Retry connection test with new token
                        return self.connect_salla()
                    else:
                        _logger.error("Token refresh failed: %s", refresh_msg)
                        _logger.info("=" * 80)
                        _logger.info("SALLA CONNECTION TEST - FAILED")
                        _logger.info("=" * 80)
                        return False, f"<p class='text-danger'>Token expired and refresh failed: {refresh_msg}</p>"
                else:
                    _logger.error("No refresh token available, cannot refresh expired token")
                    _logger.error("Access token expired or invalid. Refresh token is missing.")
                    _logger.info("=" * 80)
                    _logger.info("SALLA CONNECTION TEST - FAILED")
                    _logger.info("=" * 80)
                    return False, "<p class='text-danger'>Access token expired or invalid. Refresh token is missing. Please re-authenticate with Salla.</p>"
            
            # Handle forbidden - token revoked or insufficient permissions
            elif response.status_code == 403:
                _logger.error("FORBIDDEN: HTTP 403 - Token revoked or insufficient permissions")
                try:
                    error_data = response.json()
                    _logger.error("Error response: %s", error_data)
                except:
                    _logger.error("Error response text: %s", response.text[:500])
                _logger.info("=" * 80)
                _logger.info("SALLA CONNECTION TEST - FAILED")
                _logger.info("=" * 80)
                return False, "<p class='text-danger'>Access forbidden. Token may have been revoked or you lack required permissions.</p>"
            
            # Handle other HTTP errors
            elif response.status_code >= 500:
                _logger.error("SERVER ERROR: HTTP %s - Salla API server error", response.status_code)
                try:
                    error_data = response.json()
                    _logger.error("Error response: %s", error_data)
                except:
                    _logger.error("Error response text: %s", response.text[:500])
                _logger.info("=" * 80)
                _logger.info("SALLA CONNECTION TEST - FAILED")
                _logger.info("=" * 80)
                return False, f"<p class='text-danger'>Salla API server error (HTTP {response.status_code}). Please try again later.</p>"
            
            else:
                _logger.warning("UNEXPECTED STATUS: HTTP %s", response.status_code)
                error_msg = f"Connection failed with HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    _logger.warning("Error response: %s", error_data)
                    if 'message' in error_data:
                        error_msg = error_data.get('message', error_msg)
                except:
                    _logger.warning("Error response text: %s", response.text[:500])
                _logger.info("=" * 80)
                _logger.info("SALLA CONNECTION TEST - FAILED")
                _logger.info("=" * 80)
                return False, f"<p class='text-danger'>{error_msg}</p>"
        
        except requests.exceptions.Timeout:
            _logger.error("TIMEOUT: Connection timeout after 15 seconds")
            _logger.error("Endpoint: %s", endpoint)
            _logger.info("=" * 80)
            _logger.info("SALLA CONNECTION TEST - FAILED (Timeout)")
            _logger.info("=" * 80)
            return False, "<p class='text-danger'>Connection timeout. Salla API is unreachable or taking too long to respond.</p>"
        
        except requests.exceptions.ConnectionError as e:
            _logger.error("CONNECTION ERROR: Network error - %r", e)
            _logger.error("Endpoint: %s", endpoint)
            _logger.info("=" * 80)
            _logger.info("SALLA CONNECTION TEST - FAILED (Connection Error)")
            _logger.info("=" * 80)
            return False, "<p class='text-danger'>Network error. Cannot reach Salla API. Please check your internet connection.</p>"
        
        except Exception as e:
            _logger.error("UNEXPECTED ERROR: %r", e, exc_info=True)
            _logger.error("Exception type: %s", type(e).__name__)
            _logger.info("=" * 80)
            _logger.info("SALLA CONNECTION TEST - FAILED (Unexpected Error)")
            _logger.info("=" * 80)
            return False, f"<p class='text-danger'>Unexpected error: {str(e)}</p>"
    
    def _refresh_salla_token(self):
        """
        Refresh Salla access token using refresh_token.
        
        Returns:
            tuple: (bool, str) - (success, message)
        """
        _logger.info("=" * 80)
        _logger.info("SALLA TOKEN REFRESH - Starting")
        _logger.info("Channel ID: %s | Channel Name: %s", self.id, self.name)
        _logger.info("=" * 80)
        
        if not self.refresh_token:
            _logger.error("Token refresh failed: No refresh token available")
            _logger.info("=" * 80)
            _logger.info("SALLA TOKEN REFRESH - FAILED")
            _logger.info("=" * 80)
            return False, "No refresh token available"
        
        if not self.salla_client_id or not self.salla_client_secret:
            _logger.error("Token refresh failed: Client credentials missing")
            _logger.info("=" * 80)
            _logger.info("SALLA TOKEN REFRESH - FAILED")
            _logger.info("=" * 80)
            return False, "Client credentials missing"
        
        _logger.info("Refresh token exists: %s...%s", 
                     self.refresh_token[:10] if len(self.refresh_token) > 10 else self.refresh_token[:5],
                     self.refresh_token[-5:] if len(self.refresh_token) > 10 else "")
        _logger.info("Client ID: %s", self.salla_client_id)
        _logger.debug("Client Secret (masked): %s...%s", 
                     self.salla_client_secret[:5] if len(self.salla_client_secret) > 5 else "***",
                     self.salla_client_secret[-3:] if len(self.salla_client_secret) > 5 else "")
        
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            data = urlencode({
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.salla_client_id,
                'client_secret': self.salla_client_secret,
            })
            
            # Log request details
            _logger.info("-" * 80)
            _logger.info("TOKEN REFRESH REQUEST DETAILS:")
            _logger.info("  Method: POST")
            _logger.info("  URL: %s", token_url)
            _logger.info("  Headers:")
            for key, value in headers.items():
                _logger.info("    %s: %s", key, value)
            _logger.info("  Request Data (form-urlencoded):")
            _logger.info("    grant_type: refresh_token")
            _logger.info("    refresh_token: %s...%s", 
                        self.refresh_token[:10] if len(self.refresh_token) > 10 else self.refresh_token[:5],
                        self.refresh_token[-5:] if len(self.refresh_token) > 10 else "")
            _logger.info("    client_id: %s", self.salla_client_id)
            _logger.info("    client_secret: %s...%s", 
                        self.salla_client_secret[:5] if len(self.salla_client_secret) > 5 else "***",
                        self.salla_client_secret[-3:] if len(self.salla_client_secret) > 5 else "")
            _logger.info("  Timeout: 15 seconds")
            _logger.info("-" * 80)
            
            response = requests.post(token_url, data=data, headers=headers, timeout=15)
            
            # Log response details
            _logger.info("-" * 80)
            _logger.info("TOKEN REFRESH RESPONSE DETAILS:")
            _logger.info("  Status Code: %s", response.status_code)
            _logger.info("  Status Text: %s", response.reason)
            _logger.info("  Response Headers:")
            for key, value in response.headers.items():
                _logger.info("    %s: %s", key, value)
            
            # Log response body (mask sensitive tokens)
            try:
                response_text = response.text
                _logger.info("  Response Body (raw): %s", response_text[:1000] if len(response_text) > 1000 else response_text)
                
                if response_text:
                    try:
                        response_json = response.json()
                        # Mask tokens in JSON log
                        masked_json = response_json.copy()
                        if 'access_token' in masked_json:
                            token = masked_json['access_token']
                            masked_json['access_token'] = token[:10] + "..." + token[-5:] if len(token) > 15 else "***MASKED***"
                        if 'refresh_token' in masked_json:
                            token = masked_json['refresh_token']
                            masked_json['refresh_token'] = token[:10] + "..." + token[-5:] if len(token) > 15 else "***MASKED***"
                        
                        _logger.info("  Response Body (JSON formatted, tokens masked):")
                        _logger.info("    %s", json.dumps(masked_json, indent=2, ensure_ascii=False)[:2000])
                    except:
                        _logger.info("  Response Body (not JSON): %s", response_text[:500])
                else:
                    _logger.info("  Response Body: (empty)")
            except Exception as e:
                _logger.warning("  Could not log response body: %r", e)
            
            _logger.info("-" * 80)
            
            if response.status_code in [200, 201]:
                _logger.info("SUCCESS: HTTP %s - Token refresh successful", response.status_code)
                res = response.json()
                new_access_token = res.get('access_token')
                new_refresh_token = res.get('refresh_token', self.refresh_token)  # Keep old if not provided
                
                if not new_access_token:
                    _logger.error("No access token in refresh response")
                    _logger.info("=" * 80)
                    _logger.info("SALLA TOKEN REFRESH - FAILED")
                    _logger.info("=" * 80)
                    return False, "No access token in refresh response"
                
                _logger.info("New access token received: %s...%s", 
                            new_access_token[:10] if len(new_access_token) > 10 else new_access_token[:5],
                            new_access_token[-5:] if len(new_access_token) > 10 else "")
                if new_refresh_token != self.refresh_token:
                    _logger.info("New refresh token received: %s...%s", 
                                new_refresh_token[:10] if len(new_refresh_token) > 10 else new_refresh_token[:5],
                                new_refresh_token[-5:] if len(new_refresh_token) > 10 else "")
                else:
                    _logger.info("Using existing refresh token (not replaced)")
                
                self.write({
                    'access_token': new_access_token,
                    'refresh_token': new_refresh_token,
                    'salla_token_expiry': datetime.now(),
                })
                
                _logger.info("Tokens updated in database")
                _logger.info("Token expiry set to: %s", datetime.now())
                _logger.info("=" * 80)
                _logger.info("SALLA TOKEN REFRESH - SUCCESS")
                _logger.info("=" * 80)
                return True, "Token refreshed successfully"
            
            elif response.status_code == 401:
                # Refresh token is invalid or expired
                _logger.error("UNAUTHORIZED: HTTP 401 - Refresh token expired or invalid")
                try:
                    error_data = response.json()
                    _logger.error("Error response: %s", error_data)
                except:
                    _logger.error("Error response text: %s", response.text[:500])
                _logger.info("=" * 80)
                _logger.info("SALLA TOKEN REFRESH - FAILED")
                _logger.info("=" * 80)
                return False, "Refresh token expired or invalid. Please re-authenticate."
            
            else:
                _logger.error("FAILED: HTTP %s - Token refresh failed", response.status_code)
                error_msg = f"Token refresh failed with HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    _logger.error("Error response: %s", error_data)
                    if 'message' in error_data:
                        error_msg = error_data.get('message', error_msg)
                except:
                    _logger.error("Error response text: %s", response.text[:500])
                _logger.info("=" * 80)
                _logger.info("SALLA TOKEN REFRESH - FAILED")
                _logger.info("=" * 80)
                return False, error_msg
        
        except requests.exceptions.Timeout:
            _logger.error("TIMEOUT: Token refresh timeout after 15 seconds")
            _logger.error("URL: %s", token_url)
            _logger.info("=" * 80)
            _logger.info("SALLA TOKEN REFRESH - FAILED (Timeout)")
            _logger.info("=" * 80)
            return False, "Token refresh timeout"
        
        except requests.exceptions.ConnectionError as e:
            _logger.error("CONNECTION ERROR: Network error during token refresh - %r", e)
            _logger.error("URL: %s", token_url)
            _logger.info("=" * 80)
            _logger.info("SALLA TOKEN REFRESH - FAILED (Connection Error)")
            _logger.info("=" * 80)
            return False, "Network error during token refresh"
        
        except Exception as e:
            _logger.error("UNEXPECTED ERROR: Error refreshing Salla token: %r", e, exc_info=True)
            _logger.error("Exception type: %s", type(e).__name__)
            _logger.info("=" * 80)
            _logger.info("SALLA TOKEN REFRESH - FAILED (Unexpected Error)")
            _logger.info("=" * 80)
            return False, f"Token refresh error: {str(e)}"

    def old_getAccessToken(self):
        status = True
        if not self.refresh_token:  # Connection first time
            status = False
            return status, "<p class='text-warning'>No Connection exists with salla, please create connection first</p>"
        if self._context.get('operation') and self.salla_token_expiry:
            diff = datetime.now() - self.salla_token_expiry
            token_time = float(diff.total_seconds()/(60*60))
            if token_time < 7:  # condition for 7 days, Token expires in 14 days
                return status, 'Token is not expired yet'
        message = "<p class='text-danger'>Error: something went wrong in getting tokens</p>"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer ' + self.access_token,
        }
        data = urlencode({
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.salla_client_id,
            'client_secret': self.salla_client_secret,
        })
        response = requests.post(token_url, data=data, headers=headers)
        if response.status_code in [200, 201]:
            res = response.json()
            message = "<p class='text-success'>Connection refreshed successfully with Salla</p>"
            self.write({
                'state': 'validate',
                'refresh_token': res.get('refresh_token', ''),
                'access_token': res.get('access_token', ''),
                'salla_token_expiry': datetime.now(),
            })
        else:
            status = False
            if not self._context.get('operation'):
                self.state = "error"
            _logger.error(response.content)
            message += '<br/>'+ str(response.content)
        return status, message

    def getAccessToken(self):
        """
        Only checks if Salla token is valid.
        Does NOT refresh or call Salla API.
        """

        if not self.access_token or not self.refresh_token:
            return False, "<p class='text-warning'>No connection exists with Salla</p>"

        if not self.salla_token_expiry:
            return False, "<p class='text-warning'>Token expiry date not found</p>"

        # Access token is valid for 14 days
        expiry_date = self.salla_token_expiry + timedelta(days=14)

        # We consider it expired 1 day before for safety
        safe_expiry = expiry_date - timedelta(days=1)

        if datetime.now() >= safe_expiry:
            return False, "<p class='text-warning'>Salla token expired, waiting for refresh</p>"

        return True, "Token is valid"



    def cron_refresh_salla_token(self, salla_id):
        """
        Called only by Odoo cron
        salla_id = id of Salla connection record
        """

        salla = self.browse(salla_id)

        if not salla.exists():
            _logger.error("Salla record not found: %s", salla_id)
            return False

        if not salla.refresh_token:
            _logger.error("No refresh token for Salla ID %s", salla_id)
            return False

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = urlencode({
            'grant_type': 'refresh_token',
            'refresh_token': salla.refresh_token,
            'client_id': salla.salla_client_id,
            'client_secret': salla.salla_client_secret,
        })

        try:
            response = requests.post(token_url, data=data, headers=headers, timeout=20)
        except Exception:
            _logger.exception("Salla refresh request failed for ID %s", salla_id)
            return False

        if response.status_code not in (200, 201):
            _logger.error("Salla refresh failed for ID %s: %s", salla_id, response.text)
            salla.state = "error"
            return False

        res = response.json()

        salla.write({
            'state': 'validate',
            'access_token': res.get('access_token'),
            'refresh_token': res.get('refresh_token'),  # IMPORTANT: replace old one
            'salla_token_expiry': datetime.now(),
        })

        _logger.info("Salla token refreshed for ID %s", salla_id)
        return True




    def import_salla(self, object, **kw): # if refresh token expired, channel state will be error
        self.with_context(operation=True).getAccessToken()
        with SallaApi(self.salla_client_id, self.salla_client_secret, self.access_token, self.refresh_token, channel=self, **kw) as api:
            if object == 'res.partner':
                data_list, kw = api.get_partners(**kw)
            elif object == 'sale.order':
                data_list, kw = api.get_orders(**kw)
            elif object == "product.template":
                data_list, kw = api.get_products(**kw)
            elif object == "product.category":
                data_list, kw = api.get_categories(**kw)
                kw.update({'page_size': float('inf')})  # no limit for category
            elif object == "delivery.carrier":
                data_list, kw = api.get_shippings(**kw)
            else:
                data_list = []
                kw = {'message': 'Selected Channel does not allow this.'}
            if object in ['res.partner', 'product.template', 'sale.order']:
                kw.update({'page_size': kw.get('page_size') +
                           1 if not kw.get('next_url') else kw.get('page_size')})
            if object in ['sale.order']:
                if data_list and (kw.get('from_cron') and not kw.get('import_order_date_updated')):
                    self.import_order_date = datetime.strptime(
                        data_list[0].get('date_order'), "%Y-%m-%d %H:%M:%S.%f")
                    kw.update({'import_order_date_updated': True})
            return data_list, kw

    def export_salla(self, record, **kw): # if token expired, channel will be in error
        self.with_context(operation=True).getAccessToken()
        with SallaApi(self.salla_client_id, self.salla_client_secret, self.access_token, self.refresh_token, channel=self, **kw) as api:
            if record._name == 'product.category':
                return api.post_category(record, record.id)
            elif record._name == 'product.template':
                res, object = api.post_product(record)
                return res, object
            else:
                raise NotImplementedError

    def update_salla(self, record, get_remote_id):
        try:
            self.with_context(operation=True).getAccessToken()
            channel = self.with_context(operation='update')
            with SallaApi(self.salla_client_id, self.salla_client_secret, self.access_token, self.refresh_token, channel=channel) as api:
                data_list = [False, {}]
                remote_id = get_remote_id(record)
                if record._name == 'product.template':
                    data_list = api.update_salla_product(record, remote_id)
                elif record._name == "product.category":
                    data_list = api.update_category(
                        record, record.id, remote_id)
        except Exception as e:
            _logger.error('Error: occurred %r', e, exc_info=True)
        return data_list

    def sync_quantity_salla(self, mapping, qty):
        with SallaApi(self.salla_client_id, self.salla_client_secret, self.access_token, self.refresh_token, channel=self) as api:
            if mapping.store_product_id == mapping.store_variant_id or mapping.store_variant_id == "No Variants":
                typ = "product"
                product_id = mapping.store_product_id
            else:
                typ = "variant"
                product_id = mapping.store_variant_id
            return api.set_quantity(product_id, qty, typ)

    # ++++++++++++++++++++++CORE METHODS++++++++++++++++++++++++
    def salla_post_do_transfer(self, stock_picking, mapping_ids, result):
        self.update_salla_order_status('delivered', mapping_ids.store_order_id)

    def salla_post_confirm_paid(self, invoice, mapping_ids, result):
        self.update_salla_order_status('completed', mapping_ids.store_order_id)

    def salla_post_cancel_order(self, sale_order, mapping_ids, result):
        self.update_salla_order_status('canceled', mapping_ids.store_order_id)

    def update_salla_order_status(self, slug, remote_id):
        "under_review, payment_pending , canceled , delivered, completed , shipped , restored , in_progress, delivering, restoring"
        try:
            order_status = self.order_state_ids.filtered(
                lambda order_state_id: order_state_id.channel_state == slug
            )
            if order_status:
                api = self.get_sallaApi()
                endpoint = api.import_url + f"orders/{remote_id}/status"
                data = {'slug': slug}
                if slug == 'completed' and order_status[0].odoo_set_invoice_state != 'paid':
                    _logger.error(
                        'Error: set invoice state in order state mapping for \'completed\' channel order state should be paid in channel configuration')
                else:
                    response = api.salla_response(
                        endpoint, method="POST", data=data)
            else:
                _logger.warning(
                    'Error: Can not update order state, please create order state  mapping for [{}] status in channel configuration'.format(slug))
        except Exception as e:
            _logger.error(
                'Exception occurred during realtime status sync to: {}'.format(slug), exc_info=True)


# ==================== Import Crons ==============================

    def salla_import_order_cron(self):  # Cron implemented
        _logger.info("+++++++++++Import Order Cron Started++++++++++++")
        kw = dict(
            object="sale.order",
            salla_from_date=self.import_order_date,
            salla_to_date=datetime.now(timezone.utc),
            from_cron=True
        )
        if self.import_order_date:
            kw.update({'filter_type': 'date'})
        self.env["import.operation"].create({
            "channel_id": self.id,
        }).import_with_filter(**kw)

    def salla_import_category_cron(self):  # Cron implemented
        _logger.info("+++++++++++Import Category Cron Started++++++++++++")
        kw = dict(
            object="product.category",
            from_cron=True,
        )
        self.env["import.operation"].create({
            "channel_id": self.id,
        }).import_with_filter(**kw)

    def salla_import_product_cron(self):
        _logger.info(
            "+++++ Import Product Cron is not supported in Salla Connector ++++++")

    def salla_import_partner_cron(self):
        _logger.info(
            "+++++ Import Partner Cron is not supported in Salla Connector ++++++")
