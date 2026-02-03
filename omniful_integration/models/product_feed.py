from odoo import models, fields, api
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class ProductFeed(models.Model):
    _name = 'product_omniful.feed'
    _description = 'Product Feed from Omniful Webhook'
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
    
    # Product data fields
    product_id = fields.Char(
        string='Product ID',
        help='Unique product identifier'
    )
    
    sku_code = fields.Char(
        string='SKU Code',
        help='Product SKU code'
    )
    
    product_name = fields.Char(
        string='Product Name',
        help='Product display name'
    )
    
    description = fields.Text(
        string='Description',
        help='Product description'
    )
    
    category = fields.Char(
        string='Category',
        help='Product category'
    )
    
    brand = fields.Char(
        string='Brand',
        help='Product brand'
    )
    
    price = fields.Float(
        string='Price',
        help='Product price'
    )
    
    cost = fields.Float(
        string='Cost',
        help='Product cost'
    )
    
    weight = fields.Float(
        string='Weight',
        help='Product weight'
    )
    
    dimensions = fields.Char(
        string='Dimensions',
        help='Product dimensions'
    )
    
    status = fields.Char(
        string='Product Status',
        help='Product status (active, inactive, etc.)'
    )
    
    # System fields
    raw_data = fields.Text(
        string='Raw Webhook Data',
        help='Complete raw data received from webhook'
    )
    
    state = fields.Selection([
        ('received', 'Received'),
        ('processed', 'Processed'),
        ('error', 'Error')
    ], string='Status', default='received', help='Processing status of the feed')
    
    error_message = fields.Text(
        string='Error Message',
        help='Error message if processing failed'
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('sku_code', 'product_name', 'received_at')
    def _compute_display_name(self):
        for record in self:
            if record.sku_code and record.product_name:
                record.display_name = f"{record.sku_code} - {record.product_name}"
            elif record.sku_code:
                record.display_name = f"SKU: {record.sku_code}"
            else:
                record.display_name = f"Product Feed - {record.received_at}"
    
    @api.model
    def create_from_webhook_data(self, webhook_data):
        """Create product feed record from webhook data"""
        try:
            data = webhook_data.get('data', {})
            if isinstance(data, list) and data:
                data = data[0]
            
            # Find associated channel
            channel_id = False
            hub_code = data.get('hub_code')
            if hub_code:
                channel = self.env['channel.omniful'].search([
                    ('hub_code', '=', hub_code)
                ], limit=1)
                if channel:
                    channel_id = channel.id
            
            product_omniful_feed = self.create({
                'event_name': webhook_data.get('event_name'),
                'channel_id': channel_id,
                'product_id': data.get('product_id'),
                'sku_code': data.get('sku_code'),
                'product_name': data.get('name'),
                'description': data.get('description'),
                'category': data.get('category'),
                'brand': data.get('brand'),
                'price': data.get('price'),
                'cost': data.get('cost'),
                'weight': data.get('weight'),
                'dimensions': data.get('dimensions'),
                'status': data.get('status'),
                'raw_data': json.dumps(webhook_data),
                'state': 'received'
            })
            
            _logger.info(f"Created product feed record: {product_omniful_feed.id}")
            return product_omniful_feed
            
        except Exception as e:
            _logger.error(f"Error creating product feed: {str(e)}")
            return self.create({
                'event_name': webhook_data.get('event_name', 'unknown'),
                'raw_data': json.dumps(webhook_data),
                'state': 'error',
                'error_message': str(e)
            })
    
    def action_reprocess(self):
        """Reprocess failed product feeds"""
        for record in self.filtered(lambda r: r.state == 'error'):
            try:
                if record.raw_data:
                    webhook_data = json.loads(record.raw_data)
                    data = webhook_data.get('data', {})
                    if isinstance(data, list) and data:
                        data = data[0]
                    
                    record.write({
                        'product_id': data.get('product_id'),
                        'sku_code': data.get('sku_code'),
                        'product_name': data.get('name'),
                        'status': data.get('status'),
                        'state': 'processed',
                        'error_message': False
                    })
                    _logger.info(f"Reprocessed product feed: {record.id}")
            except Exception as e:
                _logger.error(f"Error reprocessing product feed {record.id}: {str(e)}")
                record.error_message = str(e)