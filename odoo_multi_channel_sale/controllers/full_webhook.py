import json

from odoo import http, SUPERUSER_ID, api
from odoo.http import request

from ..ApiTransaction import Transaction


from datetime import datetime
from datetime import datetime, timezone

import pytz

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.ERROR)

from . import handle_data as handle


class FullSallaWebhook(http.Controller):

    def get_user_act(self):
        return request.env['res.users'].sudo().browse(2)

    def get_operation(self, instance_id, object):
        return request.env['import.operation'].sudo().create({
            'channel_id': instance_id,
            'operation': 'import',
            'api_record_limit': 1,
            'object': object
        })

    def _get_secret_key(self):
        """Fetch secret key from settings safely"""
        key = request.env['ir.config_parameter'].sudo().get_param('odoo_multi_channel_sale.secret_key_webhook')
        return key

    def _check_auth(self, auth_header):
        """Validate incoming Authorization header"""
        _logger.info(f"Validating Authorization header {auth_header}")
        secret = self._get_secret_key()
        _logger.info(f"Secret Key: {secret}")
        if not auth_header:
            _logger.warning("No Authorization header provided")
            return False
        token = auth_header.split()[-1]
        if token == secret:
            _logger.info("Authorization token valid")
            return True
        _logger.info("Authorization token invalid")
        return False

    @http.route('/salla/webhook', type="http", auth="public", csrf=False)
    def full_salla_webhook(self, **kwargs):
        event_data = request.httprequest.data
        auth_header = request.httprequest.headers.get('Authorization')

        if not auth_header:
            return request.make_response(json.dumps({"status": "unauthorized"}),
                                         headers=[('Content-Type', 'application/json')], status=401)
        if not self._check_auth(auth_header):
            return request.make_response(json.dumps({"status": "unauthorized"}), 401)

        if not event_data:
            return request.make_response(json.dumps({"status": "no data"}),
                                         headers=[('Content-Type', 'application/json')], status=400)

        try:
            data = json.loads(event_data)
            _logger.info("Salla Webhook Event: %s", data.get("event"))
            _logger.info("Salla Webhook Data: %s", data)

            user = self.get_user_act()
            env = request.env
            instance = env['multi.channel.sale'].sudo().search([], limit=1)
            event_type = data.get("event", "")

            # ---------------- Order ----------------
            if "order" in event_type:
                if instance.webhook_sales_order == "active_api":
                    # API Mode
                    _operation = self.get_operation(instance.id, "sale.order")
                    _operation.with_user(user).sudo().import_button()

                    channel = instance
                    env['order.feed'].sudo().with_context(order_feeds={}, channel_id=channel)._create_feed(data)

                elif instance.webhook_sales_order == "active_webhook":
                    parser = handle.ParseHandleData()
                    _logger.info("===== 🧾 Salla Webhook Received (Order) =====")
                    _logger.info("📦 Raw Data: %s", data)

                    # ---------------- Parse order date (NOT webhook created_at) ----------------
                    order_date_data = data.get("data", {}).get("date", {})
                    order_date_str = order_date_data.get("date")

                    # Fallback
                    if not order_date_str:
                        order_date_str = data.get("created_at")
                        _logger.warning("⚠️ Using webhook created_at as fallback: %s", order_date_str)
                    else:
                        _logger.info("🕒 Using actual order date: %s", order_date_str)

                    order_date_dt = None
                    parse_formats = [
                        "%Y-%m-%d %H:%M:%S.%f",
                        "%Y-%m-%d %H:%M:%S",
                        "%a %b %d %Y %H:%M:%S GMT%z",
                        "%Y-%m-%dT%H:%M:%S%z",
                    ]

                    for fmt in parse_formats:
                        try:
                            order_date_dt = datetime.strptime(order_date_str, fmt)
                            _logger.info("✅ Parsed order date using format '%s' => %s", fmt, order_date_dt)
                            break
                        except Exception as e:
                            _logger.debug("Failed parsing with format %s: %s", fmt, e)

                    if not order_date_dt:
                        _logger.error("❌ Failed to parse order date with known formats: %s", order_date_str)
                        return request.make_response(
                            json.dumps({"status": f"invalid order date format: {order_date_str}"}),
                            headers=[('Content-Type', 'application/json')],
                            status=400
                        )

                    # ---------------- Convert timezone ----------------
                    local_tz = pytz.timezone("Asia/Riyadh")

                    if not order_date_dt.tzinfo:
                        order_date_local = local_tz.localize(order_date_dt)
                        _logger.info("🕋 Localized order date to Riyadh timezone: %s", order_date_local)
                    else:
                        order_date_local = order_date_dt.astimezone(local_tz)
                        _logger.info("🕋 Converted order date to Riyadh timezone: %s", order_date_local)

                    # ---------------- Process start_date ----------------
                    try:
                        start_date = instance.start_date
                        _logger.info("📅 Instance start_date (raw): %s", start_date)

                        if not start_date:
                            _logger.warning("⚠️ No start_date configured - accepting all orders")
                        else:
                            if not isinstance(start_date, datetime):
                                start_date = datetime.combine(start_date, datetime.min.time())
                                _logger.info("🔄 Converted start_date from date to datetime: %s", start_date)

                            if not start_date.tzinfo:
                                start_date_local = local_tz.localize(start_date)
                            else:
                                start_date_local = start_date.astimezone(local_tz)

                            _logger.info("🕋 start_date localized to Riyadh timezone: %s", start_date_local)

                            # ---------------- Compare order_date vs start_date ----------------
                            if order_date_local < start_date_local:
                                _logger.warning(
                                    "🚫 Order REJECTED: order_date(Riyadh)=%s < start_date(Riyadh)=%s",
                                    order_date_local, start_date_local
                                )
                                return request.make_response(
                                    json.dumps({
                                        "status": "rejected",
                                        "reason": "order is older than start date",
                                        "order_date": str(order_date_local),
                                        "start_date": str(start_date_local)
                                    }),
                                    headers=[('Content-Type', 'application/json')],
                                    status=200
                                )

                            _logger.info(
                                "✅ Order ACCEPTED: order_date(Riyadh)=%s >= start_date(Riyadh)=%s",
                                order_date_local, start_date_local
                            )

                    except Exception as e:
                        _logger.error("❌ Failed to process start_date: %s", e)
                        return request.make_response(
                            json.dumps({"status": f"invalid start_date: {e}"}),
                            headers=[('Content-Type', 'application/json')],
                            status=400
                        )

                    # ---------------- Parse & Import Order ----------------
                    data = parser.parse_handle_data_sales_order_create(data)
                    kw = {
                        'filter_type': 'all',
                        'salla_product_keyword': False,
                        'salla_enable_keyword': False,
                        'salla_order_status': False
                    }

                    _logger.info("📤 Importing order data via webhook for instance %s", instance.name)

                    Transaction(channel=instance).import_data_webhook(
                        object="sale.order",
                        data_list=(data, kw),
                        **kw
                    )

                    # ---------------- Import items for order.feed ----------------
                    # items = env['order.feed'].sudo().search([('state', '=', 'draft')])
                    # item = env['order.feed'].sudo().search([('state', '=', 'draft')], order='id desc', limit=1)
                    # for item in items:
                    # if item:
                    #     item.with_user(user).sudo().import_items()
                    #     _logger.info("📦 Imported items for order_feed id=%s", item.id)

                _logger.info("🎯 Webhook processing for order completed successfully.")

            # ---------------- Product ----------------
            if "product" in event_type:
                if instance.webhook_product == "active_api":
                    _operation = self.get_operation(instance.id, "product.template")
                    _operation.with_user(user).sudo().import_button()

                elif instance.webhook_product == "active_webhook":
                    parser = handle.ParseHandleData()
                    data = parser.parse_final_product_data_create(data, instance.id)
                    kw = {'filter_type': 'all', 'salla_product_keyword': False, 'salla_enable_keyword': False,
                          'salla_order_status': False}
                    Transaction(channel=instance).import_data_webhook(
                        object="product.template",
                        data_list=(data, kw),
                        **kw
                    )
                    items = env['product.feed'].sudo().search([('state', '=', 'draft')])
                    for item in items:
                        item.with_user(user).sudo().import_items()

            # ---------------- Category ----------------
            if "category" in event_type:
                if instance.webhook_category == "active_api":
                    _operation = self.get_operation(instance.id, "product.category")
                    _operation.with_user(user).sudo().import_button()

                elif instance.webhook_category == "active_webhook":
                    parser = handle.ParseHandleData()
                    data = parser.parse_final_category_data_create(data, instance.id)
                    kw = {'filter_type': 'all', 'salla_product_keyword': False, 'salla_enable_keyword': False,
                          'salla_order_status': False}
                    Transaction(channel=instance).import_data_webhook(
                        object="product.category",
                        data_list=(data, kw),
                        **kw
                    )
                    items = env['category.feed'].sudo().search([('state', '=', 'draft')])
                    for item in items:
                        item.with_user(user).sudo().import_items()

            # ---------------- Customer ----------------
            if "customer" in event_type:
                if instance.webhook_customer == "active_api":
                    _operation = self.get_operation(instance.id, "res.partner")
                    _operation.with_user(user).sudo().import_button()

                elif instance.webhook_customer == "active_webhook":
                    parser = handle.ParseHandleData()
                    data = parser.parse_final_partner_data_create(data, instance.id)
                    kw = {'filter_type': 'all', 'salla_product_keyword': False, 'salla_enable_keyword': False,
                          'salla_order_status': False}
                    Transaction(channel=instance).import_data_webhook(
                        object="res.partner",
                        data_list=(data, kw),
                        **kw
                    )
                    items = env['partner.feed'].sudo().search([('state', '=', 'draft')])
                    for item in items:
                        item.with_user(user).sudo().import_items()

            # ---------------- Shipment ----------------
            if "shipment" in event_type or "shipping" in event_type:
                _operation = self.get_operation(instance.id, "delivery.carrier")
                _operation.with_user(user).sudo().import_button()

            return request.make_response(json.dumps({"status": "success"}),
                                         headers=[('Content-Type', 'application/json')],
                                         status=200)

        except Exception as e:
            _logger.exception("Error in Salla Webhook: %s", e)
            return request.make_response(json.dumps({"status": "error", "error": str(e)}),
                                         headers=[('Content-Type', 'application/json')], status=500)