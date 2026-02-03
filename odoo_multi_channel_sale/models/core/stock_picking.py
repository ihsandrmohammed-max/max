# -*- coding: utf-8 -*-

from odoo import models, fields, api
from logging import getLogger

_logger = getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    salla_order_status_id = fields.Many2one(
        'salla.order.status',
        string='Salla Order Status',
        help='Salla order status'
    )

    def _action_done(self):
        from_webhook = self._context.get('from_webhook')
        for rec in self:
            if not from_webhook:
                rec.wk_pre_do_transfer()
            result = super(StockPicking, rec)._action_done()
            if not from_webhook:
                rec.wk_post_do_transfer(result)

    def button_validate(self):
        result = super(StockPicking, self).button_validate()

        for picking in self:
            # Apply only on outgoing deliveries
            if picking.picking_type_code != 'outgoing':
                continue

            # Must be linked to a Sale Order
            if not picking.sale_id:
                continue

            # Skip return pickings
            if picking.is_return_picking:
                continue

            sale = picking.sale_id

            # Skip if already fully invoiced
            if sale.invoice_status == 'invoiced':
                continue

            # Create invoice if not exists
            sale._create_invoices()

        return result


    def wk_pre_do_transfer(self):
        if self.sale_id and self.picking_type_code == 'outgoing':
            mapping_ids = self.sudo().sale_id.channel_mapping_ids
            if mapping_ids and mapping_ids[0].channel_id.state == 'validate' and mapping_ids[0].channel_id.active:
                channel_id = mapping_ids[0].channel_id
                if hasattr(channel_id, '%s_pre_do_transfer' % channel_id.channel) and channel_id.sync_shipment and channel_id.state == 'validate':
                    getattr(channel_id, '%s_pre_do_transfer' % channel_id.channel)(self, mapping_ids)

    def wk_post_do_transfer(self, result):
        if self.sale_id and self.picking_type_code == 'outgoing':
            mapping_ids = self.sudo().sale_id.channel_mapping_ids
            if mapping_ids and mapping_ids[0].channel_id.state == 'validate' and mapping_ids[0].channel_id.active:
                channel_id = mapping_ids[0].channel_id
                if hasattr(channel_id, '%s_post_do_transfer' % channel_id.channel) and channel_id.sync_shipment and channel_id.state == 'validate':
                    res = getattr(channel_id, '%s_post_do_transfer' % channel_id.channel)(self, mapping_ids, result)
                    sync_vals = dict(
                        action_on='order_status',
                        ecomstore_refrence=mapping_ids[0].store_order_id,
                        odoo_id=mapping_ids[0].odoo_order_id,
                        action_type='export',
                    )
                    if res:
                        sync_vals['status'] = 'success'
                        sync_vals['summary'] = 'RealTime Order Status -> Shipped'
                    else:
                        sync_vals['status'] = 'error'
                        sync_vals['summary'] = 'The order has not been shipped at the ecommerce end.'
                    channel_id._create_sync(sync_vals)

    def btn_update_in_salla(self):
        """
        Update order in Salla platform.
        This method is called when the "Update in Salla" button is clicked.
        Currently logs order information for validation purposes.

        Extra debug information added:
        - Read the first record in `multi.channel.sale` and log its `access_token`.
        - Read the first `order.feed` record where `name` matches the picking `origin`
          and log: `id`, `name`, and `store_id`.

        Note:
        - This method uses `sudo()` when reading the above models to avoid access right
          issues during troubleshooting. Be careful when logging sensitive values such
          as access tokens in production.
        """
        for picking in self:
            _logger.info("Updating order in Salla | picking_id=%s", picking.id)
            _logger.info("Origin: %s", picking.origin or 'N/A')

            # Log first Multi Channel Sale instance access token for troubleshooting.
            channel = self.env['multi.channel.sale'].sudo().search([], order='id asc', limit=1)
            if channel:
                _logger.info(
                    "Multi Channel Sale (first) | id=%s | name=%s | access_token=%s",
                    channel.id, channel.name, channel.access_token or 'N/A'
                )
            else:
                _logger.info("Multi Channel Sale (first) | Not found")

            # Log matching Order Feed record (first) by origin.
            if picking.origin:
                order_feed = self.env['order.feed'].sudo().search(
                    [('name', '=', picking.origin)],
                    order='id asc',
                    limit=1
                )
                if order_feed:
                    _logger.info(
                        "Order Feed (matched by origin) | id=%s | name=%s | store_id=%s",
                        order_feed.id,
                        order_feed.name,
                        getattr(order_feed, 'store_id', False) or 'N/A',
                    )
                else:
                    _logger.info(
                        "Order Feed (matched by origin) | Not found | origin=%s",
                        picking.origin,
                    )
            else:
                _logger.info("Order Feed (matched by origin) | Skipped (no origin)")

            if picking.sale_id:
                _logger.info("Sale Order ID: %s, Name: %s", picking.sale_id.id, picking.sale_id.name)
            else:
                _logger.info("Sale Order: Not linked")
        return True

    @api.model
    def update_salla(self, picking_id):
        print(picking_id)
        picking = self.browse(int(picking_id))

        _logger.info("Updating order in Salla | picking_id=%s", picking.id)
        _logger.info("Origin: %s", picking.origin or 'N/A')

        # Log first Multi Channel Sale instance access token for troubleshooting.
        channel = self.env['multi.channel.sale'].sudo().search([], order='id asc', limit=1)
        if channel:
            _logger.info(
                "Multi Channel Sale (first) | id=%s | name=%s | access_token=%s",
                channel.id, channel.name, channel.access_token or 'N/A'
            )
        else:
            _logger.info("Multi Channel Sale (first) | Not found")

        # Log matching Order Feed record (first) by origin.
        if picking.origin:
            order_feed = self.env['order.feed'].sudo().search(
                [('name', '=', picking.origin)],
                order='id asc',
                limit=1
            )
            if order_feed:
                _logger.info(
                    "Order Feed (matched by origin) | id=%s | name=%s | store_id=%s",
                    order_feed.id,
                    order_feed.name,
                    getattr(order_feed, 'store_id', False) or 'N/A',
                )
            else:
                _logger.info(
                    "Order Feed (matched by origin) | Not found | origin=%s",
                    picking.origin,
                )
        else:
            _logger.info("Order Feed (matched by origin) | Skipped (no origin)")

        if picking.sale_id:
            _logger.info("Sale Order ID: %s, Name: %s", picking.sale_id.id, picking.sale_id.name)
        else:
            _logger.info("Sale Order: Not linked")
        return True