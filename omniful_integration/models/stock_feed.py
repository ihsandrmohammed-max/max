from odoo import models, fields, api
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class StockFeed(models.Model):
    _name = 'stock.feed'
    _description = 'Stock Feed from Omniful Webhook'
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
    product_sku = fields.Char(
        string='Product SKU',
        help='Product SKU'
    )
    warehouse_code = fields.Char(
        string='Warehouse Code',
        help='Warehouse code'
    )
    reserved_quantity = fields.Float(
        string='Reserved Quantity',
        help='Reserved stock quantity'
    )

    available_quantity = fields.Float(
        string='Available Quantity',
        help='Available stock quantity'
    )
    
    channel_id = fields.Many2one(
        'channel.omniful',
        string='Channel',
        help='Omniful channel this feed belongs to'
    )
    
    # Stock data fields
    stock_id = fields.Char(
        string='Stock ID',
        help='Unique stock record identifier'
    )
    
    sku_code = fields.Char(
        string='SKU Code',
        help='Product SKU code'
    )
    
    hub_code = fields.Char(
        string='Hub Code',
        help='Hub/warehouse code'
    )
    
    location_code = fields.Char(
        string='Location Code',
        help='Specific location within hub'
    )
    
    quantity_available = fields.Float(
        string='Available Quantity',
        help='Available stock quantity'
    )
    
    quantity_reserved = fields.Float(
        string='Reserved Quantity',
        help='Reserved stock quantity'
    )
    
    quantity_incoming = fields.Float(
        string='Incoming Quantity',
        help='Incoming stock quantity'
    )
    
    quantity_outgoing = fields.Float(
        string='Outgoing Quantity',
        help='Outgoing stock quantity'
    )
    total_quantity = fields.Float(
        string='Total Quantity',
        help='Total stock quantity'
    )
    product_name = fields.Char(
        string='Product Name',
        help='Product name'
    )
    product_id = fields.Char(
        string='Product',
        help='Product'
    )
    zone_code = fields.Char(
        string='Zone Code',
        help='Zone code'
    )
    movement_reference = fields.Char(
        string='Movement Reference',
        help='Movement reference'
        )

    movement_date = fields.Char(
        string='Movement Date',
        help='Movement date'
        )
    movement_reason = fields.Char(
        string='Movement Reason',
        help='Movement reason'
        )
    
    unit_cost = fields.Float(
        string='Unit Cost',
        help='Cost per unit'
    )
    
    total_value = fields.Float(
        string='Total Value',
        help='Total stock value'
    )
    
    last_movement_date = fields.Char(
        string='Last Movement Date',
        help='Date of last stock movement'
    )
    
    movement_type = fields.Char(
        string='Movement Type',
        help='Type of stock movement'
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
    
    @api.depends('sku_code', 'hub_code', 'received_at')
    def _compute_display_name(self):
        for record in self:
            if record.sku_code and record.hub_code:
                record.display_name = f"{record.sku_code} @ {record.hub_code}"
            elif record.sku_code:
                record.display_name = f"SKU: {record.sku_code}"
            else:
                record.display_name = f"Stock Feed - {record.received_at}"
    
    @api.model
    def create_from_webhook_data(self, webhook_data):
        """Create stock feed record from webhook data"""
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
            
            stock_feed = self.create({
                'event_name': webhook_data.get('event_name'),
                'channel_id': channel_id,
                'stock_id': data.get('stock_id'),
                'sku_code': data.get('sku_code'),
                'hub_code': data.get('hub_code'),
                'location_code': data.get('location_code'),
                'quantity_available': data.get('quantity_available'),
                'quantity_reserved': data.get('quantity_reserved'),
                'quantity_incoming': data.get('quantity_incoming'),
                'quantity_outgoing': data.get('quantity_outgoing'),
                'unit_cost': data.get('unit_cost'),
                'total_value': data.get('total_value'),
                'last_movement_date': data.get('last_movement_date'),
                'movement_type': data.get('movement_type'),
                'raw_data': json.dumps(webhook_data),
                'state': 'received'
            })
            
            _logger.info(f"Created stock feed record: {stock_feed.id}")
            return stock_feed
            
        except Exception as e:
            _logger.error(f"Error creating stock feed: {str(e)}")
            return self.create({
                'event_name': webhook_data.get('event_name', 'unknown'),
                'raw_data': json.dumps(webhook_data),
                'state': 'error',
                'error_message': str(e)
            })
    
    def action_reprocess(self):
        """Reprocess failed stock feeds"""
        for record in self.filtered(lambda r: r.state == 'error'):
            try:
                if record.raw_data:
                    webhook_data = json.loads(record.raw_data)
                    data = webhook_data.get('data', {})
                    if isinstance(data, list) and data:
                        data = data[0]
                    
                    record.write({
                        'stock_id': data.get('stock_id'),
                        'sku_code': data.get('sku_code'),
                        'hub_code': data.get('hub_code'),
                        'quantity_available': data.get('quantity_available'),
                        'state': 'processed',
                        'error_message': False
                    })
                    _logger.info(f"Reprocessed stock feed: {record.id}")
            except Exception as e:
                _logger.error(f"Error reprocessing stock feed {record.id}: {str(e)}")
                record.error_message = str(e)