# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons.odoo_multi_channel_sale.tools import parse_float, extract_list as EL

import copy
import logging
import requests
import json

_logger = logging.getLogger(__name__)
#_logger.setLevel(logging.ERROR)


OrderFields = [
    'name',
    'store_id',
    'store_source',

    'partner_id',
    'order_state',
    'carrier_id',
    'date_invoice',
    'date_order',
    'confirmation_date',
    'date_shipping',
    'line_ids',
    'line_name',
    'line_price_unit',
    'line_product_id',
    'line_product_default_code',
    'line_product_barcode',
    'line_variant_ids',
    'line_source',
    'line_product_uom_qty',
    'line_taxes',
    'note',
    'total_amount',
]


class OrderFeed(models.Model):
    _name = 'order.feed'
    _inherit = ['wk.feed', 'order.line.feed']
    _description = 'Order Feed'

    name = fields.Char('Name', required=True, index=True)

    partner_id = fields.Char('Store Customer ID')
    order_state = fields.Char('Order State')
    date_order = fields.Char('Order Date')
    confirmation_date = fields.Char('Confirmation Date')
    date_invoice = fields.Char('Invoice Date')
    date_shipping = fields.Char('Shipping Date')
    carrier_id = fields.Char('Delivery Method', help='Delivery Method Name')
    payment_method = fields.Char('Payment Method', help='Payment Method Name')
    currency = fields.Char('Currency Name')
    customer_is_guest = fields.Boolean('Customer Is Guest')
    customer_name = fields.Char('Customer Name')
    customer_phone = fields.Char('Customer Phone')
    customer_mobile = fields.Char('Customer Mobile')
    customer_last_name = fields.Char('Customer Last Name')
    customer_email = fields.Char('Customer Email')
    customer_company = fields.Char('Customer Company')

    shipping_partner_id = fields.Char('Shipping Partner ID')
    shipping_name = fields.Char('Shipping Name')
    shipping_last_name = fields.Char('Shipping Last Name')
    shipping_email = fields.Char('Shipping Email')
    shipping_phone = fields.Char('Shipping Phone')
    shipping_mobile = fields.Char('Shipping Mobile')
    shipping_street = fields.Char('Shipping Street')
    shipping_street2 = fields.Char('Shipping street2')
    shipping_city = fields.Char('Shipping City')
    shipping_zip = fields.Char('Shipping Zip Code')
    shipping_state_name = fields.Char('Shipping State Name')
    shipping_state_id = fields.Char('Shipping State Code')
    shipping_country_id = fields.Char('Shipping Country Code')

    invoice_partner_id = fields.Char('Invoice Partner ID')
    invoice_name = fields.Char('Invoice Name')
    invoice_last_name = fields.Char('Invoice Last Name')
    invoice_email = fields.Char('Invoice Email')
    invoice_phone = fields.Char('Invoice Phone')
    invoice_mobile = fields.Char('Invoice Mobile')
    invoice_street = fields.Char('Invoice Street')
    invoice_street2 = fields.Char('Invoice street2')
    invoice_city = fields.Char('Invoice City')
    invoice_zip = fields.Char('Invoice Zip Code')
    invoice_state_name = fields.Char('Invoice State Name')
    invoice_state_id = fields.Char('Invoice State Code')
    invoice_country_id = fields.Char('Invoice Country Code')
    customer_vat = fields.Char('Customer VAT')
    note = fields.Text('Notes')

    same_shipping_billing = fields.Boolean(
        string='Shipping Address Same As Billing',
        default=True
    )
    line_type = fields.Selection(
        selection=[
            ('single', 'Single Order Line'),
            ('multi', 'Multi Order Line')
        ],
        default='single',
        string='Line Type',
    )
    total_amount = fields.Float('Total Amount Salla')
    line_ids = fields.One2many('order.line.feed', 'order_feed_id', string='Line Ids')

    _sql_constraints = [
        (
            'order_feed_name_unique',
            'unique(name)',
            'Order Feed with this Name already exists!'
        )
    ]



    def _create_feed(self, order_data):
        channel_id, store_id = order_data.get('channel_id'), str(order_data.get('store_id'))
        feed_id = self._context.get('order_feeds').get(channel_id, {}).get(store_id)
        print(order_data)
# Todo(Pankaj Kumar): Change feed field from state_id,country_id to state_code,country_code
        order_data['invoice_state_id'] = order_data.pop('invoice_state_code', False) or order_data.pop('invoice_state_id', False)
        order_data['invoice_country_id'] = order_data.pop('invoice_country_code', False) or order_data.pop('invoice_country_id', False)

        if not order_data.get('same_shipping_billing'):
            order_data['shipping_state_id'] = order_data.pop('shipping_state_code', False) or order_data.pop('shipping_state_id', False)
            order_data['shipping_country_id'] = order_data.pop('shipping_country_code', False) or order_data.pop('shipping_country_id', False)
