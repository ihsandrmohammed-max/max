from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    omniful_send_json = fields.Text(string="Omniful Response", readonly=True, copy=False)
    omniful_response_json = fields.Text(string="Omniful Response", readonly=True, copy=False)
    omniful_order_id = fields.Char(string="Omniful Order ID", readonly=True, copy=False)

    def _prepare_omniful_payload(self, channel):
        """Prepare payload for Omniful order API."""
        self.ensure_one()
        order = self

        rec_order_feed = self.env['order.feed'].search([('name', '=', order.name)])
        rec_invoice = self.env['account.move'].search([('salla_so_id', '=', order.name)])
        _logger.info(rec_order_feed.read())
        _logger.info(rec_invoice.read())

        # Map order lines
        order_items = []
        for line in order.order_line:
            order_items.append({
                "sku_code": line.product_id.default_code or f"sku_{line.id}",
                "name": line.product_id.name,
                "display_price": line.price_unit,
                "selling_price": line.price_unit,
                "is_substituted": False,
                "quantity": int(line.product_uom_qty),
                "tax_percent": sum(line.tax_id.mapped("amount")),
                "tax": line.price_tax,
                "unit_price": line.price_unit,
                "subtotal": line.price_subtotal,
                "total": line.price_total,
                "discount": line.discount,
                "tax_inclusive": order.company_id.tax_calculation_rounding_method == "round_globally",
            })

        partner = order.partner_id
        billing_address = {
            "address1": rec_order_feed.invoice_street or "",
            "address2": rec_order_feed.invoice_street2 or "",
            "city": partner.city or "",
            "country": partner.country_id.name or "",
            "country": rec_order_feed.invoice_city or "",
            "first_name": partner.name.split(" ")[0] if partner.name else "",
            "last_name": " ".join(partner.name.split(" ")[1:]) if partner.name and len(partner.name.split(" ")) > 1 else "",
            "phone": rec_order_feed.invoice_phone or "",
            "state": partner.state_id.name or "",
            "zip": partner.zip or "",
            "state_code": partner.state_id.code or "",
            "country_code": partner.country_id.code or "",
            "latitude": 24.7136,    # TODO: Get from Salla
            "longitude": 46.6753    # TODO: Get from Salla
        }
        # invoice_email_0
        shipping_address = {}

        if rec_order_feed.same_shipping_billing:
            shipping_address = billing_address
        else:
            shipping_address = {
                "address1": rec_order_feed.invoice_street or "",
                "address2": rec_order_feed.invoice_street2 or "",
                "city": partner.city or "",
                "country": partner.country_id.name or "",
                "first_name": partner.name.split(" ")[0] if partner.name else "",
                "last_name": " ".join(partner.name.split(" ")[1:]) if partner.name and len(
                    partner.name.split(" ")) > 1 else "",
                "phone": partner.phone or "",
                "state": partner.state_id.name or "",
                "zip": partner.zip or "",
                "state_code": partner.state_id.code or "",
                "country_code": partner.country_id.code or "",
                "latitude": 24.7136,  # TODO: Get from Salla
                "longitude": 46.6753  # TODO: Get from Salla
            }

        customer = {
                "id": str(partner.omniful_customer_id),
                "first_name": partner.name.split(" ")[0] if partner.name else "",
                "last_name": " ".join(partner.name.split(" ")[1:]) if partner.name and len(partner.name.split(" ")) > 1 else "",
                "mobile": rec_order_feed.invoice_phone or partner._clean_mobile() or "",
                "mobile_code": f"+{partner.country_id.phone_code}" if partner.country_id.phone_code else "",
                "email": rec_order_feed.invoice_email or "",
                "gender": "male" if partner.title and partner.title.name.lower() == "mr" else "female" if partner.title and partner.title.name.lower() == "ms" else "male",
            }
        # TODO: Get transactions after payment confirmation ? if not have payment ?
        # TODO: you have option payment on delivery?
        transactions = [{
                "transaction_id": f"PAYMENT_{order.name}",     # TODO: source data ?
                "amount": order.amount_total,
                "type": 1,
                "card_number": "4111111111111111",
                "source_account": "source_account_123",     # TODO: source data ?
                "destination_account": "destination_account_456",     # TODO: source data ?
                "status": 1,     # TODO: source data ?
                "description": f"Payment for order {order.name}",     # TODO: source data ? memo in payment
            }]


        payload = {
            "shipment_type": "omniful_generated",
            "order_id": order.name,
            "order_alias": order.client_order_ref or str(order.name) or f"NA_{order.id}",
            "hub_code": channel.hub_code,
            "order_items": order_items,
            "billing_address": billing_address,
            "shipping_address": shipping_address,  # You can use partner_shipping_id if different
            # TODO: source data  invoice ? send info ? send after payment confirmation ? send after confirmation ?
            "invoice": {
                "currency": order.currency_id.name,
                "subtotal": order.amount_untaxed,
                "shipping_price": 0,
                "shipping_refund": 0,
                "tax": order.amount_tax,
                "discount": sum(line.price_unit * line.discount / 100 for line in order.order_line),
                "total": order.amount_total,
                "total_paid": order.amount_total if order.invoice_status == "invoiced" else 0,
                "total_due": order.amount_total if order.invoice_status != "invoiced" else 0,
                "total_refunded": 0,
                "payment_method": order.payment_term_id.name if order.payment_term_id else "Unknown",
                "tax_percent": 0,  # can compute from lines if needed
                "sub_total_tax_inclusive": True,
                "sub_total_discount_inclusive": True,
                "shipping_tax_inclusive": False,
                "shipping_discount_inclusive": False,
                "attachments": [],
            },
            "customer": customer,
            "note": order.note or "",    # TODO: source data ? not in sale order
            "require_shipping": True,    # TODO: what is this ?
            "payment_method": "prepaid",    # TODO: what is option ?
            "transactions": transactions,
            "type": "b2b",     # TODO: source data ?
            "cancel_order_after_seconds": 30    # TODO: source data ?
        }

        return payload

    def action_send_to_omniful(self):
        # TODO: what time is send to omniful ? and update ? status = Confirm ?!
        for order in self:
            channel = self.env['channel.omniful'].search([('active', '=', True)], limit=1)
            if not channel:
                order.message_post(body="No active Omniful channel found.")
                continue

            payload = order._prepare_omniful_payload(channel)
            _logger.info("Omniful Payload: %s", payload)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {channel.omniful_access_token}",
            }

            try:
                response = requests.post(
                    f"{channel.base_url_omniful}/sales-channel/public/v1/orders",
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=30
                )
                _logger.info("Omniful Response: %s", response.json())
                res_json = response.json()

                order.omniful_send_json = json.dumps(payload, ensure_ascii=False, indent=2)
                order.omniful_response_json = json.dumps(response.json(), indent=2)
                order.omniful_order_id = res_json.get("data", {}).get("id")

                if response.status_code in (200, 201):
                    order.message_post(body=f"✅ Order {order.name} sent to Omniful successfully.")
                else:
                    order.message_post(body=f"⚠️ Failed to send order {order.name}. Status: {response.status_code}<br/>{response.text}")

            except Exception as e:
                _logger.error(f"Error sending order {order.name}: {str(e)}")
                order.message_post(body=f"❌ Error sending order {order.name}: {str(e)}")

    def action_update_in_omniful(self):
        """Update existing Omniful order using PUT request with full logging and safe JSON parsing."""
        for order in self:
            if not order.omniful_order_id:
                order.message_post(body="⚠️ Cannot update: Omniful Order ID is missing.")
                continue

            channel = self.env['channel.omniful'].search([('active', '=', True)], limit=1)
            if not channel:
                order.message_post(body="No active Omniful channel found.")
                continue

            payload = order._prepare_omniful_payload(channel)
            payload.pop("shipment_type", None)
            payload["order_id"] = order.name
            # _logger.info("Omniful Update Payload: %s", json.dumps(payload, indent=2))
            _logger.info("Omniful Update Payload: %s", payload)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {channel._get_omniful_access_token()}",
            }

            try:
                url = f"{channel.base_url_omniful}/sales-channel/public/v1/orders"
                _logger.info("Omniful Update URL: %s", url)

                response = requests.put(url, headers=headers, data=json.dumps(payload), timeout=30)

                _logger.info("Omniful Update Status Code: %s", response.status_code)
                _logger.info("Omniful Update Raw Response: %s", response.text)

                try:
                    res_json = response.json()
                except ValueError:
                    _logger.error("Omniful returned a non-JSON response for order %s: %s", order.name, response.text)
                    order.message_post(
                        body=f"❌ Omniful update failed for order {order.name}. "
                             f"Non-JSON response returned:<br/>{response.text}"
                    )
                    continue

                _logger.info("Omniful Parsed JSON Response: %s", json.dumps(res_json, indent=2))

                order.omniful_send_json = json.dumps(payload, indent=2)
                order.omniful_response_json = json.dumps(res_json, indent=2)

                if response.status_code in (200, 201):
                    order.message_post(body=f"✅ 🔄 Order {order.name} updated in Omniful successfully.")
                else:
                    order.message_post(
                        body=f"⚠️ Failed to update order {order.name}. "
                             f"Status: {response.status_code}<br/>{json.dumps(res_json, indent=2)}"
                    )

            except Exception as e:
                _logger.error("Error updating order %s: %s", order.name, str(e))
                order.message_post(body=f"❌ Error updating order {order.name}: {str(e)}")

    def action_cancel_in_omniful(self):
        """Cancel an order in Omniful using the API."""
        for order in self:
            if not order.omniful_order_id:
                order.message_post(body="⚠️ Cannot cancel: Omniful Order ID is missing.")
                continue

            channel = self.env['channel.omniful'].search([('active', '=', True)], limit=1)
            if not channel:
                order.message_post(body="No active Omniful channel found.")
                continue

            url = f"{channel.base_url_omniful}/sales-channel/public/v1/orders/{order.name}/cancel"
            payload = {
                "cancel_reason": "Not needed now."
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {channel._get_omniful_access_token()}",
            }

            try:
                response = requests.put(url, headers=headers, data=json.dumps(payload), timeout=30)

                _logger.info("Omniful Cancel URL: %s", url)
                _logger.info("Omniful Cancel Status Code: %s", response.status_code)
                _logger.info("Omniful Cancel Raw Response: %s", response.text)

                try:
                    res_json = response.json()
                except ValueError:
                    order.message_post(
                        body=f"❌ Omniful cancel failed for order {order.name}. "
                             f"Non-JSON response returned:<br/>{response.text}"
                    )
                    continue

                if response.status_code in (200, 201):
                    order.message_post(body=f"✅ 🛑 Order {order.name} cancelled in Omniful successfully.")
                else:
                    order.message_post(
                        body=f"⚠️ Failed to cancel order {order.name}. "
                             f"Status: {response.status_code}<br/>{json.dumps(res_json, indent=2)}"
                    )

            except Exception as e:
                _logger.error("Error cancelling order %s: %s", order.name, str(e))
                order.message_post(body=f"❌ Error cancelling order {order.name}: {str(e)}")

    def action_approve_in_omniful(self):
        """Approve Omniful order using API."""
        for order in self:
            if not order.omniful_order_id:
                order.message_post(body="⚠️ Cannot approve: Omniful Order ID is missing.")
                continue

            channel = self.env['channel.omniful'].search([('active', '=', True)], limit=1)
            if not channel:
                order.message_post(body="No active Omniful channel found.")
                continue

            url = f"{channel.base_url_omniful}/sales-channel/public/v1/orders/{order.name}/approve"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {channel._get_omniful_access_token()}",
            }

            try:
                response = requests.put(url, headers=headers, timeout=30)
                _logger.info("Omniful Approve Response: %s", response.json())
                order.omniful_response_json = json.dumps(response.json(), indent=2)

                if response.status_code in (200, 201):
                    order.message_post(body=f"✅ Order {order.name} approved in Omniful successfully.")
                else:
                    order.message_post(
                        body=f"⚠️ Failed to approve order {order.name}. Status: {response.status_code}<br/>{response.text}")

            except Exception as e:
                _logger.error(f"Error approving order {order.name}: {str(e)}")
                order.message_post(body=f"❌ Error approving order {order.name}: {str(e)}")

    def action_send_to_omniful_rec(self):
        for order in self:
            if not order.omniful_order_id:
                order.action_send_to_omniful()