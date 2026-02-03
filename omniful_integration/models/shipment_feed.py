from odoo import models, fields, api
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class ShipmentFeed(models.Model):
    _name = 'shipment.feed'
    _description = 'Shipment Feed from Omniful Webhook'
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
    
    # Shipment data fields
    shipment_id = fields.Char(
        string='Shipment ID',
        help='Unique shipment identifier'
    )
    
    tracking_number = fields.Char(
        string='Tracking Number',
        help='Shipment tracking number'
    )
    
    order_id = fields.Char(
        string='Order ID',
        help='Related order identifier'
    )
    
    carrier = fields.Char(
        string='Carrier',
        help='Shipping carrier name'
    )
    
    service_type = fields.Char(
        string='Service Type',
        help='Shipping service type'
    )
    
    shipment_status = fields.Char(
        string='Shipment Status',
        help='Current shipment status'
    )
    
    shipped_date = fields.Char(
        string='Shipped Date',
        help='Date when shipment was dispatched'
    )
    
    estimated_delivery = fields.Char(
        string='Estimated Delivery',
        help='Estimated delivery date'
    )
    
    actual_delivery = fields.Char(
        string='Actual Delivery',
        help='Actual delivery date'
    )
    
    shipping_address = fields.Text(
        string='Shipping Address',
        help='Complete shipping address'
    )
    
    weight = fields.Float(
        string='Weight',
        help='Shipment weight'
    )
    
    dimensions = fields.Char(
        string='Dimensions',
        help='Shipment dimensions'
    )
    
    shipping_cost = fields.Float(
        string='Shipping Cost',
        help='Cost of shipping'
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
    
    @api.depends('tracking_number', 'carrier', 'received_at')
    def _compute_display_name(self):
        for record in self:
            if record.tracking_number and record.carrier:
                record.display_name = f"{record.carrier} - {record.tracking_number}"
            elif record.tracking_number:
                record.display_name = f"Tracking: {record.tracking_number}"
            else:
                record.display_name = f"Shipment Feed - {record.received_at}"
    
    @api.model
    def create_from_webhook_data(self, webhook_data):
        """Create shipment feed record from webhook data"""
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
            
            shipment_feed = self.create({
                'event_name': webhook_data.get('event_name'),
                'channel_id': channel_id,
                'shipment_id': data.get('shipment_id'),
                'tracking_number': data.get('tracking_number'),
                'order_id': data.get('order_id'),
                'carrier': data.get('carrier'),
                'service_type': data.get('service_type'),
                'shipment_status': data.get('status'),
                'shipped_date': data.get('shipped_date'),
                'estimated_delivery': data.get('estimated_delivery'),
                'actual_delivery': data.get('actual_delivery'),
                'shipping_address': json.dumps(data.get('shipping_address', {})),
                'weight': data.get('weight'),
                'dimensions': data.get('dimensions'),
                'shipping_cost': data.get('shipping_cost'),
                'raw_data': json.dumps(webhook_data),
                'state': 'received'
            })
            
            _logger.info(f"Created shipment feed record: {shipment_feed.id}")
            return shipment_feed
            
        except Exception as e:
            _logger.error(f"Error creating shipment feed: {str(e)}")
            return self.create({
                'event_name': webhook_data.get('event_name', 'unknown'),
                'raw_data': json.dumps(webhook_data),
                'state': 'error',
                'error_message': str(e)
            })
    
    def action_reprocess(self):
        """Reprocess failed shipment feeds"""
        for record in self.filtered(lambda r: r.state == 'error'):
            try:
                if record.raw_data:
                    webhook_data = json.loads(record.raw_data)
                    data = webhook_data.get('data', {})
                    if isinstance(data, list) and data:
                        data = data[0]
                    
                    record.write({
                        'shipment_id': data.get('shipment_id'),
                        'tracking_number': data.get('tracking_number'),
                        'carrier': data.get('carrier'),
                        'shipment_status': data.get('status'),
                        'state': 'processed',
                        'error_message': False
                    })
                    _logger.info(f"Reprocessed shipment feed: {record.id}")
            except Exception as e:
                _logger.error(f"Error reprocessing shipment feed {record.id}: {str(e)}")
                record.error_message = str(e)