# & remove this code
        try:
            if feed_id:
                feed = self.browse(feed_id)
                order_data.get('line_ids').insert(0, (5, 0))
                order_data.update(state='draft', total_amount=order_data.get('total_amount'))
                feed.write(order_data)
            else:
                print(order_data)
                feed = self.create(order_data)
        except Exception as e:
            _logger.error(
                "Failed to create feed for Order: "
                f"{order_data.get('store_id')}"
                f" Due to: {e.args[0]}"
            )
        else:
            return feed

    @api.model
    def old_get_order_line_vals(self, vals, carrier_id, channel_id):
        _logger.info("_get_order_line_vals", vals)
        _logger.info(carrier_id)
        _logger.info(channel_id)
        message = ''
        status = True
        lines = []
        line_ids, line_name = vals.pop('line_ids'), vals.pop('line_name')
        line_price_unit = vals.pop('line_price_unit')
        if line_price_unit:
            line_price_unit = parse_float(line_price_unit)
        line_product_id = vals.pop('line_product_id')
        line_variant_ids = vals.pop('line_variant_ids')
        line_product_uom_qty = vals.pop('line_product_uom_qty')
        line_product_default_code = vals.pop('line_product_default_code')
        line_source = vals.pop('line_source')
        line_product_barcode = vals.pop('line_product_barcode')
        line_taxes = vals.pop('line_taxes')

        tax_list, discount_tax_ids, apply_tax_on_discount_line = [], False, False

        if line_ids:
            order_line_feed = self.env['order.line.feed'].browse(line_ids)
            discount_line = order_line_feed.filtered(lambda line: line.line_source == 'discount')
            if channel_id.tax_on_discount_line and discount_line and not discount_line.line_taxes:
                for line_id in order_line_feed.filtered(lambda line: line.line_source == 'product'):
                    tax_lines = eval(line_id.line_taxes) if line_id.line_taxes else []
                    if not tax_lines or (tax_list and len(tax_list) != len(tax_lines)):
                        apply_tax_on_discount_line = False
                        break
                    tax = [float(tax_line.get('rate', tax_line.get('tax_rate', tax_line.get('value',0)))) for tax_line in tax_lines]
                    tax.sort()
                    if tax_list and tax_list != tax:
                        apply_tax_on_discount_line = False
                        break
                    elif not tax_list:
                        apply_tax_on_discount_line = True
                        tax_list.extend(tax)
                    if not discount_tax_ids:
                        discount_tax_ids = self.get_taxes_ids(line_id.line_taxes)

            for line_id in order_line_feed:
                product_id = False
                line_price_unit = line_id.line_price_unit
                if line_price_unit:
                    line_price_unit = parse_float(line_price_unit)
                if line_id.line_source == 'delivery' and type(carrier_id) is not str:
                    product_id = carrier_id.product_id
                elif line_id.line_source == 'discount':
                    if not channel_id.discount_product_id:
                        product_id = channel_id.create_product('discount')
                        channel_id.discount_product_id = product_id.id
                    product_id = channel_id.discount_product_id
                    line_price_unit = -line_price_unit
                elif line_id.line_source == 'product':
                    product_res = self.get_product_id(
                        line_id.line_product_id,
                        line_id.line_variant_ids or 'No Variants',
                        channel_id,
                        line_id.line_product_default_code,
                        line_id.line_product_barcode,
                    )
                    product_id = product_res.get('product_id')
                    if product_res.get('message'):
                        _logger.error("OrderLineError1 %r" % product_res)
                        message += product_res.get('message')
                if product_id:
                    product_uom_id = product_id.uom_id.id
                    line = dict(
                        name=line_id.line_name,
                        price_unit=line_price_unit,
                        product_id=product_id.id,
                        customer_lead=product_id.sale_delay,
                        product_uom_qty=line_id.line_product_uom_qty,
                        is_delivery=line_id.line_source == 'delivery',
                        product_uom=product_uom_id,

                    )


                     ### Manange the discount tax here ##############
                    if apply_tax_on_discount_line and line_id.line_source != 'delivery':
                        line['tax_id'] = discount_tax_ids
                    else:
                        line['tax_id'] = self.get_taxes_ids(line_id.line_taxes)


                    # ADD TAX
                    lines += [(0, 0, line)]
                else:
                    status = False
                    message += f"No product found for order line {line_id.line_name}"
        else:
            product_res = self.get_product_id(
                line_product_id,
                line_variant_ids or 'No Variants',
                channel_id,
                line_product_default_code,
                line_product_barcode,

            )
            product_id = product_res.get('product_id')
            if product_id:
                if line_product_uom_qty:
                    line_product_uom_qty = parse_float(line_product_uom_qty) or 1
                line = dict(
                    name=line_name or '',
                    price_unit=(line_price_unit),
                    product_id=product_id.id,
                    customer_lead=product_id.sale_delay,
                    is_delivery=line_source == 'delivery',
                    product_uom_qty=(line_product_uom_qty),
                    product_uom=product_id.uom_id.id,
                )
                line['tax_id'] = self.get_taxes_ids(line_taxes)
                # ADD TAX
                lines += [(0, 0, line)]
            else:
                _logger.error("OrderLineError2 %r" % product_res)
                message += product_res.get('message')
                status = False
        return dict(
            message=message,
            order_line=lines,
            status=status
        )

    @api.model
    def old_get_order_line_vals(self, vals, carrier_id, channel_id):
        _logger.info("=== _get_order_line_vals START ===")
        _logger.info("Input vals: %s", vals)
        _logger.info("Carrier ID: %s", carrier_id)
        _logger.info("Channel ID: %s", channel_id)

        message = ''
        status = True
        lines = []

        # --- Extract values ---
        line_ids = vals.pop('line_ids')
        line_name = vals.pop('line_name')
        line_price_unit = vals.pop('line_price_unit')
        if line_price_unit:
            _logger.info("Raw line_price_unit: %s", line_price_unit)
            line_price_unit = parse_float(line_price_unit)
            _logger.info("Parsed line_price_unit: %s", line_price_unit)

        line_product_id = vals.pop('line_product_id')
        line_variant_ids = vals.pop('line_variant_ids')
        line_product_uom_qty = vals.pop('line_product_uom_qty')
        line_product_default_code = vals.pop('line_product_default_code')
        line_source = vals.pop('line_source')
        line_product_barcode = vals.pop('line_product_barcode')
        line_taxes = vals.pop('line_taxes')

        _logger.info("Extracted vals -> IDs: %s, Name: %s, ProductID: %s, VariantIDs: %s, Qty: %s, Source: %s",
                     line_ids, line_name, line_product_id, line_variant_ids, line_product_uom_qty, line_source)

        tax_list, discount_tax_ids, apply_tax_on_discount_line = [], False, False

        if line_ids:
            _logger.info("Processing existing order lines with IDs: %s", line_ids)
            order_line_feed = self.env['order.line.feed'].browse(line_ids)
            discount_line = order_line_feed.filtered(lambda line: line.line_source == 'discount')

            if channel_id.tax_on_discount_line and discount_line and not discount_line.line_taxes:
                _logger.info("Checking tax application for discount line.")
                for line_id in order_line_feed.filtered(lambda l: l.line_source == 'product'):
                    tax_lines = eval(line_id.line_taxes) if line_id.line_taxes else []
                    _logger.info("Product line taxes: %s", tax_lines)
                    if not tax_lines or (tax_list and len(tax_list) != len(tax_lines)):
                        _logger.info("Tax list mismatch. Will not apply tax on discount.")
                        apply_tax_on_discount_line = False
                        break

                    tax = [float(tax_line.get('rate', tax_line.get('tax_rate', tax_line.get('value', 0)))) for tax_line
                           in tax_lines]
                    tax.sort()
                    if tax_list and tax_list != tax:
                        _logger.info("Different tax sets found. Skipping discount tax application.")
                        apply_tax_on_discount_line = False
                        break
                    elif not tax_list:
                        apply_tax_on_discount_line = True
                        tax_list.extend(tax)
                        _logger.info("Tax list collected for discount: %s", tax_list)
                    if not discount_tax_ids:
                        discount_tax_ids = self.get_taxes_ids(line_id.line_taxes)
                        _logger.info("Collected discount tax IDs: %s", discount_tax_ids)

            for line_id in order_line_feed:
                _logger.info("Processing line: %s", line_id.line_name)
                product_id = False
                line_price_unit = line_id.line_price_unit
                if line_price_unit:
                    line_price_unit = parse_float(line_price_unit)
                _logger.info("Line source: %s, price_unit: %s", line_id.line_source, line_price_unit)

                if line_id.line_source == 'delivery' and type(carrier_id) is not str:
                    product_id = carrier_id.product_id
                    _logger.info("Using carrier product: %s", product_id)
                elif line_id.line_source == 'discount':
                    if not channel_id.discount_product_id:
                        product_id = channel_id.create_product('discount')
                        channel_id.discount_product_id = product_id.id
                        _logger.info("Created discount product: %s", product_id)
                    product_id = channel_id.discount_product_id
                    line_price_unit = -line_price_unit
                    _logger.info("Negative price applied for discount: %s", line_price_unit)

                elif line_id.line_source == 'cash_on_delivery':
                    if not channel_id.cash_delivery_product_id:
                        product_id = channel_id.create_product('Cash on Delivery')
                        channel_id.cash_delivery_product_id = product_id.id
                        _logger.info("Created cash_delivery_product_id product: %s", product_id)
                    product_id = channel_id.cash_delivery_product_id
                    line_price_unit = line_price_unit

                elif line_id.line_source == 'product':
                    product_res = self.get_product_id(
                        line_id.line_product_id,
                        line_id.line_variant_ids or 'No Variants',
                        channel_id,
                        line_id.line_product_default_code,
                        line_id.line_product_barcode,
                    )
                    _logger.info("Product resolution result: %s", product_res)
                    product_id = product_res.get('product_id')

                    if product_res.get('message'):
                        _logger.error("OrderLineError1: %s", product_res)
                        message += product_res.get('message')

                if product_id:
                    product_uom_id = product_id.uom_id.id
                    line = dict(
                        name=line_id.line_name,
                        price_unit=line_price_unit,
                        product_id=product_id.id,
                        customer_lead=product_id.sale_delay,
                        product_uom_qty=line_id.line_product_uom_qty,
                        is_delivery=line_id.line_source,
                        product_uom=product_uom_id,
                        discount=line_id.discount_percentage,
                        # for Tax
                        tax_id=self.get_taxes_ids(line_id.line_taxes),
                    )

                    if apply_tax_on_discount_line and line_id.line_source != 'delivery':
                        line['tax_id'] = discount_tax_ids
                    else:
                        line['tax_id'] = self.get_taxes_ids(line_id.line_taxes)

                    if line_id.line_source == 'product' and line['tax_id'] == []:
                        line['tax_id'] = product_id.taxes_id.ids

                    _logger.info("Built line dict: %s", line)
                    # start check if line source is cash_on_delivery or delivery get tax from product and set in line
                    _logger.info("line_id dict 01: %s", line_id.read())
                    if line_id.line_source == 'cash_on_delivery' or line_id.line_source == 'delivery' or line_id.line_source == 'discount':
                        _logger.info(" line_id.line_source  >>>> : %s",  line_id.line_source )
                        line['tax_id'] = product_id.taxes_id.ids
                        _logger.info("Product tax_id: %s", product_id.taxes_id.ids)
                    _logger.info("Built line dict 02: %s", line)
                    lines.append((0, 0, line))
                else:
                    status = False
                    _logger.warning("No product found for order line: %s", line_id.line_name)
                    message += f"No product found for order line {line_id.line_name}"
        else:
            _logger.info("Processing single line (no line_ids).")
            product_res = self.get_product_id(
                line_product_id,
                line_variant_ids or 'No Variants',
                channel_id,
                line_product_default_code,
                line_product_barcode,
            )
            _logger.info("Product resolution result: %s", product_res)
            product_id = product_res.get('product_id')
            if product_id:
                if line_product_uom_qty:
                    line_product_uom_qty = parse_float(line_product_uom_qty) or 1
                line = dict(
                    name=line_name or '',
                    price_unit=line_price_unit,
                    product_id=product_id.id,
                    customer_lead=product_id.sale_delay,
                    is_delivery=line_source == 'delivery',
                    product_uom_qty=line_product_uom_qty,
                    product_uom=product_id.uom_id.id,
                )
                line['tax_id'] = self.get_taxes_ids(line_taxes)
                _logger.info("Built single line dict: %s", line)



                lines.append((0, 0, line))
            else:
                _logger.error("OrderLineError2: %s", product_res)
                message += product_res.get('message')
                status = False

        _logger.info("=== _get_order_line_vals END ===")
        _logger.info("Final lines: %s", lines)
        _logger.info("Final status: %s, message: %s", status, message)

        return dict(
            message=message,
            order_line=lines,
            status=status
        )

    @api.model
    def _get_order_line_vals(self, vals, carrier_id, channel_id):
        _logger.info("=== _get_order_line_vals START ===")
        _logger.info("Input vals: %s", vals)
        _logger.info("Carrier ID: %s", carrier_id)
        _logger.info("Channel ID: %s", channel_id)

        message = ''
        status = True
        lines = []

        # --- Extract values ---
        line_ids = vals.pop('line_ids')
        line_name = vals.pop('line_name')
        line_price_unit = vals.pop('line_price_unit')
        if line_price_unit:
            _logger.info("Raw line_price_unit: %s", line_price_unit)
            line_price_unit = parse_float(line_price_unit)
            _logger.info("Parsed line_price_unit: %s", line_price_unit)

        line_product_id = vals.pop('line_product_id')
        line_variant_ids = vals.pop('line_variant_ids')
        line_product_uom_qty = vals.pop('line_product_uom_qty')
        line_product_default_code = vals.pop('line_product_default_code')
        line_source = vals.pop('line_source')
        line_product_barcode = vals.pop('line_product_barcode')
        line_taxes = vals.pop('line_taxes')

        _logger.info(
            "Extracted vals -> IDs: %s, Name: %s, ProductID: %s, VariantIDs: %s, Qty: %s, Source: %s",
            line_ids, line_name, line_product_id, line_variant_ids, line_product_uom_qty, line_source
        )

        tax_list, discount_tax_ids, apply_tax_on_discount_line = [], False, False

        if line_ids:
            _logger.info("Processing existing order lines with IDs: %s", line_ids)
            order_line_feed = self.env['order.line.feed'].browse(line_ids)
            discount_line = order_line_feed.filtered(lambda line: line.line_source == 'discount')

            if channel_id.tax_on_discount_line and discount_line and not discount_line.line_taxes:
                _logger.info("Checking tax application for discount line.")
                for line_id in order_line_feed.filtered(lambda l: l.line_source == 'product'):
                    tax_lines = eval(line_id.line_taxes) if line_id.line_taxes else []
                    _logger.info("Product line taxes: %s", tax_lines)
                    if not tax_lines or (tax_list and len(tax_list) != len(tax_lines)):
                        _logger.info("Tax list mismatch. Will not apply tax on discount.")
                        apply_tax_on_discount_line = False
                        break

                    tax = [float(tax_line.get('rate', tax_line.get('tax_rate', tax_line.get('value', 0)))) for tax_line
                           in tax_lines]
                    tax.sort()
                    if tax_list and tax_list != tax:
                        _logger.info("Different tax sets found. Skipping discount tax application.")
                        apply_tax_on_discount_line = False
                        break
                    elif not tax_list:
                        apply_tax_on_discount_line = True
                        tax_list.extend(tax)
                        _logger.info("Tax list collected for discount: %s", tax_list)
                    if not discount_tax_ids:
                        discount_tax_ids = self.get_taxes_ids(line_id.line_taxes)
                        _logger.info("Collected discount tax IDs: %s", discount_tax_ids)

            for line_id in order_line_feed:
                _logger.info("Processing line: %s", line_id.line_name)
                product_id = False
                line_price_unit = line_id.line_price_unit
                if line_price_unit:
                    line_price_unit = parse_float(line_price_unit)
                _logger.info("Line source: %s, price_unit: %s", line_id.line_source, line_price_unit)

                if line_id.line_source == 'delivery':
                    if carrier_id and getattr(carrier_id, 'product_id', False):
                        product_id = carrier_id.product_id
                        _logger.info("Using carrier product from carrier: %s", product_id)

                    else:
                        if not channel_id.delivery_product_id:
                            _logger.info(
                                "No delivery_product_id on channel. Creating default Delivery product for line %s",
                                line_id.line_name
                            )
                            product_id = channel_id.create_product('Delivery')
                            channel_id.delivery_product_id = product_id.id
                            _logger.info("Created and set channel.delivery_product_id: %s", product_id)
                        product_id = channel_id.delivery_product_id
                        _logger.info("Using channel delivery_product_id: %s", product_id)

                elif line_id.line_source == 'discount':
                    if not channel_id.discount_product_id:
                        product_id = channel_id.create_product('discount')
                        channel_id.discount_product_id = product_id.id
                        _logger.info("Created discount product: %s", product_id)
                    product_id = channel_id.discount_product_id
                    line_price_unit = -line_price_unit
                    _logger.info("Negative price applied for discount: %s", line_price_unit)

                elif line_id.line_source == 'cash_on_delivery':
                    if not channel_id.cash_delivery_product_id:
                        product_id = channel_id.create_product('Cash on Delivery')
                        channel_id.cash_delivery_product_id = product_id.id
                        _logger.info("Created cash_delivery_product_id product: %s", product_id)
                    product_id = channel_id.cash_delivery_product_id
                    line_price_unit = line_price_unit

                elif line_id.line_source == 'product':
                    product_res = self.get_product_id(
                        line_id.line_product_id,
                        line_id.line_variant_ids or 'No Variants',
                        channel_id,
                        line_id.line_product_default_code,
                        line_id.line_product_barcode,
                    )
                    _logger.info("Product resolution result: %s", product_res)
                    product_id = product_res.get('product_id')

                    if product_res.get('message'):
                        _logger.error("OrderLineError1: %s", product_res)
                        message += product_res.get('message')

                if product_id:
                    product_uom_id = product_id.uom_id.id
                    line = dict(
                        name=line_id.line_name,
                        price_unit=line_price_unit,
                        product_id=product_id.id,
                        customer_lead=product_id.sale_delay,
                        product_uom_qty=line_id.line_product_uom_qty,
                        is_delivery=line_id.line_source,
                        product_uom=product_uom_id,
                        discount=line_id.discount_percentage,
                        tax_id=self.get_taxes_ids(line_id.line_taxes),
                    )

                    if apply_tax_on_discount_line and line_id.line_source != 'delivery':
                        line['tax_id'] = discount_tax_ids
                    else:
                        line['tax_id'] = self.get_taxes_ids(line_id.line_taxes)

                    if line_id.line_source == 'product' and line['tax_id'] == []:
                        line['tax_id'] = product_id.taxes_id.ids

                    _logger.info("Built line dict: %s", line)
                    # start check if line source is cash_on_delivery or delivery get tax from product and set in line
                    _logger.info("line_id dict 01: %s", line_id.read())
                    if line_id.line_source == 'cash_on_delivery' or line_id.line_source == 'delivery' or line_id.line_source == 'discount':
                        _logger.info(" line_id.line_source  >>>> : %s", line_id.line_source)
                        line['tax_id'] = product_id.taxes_id.ids
                        _logger.info("Product tax_id: %s", product_id.taxes_id.ids)
                    _logger.info("Built line dict 02: %s", line)
                    lines.append((0, 0, line))
                else:
                    status = False
                    _logger.warning("No product found for order line: %s", line_id.line_name)
                    message += f"No product found for order line {line_id.line_name}"
        else:
            _logger.info("Processing single line (no line_ids).")
            product_res = self.get_product_id(
                line_product_id,
                line_variant_ids or 'No Variants',
                channel_id,
                line_product_default_code,
                line_product_barcode,
            )
            _logger.info("Product resolution result: %s", product_res)
            product_id = product_res.get('product_id')
            if product_id:
                if line_product_uom_qty:
                    line_product_uom_qty = parse_float(line_product_uom_qty) or 1
                line = dict(
                    name=line_name or '',
                    price_unit=line_price_unit,
                    product_id=product_id.id,
                    customer_lead=product_id.sale_delay,
                    is_delivery=line_source == 'delivery',
                    product_uom_qty=line_product_uom_qty,
                    product_uom=product_id.uom_id.id,
                )
                line['tax_id'] = self.get_taxes_ids(line_taxes)
                _logger.info("Built single line dict: %s", line)

                lines.append((0, 0, line))
            else:
                _logger.error("OrderLineError2: %s", product_res)
                message += product_res.get('message')
                status = False

        _logger.info("=== _get_order_line_vals END ===")
        _logger.info("Final lines: %s", lines)
        _logger.info("Final status: %s, message: %s", status, message)

        return dict(
            message=message,
            order_line=lines,
            status=status
        )


    def old_get_taxes_ids(self, taxes):
        _logger.info("get_taxes_ids %r" % taxes)
        if not taxes:
            return False
        tx_ids = []
        for tax in eval(taxes):
            tax_rate = tax.get('rate', tax.get('tax_rate', tax.get('value')))
            if not tax_rate:
                continue
            tx_rate = float(tax_rate)
            tx_type = tax.get('type', tax.get('tax_type', 'percent'))
            domain = [('channel_id', '=', self.channel_id.id), ('store_tax_value_id', '=', tx_rate), ('tax_type', '=', tx_type)]
            tx_inclusive = None
            if 'included_in_price' in tax:
                tx_inclusive = tax['included_in_price']
            elif 'include_in_price' in tax:
                tx_inclusive = tax['include_in_price']
            elif 'inclusive' in tax:
                tx_inclusive = tax['inclusive']
            elif 'included' in tax:
                tx_inclusive = tax['included']
            if tx_inclusive is not None:
                domain.append(('include_in_price', '=', tx_inclusive))
            mapping = self.env['channel.account.mappings'].search(domain, limit=1)
            if mapping:
                tx_ids.append(mapping.tax_name.id)
            else:
                domain = [('amount', '=', tx_rate), ('amount_type', '=', tx_type)]
                if tx_inclusive is None:
                    tx_inclusive = self.channel_id.default_tax_type == 'include'
                domain.append(('price_include', '=', tx_inclusive))
                tx_name = tax.get('name', tax.get('tax_name'))
                if tx_name:
                    domain.append(('name', '=', tx_name))
                else:
                    tx_name = f"{self.channel_id.channel}_{self.channel_id.id}_{tx_rate}"
                tx = self.env['account.tax'].search(domain, limit=1)
                if not tx:
                    tx = self.env['account.tax'].create(
                        {
                            'name': tx_name,
                            'amount_type': tx_type,
                            'price_include': tx_inclusive,
                            'amount': tx_rate,
                        }
                    )
                tx_ids.append(tx.id)
                self.env['channel.account.mappings'].create(
                    {
                        'channel_id': self.channel_id.id,
                        'store_tax_value_id': str(tx_rate),
                        'tax_type': tx_type,
                        'include_in_price': tx_inclusive,
                        'tax_name': tx.id,
                        'odoo_tax_id': tx.id,
                    }
                )
        return [(6, 0, tx_ids)]

    def get_taxes_ids(self, taxes):
        _logger.info("🔍 [get_taxes_ids] Raw input taxes: %r", taxes)

        if not taxes:
            _logger.warning("⚠️ [get_taxes_ids] No taxes provided, returning False.")
            return False

        try:
            parsed_taxes = eval(taxes) if isinstance(taxes, str) else taxes
            _logger.info("✅ [get_taxes_ids] Parsed taxes: %r", parsed_taxes)
        except Exception as e:
            _logger.error("❌ [get_taxes_ids] Failed to eval taxes: %s", e, exc_info=True)
            return False

        tx_ids = []

        for idx, tax in enumerate(parsed_taxes):
            _logger.info("➡️ [get_taxes_ids] Processing tax #%d: %r", idx + 1, tax)

            tax_rate = tax.get('rate', tax.get('tax_rate', tax.get('value')))
            _logger.info("   🔹 tax_rate: %r", tax_rate)

            if not tax_rate:
                _logger.warning("   ⚠️ No tax_rate found, skipping this tax.")
                continue

            try:
                tx_rate = float(tax_rate)
            except Exception as e:
                _logger.error("   ❌ Failed to convert tax_rate to float: %s", e, exc_info=True)
                continue

            tx_type = tax.get('type', tax.get('tax_type', 'percent'))
            _logger.info("   🔹 tx_type: %s", tx_type)

            domain = [
                ('channel_id', '=', self.channel_id.id),
                ('store_tax_value_id', '=', tx_rate),
                ('tax_type', '=', tx_type),
            ]

            tx_inclusive = None
            for key in ['included_in_price', 'include_in_price', 'inclusive', 'included']:
                if key in tax:
                    tx_inclusive = tax[key]
                    _logger.info("   🔹 Found tax inclusivity: %s = %r", key, tx_inclusive)
                    break

            if tx_inclusive is not None:
                domain.append(('include_in_price', '=', tx_inclusive))

            _logger.info("   🔍 Searching channel.account.mappings with domain: %s", domain)
            mapping = self.env['channel.account.mappings'].search(domain, limit=1)

            if mapping:
                _logger.info("   ✅ Found mapping: %s (tax_name.id=%s)", mapping, mapping.tax_name.id)
                tx_ids.append(mapping.tax_name.id)
                continue

            _logger.warning("   ⚠️ No mapping found, searching account.tax")
            domain = [('amount', '=', tx_rate), ('amount_type', '=', tx_type)]
            if tx_inclusive is None:
                tx_inclusive = self.channel_id.default_tax_type == 'include'
            domain.append(('price_include', '=', tx_inclusive))

            tx_name = tax.get('name', tax.get('tax_name'))
            if tx_name:
                domain.append(('name', '=', tx_name))
            else:
                tx_name = f"{self.channel_id.channel}_{self.channel_id.id}_{tx_rate}"

            _logger.info("   🔍 Searching account.tax with domain: %s", domain)
            tx = self.env['account.tax'].search(domain, limit=1)

            if not tx:
                _logger.warning(
                    "   ➕ Creating new account.tax with name=%s, amount=%s, amount_type=%s, price_include=%s",
                    tx_name, tx_rate, tx_type, tx_inclusive)
                tx = self.env['account.tax'].create({
                    'name': tx_name,
                    'amount_type': tx_type,
                    'price_include': tx_inclusive,
                    'amount': tx_rate,
                })

            _logger.info("   ✅ Using tax id: %s (%s)", tx.id, tx.name)
            tx_ids.append(tx.id)

            self.env['channel.account.mappings'].create({
                'channel_id': self.channel_id.id,
                'store_tax_value_id': str(tx_rate),
                'tax_type': tx_type,
                'include_in_price': tx_inclusive,
                'tax_name': tx.id,
                'odoo_tax_id': tx.id,
            })
            _logger.info("   ➕ Created channel.account.mappings for tax %s", tx.id)

        _logger.info("🎯 [get_taxes_ids] Final tx_ids: %s", tx_ids)
        return [(6, 0, tx_ids)]

    @api.model
    def get_order_date_info(self, channel_id, vals):
        _logger.info("get_order_date_info %r" % vals)
        date_order = None
        confirmation_date = None
        date_invoice = None
        date_shipping = None
        total_amount = 0
        date_order_res = channel_id.om_format_date(vals.pop('date_order'))
        if date_order_res.get('om_date_time'):
            date_order = date_order_res.get('om_date_time')

        confirmation_date_res = channel_id.om_format_date(vals.pop('confirmation_date'))
        if confirmation_date_res.get('om_date_time'):
            confirmation_date = confirmation_date_res.get('om_date_time')

        date_invoice_res = channel_id.om_format_date(vals.pop('date_invoice'))
        if date_invoice_res.get('om_date_time'):
            date_invoice = date_invoice_res.get('om_date_time')

        date_shipping_res = channel_id.om_format_date(vals.pop('date_shipping'))
        if date_shipping_res.get('om_date_time'):
            date_shipping = date_shipping_res.get('om_date_time')

        return dict(
            date_order=date_order,
            confirmation_date=confirmation_date,
            date_invoice=date_invoice,
            date_shipping=date_shipping,
        )

    @api.model
    def get_order_fields(self):
        return copy.deepcopy(OrderFields)

    def xx_import_order(self, channel_id):
        _logger.info("import_order %r" % channel_id)
        message = ""
        update_id = None
        create_id = None
        self.ensure_one()
        vals = EL(self.read(self.get_order_fields()))
        _logger.info(vals)

        if vals.get('name'):                                ###### Store name in source document ######
            vals['origin'] = vals.get('name')

        store_id = vals.pop('store_id')
        store_source = vals.pop('store_source')
        match = self._context.get('order_mappings').get(channel_id.id, {}).get(store_id)
        if match:
            match = self.env['channel.order.mappings'].browse(match)
        state = 'done'
        store_partner_id = vals.pop('partner_id')

        date_info = self.get_order_date_info(channel_id, vals)
        if date_info.get('confirmation_date'):
            vals['date_order'] = date_info.get('confirmation_date')
        elif date_info.get('date_order'):
            vals['date_order'] = date_info.get('date_order')

        # date_invoice = date_info.get('date_invoice')
        # date_shipping = date_info.get('date_shipping')
        if date_info.get('date_invoice'):
            date_invoice = date_info.get('date_invoice')
        else:
            date_invoice = vals.get('date_order')

        if date_info.get('date_shipping'):
            date_shipping = date_info.get('date_shipping')
        else:
            date_shipping = date_info.get('date_order')

        confirmation_date = date_info.get('confirmation_date')
        _logger.info("import_order >>> store_partner_id %r" % store_partner_id)
        _logger.info("import_order >>> self.customer_name %r" % self.customer_name)
        _logger.info("import_order >>> match %r" % match)
        if store_partner_id and self.customer_name:
            if not match:
                res_partner = self.get_order_partner_id(store_partner_id, channel_id)
                _logger.info("import_order >>> res_partner %r" % res_partner)
                message += res_partner.get('message', '')
                partner_id = res_partner.get('partner_id')
                partner_invoice_id = res_partner.get('partner_invoice_id')
                partner_shipping_id = res_partner.get('partner_shipping_id')
                if partner_id and partner_invoice_id and partner_shipping_id:
                    vals['partner_id'] = partner_id.id
                    vals['partner_invoice_id'] = partner_invoice_id.id
                    vals['partner_shipping_id'] = partner_shipping_id.id
                else:
                    message += '<br/>Partner,Invoice,Shipping Address must present.'
                    state = 'error'
                    _logger.error('#OrderError1 %r' % message)
        else:
            message += '<br/>No partner in sale order data.'
            state = 'error'
            _logger.error('#OrderError2 %r' % message)

        if state == 'done':
            carrier_id = vals.pop('carrier_id', '')

            if carrier_id:
                carrier_res = self.get_carrier_id(carrier_id, channel_id=channel_id)
                message += carrier_res.get('message')
                carrier_id = carrier_res.get('carrier_id')
                if carrier_id:
                    vals['carrier_id'] = carrier_id.id
            order_line_res = self._get_order_line_vals(vals, carrier_id, channel_id)
            message += order_line_res.get('message', '')
            if not order_line_res.get('status'):
                state = 'error'
                _logger.error('#OrderError3 %r' % order_line_res)
            else:
                order_line = order_line_res.get('order_line')
                if len(order_line):
                    vals['order_line'] = order_line
                    state = 'done'
        currency = self.currency

        if state == 'done' and currency:
            currency_id = channel_id.get_currency_id(currency)
            if not currency_id.active:
                if currency_id: # Currency Form View URL
                    currency = f'<strong><a href="/web#id={currency_id.id}&model=res.currency&view_type=form" target = "_blank">{currency}</a></strong>'
                message += '<br/> Currency %s no active in Odoo' % (currency)
                state = 'error'
                _logger.error('#OrderError4 %r' % message)
            else:
                pricelist_id = channel_id.match_create_pricelist_id(currency_id)
                vals['pricelist_id'] = pricelist_id.id
        if not (channel_id.order_ecomm_sequence and vals.get('name')):
            vals.pop('name')
        vals.pop('id')
        vals.pop('website_message_ids', '')
        vals.pop('message_follower_ids', '')

        if match and match.order_name:
            if state == 'done':
                try:
                    order_state = vals.pop('order_state')
                    if match.order_name.state == 'draft':
                        match.order_name.write(dict(order_line=[(5, 0)]))
                        extra_values = channel_id.get_order_extra_vals(vals, False)
                        vals.update(extra_values)
                        if match.order_name.note and vals['note']:
                            vals['note'] =  match.order_name.note+vals['note']
                        match.order_name.write(vals)
                        message += '<br/> Order %s successfully updated' % (vals.get('name', ''))
                    else:
                        message += 'Only order state can be update as order not in draft state. '
                    if match.order_name.state == 'cancel':
                        message += 'No changes made for this order as the odoo order is already cancelled. '
                    else:
                        message += self.env['multi.channel.skeleton']._SetOdooOrderState(match.order_name, channel_id,
                                                                                         order_state, self.payment_method, date_invoice=date_invoice, confirmation_date=confirmation_date, date_shipping=date_shipping)
                    if not match.store_order_status == order_state:
                        match.store_order_status = order_state
                except Exception as e:
                    message += '<br/>%s' % (e)
                    _logger.error('#OrderError5  %r' % message)
                    state = 'error'
                update_id = match
            elif state == 'error':
                message += '<br/>Error while order update.'
        else:
            if state == 'done':
                try:
                    order_state = vals.pop('order_state')
                    extra_values = channel_id.get_order_extra_vals(vals, True)
                    vals.update(extra_values)
                    _logger.info("Start creating order with vals %r" % vals)
                    erp_id = self.env['sale.order'].create(vals)
                    message += self.env['multi.channel.skeleton']._SetOdooOrderState(erp_id, channel_id, order_state, self.payment_method, date_invoice=date_invoice, confirmation_date=confirmation_date,date_shipping=date_shipping)
                    message += '<br/> Order %s successfully evaluated' % (self.store_id)
                    create_id = channel_id.create_order_mapping(erp_id, store_id, store_source, order_state)

                except Exception as e:
                    message += '<br/>%s' % (e)
                    _logger.error('#OrderError6 %r' % message)
                    state = 'error'
        self.set_feed_state(state=state)
        self.message = "%s <br/> %s" % (message, self.message)
        return dict(
            create_id=create_id,
            update_id=update_id,
            message=message
        )

    def import_order(self, channel_id):
        _logger.info("import_order %r" % channel_id)
        message = ""
        update_id = None
        create_id = None
        self.ensure_one()

        vals = EL(self.read(self.get_order_fields()))
        _logger.info(vals)

        # Store name in source document
        if vals.get('name'):
            vals['origin'] = vals.get('name')

        vals['total_amount'] = vals.get('total_amount')
        _logger.info("total_amount : %s", vals.get('total_amount'))

        store_id = vals.pop('store_id')
        store_source = vals.pop('store_source')
        match = self._context.get('order_mappings', {}).get(channel_id.id, {}).get(store_id)
        if match:
            match = self.env['channel.order.mappings'].browse(match)

        state = 'done'
        store_partner_id = vals.pop('partner_id', None)

        # Get dates
        date_info = self.get_order_date_info(channel_id, vals)
        _logger.info("date_info : %s", date_info)
        vals['date_order'] = date_info.get('confirmation_date') or date_info.get('date_order') or vals.get('date_order')
        date_invoice = date_info.get('date_invoice') or vals.get('date_order')
        date_shipping = date_info.get('date_shipping') or vals.get('date_order')
        confirmation_date = date_info.get('confirmation_date')

        _logger.info("import_order >>> store_partner_id %r" % store_partner_id)
        _logger.info("import_order >>> self.customer_name %r" % self.customer_name)
        _logger.info("import_order >>> match %r" % match)

        # Handle partner
        if store_partner_id and self.customer_name:
            if not match:
                res_partner = self.get_order_partner_id(store_partner_id, channel_id)
                _logger.info("import_order >>> res_partner %r" % res_partner)
                message += res_partner.get('message', '')
                partner_id = res_partner.get('partner_id')
                partner_invoice_id = res_partner.get('partner_invoice_id')
                partner_shipping_id = res_partner.get('partner_shipping_id')
                if partner_id and partner_invoice_id and partner_shipping_id:
                    vals['partner_id'] = partner_id.id
                    vals['partner_invoice_id'] = partner_invoice_id.id
                    vals['partner_shipping_id'] = partner_shipping_id.id
                else:
                    message += '<br/>Partner, Invoice, Shipping Address must be present.'
                    state = 'error'
                    _logger.error('#OrderError1 %r' % message)
        else:
            message += '<br/>No partner in sale order data.'
            state = 'error'
            _logger.error('#OrderError2 %r' % message)

        # Handle carrier and order lines
        if state == 'done':
            carrier_id = vals.pop('carrier_id', '')
            if carrier_id:
                carrier_res = self.get_carrier_id(carrier_id, channel_id=channel_id)
                message += carrier_res.get('message', '')
                carrier_id = carrier_res.get('carrier_id')
                if carrier_id:
                    vals['carrier_id'] = carrier_id.id

            order_line_res = self._get_order_line_vals(vals, carrier_id, channel_id)
            _logger.info("order_line_res : %s", order_line_res)
            message += order_line_res.get('message', '')
            if not order_line_res.get('status'):
                state = 'error'
                _logger.error('#OrderError3 %r' % order_line_res)
            else:
                order_line = order_line_res.get('order_line')
                if len(order_line):
                    vals['order_line'] = order_line
                    _logger.info("order_line vals: %s", vals)
                    state = 'done'

        # Handle currency and pricelist
        currency = self.currency
        if state == 'done' and currency:
            currency_id = channel_id.get_currency_id(currency)
            if not currency_id.active:
                currency = f'<strong><a href="/web#id={currency_id.id}&model=res.currency&view_type=form" target="_blank">{currency}</a></strong>'
                message += '<br/> Currency %s not active in Odoo' % currency
                state = 'error'
                _logger.error('#OrderError4 %r' % message)
            else:
                pricelist_id = channel_id.match_create_pricelist_id(currency_id)
                vals['pricelist_id'] = pricelist_id.id

        # Clean unnecessary fields
        if not (channel_id.order_ecomm_sequence and vals.get('name')):
            vals.pop('name', None)
        vals.pop('id', None)
        vals.pop('website_message_ids', None)
        vals.pop('message_follower_ids', None)

        # Update existing order if mapping exists
        if match and match.order_name:
            if state == 'done':
                try:
                    order_state = vals.pop('order_state')
                    if match.order_name.state == 'draft':
                        match.order_name.write({'order_line': [(5, 0)]})
                        extra_values = channel_id.get_order_extra_vals(vals, False)
                        vals.update(extra_values)
                        if match.order_name.note and vals['note']:
                            vals['note'] = match.order_name.note + vals['note']
                        match.order_name.write(vals)
                        message += '<br/> Order %s successfully updated' % (vals.get('name', ''))
                    else:
                        match.order_name.write({'total_amount': vals.get('total_amount')})
                        message += 'Only draft orders can be updated. '
                    if match.order_name.state != 'cancel':
                        message += self.env['multi.channel.skeleton']._SetOdooOrderState(
                            match.order_name, channel_id, order_state, self.payment_method,
                            date_invoice=date_invoice, confirmation_date=confirmation_date, date_shipping=date_shipping
                        )
                    if match.store_order_status != order_state:
                        match.store_order_status = order_state
                except Exception as e:
                    message += '<br/>%s' % e
                    _logger.error('#OrderError5 %r' % message)
                    state = 'error'
                update_id = match
            elif state == 'error':
                message += '<br/>Error while order update.'

        # Create new order if no mapping exists
        else:
            if state == 'done':
                # Ensure partner_id exists before creating
                if 'partner_id' not in vals or not vals['partner_id']:
                    message += '<br/>Cannot create order: partner_id is missing.'
                    _logger.error('#OrderError6 %r' % message)
                    state = 'error'
                else:
                    try:
                        order_state = vals.pop('order_state')
                        extra_values = channel_id.get_order_extra_vals(vals, True)
                        vals.update(extra_values)
                        _logger.info("extra_values : %s", extra_values)
                        _logger.info("vals : %s", vals)

                        vals['name'] = vals['origin']

                        _logger.info("Start creating order with vals %r" % vals)

                        des_product_id = channel_id.discount_product_id.id
                        order_lines = vals.get("order_line", [])

                        for index, line_data in enumerate(order_lines):
                            # Each line_data is like (0, 0, {...})
                            line_vals = line_data[2]

                            # Check if it's the discount product
                            if line_vals.get("product_id") == des_product_id:
                                product = self.env["product.product"].browse(des_product_id)
                                _logger.info("import_order >> Found Discount product: %r" % product)
                                _logger.info("import_order >> Discount product exists? %r" % product.exists())
                                _logger.info("import_order >> Product Discount > %r" % product.read())

                                # Get taxes from that product
                                taxes = product.taxes_id
                                tax_ids = [(6, 0, taxes.ids)] if taxes else [(6, 0, [])]
                                _logger.info("import_order >> Found tax_ids in : %r" % tax_ids)

                                # Update tax_id and rewrite the tuple in vals
                                line_vals["tax_id"] = tax_ids
                                vals["order_line"][index] = (0, 0, line_vals)

                                _logger.info(f"✅ Updated discount line tax_id for product {des_product_id} to {tax_ids}")

                        _logger.info("✅ Final vals after tax update: %r" % vals)

                        existing_order = self.env['sale.order'].search([('name', '=', vals['origin'])], limit=1)

                        if existing_order:
                            _logger.warning("Order already exists with name %s, reusing it", vals['origin'])
                            erp_id = existing_order
                            self.process_payment_without_invoice()
                        else:
                            erp_id = self.env['sale.order'].create(vals)
                            self.process_payment_without_invoice()

                        message += self.env['multi.channel.skeleton']._SetOdooOrderState(
                            erp_id, channel_id, order_state, self.payment_method,
                            date_invoice=date_invoice, confirmation_date=confirmation_date, date_shipping=date_shipping
                        )
                        message += '<br/> Order %s successfully evaluated' % self.store_id
                        create_id = channel_id.create_order_mapping(erp_id, store_id, store_source, order_state)
                    except Exception as e:
                        message += '<br/>%s' % e
                        _logger.error('#OrderError6 %r' % message)
                        state = 'error'
        self.process_payment_without_invoice()
        # Finalize feed state and message
        self.set_feed_state(state=state)
        self.message = "%s <br/> %s" % (message, self.message)
        return dict(
            create_id=create_id,
            update_id=update_id,
            message=message
        )

    def import_items(self):
        _logger.info('import_items')
        # initial check for required fields.
        # required_fields = self.env['wk.feed'].get_required_feed_fields()
        self = self.env['wk.feed'].verify_required_fields(self, 'orders')
        if not self and not self._context.get('get_mapping_ids'):
            message = self.get_feed_result(feed_type='Sale Order')
            return self.env['multi.channel.sale'].display_message(message)

        self = self.contextualize_feeds('category', self.mapped('channel_id').ids)
        self = self.contextualize_mappings('category', self.mapped('channel_id').ids)
        self = self.contextualize_feeds('product', self.mapped('channel_id').ids)
        self = self.contextualize_mappings('product', self.mapped('channel_id').ids)
        self = self.contextualize_mappings('order', self.mapped('channel_id').ids)
        self = self.with_context(from_multichannel=True)
        update_ids = []
        create_ids = []
        message = ''
        for record in self:
            channel_id = record.channel_id
            sync_vals = dict(
                status='error',
                action_on='order',
                action_type='import',
            )
            record = record.with_company(channel_id.company_id.id)
            res = record.import_order(channel_id)
            msz = res.get('message', '')
            message += msz
            update_id = res.get('update_id')
            if update_id:
                update_ids.append(update_id)
            create_id = res.get('create_id')
            if create_id:
                create_ids.append(create_id)
            mapping_id = update_id or create_id
            if mapping_id:
                sync_vals['status'] = 'success'
                sync_vals['ecomstore_refrence'] = mapping_id.store_order_id
                sync_vals['odoo_id'] = mapping_id.odoo_order_id
            sync_vals['summary'] = msz
            channel_id._create_sync(sync_vals)
        if self._context.get('get_mapping_ids'):
            return dict(
                update_ids=update_ids,
                create_ids=create_ids,
            )
        message = self.get_feed_result(feed_type='Sale Order')
        return self.env['multi.channel.sale'].display_message(message)

    def action_open_sale_order(self):
        """
        Open the related Sale Order by searching with name or origin field.
        Returns action to open sale.order form view.
        """
        self.ensure_one()
        if not self.name:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Order name is not available.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        sale_order = self.env['sale.order'].search([
            '|', ('name', '=', self.name), ('origin', '=', self.name)
        ], limit=1)
        if not sale_order:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Information',
                    'message': f'No Sale Order found with name or origin: {self.name}',
                    'type': 'info',
                    'sticky': False,
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_payment(self):
        """
        Open the related Payment by searching with memo field equals name.
        Returns action to open account.payment form view.
        """
        self.ensure_one()
        if not self.name:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Order name is not available.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        payment = self.env['account.payment'].search([('memo', '=', self.name)], limit=1)
        if not payment:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Information',
                    'message': f'No Payment found with memo: {self.name}',
                    'type': 'info',
                    'sticky': False,
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_invoice(self):
        """
        Open the related Invoice by searching with salla_so_id field equals name.
        Returns action to open account.move form view.
        """
        self.ensure_one()
        if not self.name:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Order name is not available.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        invoice = self.env['account.move'].search([('salla_so_id', '=', self.name)], limit=1)
        if not invoice:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Information',
                    'message': f'No Invoice found with salla_so_id: {self.name}',
                    'type': 'info',
                    'sticky': False,
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_stock_picking(self):
        """
        Open the related Stock Picking by searching with sale_id.name or sale_id.origin equals name.
        Returns action to open stock.picking form view.
        """
        self.ensure_one()
        if not self.name:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Order name is not available.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        stock_picking = self.env['stock.picking'].search([
            ('sale_id.origin', '=', self.name)
        ], limit=1)
        if not stock_picking:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Information',
                    'message': f'No Stock Picking found with sale order name or origin: {self.name}',
                    'type': 'info',
                    'sticky': False,
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Picking',
            'res_model': 'stock.picking',
            'res_id': stock_picking.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_set_to_draft(self):
        """
        Set selected order feeds state to draft.
        This method can be called from list view with multiple records selected.
        """
        if not self:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Please select at least one record.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        updated_count = 0
        skipped_count = 0
        for record in self:
            if record.state != 'draft':
                record.set_feed_state(state='draft')
                updated_count += 1
            else:
                skipped_count += 1

        if updated_count > 0:
            message = f'{updated_count} record(s) set to draft successfully.'
            if skipped_count > 0:
                message += f' {skipped_count} record(s) were already in draft state.'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Information',
                    'message': 'All selected records are already in draft state.',
                    'type': 'info',
                    'sticky': False,
                }
            }

    def action_fetch_order_from_salla(self):
        """
        Fetch order data from Salla API and log the response.
        Retrieves access token from first available multi.channel.sale record.
        Uses order.feed.store_id as ORDER_ID.
        """
        self.ensure_one()
        
        _logger.info("=" * 80)
        _logger.info("Fetching order data from Salla")
        _logger.info("=" * 80)
        
        # Log Order Feed information
        _logger.info("Order Feed Record | id=%s | name=%s | store_id=%s", 
                     self.id, self.name or 'N/A', self.store_id or 'N/A')
        
        # Find related stock.picking if exists
        picking = self.env['stock.picking'].search([
            ('sale_id.origin', '=', self.name)
        ], limit=1)
        if picking:
            _logger.info("Related Stock Picking | id=%s | origin=%s", 
                         picking.id, picking.origin or 'N/A')
        else:
            _logger.info("Related Stock Picking | Not found")
        
        # Find related sale.order if exists
        sale_order = self.env['sale.order'].search([
            '|', ('name', '=', self.name), ('origin', '=', self.name)
        ], limit=1)
        if sale_order:
            _logger.info("Related Sale Order | id=%s | name=%s", 
                         sale_order.id, sale_order.name or 'N/A')
        else:
            _logger.info("Related Sale Order | Not found")
        
        # Validate ORDER_ID
        order_id = self.store_id
        if not order_id:
            _logger.warning("ORDER_ID is missing. order.feed.store_id is empty.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Order ID (store_id) is missing. Cannot fetch order from Salla.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # Fetch access token from first available multi.channel.sale record
        channel = self.env['multi.channel.sale'].search([], order='id asc', limit=1)
        if not channel:
            _logger.error("No multi.channel.sale record found. Cannot fetch access token.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No channel configuration found. Please configure a multi channel sale instance first.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        
        # Log channel information for troubleshooting
        _logger.info("Multi Channel Sale (first) | id=%s | name=%s | access_token=%s",
                     channel.id, channel.name or 'N/A', channel.access_token or 'N/A')
        
        access_token = channel.access_token
        if not access_token:
            _logger.error("Access token is missing for channel id=%s, name=%s", 
                          channel.id, channel.name or 'N/A')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Access token is not configured for channel: {channel.name or "N/A"}. Please configure the access token first.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        
        # Prepare API headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Fetch order data
        order_url = f'https://api.salla.dev/admin/v2/orders/{order_id}'
        _logger.info("Fetching order data | URL=%s | ORDER_ID=%s", order_url, order_id)
        
        try:
            # Make request to fetch order
            response = requests.get(order_url, headers=headers, timeout=30)
            
            # Handle HTTP errors
            if response.status_code == 404:
                _logger.warning("Order not found | ORDER_ID=%s | Status Code=404", order_id)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Not Found',
                        'message': f'Order {order_id} not found in Salla. Please verify the order ID.',
                        'type': 'warning',
                        'sticky': False,
                    }
                }
            
            response.raise_for_status()
            order_data = response.json()
            _logger.info("Order data fetched successfully | ORDER_ID=%s", order_id)
            
            # Fetch order items
            items_url = 'https://api.salla.dev/admin/v2/orders/items/'
            items_params = {'order_id': order_id}
            _logger.info("Fetching order items | URL=%s | params=%s", items_url, items_params)
            
            items_response = requests.get(items_url, headers=headers, params=items_params, timeout=30)
            items_response.raise_for_status()
            items_data = items_response.json()
            _logger.info("Order items fetched successfully | ORDER_ID=%s", order_id)
            
            # Merge items into order response
            if items_data and items_data.get('data'):
                if 'data' in order_data:
                    order_data['data']['items'] = items_data.get('data')
                else:
                    order_data['items'] = items_data.get('data')
                _logger.info("Order items merged into order data | items_count=%s", 
                             len(items_data.get('data', [])))
            
            # Log the full JSON response (pretty-printed)
            _logger.info("=" * 80)
            _logger.info("FULL ORDER DATA FROM SALLA API (ORDER_ID=%s):", order_id)
            _logger.info("=" * 80)
            _logger.info(json.dumps(order_data, ensure_ascii=False, indent=2))
            _logger.info("=" * 80)
            
            # Return success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Order data fetched successfully from Salla. Check server logs for full response. (ORDER_ID: {order_id})',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 'N/A'
            response_body = e.response.text if e.response else 'N/A'
            _logger.error("HTTP Error while fetching order | ORDER_ID=%s | Status Code=%s | Response=%s",
                          order_id, status_code, response_body)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'HTTP Error',
                    'message': f'Failed to fetch order from Salla. Status Code: {status_code}. Check server logs for details.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
            
        except requests.exceptions.RequestException as e:
            _logger.error("Request Exception while fetching order | ORDER_ID=%s | Error=%s",
                          order_id, str(e), exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Request Error',
                    'message': f'Network error while fetching order from Salla: {str(e)}',
                    'type': 'danger',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error("Unexpected error while fetching order | ORDER_ID=%s | Error=%s",
                          order_id, str(e), exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Unexpected error occurred: {str(e)}. Check server logs for details.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
