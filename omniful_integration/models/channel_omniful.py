from odoo import models, fields, api


class ChannelOmniful(models.Model):
    _name = 'channel.omniful'
    _description = 'Omniful Channel Configuration'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(
        string='Channel Name',
        required=True,
        help='Name of the Omniful channel'
    )
    
    omniful_access_token = fields.Char(
        string='Access Token',
        help='Access token for Omniful API authentication'
    )
    
    base_url_omniful = fields.Char(
        string='Base URL',
        default='https://api.omniful.com',
        help='Base URL for Omniful API endpoints'
    )
    
    omniful_refresh_token = fields.Char(
        string='Refresh Token',
        help='Refresh token for retrieving new access tokens',
        size=2000
    )
    
    omniful_client_id = fields.Char(
        string='Client ID',
        help='Client ID for API authentication'
    )
    
    omniful_client_secret = fields.Char(
        string='Client Secret',
        help='Client secret for API authentication'
    )

    webhook_secret_key = fields.Char(
        string='Webhook Secret Key',
        help='Webhook secret key for Omniful API authentication'
    )

    hub_code = fields.Char(
        string='Hub Code',
        help='Hub code for Shop code'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this channel is active'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help='Company this channel belongs to'
    )
    
    # Computed fields
    inventory_feed_count = fields.Integer(
        string='Inventory Feeds',
        compute='_compute_inventory_feed_count',
        help='Number of inventory feeds for this channel'
    )
    
    @api.depends('name', 'hub_code')
    def _compute_inventory_feed_count(self):
        for record in self:
            record.inventory_feed_count = self.env['inventory.feed'].search_count([
                ('channel_id', '=', record.id)
            ])
    
    def action_view_inventory_feeds(self):
        """Action to view inventory feeds for this channel"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Inventory Feeds - {self.name}',
            'res_model': 'inventory.feed',
            'view_mode': 'list,form',
            'domain': [('channel_id', '=', self.id)],
            'context': {'default_channel_id': self.id}
        }

    def _get_omniful_access_token(self):
        # TODO implement refresh token logic
        return self.omniful_access_token