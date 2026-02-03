# -*- coding: utf-8 -*-

from odoo import fields, models
import json


class SallaOrderJsonViewer(models.TransientModel):
    """
    Transient model to display Salla order JSON data in a popup.
    Stores the JSON response from Salla API for viewing in a tree format.
    """
    _name = 'salla.order.json.viewer'
    _description = 'Salla Order JSON Viewer'

    order_id = fields.Char(
        string='Order ID',
        readonly=True,
        help='Salla order ID (store_id)'
    )
    order_name = fields.Char(
        string='Order Name',
        readonly=True,
        help='Order feed name'
    )
    json_data = fields.Text(
        string='JSON Data',
        readonly=True,
        help='Formatted JSON data from Salla API'
    )

    def format_json(self, data):
        """
        Format dictionary to pretty JSON string.
        
        :param data: Dictionary or list to format
        :return: Formatted JSON string
        """
        try:
            return json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as e:
            return f"Error formatting JSON: {str(e)}"
