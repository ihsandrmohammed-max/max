# -*- coding: utf-8 -*-

import requests
from odoo import models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MultiChannelSale(models.Model):
    _inherit = 'multi.channel.sale'

    def sync_salla_order_statuses(self):
        """
        Synchronize order statuses from Salla API.
        Fetches statuses, creates or updates records, and resolves hierarchy.
        """
        self.ensure_one()

        # Validate channel
        if self.channel != 'salla':
            raise UserError(_('This action is only available for Salla channels.'))

        # Validate access token
        if not self.access_token:
            raise UserError(_('Access token is not configured. Please configure the Salla connection first.'))

        # API endpoint
        url = 'https://api.salla.dev/admin/v2/orders/statuses'

        # Prepare headers
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        try:
            # Make API request
            _logger.info('Fetching Salla order statuses from: %s', url)
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Validate response structure
            if not isinstance(data, dict) or 'data' not in data:
                raise UserError(_('Invalid response format from Salla API.'))

            statuses_data = data.get('data', [])

            if not statuses_data:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sync Completed'),
                        'message': _('No order statuses found to sync.'),
                        'type': 'info',
                        'sticky': False,
                    }
                }

            # Process statuses in two passes:
            # Pass 1: Create/update all statuses without resolving parent relationships
            # Pass 2: Resolve parent relationships

            status_mapping = {}  # Maps salla_status_id to record

            _logger.info('Processing %d order statuses...', len(statuses_data))

            # Pass 1: Create/update records
            for status_data in statuses_data:
                salla_status_id = status_data.get('id')
                if not salla_status_id:
                    _logger.warning('Skipping status with missing ID: %s', status_data)
                    continue

                # Prepare values
                original_data = status_data.get('original', {})
                parent_data = status_data.get('parent')

                vals = {
                    'salla_status_id': salla_status_id,
                    'name': status_data.get('name', ''),
                    'type': status_data.get('type', ''),
                    'slug': status_data.get('slug') or '',
                    'sort': status_data.get('sort', 0),
                    'message': status_data.get('message', ''),
                    'icon': status_data.get('icon', ''),
                    'is_active': status_data.get('is_active', True),
                    'original_id': original_data.get('id') if original_data else False,
                    'original_name': original_data.get('name', '') if original_data else '',
                    'parent_salla_id': parent_data.get('id') if parent_data else False,
                    'channel_id': self.id,
                }

                # Search for existing record (using sudo for admin access)
                existing = self.env['salla.order.status'].sudo().search([
                    ('salla_status_id', '=', salla_status_id)
                ], limit=1)

                if existing:
                    # Update existing record
                    existing.write(vals)
                    status_mapping[salla_status_id] = existing
                    _logger.info('Updated status: %s (ID: %s)', existing.name, salla_status_id)
                else:
                    # Create new record
                    new_record = self.env['salla.order.status'].sudo().create(vals)
                    status_mapping[salla_status_id] = new_record
                    _logger.info('Created status: %s (ID: %s)', new_record.name, salla_status_id)

            # Pass 2: Resolve parent relationships
            _logger.info('Resolving parent relationships...')
            for status_data in statuses_data:
                salla_status_id = status_data.get('id')
                parent_data = status_data.get('parent')

                if not salla_status_id or salla_status_id not in status_mapping:
                    continue

                current_record = status_mapping[salla_status_id]

                if parent_data and parent_data.get('id'):
                    parent_salla_id = parent_data.get('id')
                    if parent_salla_id in status_mapping:
                        # Link to parent
                        current_record.parent_id = status_mapping[parent_salla_id].id
                        _logger.info('Linked %s to parent %s', current_record.name, status_mapping[parent_salla_id].name)
                    else:
                        # Parent not found in current sync, clear parent reference
                        current_record.parent_id = False
                        _logger.warning('Parent status %s not found for status %s', parent_salla_id, salla_status_id)
                else:
                    # No parent, clear reference
                    current_record.parent_id = False

            # Commit changes
            self.env.cr.commit()

            # Return success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Completed'),
                    'message': _('Successfully synchronized %d order statuses from Salla.') % len(statuses_data),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except requests.exceptions.RequestException as e:
            _logger.error('Error fetching Salla order statuses: %s', str(e))
            raise UserError(_('Failed to fetch order statuses from Salla API: %s') % str(e))
        except Exception as e:
            _logger.error('Unexpected error during Salla order status sync: %s', str(e), exc_info=True)
            raise UserError(_('An error occurred during synchronization: %s') % str(e))
