from odoo import models, fields, api
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class InventoryFeed(models.Model):
    _name = 'inventory.feed'
    _description = 'Inventory Feed from Omniful Webhook'
    _rec_name = 'display_name'
    _order = 'received_at desc'

    # Webhook metadata
    event_name = fields.Char(
        string='Event Name',
        help='Name of the webhook event'
    )
    
    received_at = fields.Datetime(
        string='Received At',
        default=fields.Datetime.now,
        help='When the webhook was received'
    )
    
    channel_id = fields.Many2one(
        'channel.omniful',
        string='Channel',
        help='Omniful channel this feed belongs to'
    )
    
    # Header summary fields
    total_lines = fields.Integer(
        string='Total Lines',
        compute='_compute_totals',
        store=True,
        help='Total number of inventory lines'
    )
    
    total_quantity = fields.Float(
        string='Total Quantity',
        compute='_compute_totals',
        store=True,
        help='Sum of all line quantities'
    )
    
    # Raw data storage
    raw_data = fields.Text(
        string='Raw Webhook Data',
        help='Complete raw data received from webhook'
    )
    
    # Processing status
    state = fields.Selection([
        ('received', 'Received'),
        ('processed', 'Processed'),
        ('error', 'Error')
    ], string='Status', default='received', help='Processing status of the feed')
    
    error_message = fields.Text(
        string='Error Message',
        help='Error message if processing failed'
    )
    
    # Computed fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # One2many relationship to line items
    line_ids = fields.One2many(
        'inventory.feed.line',
        'inventory_feed_id',
        string='Inventory Lines',
        help='Inventory feed line items'
    )
    
    @api.depends('line_ids')
    def _compute_totals(self):
        for record in self:
            record.total_lines = len(record.line_ids)
            record.total_quantity = sum(record.line_ids.mapped('quantity'))
    
    @api.depends('event_name', 'received_at', 'total_lines')
    def _compute_display_name(self):
        for record in self:
            if record.event_name:
                record.display_name = f"{record.event_name} - {record.total_lines} lines ({record.received_at})"
            else:
                record.display_name = f"Inventory Feed {record.id} - {record.total_lines} lines ({record.received_at})"
    
    @api.model
    def create_from_webhook_data(self, webhook_data):
        """Create inventory feed header and line records from webhook data"""
        try:
            if isinstance(webhook_data, str):
                webhook_data = json.loads(webhook_data)
            
            event_name = webhook_data.get('event_name', '')
            data_items = webhook_data.get('data', [])
            
            # Find channel from first item if available
            channel_id = False
            if data_items:
                first_item = data_items[0]
                channel = self.env['channel.omniful'].search([('hub_code', '=', first_item.get('hub_code', ''))], limit=1)
                if channel:
                    channel_id = channel.id
            
            # Create header record
            header_record = self.create({
                'event_name': event_name,
                'channel_id': channel_id,
                'raw_data': json.dumps(webhook_data, ensure_ascii=False, indent=4),
                'state': 'received'
            })
            
            # Create line records
            line_model = self.env['inventory.feed.line']
            created_lines = []
            
            for item in data_items:
                # Find channel for this specific item
                item_channel_id = channel_id
                if not item_channel_id:
                    channel = self.env['channel.omniful'].search([('hub_code', '=', item.get('hub_code', ''))], limit=1)
                    if channel:
                        item_channel_id = channel.id
                
                line_data = {
                    'inventory_feed_id': header_record.id,
                    'event_name': event_name,
                    'received_at': header_record.received_at,
                    'channel_id': item_channel_id,
                    'hub_code': item.get('hub_code', ''),
                    'seller_code': item.get('seller_code', ''),
                    'sku_code': item.get('sku_code', ''),
                    'quantity': item.get('quantity', 0.0),
                    'unlimited_quantity': item.get('unlimited_quantity', False),
                    'quantity_on_hand': item.get('quantity_on_hand', 0.0),
                    'quantity_reserved': item.get('quantity_reserved', 0.0),
                    'uom': item.get('uom', ''),
                    'updated_at': item.get('updated_at', ''),
                    'updated_at_epoch': item.get('updated_at_epoch', 0.0),
                    'raw_data': json.dumps(item, ensure_ascii=False, indent=4),
                    'state': 'received'
                }
                
                line_record = line_model.create(line_data)
                created_lines.append(line_record)
            
            _logger.info(f"Created inventory feed header {header_record.id} with {len(created_lines)} lines")
            return header_record
            
        except Exception as e:
            _logger.error(f"Error creating inventory feed from webhook data: {str(e)}")
            # Create error record
            error_record = self.create({
                'event_name': 'error',
                'raw_data': json.dumps(webhook_data, ensure_ascii=False, indent=4) if isinstance(webhook_data, dict) else str(webhook_data),
                'state': 'error',
                'error_message': str(e)
            })
            return error_record
    
    def action_reprocess(self):
        """Reprocess failed inventory feed"""
        for record in self:
            if record.state == 'error' and record.raw_data:
                try:
                    raw_data = json.loads(record.raw_data)
                    # Add your reprocessing logic here
                    record.state = 'processed'
                    record.error_message = False
                except Exception as e:
                    record.error_message = str(e)