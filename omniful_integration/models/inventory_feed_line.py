from odoo import models, fields, api
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class InventoryFeedLine(models.Model):
    _name = 'inventory.feed.line'
    _description = 'Inventory Feed Line Items'
    _rec_name = 'display_name'
    _order = 'id desc'

    # Link to parent inventory feed
    inventory_feed_id = fields.Many2one(
        'inventory.feed',
        string='Inventory Feed',
        required=True,
        ondelete='cascade',
        help='Parent inventory feed record'
    )
    
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
    
    # Inventory data fields
    hub_code = fields.Char(
        string='Hub Code',
        help='Hub/warehouse code'
    )
    
    seller_code = fields.Char(
        string='Seller Code',
        help='Seller identification code'
    )
    
    sku_code = fields.Char(
        string='SKU Code',
        help='Product SKU code'
    )
    
    quantity = fields.Float(
        string='Available Quantity',
        help='Available quantity for sale'
    )
    
    unlimited_quantity = fields.Boolean(
        string='Unlimited Quantity',
        help='Whether the product has unlimited quantity'
    )
    
    quantity_on_hand = fields.Float(
        string='Quantity On Hand',
        help='Total quantity on hand'
    )
    
    quantity_reserved = fields.Float(
        string='Quantity Reserved',
        help='Quantity reserved for orders'
    )
    
    uom = fields.Char(
        string='Unit of Measure',
        help='Unit of measure for the product'
    )
    
    updated_at = fields.Char(
        string='Updated At (Original)',
        help='Original update timestamp from Omniful'
    )
    
    updated_at_epoch = fields.Float(
        string='Updated At Epoch',
        help='Epoch timestamp from Omniful'
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
    
    @api.depends('sku_code', 'hub_code', 'quantity')
    def _compute_display_name(self):
        for record in self:
            if record.sku_code and record.hub_code:
                record.display_name = f"{record.sku_code} - {record.hub_code} (Qty: {record.quantity})"
            elif record.sku_code:
                record.display_name = f"{record.sku_code} (Qty: {record.quantity})"
            else:
                record.display_name = f"Inventory Line - {record.id}"
    
    @api.model
    def create_from_webhook_data(self, inventory_feed_id, line_data):
        """Create inventory feed line record from webhook line data"""
        try:
            # Create inventory feed line record
            line_record = self.create({
                'inventory_feed_id': inventory_feed_id,
                'event_name': line_data.get('event_name'),
                'channel_id': line_data.get('channel_id'),
                'hub_code': line_data.get('hub_code'),
                'seller_code': line_data.get('seller_code'),
                'sku_code': line_data.get('sku_code'),
                'quantity': line_data.get('quantity', 0.0),
                'unlimited_quantity': line_data.get('unlimited_quantity', False),
                'quantity_on_hand': line_data.get('quantity_on_hand', 0.0),
                'quantity_reserved': line_data.get('quantity_reserved', 0.0),
                'uom': line_data.get('uom'),
                'updated_at': line_data.get('updated_at'),
                'updated_at_epoch': line_data.get('updated_at_epoch'),
                'raw_data': json.dumps(line_data, ensure_ascii=False),
                'state': 'received'
            })
            
            _logger.info(f"Created inventory feed line record: {line_record.id}")
            return line_record
            
        except Exception as e:
            _logger.error(f"Error creating inventory feed line: {str(e)}")
            # Create error record
            return self.create({
                'inventory_feed_id': inventory_feed_id,
                'raw_data': json.dumps(line_data, ensure_ascii=False),
                'state': 'error',
                'error_message': str(e)
            })