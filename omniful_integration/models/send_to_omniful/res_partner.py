from odoo import models, fields, api
import json
import requests
import re


class ResPartner(models.Model):
    _inherit = "res.partner"

    omniful_customer_id = fields.Char(string="Omniful Customer ID", readonly=True)
    omniful_response_json = fields.Text(string="Omniful Response", readonly=True)

    omniful_status = fields.Char(string="Omniful Status", readonly=True)
    omniful_email = fields.Char(string="Omniful Email", readonly=True)
    omniful_mobile = fields.Char(string="Omniful Mobile", readonly=True)



    def _get_channel(self):
        channel = self.env['channel.omniful'].search([('active', '=', True)], limit=1)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {channel.omniful_access_token}"}
        return channel, headers

    def _pretty_json(self, data):
        """Return pretty formatted JSON string for storage."""
        try:
            return json.dumps(data, indent=4, ensure_ascii=False)
        except Exception:
            return data if isinstance(data, str) else str(data)


    def _clean_mobile(self):
        raw_mobile = self.phone or self.mobile or ""
        raw_mobile = raw_mobile.strip().replace(" ", "")
        country_code = (self.country_id.phone_code and str(self.country_id.phone_code)) or ""

        # Remove country calling code like +966 or 00966
        cleaned = re.sub(rf"^\+?{country_code}", "", raw_mobile)
        cleaned = re.sub(rf"^00{country_code}", "", cleaned)

        # Keep only digits
        cleaned = re.sub(r"\D", "", cleaned)

        return cleaned

    def _build_omniful_payload(self):
        """Build a payload for Omniful based on partner fields."""
        self.ensure_one()
        data = {
            "title": self.title.name if self.title else "Mr",
            "first_name": self.name.split(" ")[0] if self.name else "",
            "last_name": " ".join(self.name.split(" ")[1:]) if self.name and len(self.name.split(" ")) > 1 else "",
            "email": self.email,
            "mobile": self._clean_mobile(),
            "country_calling_code": "+966",  # Change if dynamic calling codes needed
            "country_code": self.country_id.code or "",
            "gender": "male",  # Add gender field mapping if available
            "date_of_birth": "1990-01-01",  # Map DOB if available
            "user_name": self.email or "",
            "preferred_languages": [self.lang] if self.lang else ["en"],
            "address": {
                "address1": self.street or "",
                "address2": self.street2 or "",
                "city": self.city or "",
                "country": self.country_id.code or "",
                "state": self.state_id.name or "",
                "zip": self.zip or "",
                "default_address": True
            }
        }
        print(data)
        return data

    def action_send_to_omniful(self):
        """Send customer data to Omniful."""
        for partner in self:
            payload = partner._build_omniful_payload()

            channel, headers =self._get_channel()

            url = f"{channel.base_url_omniful}/sales-channel/public/v1/customers"
            response = requests.post(url, headers=headers, data=json.dumps(payload))

            try:
                res_json = response.json()
            except Exception:
                res_json = {"raw": response.text}

            partner.omniful_response_json = partner._pretty_json(res_json)
            if res_json.get("is_success"):
                data = res_json.get("data", {})
                partner.write({
                    "omniful_customer_id": data.get("id"),
                    "omniful_status": "Created",
                    "omniful_email": data.get("email"),
                    "omniful_mobile": data.get("mobile")
                })

    def action_check_in_omniful(self):
        """Check if this customer exists in Omniful."""
        for partner in self:
            if not partner.omniful_customer_id:
                continue

            channel, headers = self._get_channel()

            url = f"{channel.base_url_omniful}/sales-channel/public/v1/customers/{partner.omniful_customer_id}"
            response = requests.get(url, headers=headers)

            try:
                res_json = response.json()
            except Exception:
                res_json = {"raw": response.text}

            partner.omniful_response_json = partner._pretty_json(res_json)
            if res_json.get("is_success"):
                data = res_json.get("data", {})
                partner.write({
                    "omniful_status": "Exists",
                    "omniful_email": data.get("email"),
                    "omniful_mobile": data.get("mobile")
                })

    def action_update_omniful(self):
        """Update customer in Omniful."""
        for partner in self:
            if not partner.omniful_customer_id:
                continue

            payload = partner._build_omniful_payload()
            channel, headers = self._get_channel()

            url = f"{channel.base_url_omniful}/sales-channel/public/v1/customers/{partner.omniful_customer_id}"
            response = requests.put(url, headers=headers, data=json.dumps(payload))

            try:
                res_json = response.json()
            except Exception:
                res_json = {"raw": response.text}

            partner.omniful_response_json = partner._pretty_json(res_json)
            if res_json.get("is_success"):
                partner.omniful_status = "Updated"
