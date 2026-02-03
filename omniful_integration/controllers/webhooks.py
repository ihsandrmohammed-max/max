from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class OmnifulWebhook(http.Controller):
    
    @http.route('/omniful/webhook/inventory', type="http", auth="public", csrf=False, methods=['POST'])
    def inventory_webhook(self, **kwargs):
        """Handle inventory update webhooks from Omniful"""
        try:
            # Get the raw data
            data = request.httprequest.get_data()

            auth_header = request.httprequest.headers.get('Authorization')
            _logger.info(f"Received inventory webhook: {auth_header}")
            print(data)

            if not data:
                _logger.warning("Received empty webhook data")
                return "No data received"
            
            # Parse JSON data
            try:
                webhook_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in webhook data: {str(e)}")
                return "Invalid JSON data"
            
            # Log the received webhook
            _logger.info(f"Received inventory webhook: {webhook_data.get('event_name', 'unknown')}")
            
            # Create inventory feed records
            inventory_feed_model = request.env['inventory.feed'].sudo()
            
            # Create the feed records
            created_records = inventory_feed_model.create_from_webhook_data(webhook_data)
            
            _logger.info(f"Successfully processed webhook, created {len(created_records)} records")

            return request.make_response(json.dumps({"status": "success"}),
                                         headers=[('Content-Type', 'application/json')],
                                         status=200)
            
        except Exception as e:
            _logger.error(f"Error processing inventory webhook: {str(e)}")
            return f"Error: {str(e)}"

    @http.route('/omniful/webhook/order', type="http", auth="public", csrf=False, methods=['POST'])
    def order_webhook(self, **kwargs):
        """Handle order update webhooks from Omniful"""
        try:
            # Get the raw data
            data = request.httprequest.get_data()

            auth_header = request.httprequest.headers.get('Authorization')
            _logger.info(f"Received order webhook: {auth_header}")

            if not data:
                _logger.warning("Received empty webhook data")
                return "No data received"
            
            # Parse JSON data
            try:
                webhook_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in webhook data: {str(e)}")
                return "Invalid JSON data"
            
            # Log the received webhook
            _logger.info(f"Received order webhook: {webhook_data.get('event_name', 'unknown')}")
            
            # Create order feed records
            order_feed_model = request.env['order_omniful.feed'].sudo()
            
            # Create the feed records
            created_records = order_feed_model.create_from_webhook_data(webhook_data)
            
            _logger.info(f"Successfully processed order webhook, created {len(created_records)} records")

            return request.make_response(json.dumps({"status": "success"}),
                                         headers=[('Content-Type', 'application/json')],
                                         status=200)

        except Exception as e:
            _logger.error(f"Error processing order webhook: {str(e)}")
            return f"Error: {str(e)}"

    @http.route('/omniful/webhook/product', type="http", auth="public", csrf=False, methods=['POST'])
    def product_webhook(self, **kwargs):
        """Handle product update webhooks from Omniful"""
        try:
            # Get the raw data
            data = request.httprequest.get_data()

            auth_header = request.httprequest.headers.get('Authorization')
            _logger.info(f"Received product webhook: {auth_header}")

            if not data:
                _logger.warning("Received empty webhook data")
                return "No data received"
            
            # Parse JSON data
            try:
                webhook_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in webhook data: {str(e)}")
                return "Invalid JSON data"
            
            # Log the received webhook
            _logger.info(f"Received product webhook: {webhook_data.get('event_name', 'unknown')}")
            
            # Create product feed records
            product_omniful_feed_model = request.env['product_omniful.feed'].sudo()
            
            # Create the feed records
            created_records = product_omniful_feed_model.create_from_webhook_data(webhook_data)
            
            _logger.info(f"Successfully processed product webhook, created {len(created_records)} records")

            return request.make_response(json.dumps({"status": "success"}),
                                         headers=[('Content-Type', 'application/json')],
                                         status=200)

        except Exception as e:
            _logger.error(f"Error processing product webhook: {str(e)}")
            return f"Error: {str(e)}"

    @http.route('/omniful/webhook/purchase', type="http", auth="public", csrf=False, methods=['POST'])
    def purchase_webhook(self, **kwargs):
        """Handle purchase order webhooks from Omniful"""
        try:
            # Get the raw data
            data = request.httprequest.get_data()

            auth_header = request.httprequest.headers.get('Authorization')
            _logger.info(f"Received purchase webhook: {auth_header}")

            if not data:
                _logger.warning("Received empty webhook data")
                return "No data received"
            
            # Parse JSON data
            try:
                webhook_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in webhook data: {str(e)}")
                return "Invalid JSON data"
            
            # Log the received webhook
            _logger.info(f"Received purchase webhook: {webhook_data.get('event_name', 'unknown')}")
            
            # Create purchase feed records
            purchase_feed_model = request.env['purchase.feed'].sudo()
            
            # Create the feed records
            created_records = purchase_feed_model.create_from_webhook_data(webhook_data)
            
            _logger.info(f"Successfully processed purchase webhook, created {len(created_records)} records")

            return request.make_response(json.dumps({"status": "success"}),
                                         headers=[('Content-Type', 'application/json')],
                                         status=200)

        except Exception as e:
            _logger.error(f"Error processing purchase webhook: {str(e)}")
            return f"Error: {str(e)}"

    @http.route('/omniful/webhook/shipment', type="http", auth="public", csrf=False, methods=['POST'])
    def shipment_webhook(self, **kwargs):
        """Handle shipment update webhooks from Omniful"""
        try:
            # Get the raw data
            data = request.httprequest.get_data()

            auth_header = request.httprequest.headers.get('Authorization')
            _logger.info(f"Received shipment webhook: {auth_header}")

            if not data:
                _logger.warning("Received empty webhook data")
                return "No data received"
            
            # Parse JSON data
            try:
                webhook_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in webhook data: {str(e)}")
                return "Invalid JSON data"
            
            # Log the received webhook
            _logger.info(f"Received shipment webhook: {webhook_data.get('event_name', 'unknown')}")
            
            # Create shipment feed records
            shipment_feed_model = request.env['shipment.feed'].sudo()
            
            # Create the feed records
            created_records = shipment_feed_model.create_from_webhook_data(webhook_data)
            
            _logger.info(f"Successfully processed shipment webhook, created {len(created_records)} records")

            return request.make_response(json.dumps({"status": "success"}),
                                         headers=[('Content-Type', 'application/json')],
                                         status=200)

        except Exception as e:
            _logger.error(f"Error processing shipment webhook: {str(e)}")
            return f"Error: {str(e)}"

    @http.route('/omniful/webhook/stock', type="http", auth="public", csrf=False, methods=['POST'])
    def stock_webhook(self, **kwargs):
        """Handle stock update webhooks from Omniful"""
        try:
            # Get the raw data
            data = request.httprequest.get_data()

            auth_header = request.httprequest.headers.get('Authorization')
            _logger.info(f"Received stock webhook: {auth_header}")

            if not data:
                _logger.warning("Received empty webhook data")
                return "No data received"
            
            # Parse JSON data
            try:
                webhook_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in webhook data: {str(e)}")
                return "Invalid JSON data"
            
            # Log the received webhook
            _logger.info(f"Received stock webhook: {webhook_data.get('event_name', 'unknown')}")
            
            # Create stock feed records
            stock_feed_model = request.env['stock.feed'].sudo()
            
            # Create the feed records
            created_records = stock_feed_model.create_from_webhook_data(webhook_data)
            
            _logger.info(f"Successfully processed stock webhook, created {len(created_records)} records")

            return request.make_response(json.dumps({"status": "success"}),
                                         headers=[('Content-Type', 'application/json')],
                                         status=200)

        except Exception as e:
            _logger.error(f"Error processing stock webhook: {str(e)}")
            return f"Error: {str(e)}"


