from odoo import models, fields, api
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class PurchaseFeed(models.Model):
    _name = 'purchase.feed'
    _description = 'Purchase Feed from Omniful Webhook'
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
    
    # Purchase data fields
    purchase_id = fields.Char(
        string='Purchase ID',
        help='Unique purchase order identifier'
    )
    
    purchase_number = fields.Char(
        string='Purchase Number',
        help='Purchase order reference number'
    )
    
    supplier_id = fields.Char(
        string='Supplier ID',
        help='Supplier identifier'
    )
    
    supplier_name = fields.Char(
        string='Supplier Name',
        help='Supplier company name'
    )
    
    supplier_email = fields.Char(
        string='Supplier Email',
        help='Supplier contact email'
    )
    
    purchase_status = fields.Char(
        string='Purchase Status',
        help='Current status of the purchase order'
    )
    
    total_amount = fields.Float(
        string='Total Amount',
        help='Total purchase order amount'
    )
    
    currency = fields.Char(
        string='Currency',
        help='Purchase order currency'
    )
    
    order_date = fields.Char(
        string='Order Date',
        help='Date when purchase order was created'
    )
    
    expected_delivery_date = fields.Char(
        string='Expected Delivery Date',
        help='Expected delivery date'
    )
    
    delivery_address = fields.Text(
        string='Delivery Address',
        help='Complete delivery address'
    )
    
    payment_terms = fields.Char(
        string='Payment Terms',
        help='Payment terms for the purchase'
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
    
    @api.depends('purchase_number', 'supplier_name', 'received_at')
    def _compute_display_name(self):
        for record in self:
            if record.purchase_number and record.supplier_name:
                record.display_name = f"PO {record.purchase_number} - {record.supplier_name}"
            elif record.purchase_number:
                record.display_name = f"PO {record.purchase_number}"
            else:
                record.display_name = f"Purchase Feed - {record.received_at}"
    
    @api.model
    def create_from_webhook_data(self, webhook_data):
        """Create purchase feed record from webhook data"""
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
            
            purchase_feed = self.create({
                'event_name': webhook_data.get('event_name'),
                'channel_id': channel_id,
                'purchase_id': data.get('purchase_id'),
                'purchase_number': data.get('purchase_number'),
                'supplier_id': data.get('supplier_id'),
                'supplier_name': data.get('supplier_name'),
                'supplier_email': data.get('supplier_email'),
                'purchase_status': data.get('status'),
                'total_amount': data.get('total_amount'),
                'currency': data.get('currency'),
                'order_date': data.get('order_date'),
                'expected_delivery_date': data.get('expected_delivery_date'),
                'delivery_address': json.dumps(data.get('delivery_address', {})),
                'payment_terms': data.get('payment_terms'),
                'raw_data': json.dumps(webhook_data),
                'state': 'received'
            })
            
            _logger.info(f"Created purchase feed record: {purchase_feed.id}")
            return purchase_feed
            
        except Exception as e:
            _logger.error(f"Error creating purchase feed: {str(e)}")
            return self.create({
                'event_name': webhook_data.get('event_name', 'unknown'),
                'raw_data': json.dumps(webhook_data),
                'state': 'error',
                'error_message': str(e)
            })
    
    def action_reprocess(self):
        """Reprocess failed purchase feeds"""
        for record in self.filtered(lambda r: r.state == 'error'):
            try:
                if record.raw_data:
                    webhook_data = json.loads(record.raw_data)
                    data = webhook_data.get('data', {})
                    if isinstance(data, list) and data:
                        data = data[0]
                    
                    record.write({
                        'purchase_id': data.get('purchase_id'),
                        'purchase_number': data.get('purchase_number'),
                        'supplier_name': data.get('supplier_name'),
                        'purchase_status': data.get('status'),
                        'state': 'processed',
                        'error_message': False
                    })
                    _logger.info(f"Reprocessed purchase feed: {record.id}")
            except Exception as e:
                _logger.error(f"Error reprocessing purchase feed {record.id}: {str(e)}")
                record.error_message = str(e)