from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class ProductTemplateCustom(models.Model):
    _inherit = 'product.template'

    omniful_status = fields.Char(string="Omniful Status", readonly=True, copy=False)
    omniful_price = fields.Float(string="Omniful Selling Price", readonly=True, copy=False)
    omniful_currency = fields.Char(string="Omniful Currency", readonly=True, copy=False)
    omniful_country = fields.Char(string="Omniful Country", readonly=True, copy=False)
    omniful_response_json = fields.Text(string="Omniful Full Response", readonly=True, copy=False)

    # ----------------- Helper Methods -----------------

    def _validate_before_send(self, product):
        """Check required conditions before sending to Omniful."""
        missing_fields = []
        if not product.default_code:
            missing_fields.append("Internal Reference (SKU)")
        if not product.name:
            missing_fields.append("Product Name")
        if missing_fields:
            return {"valid": False, "message": f"Missing required fields: {', '.join(missing_fields)}"}
        return {"valid": True}

    def _build_payload(self, product):
        """Build payload for Omniful API."""
        description = (product.description_sale or product.description or "").replace("&nbsp;", " ")
        description_utf8 = description.encode("utf-8", errors="ignore").decode("utf-8")
        description_limited = (description_utf8[:47] + "...") if len(description_utf8) > 50 else description_utf8

        return {
            "name": product.name,
            "description": description_limited,
            "sku_code": product.default_code or f"sku-{product.id}",
            "barcodes": [product.barcode] if product.barcode else [],
            # "images": [{
            #     "default": f"/web/image/product.template/{product.id}/image_1920" if product.image_1920 else ""
            # }],
            "type": "simple",
            "status": "live" if product.active else "inactive",
            "brand": getattr(product, 'brand_id', False) and product.brand_id.name or "",
            "country_of_origin": product.fiscal_country_codes or "",
            "weight": {"value": product.weight or 0.0, "uom": product.weight_uom_name or "kg"},
            "uom": product.uom_name or "Units",
            "dimensions": {
                "length": {"length": 0, "unit": "cm"},
                "breadth": {"breadth": 0, "unit": "cm"},
                "height": {"height": 0, "unit": "cm"}
            },
            "retail_price": product.list_price,
            "selling_price": product.list_price,
            "is_perishable": False
        }

    # ----------------- API Methods -----------------

    def check_in_omniful(self):
        """Check if product exists in Omniful by SKU code."""
        for product in self:
            if not product.default_code:
                product.message_post(body="⚠️ Missing SKU: Product has no Internal Reference (SKU).")
                continue

            channel = self.env['channel.omniful'].search([('active', '=', True)], limit=1)
            if not channel:
                product.message_post(body="❌ Omniful: No active Omniful channel configured.")
                continue

            headers = {"Authorization": f"Bearer {channel.omniful_access_token}"}
            url = f"{channel.base_url_omniful}/sales-channel/public/v1/master/skus?sku_codes={product.default_code}"

            try:
                response = requests.get(url, headers=headers, timeout=15)
                _logger.info("Omniful GET Response [%s]: %s", response.status_code, response.text)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("is_success") and data.get("data"):
                        sku_data = data["data"][0]

                        product.omniful_status = sku_data.get("status", "unknown")
                        product.omniful_price = sku_data.get("selling_price", 0)
                        product.omniful_currency = sku_data.get("currency", "")
                        product.omniful_country = sku_data.get("country_of_origin", "")
                        product.omniful_response_json = json.dumps(data, indent=4, ensure_ascii=False)

                        # Build clean plain text message (no HTML tags)
                        message_body = (
                            f"✅ Found in Omniful\n"
                            f"SKU: {product.default_code}\n"
                            f"Status: {product.omniful_status}\n"
                            f"Price: {sku_data.get('selling_price')} {sku_data.get('currency')}\n"
                            f"Country: {sku_data.get('country_of_origin', 'N/A')}"
                        )

                        product.message_post(body=message_body)
                        return True
                    else:
                        product.omniful_status = "not_found"
                        product.message_post(body=f"ℹ️ Product {product.default_code} not found in Omniful.")
                else:
                    product.message_post(body=f"⚠️ API Error: Status {response.status_code}<br/>{response.text}")
            except Exception as e:
                _logger.error("Error checking product %s in Omniful: %s", product.name, str(e))
                product.message_post(body=f"❌ Omniful Error while checking {product.name}: {str(e)}")

    def send_to_omniful(self):
        """Send product to Omniful (create if not exist)."""
        for product in self:
            validation = self._validate_before_send(product)
            if not validation["valid"]:
                product.message_post(body=f"⚠️ Validation Failed: {validation['message']}")
                continue

            channel = self.env['channel.omniful'].search([('active', '=', True)], limit=1)
            if not channel:
                product.message_post(body=f"❌ Omniful: No active Omniful channel found.")
                continue

            payload = [self._build_payload(product)]
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {channel.omniful_access_token}"}
            _logger.info("Omniful Payload: %s", payload)

            try:
                response = requests.post(
                    f"{channel.base_url_omniful}/sales-channel/public/v1/master/skus",
                    headers=headers,
                    data=json.dumps(payload, ensure_ascii=False),
                    timeout=15
                )
                if response.status_code in (200, 201):
                    product.omniful_status = "created"
                    product.message_post(body=f"✅ Product {product.name} sent to Omniful successfully.")
                else:
                    product.message_post(body=f"⚠️ Failed to send Product {product.name}. "
                                              f"Status: {response.status_code}<br/>{response.text}")
            except Exception as e:
                _logger.error("Error sending product %s: %s", product.name, str(e))
                product.message_post(body=f"❌ Error sending {product.name}: {str(e)}")

    def update_in_omniful(self):
        """Update product details (name, price, etc.) if exists in Omniful."""
        channel = self.env['channel.omniful'].search([('active', '=', True)], limit=1)
        if not channel:
            for product in self:
                product.message_post(body="❌ Omniful: No active Omniful channel configured.")
            return

        payload = [self._build_payload(product) for product in self if product.default_code]

        if not payload:
            for product in self:
                product.message_post(body="⚠️ No products with SKU to update.")
            return

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {channel.omniful_access_token}"}
        try:
            response = requests.put(
                f"{channel.base_url_omniful}/sales-channel/public/v1/master/skus",
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False),
                timeout=15
            )
            if response.status_code in (200, 201):
                for product in self:
                    product.omniful_status = "updated"
                self.message_post(body=f"✅ {len(payload)} products updated successfully in Omniful.")
            else:
                self.message_post(body=f"⚠️ Update Failed. Status: {response.status_code}<br/>{response.text}")
        except Exception as e:
            _logger.error("Error updating products: %s", str(e))
            self.message_post(body=f"❌ Omniful Error while updating products: {str(e)}")

    def action_send_to_omniful(self):
        for product in self:
            product.send_to_omniful()
        return True
