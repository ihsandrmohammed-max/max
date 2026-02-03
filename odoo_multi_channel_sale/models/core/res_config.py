# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MultiChannelSaleConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    cron_import_partner = fields.Many2one('ir.cron', 'Import Customer Scheduler', readonly=True)
    cron_import_category = fields.Many2one('ir.cron', 'Import Category Scheduler', readonly=True)
    cron_import_product = fields.Many2one('ir.cron', 'Import Product Scheduler', readonly=True)
    cron_import_order = fields.Many2one('ir.cron', 'Import Order Scheduler', readonly=True)
    cron_evaluation = fields.Many2one('ir.cron', 'Cron Evaluation Scheduler', readonly=True)
    cron_clear_history = fields.Many2one('ir.cron', 'Clear Sync History Scheduler', readonly=True)

    avoid_duplicity = fields.Boolean(
        string='Avoid Duplicity (Default Code)',
        help="Check this if you want to avoid the duplicity of the imported products. "
             "In this case the product with same default code/sku will not be created again."
    )

    avoid_duplicity_using = fields.Selection(
        selection=[
            ('default_code', 'Default Code/SKU'),
            ('barcode', 'Barcode/UPC/EAN/ISBN'),
            ('both', 'Both')
        ],
        string="Avoid Duplicity Using",
        default='both',
        help="If set to Both, the uniqueness will be either on SKU/Default or "
             "UPC/EAN/Barcode using OR operator and should always be given high priority."
    )

    secret_key_webhook = fields.Char(
        string="Secret Key Webhook",
        help="Secret key for webhook"
    )

    # Save values to ir.config_parameter
    def set_values(self):
        super(MultiChannelSaleConfig, self).set_values()
        config = self.env['ir.config_parameter'].sudo()
        config.set_param('odoo_multi_channel_sale.avoid_duplicity', self.avoid_duplicity)
        config.set_param('odoo_multi_channel_sale.avoid_duplicity_using', self.avoid_duplicity_using)
        config.set_param('odoo_multi_channel_sale.secret_key_webhook', self.secret_key_webhook)

    # Load values from ir.config_parameter
    @api.model
    def get_values(self):
        res = super(MultiChannelSaleConfig, self).get_values()
        config = self.env['ir.config_parameter'].sudo()
        res.update({
            'avoid_duplicity': config.get_param('odoo_multi_channel_sale.avoid_duplicity', default=False),
            'avoid_duplicity_using': config.get_param('odoo_multi_channel_sale.avoid_duplicity_using', default='both'),
            'secret_key_webhook': config.get_param('odoo_multi_channel_sale.secret_key_webhook', default=''),
            'cron_import_partner': self.env.ref('odoo_multi_channel_sale.cron_import_partner').id,
            'cron_import_category': self.env.ref('odoo_multi_channel_sale.cron_import_category').id,
            'cron_import_product': self.env.ref('odoo_multi_channel_sale.cron_import_product').id,
            'cron_import_order': self.env.ref('odoo_multi_channel_sale.cron_import_order').id,
            'cron_evaluation': self.env.ref('odoo_multi_channel_sale.cron_evaluation').id,
            'cron_clear_history': self.env.ref('odoo_multi_channel_sale.cron_clear_history').id,
        })
        return res
