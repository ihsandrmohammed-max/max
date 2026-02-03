from odoo import models, fields, api
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class OrderFeed(models.Model):
    _name = 'order_omniful.feed'
    _description = 'Order Feed from Omniful Webhook'
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
    
    # Order data fields
    order_id = fields.Char(
        string='Order ID',
        help='Unique order identifier'
    )
    
    order_number = fields.Char(
        string='Order Number',
        help='Order reference number'
    )
    
    customer_id = fields.Char(
        string='Customer ID',
        help='Customer identifier'
    )
    
    customer_name = fields.Char(
        string='Customer Name',
        help='Customer full name'
    )
    
    customer_email = fields.Char(
        string='Customer Email',
        help='Customer email address'
    )
    
    order_status = fields.Char(
        string='Order Status',
        help='Current status of the order'
    )
    
    order_total = fields.Float(
        string='Order Total',
        help='Total order amount'
    )
    
    currency = fields.Char(
        string='Currency',
        help='Order currency'
    )
    
    order_date = fields.Char(
        string='Order Date',
        help='Date when order was placed'
    )
    
    shipping_address = fields.Text(
        string='Shipping Address',
        help='Complete shipping address'
    )
    
    billing_address = fields.Text(
        string='Billing Address',
        help='Complete billing address'
    )
    
    payment_method = fields.Char(
        string='Payment Method',
        help='Payment method used'
    )
    
    # System fields
    raw_data = fields.Text(
        string='Raw Webhook Data',
        help='Complete raw data received from webhook',
        # Ensure UTF-8 encoding support for Arabic content
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
    
    @api.depends('order_number', 'customer_name', 'received_at')
    def _compute_display_name(self):
        for record in self:
            if record.order_number and record.customer_name:
                record.display_name = f"Order {record.order_number} - {record.customer_name}"
            elif record.order_number:
                record.display_name = f"Order {record.order_number}"
            else:
                record.display_name = f"Order Feed - {record.received_at}"
    
    @api.model
    def create_from_webhook_data(self, webhook_data):
        """Create order feed record from webhook data"""
        try:
            # Extract order data from webhook
            data = webhook_data.get('data', {})
            if isinstance(data, list) and data:
                data = data[0]  # Take first order if multiple
            
            # Find associated channel if hub_code is provided
            channel_id = False
            hub_code = data.get('hub_code')
            if hub_code:
                channel = self.env['channel.omniful'].search([
                    ('hub_code', '=', hub_code)
                ], limit=1)
                if channel:
                    channel_id = channel.id
            
            # Create order feed record
            order_feed = self.create({
                'event_name': webhook_data.get('event_name'),
                'channel_id': channel_id,
                'order_id': data.get('order_id'),
                'order_number': data.get('order_number'),
                'customer_id': data.get('customer_id'),
                'customer_name': data.get('customer_name'),
                'customer_email': data.get('customer_email'),
                'order_status': data.get('status'),
                'order_total': data.get('total_amount'),
                'currency': data.get('currency'),
                'order_date': data.get('order_date'),
                'shipping_address': json.dumps(data.get('shipping_address', {})),
                'billing_address': json.dumps(data.get('billing_address', {})),
                'payment_method': data.get('payment_method'),
                'raw_data': json.dumps(webhook_data, ensure_ascii=False, indent=2),
                'state': 'received'
            })
            
            _logger.info(f"Created order feed record: {order_feed.id}")
            return order_feed
            
        except Exception as e:
            _logger.error(f"Error creating order feed: {str(e)}")
            # Create error record
            return self.create({
                'event_name': webhook_data.get('event_name', 'unknown'),
                'raw_data': json.dumps(webhook_data, ensure_ascii=False, indent=2),
                'state': 'error',
                'error_message': str(e)
            })
    
    def action_reprocess(self):
        """Reprocess failed order feeds"""
        for record in self.filtered(lambda r: r.state == 'error'):
            try:
                if record.raw_data:
                    webhook_data = json.loads(record.raw_data)
                    # Re-extract and update data
                    data = webhook_data.get('data', {})
                    if isinstance(data, list) and data:
                        data = data[0]
                    
                    record.write({
                        'order_id': data.get('order_id'),
                        'order_number': data.get('order_number'),
                        'customer_name': data.get('customer_name'),
                        'order_status': data.get('status'),
                        'state': 'processed',
                        'error_message': False
                    })
                    _logger.info(f"Reprocessed order feed: {record.id}")
            except Exception as e:
                _logger.error(f"Error reprocessing order feed {record.id}: {str(e)}")
                record.error_message = str(e)