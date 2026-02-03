from typing import List, Any
import json
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.ERROR)

from odoo.http import request

class ParseHandleData:
    import json

    def _get_channel(self):
        channel = request.env['multi.channel.sale'].sudo().search([], limit=1)
        return channel


    def demo_parse_handle_data_sales_order_create(self):
        data = [
            {'channel_id': 2, 'store_id': 1700266216, 'name': '200526413', 'currency': 'SAR',
             'date_order': '2025-08-18 15:19:40.000000', 'confirmation_date': '2025-08-18 15:19:40.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616',
             'invoice_street': 'يسيس', 'invoice_street2': ' شارع يسيس، الحي يسي ،, يس,, أبو ظبي, الامارات',
             'invoice_zip': '', 'invoice_city': 'ABU DHABI', 'invoice_country_code': 'AE',
             'same_shipping_billing': True, 'line_ids': [(5, 0), (0, 0,
                                                                  {'line_name': 'فستان', 'line_product_id': 338785349,
                                                                   'line_variant_ids': 'No Variants',
                                                                   'line_price_unit': 174, 'line_product_uom_qty': 100,
                                                                   'line_product_default_code': '15504447-30000023080-',
                                                                   'line_taxes': False}), (0, 0, {'line_name': 'بلوزة',
                                                                                                  'line_product_id': 265891698,
                                                                                                  'line_variant_ids': None,
                                                                                                  'line_price_unit': 83,
                                                                                                  'line_product_uom_qty': 1,
                                                                                                  'line_product_default_code': '15900691-10000030310-',
                                                                                                  'line_taxes': False}),
                                                         (0, 0, {'line_name': 'Delivery', 'line_price_unit': 50,
                                                                 'line_product_uom_qty': 1, 'line_taxes': False,
                                                                 'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 1375687807, 'name': '200525788', 'currency': 'SAR',
             'date_order': '2025-08-18 15:13:09.000000', 'confirmation_date': '2025-08-18 15:13:09.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616', 'invoice_street': '٣٢٣',
             'invoice_street2': ' شارع ٣٢٣، الحي الزمرد ،, جدة, السعودية', 'invoice_zip': '', 'invoice_city': 'Jeddah',
             'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0), (0, 0,
                                                                                                {'line_name': 'فستان',
                                                                                                 'line_product_id': 338785349,
                                                                                                 'line_variant_ids': 'No Variants',
                                                                                                 'line_price_unit': 174,
                                                                                                 'line_product_uom_qty': 100,
                                                                                                 'line_product_default_code': '15504447-30000023080-',
                                                                                                 'line_taxes': False}),
                                                                                       (0, 0, {'line_name': 'Delivery',
                                                                                               'line_price_unit': 50,
                                                                                               'line_product_uom_qty': 1,
                                                                                               'line_taxes': False,
                                                                                               'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 783395856, 'name': '200525493', 'currency': 'SAR',
             'date_order': '2025-08-18 15:11:18.000000', 'confirmation_date': '2025-08-18 15:11:18.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616', 'invoice_street': '٦٠٦',
             'invoice_street2': ' شارع ٦٠٦، الحي العمل ،, الرياض, السعودية', 'invoice_zip': '',
             'invoice_city': 'Riyadh', 'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'فستان',
                                                                                                                      'line_product_id': 338785349,
                                                                                                                      'line_variant_ids': 'No Variants',
                                                                                                                      'line_price_unit': 174,
                                                                                                                      'line_product_uom_qty': 100,
                                                                                                                      'line_product_default_code': '15504447-30000023080-',
                                                                                                                      'line_taxes': False}),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'Delivery',
                                                                                                                      'line_price_unit': 50,
                                                                                                                      'line_product_uom_qty': 1,
                                                                                                                      'line_taxes': False,
                                                                                                                      'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 40695354, 'name': '200524447', 'currency': 'SAR',
             'date_order': '2025-08-18 15:00:33.000000', 'confirmation_date': '2025-08-18 15:00:33.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616', 'invoice_street': '506',
             'invoice_street2': ' شارع 506، الحي العمل ،, الرياض, السعودية', 'invoice_zip': '',
             'invoice_city': 'Riyadh', 'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'فستان',
                                                                                                                      'line_product_id': 338785349,
                                                                                                                      'line_variant_ids': 'No Variants',
                                                                                                                      'line_price_unit': 174,
                                                                                                                      'line_product_uom_qty': 100,
                                                                                                                      'line_product_default_code': '15504447-30000023080-',
                                                                                                                      'line_taxes': False}),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'Delivery',
                                                                                                                      'line_price_unit': 50,
                                                                                                                      'line_product_uom_qty': 1,
                                                                                                                      'line_taxes': False,
                                                                                                                      'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 596686952, 'name': '200516301', 'currency': 'SAR',
             'date_order': '2025-08-18 13:41:59.000000', 'confirmation_date': '2025-08-18 13:41:59.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616',
             'invoice_street': '٩٠٩٠', 'invoice_street2': ' شارع ٩٠٩٠، الحي العمل ،, الرياض, السعودية',
             'invoice_zip': '', 'invoice_city': 'Riyadh', 'invoice_country_code': 'SA', 'same_shipping_billing': True,
             'line_ids': [(5, 0), (0, 0, {'line_name': 'فستان', 'line_product_id': 338785349,
                                          'line_variant_ids': 'No Variants', 'line_price_unit': 174,
                                          'line_product_uom_qty': 100,
                                          'line_product_default_code': '15504447-30000023080-', 'line_taxes': False}), (
                          0, 0, {'line_name': 'Delivery', 'line_price_unit': 50, 'line_product_uom_qty': 1,
                                 'line_taxes': False, 'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 1005801600, 'name': '200516133', 'currency': 'SAR',
             'date_order': '2025-08-18 13:40:19.000000', 'confirmation_date': '2025-08-18 13:40:19.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616', 'invoice_street': '٥٠٣',
             'invoice_street2': ' شارع ٥٠٣، الحي العمل ،, الرياض, السعودية', 'invoice_zip': '',
             'invoice_city': 'Riyadh', 'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'فستان',
                                                                                                                      'line_product_id': 338785349,
                                                                                                                      'line_variant_ids': 'No Variants',
                                                                                                                      'line_price_unit': 174,
                                                                                                                      'line_product_uom_qty': 100,
                                                                                                                      'line_product_default_code': '15504447-30000023080-',
                                                                                                                      'line_taxes': False}),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'Delivery',
                                                                                                                      'line_price_unit': 50,
                                                                                                                      'line_product_uom_qty': 1,
                                                                                                                      'line_taxes': False,
                                                                                                                      'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 1940350772, 'name': '200515473', 'currency': 'SAR',
             'date_order': '2025-08-18 13:34:36.000000', 'confirmation_date': '2025-08-18 13:34:36.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616', 'invoice_street': '50',
             'invoice_street2': ' شارع 50، الحي 565 ،, Riyadh Airport, السعودية', 'invoice_zip': '',
             'invoice_city': 'Riyadh Airport', 'invoice_country_code': 'SA', 'same_shipping_billing': True,
             'line_ids': [(5, 0), (0, 0, {'line_name': 'فستان', 'line_product_id': 338785349,
                                          'line_variant_ids': 'No Variants', 'line_price_unit': 174,
                                          'line_product_uom_qty': 100,
                                          'line_product_default_code': '15504447-30000023080-', 'line_taxes': False}), (
                          0, 0, {'line_name': 'Delivery', 'line_price_unit': 50, 'line_product_uom_qty': 1,
                                 'line_taxes': False, 'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 1755421353, 'name': '200515342', 'currency': 'SAR',
             'date_order': '2025-08-18 13:33:18.000000', 'confirmation_date': '2025-08-18 13:33:18.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616', 'invoice_street': 'CCX',
             'invoice_street2': ' شارع CCX، الحي العمل ،, الرياض, السعودية', 'invoice_zip': '',
             'invoice_city': 'Riyadh', 'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'فستان',
                                                                                                                      'line_product_id': 338785349,
                                                                                                                      'line_variant_ids': 'No Variants',
                                                                                                                      'line_price_unit': 174,
                                                                                                                      'line_product_uom_qty': 100,
                                                                                                                      'line_product_default_code': '15504447-30000023080-',
                                                                                                                      'line_taxes': False}),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'Delivery',
                                                                                                                      'line_price_unit': 50,
                                                                                                                      'line_product_uom_qty': 1,
                                                                                                                      'line_taxes': False,
                                                                                                                      'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 446420034, 'name': '200514791', 'currency': 'SAR',
             'date_order': '2025-08-18 13:27:39.000000', 'confirmation_date': '2025-08-18 13:27:39.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1510632791, 'customer_name': 'EZZ Samir', 'customer_email': '',
             'customer_mobile': 1000573616, 'customer_phone': 1000573616, 'invoice_partner_id': 'billing_1510632791',
             'invoice_name': 'EZZ Samir', 'invoice_email': '', 'invoice_phone': '201000573616', 'invoice_street': 'CCX',
             'invoice_street2': ' شارع CCX، الحي العمل ،, الرياض, السعودية', 'invoice_zip': '',
             'invoice_city': 'Riyadh', 'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'فستان',
                                                                                                                      'line_product_id': 338785349,
                                                                                                                      'line_variant_ids': 'No Variants',
                                                                                                                      'line_price_unit': 174,
                                                                                                                      'line_product_uom_qty': 100,
                                                                                                                      'line_product_default_code': '15504447-30000023080-',
                                                                                                                      'line_taxes': False}),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'Delivery',
                                                                                                                      'line_price_unit': 50,
                                                                                                                      'line_product_uom_qty': 1,
                                                                                                                      'line_taxes': False,
                                                                                                                      'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 437238921, 'name': '200498478', 'currency': 'SAR',
             'date_order': '2025-08-18 10:07:48.000000', 'confirmation_date': '2025-08-18 10:07:48.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1109900279, 'customer_name': 'فاطمة الشامسي',
             'customer_email': '', 'customer_mobile': 555555555, 'customer_phone': 555555555,
             'invoice_partner_id': 'billing_1109900279', 'invoice_name': 'فاطمة الشامسي', 'invoice_email': '',
             'invoice_phone': '971555555555', 'invoice_street': 'EE',
             'invoice_street2': ' شارع EE، الحي العمل ،, الرياض, السعودية', 'invoice_zip': '', 'invoice_city': 'Riyadh',
             'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0), (0, 0,
                                                                                                {'line_name': 'فستان',
                                                                                                 'line_product_id': 338785349,
                                                                                                 'line_variant_ids': 'No Variants',
                                                                                                 'line_price_unit': 174,
                                                                                                 'line_product_uom_qty': 100,
                                                                                                 'line_product_default_code': '15504447-30000023080-',
                                                                                                 'line_taxes': False}),
                                                                                       (0, 0, {'line_name': 'Delivery',
                                                                                               'line_price_unit': 50,
                                                                                               'line_product_uom_qty': 1,
                                                                                               'line_taxes': False,
                                                                                               'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 1957032909, 'name': '200497770', 'currency': 'SAR',
             'date_order': '2025-08-18 10:00:10.000000', 'confirmation_date': '2025-08-18 10:00:10.000000',
             'order_state': 'payment_pending', 'line_type': 'multi', 'payment_method': 'waiting',
             'carrier_id': 'Dev Company', 'partner_id': 1109900279, 'customer_name': 'فاطمة الشامسي',
             'customer_email': '', 'customer_mobile': 555555555, 'customer_phone': 555555555,
             'invoice_partner_id': 'billing_1109900279', 'invoice_name': 'فاطمة الشامسي', 'invoice_email': '',
             'invoice_phone': '971555555555', 'invoice_street': '٢٢',
             'invoice_street2': ' شارع ٢٢، الحي العمل ،, الرياض, السعودية', 'invoice_zip': '', 'invoice_city': 'Riyadh',
             'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0), (0, 0,
                                                                                                {'line_name': 'فستان',
                                                                                                 'line_product_id': 338785349,
                                                                                                 'line_variant_ids': 'No Variants',
                                                                                                 'line_price_unit': 174,
                                                                                                 'line_product_uom_qty': 100,
                                                                                                 'line_product_default_code': '15504447-30000023080-',
                                                                                                 'line_taxes': False}),
                                                                                       (0, 0, {'line_name': 'Delivery',
                                                                                               'line_price_unit': 50,
                                                                                               'line_product_uom_qty': 1,
                                                                                               'line_taxes': False,
                                                                                               'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 21965956, 'name': '200497697', 'currency': 'SAR',
             'date_order': '2025-08-18 09:56:42.000000', 'confirmation_date': '2025-08-18 09:56:42.000000',
             'order_state': None, 'line_type': 'multi', 'partner_id': 1013343270, 'customer_name': 'Ahmed Elsaka',
             'customer_email': 'eng.elsaka09@gmail.com', 'customer_mobile': 547075043, 'customer_phone': 547075043,
             'line_ids': [(5, 0), (0, 0, {'line_name': 'زيت زيتون', 'line_product_id': 1003023301,
                                          'line_variant_ids': 'No Variants', 'line_price_unit': 1000,
                                          'line_product_uom_qty': 1, 'line_product_default_code': '44444444',
                                          'line_taxes': False})]},
            {'channel_id': 2, 'store_id': 1813440691, 'name': '200378136', 'currency': 'SAR',
             'date_order': '2025-08-17 15:26:45.000000', 'confirmation_date': '2025-08-17 15:26:45.000000',
             'order_state': 'under_review', 'line_type': 'multi', 'payment_method': 'cod', 'carrier_id': 'Dev Company',
             'partner_id': 1013343270, 'customer_name': 'Ahmed Elsaka', 'customer_email': 'eng.elsaka09@gmail.com',
             'customer_mobile': 547075043, 'customer_phone': 547075043, 'invoice_partner_id': 'billing_1013343270',
             'invoice_name': 'Ahmed Elsaka', 'invoice_email': 'eng.elsaka09@gmail.com', 'invoice_phone': '966547075043',
             'invoice_street': 'dd', 'invoice_street2': ' شارع dd، الحي العمل ،, الرياض, السعودية', 'invoice_zip': '',
             'invoice_city': 'Riyadh', 'invoice_country_code': 'SA', 'same_shipping_billing': True, 'line_ids': [(5, 0),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'زيت زيتون',
                                                                                                                      'line_product_id': 1003023301,
                                                                                                                      'line_variant_ids': 'No Variants',
                                                                                                                      'line_price_unit': 1000,
                                                                                                                      'line_product_uom_qty': 1,
                                                                                                                      'line_product_default_code': '44444444',
                                                                                                                      'line_taxes': False}),
                                                                                                                 (0, 0,
                                                                                                                  {
                                                                                                                      'line_name': 'Delivery',
                                                                                                                      'line_price_unit': 50,
                                                                                                                      'line_product_uom_qty': 1,
                                                                                                                      'line_taxes': False,
                                                                                                                      'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 1780857730, 'name': '200377639', 'currency': 'SAR',
             'date_order': '2025-08-17 15:23:42.000000', 'confirmation_date': '2025-08-17 15:23:42.000000',
             'order_state': 'under_review', 'line_type': 'multi', 'payment_method': 'cod', 'carrier_id': 'Dev Company',
             'partner_id': 1013343270, 'customer_name': 'Ahmed Elsaka', 'customer_email': 'eng.elsaka09@gmail.com',
             'customer_mobile': 547075043, 'customer_phone': 547075043, 'invoice_partner_id': 'billing_1013343270',
             'invoice_name': 'Ahmed Elsaka', 'invoice_email': 'eng.elsaka09@gmail.com', 'invoice_phone': '966547075043',
             'invoice_street': 'cairo', 'invoice_street2': ' شارع cairo، الحي العمل ،, الرياض, السعودية',
             'invoice_zip': '', 'invoice_city': 'Riyadh', 'invoice_country_code': 'SA', 'same_shipping_billing': True,
             'line_ids': [(5, 0), (0, 0, {'line_name': 'زيت زيتون', 'line_product_id': 1003023301,
                                          'line_variant_ids': 'No Variants', 'line_price_unit': 1000,
                                          'line_product_uom_qty': 1, 'line_product_default_code': '44444444',
                                          'line_taxes': False}), (0, 0, {'line_name': 'Delivery', 'line_price_unit': 50,
                                                                         'line_product_uom_qty': 1, 'line_taxes': False,
                                                                         'line_source': 'delivery'})]},
            {'channel_id': 2, 'store_id': 114683376, 'name': '200074581', 'currency': 'SAR',
             'date_order': '2025-08-15 14:53:13.000000', 'confirmation_date': '2025-08-15 14:53:13.000000',
             'order_state': 'under_review', 'line_type': 'multi', 'payment_method': 'cod', 'carrier_id': 'Dev Company',
             'partner_id': 1013343270, 'customer_name': 'Ahmed Elsaka', 'customer_email': 'eng.elsaka09@gmail.com',
             'customer_mobile': 547075043, 'customer_phone': 547075043, 'invoice_partner_id': 'billing_1013343270',
             'invoice_name': 'Ahmed Elsaka', 'invoice_email': 'eng.elsaka09@gmail.com', 'invoice_phone': '966547075043',
             'invoice_street': 'ابي بكر الصديق الفرعي',
             'invoice_street2': ' شارع ابي بكر الصديق الفرعي، الحي العمل 13316،, ابي بكر الصديق الفرعي,, الرياض, السعودية',
             'invoice_zip': '13316', 'invoice_city': 'Riyadh', 'invoice_country_code': 'SA',
             'same_shipping_billing': True, 'line_ids': [(5, 0), (0, 0, {'line_name': 'زيت زيتون',
                                                                         'line_product_id': 1003023301,
                                                                         'line_variant_ids': 'No Variants',
                                                                         'line_price_unit': 1000,
                                                                         'line_product_uom_qty': 1,
                                                                         'line_product_default_code': '44444444',
                                                                         'line_taxes': False}), (0, 0, {
                'line_name': 'Delivery', 'line_price_unit': 50, 'line_product_uom_qty': 1, 'line_taxes': False,
                'line_source': 'delivery'})]}]

        return data

    def old_parse_handle_data_sales_order_create(self, payload):
        """
        Expect full webhook payload (top-level dict).
        Returns a dict in the desired Odoo-like format.
        Fixed version to handle currency conversion and required fields properly.
        """
        data = payload.get("data", {}) or {}
        store_id = data.get("id")

        # Customer
        customer = data.get("customer", {}) or {}
        first = customer.get("first_name") or ""
        last = customer.get("last_name") or ""
        customer_name = (first + " " + last).strip() or "Unknown Customer"

        # Normalize phone
        mobile = customer.get("mobile")
        mobile_code = (customer.get("mobile_code") or "")
        code = mobile_code.lstrip("+") if isinstance(mobile_code, str) else ""
        invoice_phone = f"{code}{mobile}" if mobile is not None else "N/A"

        # Items
        items = data.get("items", []) or []
        _logger.info(f"Items: {items}")

        # Build lines - Fix the structure
        line_ids: List[Any] = [(5, 0)]  # Clear existing lines

        for item in items:
            # Get price from amounts structure
            amounts = item.get("amounts", {}) or {}
            price_without_tax = amounts.get("price_without_tax", {}) or {}
            total_amount = amounts.get("total", {}) or {}

            # Prepare taxes in proper format
            line_taxes_data = amounts.get("tax", {}) or {}
            if isinstance(line_taxes_data, dict):
                percent = line_taxes_data.get("percent")
                try:
                    percent = float(percent)
                except (TypeError, ValueError):
                    percent = 0.0

                line_taxes = json.dumps([{"rate": percent}])
            else:
                line_taxes = json.dumps([])

            # Extract price values
            unit_price = price_without_tax.get("amount", 0)
            total_price = total_amount.get("amount", 0)

            # Convert to float and handle price calculation
            try:
                unit_price = float(unit_price) if unit_price else 0
                total_price = float(total_price) if total_price else 0
                quantity = float(item.get("quantity", 1))
                discount_percentage = 0

                total_discount = float(item.get('amounts').get('total_discount').get('amount')) if total_price else 0

                if total_discount != 0 and total_price != 0:
                    discount_percentage = (total_discount / total_price) * 100
                else:
                    discount_percentage = 0

                # Determine the correct unit price
                if unit_price > 0:
                    # Use the unit price directly (already in SAR)
                    price_unit = unit_price
                elif total_price > 0 and quantity > 0:
                    # Calculate unit price from total (total is already in SAR)
                    price_unit = total_price / quantity
                else:
                    price_unit = 0

                # Debug: Print the calculation for verification
                print(f"Item: {item.get('name')}")
                print(f"  Unit price from API: {unit_price}")
                print(f"  Total price from API: {total_price}")
                print(f"  Quantity: {quantity}")
                print(f"  Calculated unit price: {price_unit}")
                print(f"  Calculated unit line_taxes: {line_taxes}")
                print(f"  Verification: {price_unit} × {quantity} = {price_unit * quantity}")
                print("-" * 40)
                print(f"discount_percentage: >>> {discount_percentage}")

            except (ValueError, ZeroDivisionError):
                price_unit = 0
                quantity = 1

            line_name = item.get("name") or "Unknown Product"

            # Create line item with proper field mapping
            line_data = {
                "line_name": line_name,
                "line_product_id": item.get("product").get("id"),
                "line_variant_ids": "No Variants",
                "line_price_unit": price_unit,
                "line_product_uom_qty": quantity,
                "line_product_default_code": item.get("sku") or "",
                "line_taxes": line_taxes,
                "line_source": "product",  # Added source tracking
            }
            if discount_percentage != 0:
                line_data['discount_percentage'] = discount_percentage

            _logger.info(f"data_line : {line_data}")

            line_ids.append((0, 0, line_data))

        # Shipping line - handle currency conversion
        shipping_amounts = data.get("amounts", {}).get("shipping_cost", {})
        shipping_amount = shipping_amounts.get("amount", 0) if shipping_amounts else 0

        try:
            shipping_amount = float(shipping_amount) if shipping_amount else 0
            # No currency conversion needed - already in SAR
        except (ValueError, TypeError):
            shipping_amount = 0

        if shipping_amount > 0:
            shipping_line = {
                "line_name": "Delivery",
                "line_product_id": False,  # Should be mapped to delivery product in Odoo
                "line_price_unit": shipping_amount,
                "line_product_uom_qty": 1,
                "line_variant_ids": "No Variants",
                "line_taxes": False,
                "line_source": "delivery",
            }
            line_ids.append((0, 0, shipping_line))

        # Determine line_type based on actual content
        product_line_count = len(line_data)
        _logger.info(f"Product line count01: {product_line_count}")
        line_type = "multi" if product_line_count > 1 else "single"
        _logger.info(f"Line type01: {line_type}")

        # Handle address data with defaults
        shipping_address = data.get("shipping", {}).get("address", {}) or {}
        street_number = shipping_address.get("street_number") or "N/A"
        shipping_addr = shipping_address.get("shipping_address") or "N/A"
        postal_code = shipping_address.get("postal_code") or ""
        city = shipping_address.get("city") or "N/A"
        country_code = shipping_address.get("country_code") or "SA"

        # Build the order data with proper field mapping
        order = {
            # Basic order info
            "channel_id": self._get_channel().id or 1,
            "store_id": store_id,
            "name": str(data.get("reference_id") or data.get("id") or ""),
            "currency": data.get("currency", "SAR"),
            "date_order": data.get("date", {}).get("date"),
            "confirmation_date": data.get("date", {}).get("date"),
            "order_state": data.get("status", {}).get("slug", "pending"),
            "line_type": line_type,
            "payment_method": data.get("payment_method", "unknown"),

            # Carrier info - set to False for now, should be mapped to actual carrier
            "carrier_id": "Dev Company",

            # Customer info - create new customer or map existing
            "partner_id": customer.get("id"),  # Will be created/mapped by Odoo
            "customer_name": customer_name,
            "customer_email": customer.get("email", ""),
            "customer_mobile": str(mobile) if mobile else "",
            "customer_phone": str(mobile) if mobile else "",

            # Invoice address
            "invoice_partner_id": False,  # Will be handled by Odoo
            "invoice_name": customer_name,
            "invoice_email": customer.get("email", ""),
            "invoice_phone": invoice_phone,
            "invoice_street": street_number,
            "invoice_street2": shipping_addr,
            "invoice_zip": postal_code,
            "invoice_city": city,
            "invoice_country_id": country_code,
            "same_shipping_billing": True,

            # Order lines
            "line_ids": line_ids,
        }

        # Validation: Ensure we have at least one line
        if len(line_ids) <= 1:  # Only the clear command
            # Add a placeholder line
            placeholder_line = {
                "line_name": "Empty Order",
                "line_product_id": False,
                "line_variant_ids": "No Variants",
                "line_price_unit": 0.0,
                "line_product_uom_qty": 1.0,
                "line_taxes": False,
                "line_source": "placeholder",
            }
            line_ids.append((0, 0, placeholder_line))
            order["line_ids"] = line_ids

        return [order]

    def _prepare_order_lines(self, items: list, data: dict) -> tuple[list, str]:
        """
        Prepare order line_ids based on items and shipping cost.
        Returns (line_ids, line_type)
        """
        line_ids: List[Any] = [(5, 0)]  # Clear existing lines

        for item in items:
            amounts = item.get("amounts", {}) or {}
            price_without_tax = amounts.get("price_without_tax", {}) or {}
            total_amount = amounts.get("total", {}) or {}

            line_taxes_data = amounts.get("tax", {}) or {}
            _logger.info(f"line_taxes_data >>> {line_taxes_data}")
            percent = line_taxes_data.get("percent")
            try:
                percent = float(str(percent).replace('%', '').strip()) if percent is not None else 0.0
            except (ValueError, TypeError):
                percent = 0.0

            if percent > 0:
                line_taxes = (
                    "[{'rate': %s, 'tax_rate': %s, 'type': 'percent', 'tax_type': 'percent'}]"
                    % (percent, percent)
                )
            else:
                line_taxes = "[]"

            # Price calculation
            try:
                unit_price = float(price_without_tax.get("amount", 0) or 0)
                total_price = float(total_amount.get("amount", 0) or 0)
                quantity = float(item.get("quantity", 1))
                discount_percentage = 0.00

                total_discount = float(item.get('amounts').get('total_discount').get('amount', 0))
                price_without_tax = float(item.get('amounts').get('price_without_tax').get('amount', 0))

                if total_discount != 0 and price_without_tax != 0:
                    discount_percentage = ((total_discount / quantity) / price_without_tax) * 100
                else:
                    discount_percentage = 0.0

                if unit_price > 0:
                    price_unit = unit_price
                elif total_price > 0 and quantity > 0:
                    price_unit = total_price / quantity
                else:
                    price_unit = 0.0

                _logger.info(f"Tax data received: {line_taxes_data}")
                _logger.info(f"Processed tax string: {line_taxes}")
                _logger.debug(
                    f"Item: {item.get('name')} | Unit: {unit_price} | Total: {total_price} | "
                    f"Qty: {quantity} | Calc Unit: {price_unit} | Taxes: {line_taxes}"
                )
            except (ValueError, ZeroDivisionError):
                price_unit = 0.0
                quantity = 1.0

            line_name = item.get("name") or "Unknown Product"

            line_data = {
                "line_name": line_name,
                "line_product_id": (item.get("product") or {}).get("id"),
                "line_variant_ids": "No Variants",
                "line_price_unit": price_unit,
                "line_product_uom_qty": quantity,
                "line_product_default_code": item.get("sku") or "",
                "line_taxes": line_taxes,
                "line_source": "product",
                "discount_percentage" : 0.0     #   discount_percentage
            }

            _logger.info(f"data_line : {line_data}")

            line_ids.append((0, 0, line_data))

        # --- Shipping line ---
        shipping_amounts = (data.get("amounts", {}) or {}).get("shipping_cost", {}) or {}
        shipping_amount = shipping_amounts.get("amount", 0)
        try:
            shipping_amount = float(shipping_amount) if shipping_amount else 0.0
        except (ValueError, TypeError):
            shipping_amount = 0.0

        if shipping_amount > 0:
            shipping_line = {
                "line_name": "Delivery",
                "line_product_id": False,
                "line_price_unit": shipping_amount,
                "line_product_uom_qty": 1,
                "line_variant_ids": "No Variants",
                "line_taxes": "[]",
                "line_source": "delivery",
            }
            line_ids.append((0, 0, shipping_line))

        #   This for cash_on_delivery
        cash_on_delivery_amounts = (data.get("amounts", {}) or {}).get("cash_on_delivery", {}) or {}
        cash_on_delivery_amount = cash_on_delivery_amounts.get("amount", 0)
        if cash_on_delivery_amount > 0:
            cash_on_delivery_line = {
                "line_name": "Fess Cash on Delivery",
                "line_product_id": False,
                "line_price_unit": cash_on_delivery_amount,
                "line_product_uom_qty": 1,
                "line_variant_ids": "No Variants",
                "line_taxes": "[]",
                "line_source": "cash_on_delivery",
            }
            line_ids.append((0, 0, cash_on_delivery_line))

        # This for global Discount

        list_discounts = (data.get("amounts", {}) or {}).get("discounts", {}) or {}
        for d in list_discounts:
            try:
                discount_amount = float(d.get("discount", 0) or 0)
                title = str(d.get("title"))
            except (ValueError, TypeError):
                discount_amount = 0.0

            if discount_amount > 0:
                discount_line = {
                    "line_name": f"Discount: {title}",
                    "line_product_id": False,
                    "line_price_unit": discount_amount,
                    "line_product_uom_qty": 1,
                    "line_variant_ids": "No Variants",
                    "line_taxes": "[]",
                    "line_source": "discount",
                }
                line_ids.append((0, 0, discount_line))


        # --- Determine line_type ---
        product_line_count = len(line_ids) - 1  # subtract the clear command
        line_type = "multi" if product_line_count > 1 else "single"
        line_type = "multi"

        # --- Ensure placeholder line if empty ---
        if product_line_count <= 0:
            placeholder_line = {
                "line_name": "Empty Order",
                "line_product_id": False,
                "line_variant_ids": "No Variants",
                "line_price_unit": 0.0,
                "line_product_uom_qty": 1.0,
                "line_taxes": "[]",
                "line_source": "placeholder",
            }
            line_ids.append((0, 0, placeholder_line))

        return line_ids, line_type

    def parse_handle_data_sales_order_create(self, payload):
        """
        Expect full webhook payload (top-level dict).
        Returns a dict in the desired Odoo-like format.
        Fixed version to handle currency conversion, taxes as JSON, and required fields properly.
        """
        data = payload.get("data", {}) or {}
        store_id = data.get("id")

        # --- Customer Data ---
        customer = data.get("customer", {}) or {}
        first = customer.get("first_name") or ""
        last = customer.get("last_name") or ""
        customer_name = (first + " " + last).strip() or "Unknown Customer"

        # Normalize phone
        mobile = customer.get("mobile")
        mobile_code = (customer.get("mobile_code") or "")
        code = mobile_code.lstrip("+") if isinstance(mobile_code, str) else ""
        invoice_phone = f"{code}{mobile}" if mobile is not None else "N/A"

        # --- Order Lines ---
        items = data.get("items", []) or []
        line_ids, line_type = self._prepare_order_lines(items, data)

        # --- Shipping Address ---
        shipping_address = (data.get("shipping", {}) or {}).get("address", {}) or {}
        street_number = shipping_address.get("street_number") or "N/A"
        shipping_addr = shipping_address.get("shipping_address") or "N/A"
        postal_code = shipping_address.get("postal_code") or ""
        city = shipping_address.get("city") or "N/A"
        country_code = shipping_address.get("country_code") or "SA"

        total_amount = data.get("amounts", {}).get("total", {}).get("amount", 0)
        # --- Build order payload ---
        order = {
            "channel_id": self._get_channel().id or 1,
            "store_id": store_id,
            "name": str(data.get("reference_id") or data.get("id") or ""),
            "currency": data.get("currency", "SAR"),
            "date_order": (data.get("date") or {}).get("date"),
            "confirmation_date": (data.get("date") or {}).get("date"),
            "order_state": (data.get("status") or {}).get("slug", "pending"),
            "line_type": line_type,
            "payment_method": data.get("payment_method", "unknown"),
            "carrier_id": "Dev Company",

            # Customer info
            "partner_id": customer.get("id"),
            "customer_name": customer_name,
            "customer_email": customer.get("email", ""),
            "customer_mobile": str(mobile) if mobile else "",
            "customer_phone": str(mobile) if mobile else "",

            # Invoice address
            "invoice_partner_id": False,
            "invoice_name": customer_name,
            "invoice_email": customer.get("email", ""),
            "invoice_phone": invoice_phone,
            "invoice_street": street_number,
            "invoice_street2": shipping_addr,
            "invoice_zip": postal_code,
            "invoice_city": city,
            "invoice_country_id": country_code,
            "same_shipping_billing": True,
            "total_amount": total_amount,

            # Order lines
            "line_ids": line_ids,
        }

        return [order]
    def get_country_id_by_code(self, country_code):
        """
        Map country code to Odoo country ID.
        You should replace this with actual Odoo country lookup.
        """
        country_mapping = {
            "SA": 1,  # Saudi Arabia
            "EG": 67,  # Egypt
            "AE": 231,  # UAE
            "US": 233,  # United States
            "GB": 77,  # United Kingdom
            # Add more mappings based on your Odoo country records
        }
        return country_mapping.get(country_code.upper(), 1)  # Default to SA

    def convert_currency_if_needed(self, amount, threshold=1000):
        """
        Convert amount - in this case, no conversion needed as values are already in SAR.
        Keeping this method for backward compatibility.
        """
        try:
            amount = float(amount) if amount else 0
            return amount  # No conversion needed
        except (ValueError, TypeError):
            return 0.0

    def parse_final_order_data(self, final_data):
        """
        Process the final order data structure that's already formatted.
        This method handles the data structure you provided as the final format.
        """
        # Extract basic order information
        line_ids = self._process_line_items(final_data.get('line_ids', []))
        product_line_count = len(line_ids)
        _logger.info(f"Product line count: {product_line_count}")
        line_type = "multi" if product_line_count > 1 else "single"
        line_type = "multi"
        _logger.info(f"Line type: {line_type}")


        order_data = {
            'channel_id': final_data.get('channel_id', self._get_channel().id),
            'store_id': str(final_data.get('store_id', '')),
            'name': str(final_data.get('name', '')),
            'currency': final_data.get('currency', 'SAR'),
            'date_order': final_data.get('date_order'),
            'confirmation_date': final_data.get('confirmation_date'),
            'order_state': final_data.get('order_state', 'pending'),
            'line_type': line_type,
            'payment_method': final_data.get('payment_method', 'unknown'),
            'carrier_id': final_data.get('carrier_id'),

            # Customer information
            'partner_id': str(final_data.get('partner_id', '')) if final_data.get('partner_id') else False,
            'customer_name': final_data.get('customer_name', ''),
            'customer_email': final_data.get('customer_email', ''),
            'customer_mobile': str(final_data.get('customer_mobile', '')) if final_data.get('customer_mobile') else '',
            'customer_phone': str(final_data.get('customer_phone', '')) if final_data.get('customer_phone') else '',

            # Invoice address information
            'invoice_partner_id': str(final_data.get('invoice_partner_id', '')) if final_data.get('invoice_partner_id') else False,
            'invoice_name': final_data.get('invoice_name', ''),
            'invoice_email': final_data.get('invoice_email', ''),
            'invoice_phone': str(final_data.get('invoice_phone', '')) if final_data.get('invoice_phone') else '',
            'invoice_street': final_data.get('invoice_street', ''),
            'invoice_street2': final_data.get('invoice_street2', ''),
            'invoice_zip': final_data.get('invoice_zip', ''),
            'invoice_city': final_data.get('invoice_city', ''),
            'invoice_country_id': final_data.get('invoice_country_code', 'SA'),
            'same_shipping_billing': final_data.get('same_shipping_billing', True),

            # Process line items
            'line_ids': line_ids,
        }

        return order_data

    def _process_line_items(self, line_ids):
        """
        Process the line items from the final data structure.
        Handles the (5, 0) clear command and (0, 0, data) create commands.
        """
        processed_lines = []

        for line_item in line_ids:
            if isinstance(line_item, (list, tuple)):
                if len(line_item) == 2 and line_item[0] == 5 and line_item[1] == 0:
                    # Clear existing lines command
                    processed_lines.append((5, 0))
                elif len(line_item) == 3 and line_item[0] == 0 and line_item[1] == 0:
                    # Create new line command
                    line_data = line_item[2]
                    processed_line_data = {
                        'line_name': line_data.get('line_name', ''),
                        'line_product_id': line_data.get('line_product_id'),
                        'line_variant_ids': line_data.get('line_variant_ids', 'No Variants'),
                        'line_price_unit': float(line_data.get('line_price_unit', 0)),
                        'line_product_uom_qty': float(line_data.get('line_product_uom_qty', 1)),
                        'line_product_default_code': line_data.get('line_product_default_code', ''),
                        'line_taxes': line_data.get('line_taxes', False),
                        'line_source': line_data.get('line_source', 'product'),
                    }
                    _logger.info(f"processed_line_data >>>>> {processed_line_data}")
                    processed_lines.append((0, 0, processed_line_data))

        return processed_lines

    # Example usage and testing

    def parse_final_partner_data_create(self, payload: dict = None, channel_id=1) -> dict:
        """
        Transform raw Salla customer.created payload into normalized dict.
        """
        if not payload or "data" not in payload:
            return {}

        customer = payload.get("data", {})

        normalized = {
            "channel_id": channel_id,
            "store_id": payload.get("data").get("id"),
            "name": customer.get("full_name", "") or customer.get("first_name", ""),
            "last_name": customer.get("last_name", ""),
            "email": customer.get("email", ""),
            "mobile": customer.get("mobile", ""),
            "city": customer.get("city", ""),
            "street": customer.get("city", ""),
            "country_code": customer.get("country", ""),
            "website": customer.get("urls", {}).get("customer", ""),
            "contacts": []
        }

        return [normalized]


    def parse_final_product_data_create(self, payload: dict = None, channel_id=1) -> dict:
        """
        Transform raw Salla product.created payload into normalized dict.
        """
        if not payload or "data" not in payload:
            return {}

        product = payload.get("data", {})

        normalized = {
            "store_id": product.get("id"),
            "name": product.get("name", ""),
            "channel_id": channel_id,
            "channel": "salla",
            "description_sale": product.get("description", ""),
            "description": product.get("metadata", {}).get("description", ""),
            "image_url": product.get("main_image") or product.get("thumbnail", ""),
            "list_price": product.get("price", {}).get("amount", 0),
            "weight": product.get("weight", 0.0),
            "wk_default_code": product.get("sku", ""),
            "default_code": product.get("mpn", ""),
            "qty_available": str(product.get("quantity", "None")),
            "extra_categ_ids": False
        }

        return [normalized]

    def parse_final_category_data_create(self, payload: dict = None, channel_id=1) -> dict:
        """
        Transform raw Salla category.created payload into normalized dict.
        """
        if not payload or "data" not in payload:
            return {}

        category = payload.get("data", {})

        normalized = {
            "channel_id": channel_id,
            "channel": "salla",
            "leaf_category": not bool(category.get("sub_categories")),
            "parent_id": category.get("parent_id") or False,
            "store_id": payload.get("merchant"),
            "name": category.get("name", "")
        }

        return [normalized]


