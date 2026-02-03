from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class TempInventory(models.Model):
    _name = 'temp.inventory'
    _description = 'Temporary Inventory'
    _order = 'create_date desc'

    name = fields.Char(
        string='Name',
        required=True,
        help='Name of the temporary inventory record'
    )
    
    end_url = fields.Char(
        string='End URL',
        required=True,
        help='API endpoint URL for this inventory item'
    )
    
    content = fields.Text(
        string='Content',
        help='JSON content or data related to this inventory item'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide the record without deleting it'
    )
    
    create_date = fields.Datetime(
        string='Created On',
        readonly=True
    )
    
    write_date = fields.Datetime(
        string='Last Updated',
        readonly=True
    )
    
    @api.model
    def create(self, vals):
        """Override create to add any custom logic if needed"""
        return super(TempInventory, self).create(vals)
    
    def write(self, vals):
        """Override write to add any custom logic if needed"""
        return super(TempInventory, self).write(vals)
    
    def _get_access_token(self):
        """Retrieve access token using refresh token from global settings"""
        # Get configuration parameters
        ICPSudo = self.env['ir.config_parameter'].sudo()
        refresh_token = ICPSudo.get_param('omniful_integration.refresh_token', '')
        client_id = ICPSudo.get_param('omniful_integration.client_id', '')
        client_secret = ICPSudo.get_param('omniful_integration.client_secret', '')
        base_url = ICPSudo.get_param('omniful_integration.base_url', '')
        
        if not refresh_token or not client_id or not client_secret:
            raise UserWarning("Refresh token, client ID, and client secret must be configured in Omniful settings")
        
        if not base_url:
            raise UserWarning("Base URL not configured. Please check Omniful settings.")
        
        try:
            # Construct token endpoint URL
            token_url = f"{base_url.rstrip('/')}/sales-channel/public/v1/tenants/reports/token"
            
            # Prepare token request data
            token_data = {
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret
            }
            
            # Make token request
            _logger.info(f"Requesting access token from: {token_url}")
            response = requests.post(token_url, json=token_data, timeout=30)
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Check if response is successful
                if not token_response.get('is_success', False):
                    error_msg = f"Token request was not successful: {token_response}"
                    _logger.error(error_msg)
                    raise UserWarning(error_msg)
                
                # Extract data from response
                data = token_response.get('data', {})
                access_token = data.get('access_token')
                new_refresh_token = data.get('refresh_token')
                
                if not access_token:
                    raise UserWarning("Access token not found in response data")
                
                # Update the refresh token if a new one is provided
                if new_refresh_token and new_refresh_token != refresh_token:
                    ICPSudo.set_param('omniful_integration.refresh_token', new_refresh_token)
                    _logger.info("Updated refresh token with new value from API response")
                
                # Optionally store the access token for future use (if needed)
                ICPSudo.set_param('omniful_integration.access_token', access_token)
                
                _logger.info("Successfully retrieved new access token")
                return access_token
            else:
                error_msg = f"Token request failed with status {response.status_code}: {response.text}"
                _logger.error(error_msg)
                raise UserWarning(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during token request: {str(e)}"
            _logger.error(error_msg)
            raise UserWarning(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response from token endpoint: {str(e)}"
            _logger.error(error_msg)
            raise UserWarning(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during token retrieval: {str(e)}"
            _logger.error(error_msg)
            raise UserWarning(error_msg)
    
    def action_fetch_api_data(self):
        """Fetch data from API and populate content field"""
        for record in self:
            if not record.end_url:
                raise UserWarning("End URL is required to fetch data")
            
            try:
                # Get access token first
                access_token = record._get_access_token()
                
                # Get configuration parameters
                ICPSudo = self.env['ir.config_parameter'].sudo()
                base_url = ICPSudo.get_param('omniful_integration.base_url', '')
                
                if not base_url:
                    raise UserWarning("Base URL not configured. Please check Omniful settings.")
                
                # Construct full URL
                if record.end_url.startswith('http'):
                    full_url = record.end_url
                else:
                    full_url = f"{base_url.rstrip('/')}/{record.end_url.lstrip('/')}"
                
                # Prepare headers with the new access token
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                
                # Make API request
                _logger.info(f"Making API request to: {full_url}")
                response = requests.get(full_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    # Parse response and update content
                    api_data = response.json()
                    formatted_content = json.dumps(api_data, indent=2)
                    record.write({'content': formatted_content})
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Success',
                            'message': 'API data fetched successfully!',
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    error_msg = f"API request failed with status {response.status_code}: {response.text}"
                    _logger.error(error_msg)
                    raise UserWarning(error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Network error: {str(e)}"
                _logger.error(error_msg)
                raise UserWarning(error_msg)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON response: {str(e)}"
                _logger.error(error_msg)
                raise UserWarning(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                _logger.error(error_msg)
                raise UserWarning(error_msg)