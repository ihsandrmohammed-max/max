# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
from odoo.addons.odoo_multi_channel_sale.tools import remove_tags

class FetchData:
    def __init__(self, channel_id, **kw):
        self.channel_id = channel_id
        self.id = channel_id.id
        self.env = channel_id.env

    def get_all_categories(self, data):
        category_vals = []
        for val in data:
            category_vals.append(
                self.category_for_category(val))
        for val in data:
            if val.get('items'):
                category_vals.extend(self.get_all_categories(
                    val.get('items')))
        return category_vals

    def category_for_category(self, data):
        category_vals = ({
            "channel_id": self.channel_id.id,
            "channel": self.channel_id.channel,
            "leaf_category": False if data.get('items') else True,
            "parent_id": data.get('parent_id') or False,
            "store_id": data.get('id'),
            "name": data.get('name')
        })
        return category_vals

    def get_shipping_vals(self, channel_id, shipping_data):
        return {
            "name": shipping_data.get("name"),
            "store_id": shipping_data.get("id"),
            "shipping_carrier": shipping_data.get("name"),
            "channel_id": channel_id.id,
            "channel": channel_id.channel,
            "description": shipping_data.get("activation_type", False)
        }

    def process_customer(self, customer):
        customer_data = {
            'channel_id': self.channel_id.id,
            'store_id': customer.get('id'),
            'name': customer.get('first_name', False),
            'last_name':customer.get('last_name', False),
            'email': customer.get('email'),
            'mobile': customer.get('mobile'),
            'city': customer.get('city'),
            'street': customer.get('location', False),
            'country_code': customer.get('country_code') if customer.get('country_code') else customer.get('country'),
            'website': customer.get('urls').get('customer') if customer.get('urls') else False
        }
        address_data_list = []
        customer_data['contacts'] = address_data_list
        return customer_data

    def process_address(self, order, store_partner_id, type=False):
        contacts = {}
        billing_address = []
        email = order.get('customer').get('email')
        name = order.get('customer').get('first_name')+ " "+ order.get('customer').get('last_name')
        phone = order.get('customer').get('mobile')

        address = order.get('shipments', {})
        if isinstance(address, list):
            address = address[0]
            if isinstance(address, list):
                address = address[0]
            billing_address = address.get('ship_to', {})
            if billing_address:
                name = billing_address.get('name')
                phone = billing_address.get('phone')
        if not billing_address and order.get('shipping'):
            billing_address = order.get('shipping').get('address')
            receiver_data = order.get('shipping').get('receiver', {})
            if receiver_data and isinstance(receiver_data, dict):   
                name = receiver_data.get('name') if receiver_data.get('name') else name
                email = receiver_data.get('email') if receiver_data.get('email') else email
                phone = receiver_data.get('phone') if receiver_data.get('phone') else phone
        if billing_address:
            contacts.update({
                'invoice_partner_id': f'billing_{store_partner_id}' if store_partner_id else email,
                'invoice_name': name,
                'invoice_email':  email,
                'invoice_phone': phone,
                'invoice_street': billing_address.get('street_number'),
                'invoice_street2': billing_address.get('shipping_address') or billing_address.get('address_line'),
                'invoice_zip': billing_address.get('postal_code'),
                'invoice_city': billing_address.get('city'),
                'invoice_country_code': billing_address.get('country_code') or False,
                'same_shipping_billing': True
            })
        return contacts

    def import_product_vals(self, product):
        vals = self.get_product_basic_vals(product)
        if product.get('options'):
            variants, options = self.get_variant_vals(product)
            vals.update(
                {'variants': variants, 'salla_product_attribute_options': options})
        return vals

    def get_product_basic_vals(self, product):
        return {
            'store_id': product.get('id'),
            'name': product.get('name'),
            'channel_id': self.id,
            'channel': self.channel_id.channel,
            'description_sale': remove_tags(product.get('description') or ''),
            'description': product.get('promotion').get('sub_title'),
            'image_url': product.get('main_image'),
            'list_price': product.get("price").get('amount'),
            'weight': product.get("weight"),
            'wk_default_code': product.get("sku"),
            'default_code': product.get("sku"),
            'qty_available': product.get("quantity"),
            'extra_categ_ids': ",".join([str(x.get('id')) for x in product.get('categories')]) if product.get('categories') else False
        }

    def get_variant_vals(self, product):
        options = self.get_product_options(product.get('options'))
        variants = []
        salla_product_attribute_option_vals = {}
        for variant in product.get('skus'):
            salla_options = variant.get('related_option_values')
            if salla_options:
                salla_options.sort()
                salla_product_attribute_option_vals.update(
                    {"_".join(map(str, salla_options)): variant.get('id')})
            if options:
                name_value = [{
                    'name': options.get(attribute_id).get('name'),
                    'value': options.get(attribute_id).get('value_name'),
                } for attribute_id in salla_options if options.get(attribute_id)]
            variants.append({
                'default_code': variant.get('sku'),
                'barcode': variant.get('barcode'),
                'store_id': variant.get('id'),
                'qty_available': variant.get('stock_quantity'),
                'list_price': variant.get('price').get('amount'),
                'weight': variant.get('weight'),
                # 'image_url': image_url,
                'name_value': name_value,
            })
        return variants, salla_product_attribute_option_vals or False

    def get_product_options(self, options):
        """
            options will be : 
            {
                value_id1: {option_name:name, option_id: id, value_name: value_name},
                value_id2: {option_name:name, option_id: id, value_name: value_name},
                ...
            }
        """
        option_vals = {}
        for option in options:
            for value in option.get('values'):
                option_vals.update({value.get('id'): {'name': option.get(
                    'name'), 'id': option.get('id'), 'value_name': value.get('name')}})
        return option_vals

    def old_process_order(self, order):
        _logger.info("process_order :::: order : %s", order)
        order_data = {
            'channel_id': self.id,
            'store_id': order.get('id'),
            'name': str(order.get('reference_id')),
            'currency': order.get('currency'),
            'date_order': order.get('date').get('date'),
            'confirmation_date': order.get('date').get('date'),
            'order_state': order.get('status').get('slug'),
            'line_type': 'multi'
        }
        if order.get('payment_method'):
            order_data.update(payment_method=order.get('payment_method'))
        if order.get('shipping') or order.get('shipments'):
            if type(order.get('shipping')) == dict:
                order_data.update(
                    {'carrier_id': order.get('shipping').get('company')})
            elif type(order.get('shipments')) == dict:
                order_data.update(
                    {'carrier_id': order.get('shipments').get('courier_name')})
        if order.get('customer'):
            customer = order.get('customer')
            order_data.update(
                {
                    'partner_id': customer.get('id'),
                    'customer_name': customer.get('first_name')+' '+customer.get('last_name'),
                    'customer_email': customer.get('email'),
                    'customer_mobile': customer.get('mobile'),
                    'customer_phone': customer.get('mobile'),
                }
            )
            contacts = self.process_address(order, customer.get('id'))
            order_data.update(contacts)
        order_lines = [(5, 0)]
        for line in order.get("items"):
            line_product_id = line.get("product").get("id")
            exists = self.channel_id.match_product_mappings(line_product_id)
            attribute_options = False
            if not exists:
                #Update or create product feed only if there is no mapping exists
                attribute_options = self.create_product_feed(line_product_id)
            order_line_data = {
                'line_name': line.get("name"),
                'line_product_id': line_product_id,
                'line_variant_ids': "No Variants" if not line.get("options") else self.get_variant_id(line, attribute_options),
                'line_price_unit': line.get("amounts").get("price_without_tax").get("amount"),
                'line_product_uom_qty': line.get("quantity"),
                'line_product_default_code': line.get("sku", False),
                'line_taxes': self.process_tax(line.get("amounts").get("tax")),
            }
            order_lines.append((0, 0, order_line_data))
        # Discount Line and Delivery Line
        order_tax = self.process_tax(order.get("amounts").get("tax"))
        order_dicounts = order.get('amounts').get('discounts')
        if order_dicounts:
            discount_line = self.get_discount_line(order_dicounts, order_tax)
            if discount_line:
                order_lines.append(discount_line)
        if order.get('amounts').get('shipping_cost'):
            _logger.info("cash_on_delivery >>> process_order :::: order : %s", order)
            delivery_line = self.get_shipping_line(order, order_tax)
            _logger.info("cash_on_delivery >>> process_order :::: delivery_line : %s", delivery_line)
            if delivery_line:
                order_lines.append(delivery_line)
        if order.get('amounts').get('cash_on_delivery'):
            _logger.info("cash_on_delivery >>> process_order :::: order : %s", order)
            delivery_line = self.get_cod_line(order, order_tax)
            _logger.info("cash_on_delivery >>> process_order :::: delivery_line : %s", delivery_line)
            if delivery_line:
                order_lines.append(delivery_line)
        order_data['line_ids'] = order_lines
        return order_data

    def xxxx_process_order(self, order):
        _logger.info("Processing order: %s", order)

        # ----- Order Main Info -----
        order_data = {
            'channel_id': self.id,
            'store_id': order.get('id'),
            'name': str(order.get('reference_id')),
            'currency': order.get('currency'),
            'date_order': order.get('date', {}).get('date'),
            'confirmation_date': order.get('date', {}).get('date'),
            'order_state': order.get('status', {}).get('slug'),
            'line_type': 'multi',
        }

        # ----- Payment Method -----
        payment_method = order.get('payment_method')
        if payment_method:
            order_data['payment_method'] = payment_method

        # ----- Carrier Info -----
        shipping_info = order.get('shipping') or order.get('shipments')
        if shipping_info and isinstance(shipping_info, dict):
            carrier_id = shipping_info.get('company') or shipping_info.get('courier_name')
            if carrier_id:
                order_data['carrier_id'] = carrier_id

        # ----- Customer Info -----
        customer = order.get('customer')
        if customer:
            full_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            order_data.update({
                'partner_id': customer.get('id'),
                'customer_name': full_name or 'Unknown Customer',
                'customer_email': customer.get('email'),
                'customer_mobile': customer.get('mobile'),
                'customer_phone': customer.get('mobile'),
            })
            # Process customer addresses
            customer_contacts = self.process_address(order, customer.get('id'))
            order_data.update(customer_contacts)

        # # ----- Order Lines -----
        # order_lines = [(5, 0)]  # Clear existing lines
        # for item in order.get("items", []):
        #     product = item.get("product", {})
        #     product_id = product.get("id")
        #     mapped_product = self.channel_id.match_product_mappings(product_id)
        #     attribute_options = None
        #     if not mapped_product:
        #         attribute_options = self.create_product_feed(product_id)
        #
        #     variant_ids = "No Variants"
        #     if item.get("options"):
        #         variant_ids = self.get_variant_id(item, attribute_options)
        #
        #     line_data = {
        #         'line_name': item.get("name"),
        #         'line_product_id': product_id,
        #         'line_variant_ids': variant_ids,
        #         'line_price_unit': item.get("amounts", {}).get("price_without_tax", {}).get("amount", 0.0),
        #         'line_product_uom_qty': item.get("quantity", 1),
        #         'line_product_default_code': item.get("sku", False),
        #         'line_taxes': self.process_tax(item.get("amounts", {}).get("tax")),
        #     }
        #     order_lines.append((0, 0, line_data))
        # ----- Order Lines -----
        order_lines = [(5, 0)]  # Clear existing lines
        for item in order.get("items", []):
            product = item.get("product", {})
            product_id = product.get("id")
            mapped_product = self.channel_id.match_product_mappings(product_id)
            attribute_options = None
            if not mapped_product:
                attribute_options = self.create_product_feed(product_id)

            variant_ids = "No Variants"
            if item.get("options"):
                variant_ids = self.get_variant_id(item, attribute_options)

            line_tax = self.process_tax(item.get("amounts", {}).get("tax"))
            if not line_tax:
                product_record = self.env['product.product'].search([('id', '=', product_id)], limit=1)
                if product_record and product_record.taxes_id:
                    line_tax = product_record.taxes_id.ids
                    _logger.info("No tax found in order, using product taxes: %s", line_tax)
                else:
                    line_tax = []

            line_data = {
                'line_name': item.get("name"),
                'line_product_id': product_id,
                'line_variant_ids': variant_ids,
                'line_price_unit': item.get("amounts", {}).get("price_without_tax", {}).get("amount", 0.0),
                'line_product_uom_qty': item.get("quantity", 1),
                'line_product_default_code': item.get("sku", False),
                'line_taxes': line_tax,
            }

            order_lines.append((0, 0, line_data))

        # ----- Order Discounts & Delivery -----
        order_tax = self.process_tax(order.get("amounts", {}).get("tax"))

        # Discounts
        discounts = order.get('amounts', {}).get('discounts')
        if discounts:
            discount_line = self.get_discount_line(discounts, order_tax)
            _logger.info("Discount Line: %s", discount_line)
            if discount_line:
                order_lines.append(discount_line)

        # Shipping
        if order.get('amounts', {}).get('shipping_cost'):
            shipping_line = self.get_shipping_line(order, order_tax)
            if shipping_line:
                _logger.info("Shipping Line: %s", shipping_line)
                order_lines.append(shipping_line)

        # Cash on Delivery
        if order.get('amounts', {}).get('cash_on_delivery'):
            cod_line = self.get_cod_line(order, order_tax)
            if cod_line:
                _logger.info("COD Line: %s", cod_line)
                order_lines.append(cod_line)

        # ----- Finalize -----
        order_data['line_ids'] = order_lines
        _logger.info("OOOO order_lines: %s", order_lines)
        return order_data

    def xxxprocess_order(self, order):
        order_ref = order.get('reference_id')
        _logger.info("[START] Processing order: %s", order_ref)

        # ----- Order Main Info -----
        order_data = {
            'channel_id': self.id,
            'store_id': order.get('id'),
            'name': str(order_ref),
            'currency': order.get('currency'),
            'date_order': order.get('date', {}).get('date'),
            'confirmation_date': order.get('date', {}).get('date'),
            'order_state': order.get('status', {}).get('slug'),
            'line_type': 'multi',
        }
        _logger.info("[%s] Order base data: %s", order_ref, order_data)

        # ----- Payment Method -----
        payment_method = order.get('payment_method')
        if payment_method:
            order_data['payment_method'] = payment_method
            _logger.info("[%s] Payment method: %s", order_ref, payment_method)

        # ----- Carrier Info -----
        shipping_info = order.get('shipping') or order.get('shipments')
        if shipping_info and isinstance(shipping_info, dict):
            carrier_id = shipping_info.get('company') or shipping_info.get('courier_name')
            if carrier_id:
                order_data['carrier_id'] = carrier_id
                _logger.info("[%s] Carrier: %s", order_ref, carrier_id)

        # ----- Customer Info -----
        customer = order.get('customer')
        if customer:
            full_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            order_data.update({
                'partner_id': customer.get('id'),
                'customer_name': full_name or 'Unknown Customer',
                'customer_email': customer.get('email'),
                'customer_mobile': customer.get('mobile'),
                'customer_phone': customer.get('mobile'),
            })
            customer_contacts = self.process_address(order, customer.get('id'))
            order_data.update(customer_contacts)
            _logger.info("[%s] Customer: %s", order_ref, full_name)

        # helper: robust product record finder
        def find_product_record(mapped_product, external_product_id, sku_or_code):
            """
            Try in order:
              1) mapped_product (if it is an id or record)
              2) browse internal id if external_product_id is numeric
              3) search by default_code (sku_or_code)
            Returns a product.product recordset or an empty recordset.
            """
            # 1) mapped_product
            try:
                if mapped_product:
                    # if mapping gives a recordset-like
                    if hasattr(mapped_product, 'exists') and hasattr(mapped_product, 'id'):
                        pr = mapped_product
                        if pr.exists():
                            return pr
                    # if mapping gives an id or numeric string
                    try:
                        pid = int(mapped_product)
                        pr = self.env['product.product'].browse(pid)
                        if pr.exists():
                            return pr
                    except Exception:
                        pass
                    # mapping might be dict with product_id
                    try:
                        if isinstance(mapped_product, dict) and mapped_product.get('product_id'):
                            pid = int(mapped_product.get('product_id'))
                            pr = self.env['product.product'].browse(pid)
                            if pr.exists():
                                return pr
                    except Exception:
                        pass
            except Exception:
                pass

            # 2) try browse external id if numeric
            try:
                if external_product_id is not None:
                    pid = int(external_product_id)
                    pr = self.env['product.product'].browse(pid)
                    if pr.exists():
                        return pr
            except Exception:
                pass

            # 3) try search by default_code (sku)
            try:
                if sku_or_code:
                    pr = self.env['product.product'].search([('default_code', '=', str(sku_or_code))], limit=1)
                    if pr.exists():
                        return pr
            except Exception:
                pass

            # nothing found
            return self.env['product.product']

        # helper: build tax dict(s) from product taxes
        def build_tax_dicts_from_product(product_record):
            tax_dicts = []
            for tax in product_record.taxes_id:
                try:
                    amount = float(tax.amount or 0.0)
                except Exception:
                    amount = 0.0
                rate = f"{amount:.2f}"
                name = f"Salla Tax {rate}%"
                tax_type = getattr(tax, 'amount_type', 'percent') or 'percent'
                included = bool(getattr(tax, 'price_include', False))
                tax_dicts.append({
                    'included_in_price': included,
                    'name': name,
                    'rate': rate,
                    'tax_type': tax_type
                })
            return tax_dicts

        # ----- Order Lines -----
        order_lines = [(5, 0)]
        _logger.info("[%s] Processing order lines", order_ref)

        for item in order.get("items", []):
            product = item.get("product", {}) or {}
            external_product_id = product.get("id")
            sku = item.get("sku") or product.get("sku") or product.get("id")

            _logger.info("[%s] Processing item: %s | external_product_id: %s | sku: %s",
                         order_ref, item.get("name"), external_product_id, sku)

            mapped_product = self.channel_id.match_product_mappings(external_product_id)
            attribute_options = None
            if not mapped_product:
                attribute_options = self.create_product_feed(external_product_id)
                _logger.info("[%s] Product not mapped, product feed created for external id %s", order_ref,
                             external_product_id)

            variant_ids = "No Variants"
            if item.get("options"):
                variant_ids = self.get_variant_id(item, attribute_options)
                _logger.info("[%s] Variant IDs: %s", order_ref, variant_ids)

            # Attempt to get taxes from the order first
            raw_tax = item.get("amounts", {}).get("tax")
            line_tax = self.process_tax(raw_tax) if raw_tax else []

            # If no line_tax, attempt to find product and extract tax(s)
            if not line_tax:
                product_record = find_product_record(mapped_product, external_product_id, sku)
                if product_record and product_record.exists() and product_record.taxes_id:
                    # build tax dicts for all product taxes
                    line_tax = build_tax_dicts_from_product(product_record)
                    _logger.info("[%s] No tax in order; using product taxes for %s -> %s",
                                 order_ref, external_product_id, line_tax)
                else:
                    line_tax = []
                    _logger.info("[%s] No tax found for product (after lookup): %s", order_ref, external_product_id)

            # ----- Line Data -----
            line_data = {
                'line_name': item.get("name"),
                'line_product_id': external_product_id,
                'line_variant_ids': variant_ids,
                'line_price_unit': item.get("amounts", {}).get("price_without_tax", {}).get("amount", 0.0),
                'line_product_uom_qty': item.get("quantity", 1),
                'line_product_default_code': item.get("sku", False),
                'line_taxes': line_tax,
            }

            _logger.info("[%s] Built line data: %s", order_ref, line_data)
            order_lines.append((0, 0, line_data))

        # ----- Order Discounts & Delivery -----
        order_tax = self.process_tax(order.get("amounts", {}).get("tax"))
        _logger.info("[%s] Order tax summary: %s", order_ref, order_tax)

        discounts = order.get('amounts', {}).get('discounts')
        if discounts:
            discount_line = self.get_discount_line(discounts, order_tax)
            _logger.info("[%s] Discount line: %s", order_ref, discount_line)
            if discount_line:
                order_lines.append(discount_line)

        if order.get('amounts', {}).get('shipping_cost'):
            shipping_line = self.get_shipping_line(order, order_tax)
            if shipping_line:
                _logger.info("[%s] Shipping line: %s", order_ref, shipping_line)
                order_lines.append(shipping_line)

        if order.get('amounts', {}).get('cash_on_delivery'):
            cod_line = self.get_cod_line(order, order_tax)
            if cod_line:
                _logger.info("[%s] COD line: %s", order_ref, cod_line)
                order_lines.append(cod_line)

        # ----- Final fallback: ensure any remaining [] taxes are tried again with more lookups -----
        for index, line_tuple in enumerate(order_lines):
            if len(line_tuple) < 3:
                continue
            line_data = line_tuple[2]
            if not line_data.get('line_taxes'):
                ext_pid = line_data.get('line_product_id')
                sku = line_data.get('line_product_default_code')
                product_record = find_product_record(None, ext_pid, sku)
                if product_record and product_record.exists() and product_record.taxes_id:
                    fixed_taxes = build_tax_dicts_from_product(product_record)
                    line_data['line_taxes'] = fixed_taxes
                    order_lines[index] = (0, 0, line_data)
                    _logger.info("[%s] Fallback fixed tax for line %s -> %s", order_ref, ext_pid, fixed_taxes)
                else:
                    _logger.info("[%s] Fallback: still no tax for line %s", order_ref, ext_pid)

        # ----- Finalize -----
        order_data['line_ids'] = order_lines
        _logger.info("[%s] Final order lines after tax fix: %s", order_ref, order_lines)
        _logger.info("[END] Order %s processed successfully", order_ref)
        return order_data

    def process_order(self, order):
        order_ref = order.get('reference_id')
        _logger.info("[START] Processing order: %s", order_ref)

        # ----- Order Main Info -----
        order_data = {
            'channel_id': self.id,
            'store_id': order.get('id'),
            'name': str(order_ref),
            'currency': order.get('currency'),
            'date_order': order.get('date', {}).get('date'),
            'confirmation_date': order.get('date', {}).get('date'),
            'order_state': order.get('status', {}).get('slug'),
            'line_type': 'multi',
        }
        _logger.info("[%s] Order base data: %s", order_ref, order_data)

        # ----- Payment Method -----
        payment_method = order.get('payment_method')
        if payment_method:
            order_data['payment_method'] = payment_method
            _logger.info("[%s] Payment method: %s", order_ref, payment_method)

        # ----- Carrier Info -----
        shipping_info = order.get('shipping') or order.get('shipments')
        if shipping_info and isinstance(shipping_info, dict):
            carrier_id = shipping_info.get('company') or shipping_info.get('courier_name')
            if carrier_id:
                order_data['carrier_id'] = carrier_id
                _logger.info("[%s] Carrier: %s", order_ref, carrier_id)

        # ----- Customer Info -----
        customer = order.get('customer')
        if customer:
            full_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            order_data.update({
                'partner_id': customer.get('id'),
                'customer_name': full_name or 'Unknown Customer',
                'customer_email': customer.get('email'),
                'customer_mobile': customer.get('mobile'),
                'customer_phone': customer.get('mobile'),
                'total_amount': order.get('amounts').get('total').get('amount'),
            })
            customer_contacts = self.process_address(order, customer.get('id'))
            order_data.update(customer_contacts)
            _logger.info("[%s] Customer: %s", order_ref, full_name)

        # ---- Helpers ----
        def find_product_record(mapped_product, external_product_id, sku_or_code):
            """
            Return a product.product record if found; otherwise return an empty recordset.
            Tries (in order):
              - If mapped_product is already product.product record
              - If mapped_product has a relation field to product (product_id, product_tmpl_id, ...)
              - Browse external_product_id if numeric
              - Search by default_code (sku_or_code)
            """
            # Log mapped_product type for debugging
            try:
                mapped_type = getattr(mapped_product, '_name', type(mapped_product).__name__)
            except Exception:
                mapped_type = str(type(mapped_product))
            _logger.info("[%s] find_product_record: mapped_product type: %s", order_ref, mapped_type)

            # 1) mapped_product might already be product.product
            try:
                if mapped_product:
                    if getattr(mapped_product, '_name', None) == 'product.product' and mapped_product.exists():
                        return mapped_product
                    # If the object itself exposes taxes_id, it's likely a product record
                    if hasattr(mapped_product, 'taxes_id'):
                        try:
                            if mapped_product.exists():
                                # ensure it's product.product; if it's template convert to variant
                                if getattr(mapped_product, '_name', '') == 'product.template':
                                    variants = mapped_product.product_variant_ids
                                    if variants:
                                        return variants[0]
                                    # not found -> fallback
                                else:
                                    return mapped_product
                        except Exception:
                            pass

                    # 2) mapping record: try common relational fields
                    for field in ('product_id', 'product_tmpl_id', 'mapped_product_id', 'odoo_id', 'odoo_product_id'):
                        try:
                            val = getattr(mapped_product, field, None)
                            if not val:
                                continue
                            # if val is a recordset
                            if getattr(val, 'exists', None) and val.exists():
                                # if product.template -> return first variant
                                if getattr(val, '_name', '') == 'product.template':
                                    variants = val.product_variant_ids
                                    if variants:
                                        return variants[0]
                                    continue
                                if getattr(val, '_name', '') == 'product.product':
                                    return val
                                # if it's something else, attempt to browse product.product by its id
                                try:
                                    if hasattr(val, 'id') and int(getattr(val, 'id', 0)):
                                        pr = self.env['product.product'].browse(int(val.id))
                                        if pr.exists():
                                            return pr
                                except Exception:
                                    pass
                            else:
                                # val could be an integer or string id
                                try:
                                    pid = int(val)
                                    pr = self.env['product.product'].browse(pid)
                                    if pr.exists():
                                        return pr
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception as e:
                _logger.exception("[%s] find_product_record mapped_product handling error: %s", order_ref, e)

            # 3) try browse external_product_id if numeric
            try:
                if external_product_id is not None:
                    pid = int(external_product_id)
                    pr = self.env['product.product'].browse(pid)
                    if pr.exists():
                        _logger.info("[%s] find_product_record: found by numeric external id %s -> product %s",
                                     order_ref, external_product_id, pr.id)
                        return pr
            except Exception:
                pass

            # 4) search by default_code / sku
            try:
                if sku_or_code:
                    pr = self.env['product.product'].search([('default_code', '=', str(sku_or_code))], limit=1)
                    if pr.exists():
                        _logger.info("[%s] find_product_record: found by default_code %s -> product %s", order_ref,
                                     sku_or_code, pr.id)
                        return pr
            except Exception:
                pass

            # nothing found
            _logger.info("[%s] find_product_record: no product found for mapped_product=%s external_id=%s sku=%s",
                         order_ref, mapped_type, external_product_id, sku_or_code)
            return self.env['product.product']

        def build_tax_dicts_from_product(product_record):
            tax_dicts = []
            for tax in product_record.taxes_id:
                try:
                    amount = float(getattr(tax, 'amount', 0.0) or 0.0)
                except Exception:
                    amount = 0.0
                rate = f"{amount:.2f}"
                name = f"Salla Tax {rate}%"
                tax_type = getattr(tax, 'amount_type', None) or getattr(tax, 'type', None) or 'percent'
                included = bool(getattr(tax, 'price_include', False) or getattr(tax, 'included_in_price', False))
                tax_dicts.append({
                    'included_in_price': included,
                    'name': name,
                    'rate': rate,
                    'tax_type': tax_type
                })
            return tax_dicts

        # ----- Order Lines -----
        order_lines = [(5, 0)]
        _logger.info("[%s] Processing order lines", order_ref)

        for item in order.get("items", []):
            product = item.get("product", {}) or {}
            external_product_id = product.get("id")
            sku = item.get("sku") or product.get("sku") or product.get("default_code")

            _logger.info("[%s] Processing item: %s | external_product_id: %s | sku: %s",
                         order_ref, item.get("name"), external_product_id, sku)

            mapped_product = self.channel_id.match_product_mappings(external_product_id)
            attribute_options = None
            if not mapped_product:
                attribute_options = self.create_product_feed(external_product_id)
                _logger.info("[%s] Product not mapped, product feed created for external id %s", order_ref,
                             external_product_id)

            variant_ids = "No Variants"
            if item.get("options"):
                variant_ids = self.get_variant_id(item, attribute_options)
                _logger.info("[%s] Variant IDs: %s", order_ref, variant_ids)

            # Attempt to get taxes from the order first
            raw_tax = item.get("amounts", {}).get("tax")
            line_tax = self.process_tax(raw_tax) if raw_tax else []

            # If no line_tax, attempt to find product and extract tax(s)
            if not line_tax:
                product_record = find_product_record(mapped_product, external_product_id, sku)
                if product_record and product_record.exists() and product_record.taxes_id:
                    line_tax = build_tax_dicts_from_product(product_record)
                    _logger.info("[%s] No tax in order; using product taxes for %s -> %s",
                                 order_ref, external_product_id, line_tax)
                else:
                    line_tax = []
                    _logger.info("[%s] No tax found for product (after lookup): %s", order_ref, external_product_id)

            # ----- Line Data -----
            line_data = {
                'line_name': item.get("name"),
                'line_product_id': external_product_id,
                'line_variant_ids': variant_ids,
                'line_price_unit': item.get("amounts", {}).get("price_without_tax", {}).get("amount", 0.0),
                'line_product_uom_qty': item.get("quantity", 1),
                'line_product_default_code': item.get("sku", False) or sku,
                'line_taxes': line_tax,
            }

            _logger.info("[%s] Built line data: %s", order_ref, line_data)
            order_lines.append((0, 0, line_data))

        # ----- Order Discounts & Delivery -----
        order_tax = self.process_tax(order.get("amounts", {}).get("tax"))
        _logger.info("[%s] Order tax summary: %s", order_ref, order_tax)

        discounts = order.get('amounts', {}).get('discounts')
        if discounts:
            discount_line = self.get_discount_line(discounts, order_tax)
            _logger.info("[%s] Discount line: %s", order_ref, discount_line)
            if discount_line:
                order_lines.append(discount_line)

        if order.get('amounts', {}).get('shipping_cost'):
            shipping_line = self.get_shipping_line(order, order_tax)
            if shipping_line:
                _logger.info("[%s] Shipping line: %s", order_ref, shipping_line)
                order_lines.append(shipping_line)

        if order.get('amounts', {}).get('cash_on_delivery'):
            cod_line = self.get_cod_line(order, order_tax)
            if cod_line:
                _logger.info("[%s] COD line: %s", order_ref, cod_line)
                order_lines.append(cod_line)

        # ----- Final fallback: ensure any remaining [] taxes are tried again -----
        for index, line_tuple in enumerate(order_lines):
            if len(line_tuple) < 3:
                continue
            line_data = line_tuple[2]
            if not line_data.get('line_taxes'):
                ext_pid = line_data.get('line_product_id')
                sku_code = line_data.get('line_product_default_code')
                product_record = find_product_record(None, ext_pid, sku_code)
                if product_record and product_record.exists() and product_record.taxes_id:
                    fixed_taxes = build_tax_dicts_from_product(product_record)
                    line_data['line_taxes'] = fixed_taxes
                    order_lines[index] = (0, 0, line_data)
                    _logger.info("[%s] Fallback fixed tax for line %s -> %s", order_ref, ext_pid, fixed_taxes)
                else:
                    _logger.info("[%s] Fallback: still no tax for line %s", order_ref, ext_pid)

        # ----- Finalize -----
        order_data['line_ids'] = order_lines
        _logger.info("[%s] Final order lines after tax fix: %s", order_ref, order_lines)
        _logger.info("[END] Order %s processed successfully", order_ref)
        return order_data


    def get_discount_line(self, order_dicounts, order_tax):
        _logger.info("Discount Line: %s", order_dicounts)
        discount_amount = 0
        discount_line = False
        for discount in order_dicounts:
            discount_amount += float(discount.get('discount'))
        if discount_amount:
            discount_line =(0,0, {
                'line_name': 'Discount: {}'.format(discount.get('title') or discount.get('code')),
                'line_price_unit': float(discount.get('discount')),
                'line_product_uom_qty': 1,
                'line_source': 'discount',
                'line_taxes': order_tax,
            })
        return discount_line
    
    def old_get_delivery_line(self, order, order_tax):
        delivery_amount = 0
        delivery_line = False
        if order.get('amounts').get('shipping_cost', {}).get('amount'):
            delivery_amount += order.get('amounts').get('shipping_cost', {}).get('amount')
        if order.get('amounts').get('cash_on_delivery',{}).get('amount'):
            delivery_amount += order.get('amounts').get('cash_on_delivery',{}).get('amount')
        if delivery_amount:
            delivery_line = (0,0, {
                'line_name': 'Delivery',
                'line_price_unit': delivery_amount,
                'line_product_uom_qty': 1,
                'line_taxes': order_tax,
                'line_source': 'delivery',
            })
        return delivery_line

    def get_shipping_line(self, order, order_tax):
        shipping_amount = order.get('amounts', {}).get('shipping_cost', {}).get('amount')
        if shipping_amount:
            return (0, 0, {
                'line_name': 'Shipping',
                'line_price_unit': shipping_amount,
                'line_product_uom_qty': 1,
                'line_taxes': order_tax,
                'line_source': 'delivery',
            })
        return False

    def get_cod_line(self, order, order_tax):
        cod_amount = order.get('amounts', {}).get('cash_on_delivery', {}).get('amount')
        if cod_amount:
            return (0, 0, {
                'line_name': 'Cash on Delivery',
                'line_price_unit': cod_amount,
                'line_product_uom_qty': 1,
                'line_taxes': [],
                'line_source': 'cash_on_delivery',
            })
        return False

    def get_variant_id(self, order_line_product, attribute_options=False):
        option_vals = []
        for rec in order_line_product.get("options"):
            option_vals.append(rec.get("id"))
        option_vals.sort()
        value = "_".join(map(str, option_vals))
        mappings = self.channel_id.match_template_mappings(
            store_product_id=order_line_product.get("product").get("id"))
        if mappings:
            template_id = mappings.template_name
            if template_id:
                if template_id.salla_product_attribute_options:
                    options = eval(template_id.salla_product_attribute_options)
                    return options.get(value)
        elif attribute_options:
            return eval(attribute_options).get(value)
        return False

    def process_tax(self, tax):
        if tax and tax.get("amount").get("amount"):            
            return [
                {
                    'included_in_price': False,
                    'name': f"Salla Tax {tax.get('percent')}%",
                    'rate': tax.get('percent'),
                    'tax_type': 'percent'
                }
            ]
        else:
            return False

    def create_product_feed(self, object_id): # orders item
        try:
            kw = dict(
                filter_type='id',
                object_id=str(object_id),
                page_size= self.channel_id.api_record_limit,
            )
            values, kw = self.channel_id.get_sallaApi().get_products(**kw)
            if values:
                vals = values[0]
                variants = vals.pop('variants')
                if variants:
                    feed_variants = [(0, 0, variant) for variant in variants]
                    vals.update(feed_variants=feed_variants)
                feed = self.channel_id.match_product_feeds(object_id)
                if not feed: #create product feed
                    feed = self.env['product.feed'].create(vals)
                return feed.salla_product_attribute_options
        except Exception as e:
            _logger.error('Error occurred %r',e, exc_info=True)            
        return False
