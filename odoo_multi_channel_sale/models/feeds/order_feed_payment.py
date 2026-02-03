# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


#channel.order.states
class ChannelOrderStates(models.Model):
    _inherit = 'channel.order.states'

    make_payment = fields.Boolean(string='Make Payment', default=False)


class OrderFeedPayment(models.Model):
    """
    Inherited model for order.feed to add payment functionality without invoice creation.
    This model extends order.feed with a method to process payments directly.
    """
    _inherit = 'order.feed'

    def process_payment_without_invoice(self, amount=None):
        """
        Process payment for the order feed without creating an invoice.
        This function creates a payment record directly linked to the sale order.
        
        @param amount: Optional payment amount. If not provided, uses order total_amount.
        @return: Dictionary with status and message
        """
        self.ensure_one()
        
        status = True
        status_message = ""
        
        try:
            # Get the sale order from mapping
            channel_id = self.channel_id
            if not channel_id:
                return {
                    'status': False,
                    'status_message': 'Channel not found for this feed.'
                }
            
            # Check if make_payment is enabled for this order state
            # If no record found with make_payment=True, exit silently without doing anything
            order_states = self.channel_id.order_state_ids.filtered(
                lambda state: state.channel_state == self.order_state and state.make_payment
            )
            if not order_states:
                # Exit silently if make_payment is not enabled
                return
            
            # Find the order mapping using name
            name = str(self.name) if self.name else False
            if not name:
                return {
                    'status': False,
                    'status_message': 'Store ID not found in feed.'
                }
            
            # Check if payment already exists for this order
            existing_payment = self.env['account.payment'].search([
                ('memo', '=', name)
            ], limit=1)
            if existing_payment:
                return {
                    'status': False,
                    'status_message': f'Payment already exists for order: {name}. Payment ID: {existing_payment.name}'
                }
            
            # Search for order mapping using store_order_id (not order_name)
            order_mapping = self.env['channel.order.mappings'].search([
                ('name', '=', name),
                ('channel_id', '=', channel_id.id)
            ], limit=1)
            
            if not order_mapping or not order_mapping.order_name:
                return {
                    'status': False,
                    'status_message': f'Order mapping not found for store ID: {name}. Please evaluate the feed first.'
                }
            
            sale_order = order_mapping.order_name
            
            # Get payment amount
            payment_amount = amount if amount else (self.total_amount or sale_order.amount_total)
            if not payment_amount or payment_amount <= 0:
                return {
                    'status': False,
                    'status_message': f'Invalid payment amount: {payment_amount}'
                }
            
            # Get or create payment journal
            payment_method = self.payment_method or 'Payment'
            journal_result = self.env['multi.channel.skeleton'].CreatePaymentMethod(
                channel_id, payment_method
            )
            journal_id = journal_result.get('journal_id')
            
            if not journal_id:
                return {
                    'status': False,
                    'status_message': f'Failed to get or create payment journal for method: {payment_method}'
                }
            
            # Get payment date
            date_invoice = False
            if self.date_invoice:
                date_info = channel_id.om_format_date(self.date_invoice)
                date_invoice = date_info.get('om_date_time')
            
            if not date_invoice:
                date_invoice = sale_order.date_order or fields.Datetime.now()
            
            # Add 3 hours to date (following existing pattern)
            real_date = date_invoice + timedelta(hours=3) if isinstance(date_invoice, fields.Datetime) else fields.Datetime.now()
            
            # Get partner from feed data instead of sale_order to ensure correct customer
            # Use store_partner_id from feed to get the correct partner
            _logger.info(f"=== Partner Mapping Search Debug ===")
            
            # Search for partner mapping
            search_domain = [('order_name', '=', self.name)]
            _logger.info(f"Searching partner mapping with domain: {search_domain}")
            
            partner_mapping = self.env['channel.order.mappings'].search(search_domain, limit=1)
            _logger.info(f"Partner mapping search result count: {len(partner_mapping)}")
            
            # Get partner_id from mapping if available, otherwise use sale_order partner
            if partner_mapping and partner_mapping.odoo_partner_id:
                partner_id = partner_mapping.odoo_partner_id.id
                _logger.info(f"Using partner_id from mapping: {partner_id}")
            else:
                # Fallback to sale_order partner_id if mapping not found
                partner_id = sale_order.partner_id.id if sale_order.partner_id else False
                _logger.info(f"Using partner_id from sale_order: {partner_id}")
            
            if not partner_id:
                return {
                    'status': False,
                    'status_message': f'Partner ID not found for order: {name}. Cannot create payment.'
                }

            # Get currency
            currency_id = sale_order.currency_id.id if sale_order.currency_id else False
            if not currency_id:
                currency_id = channel_id.company_id.currency_id.id
            
            # Create payment record directly
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': partner_id,
                'amount': payment_amount,
                'currency_id': currency_id,
                'journal_id': journal_id,
                'date': real_date,
                'memo': name,  # Order number as reference
            }
            
            # Create payment
            payment = self.env['account.payment'].create(payment_vals)
            
            # Post the payment
            payment.action_post()
            
            # Set memo field if it exists (following existing pattern from invoice_order.py)
            try:
                if hasattr(payment, 'memo'):
                    payment.write({'memo': name})
            except Exception:
                _logger.warning(f"Could not set memo field on payment {payment.id}")
            
            # Update payment move lines with order number (following existing pattern)
            if payment.move_id:
                payment.move_id.write({'ref': name})
                default_account_id = payment.move_id.journal_id.default_account_id.id
                if default_account_id:
                    for line in payment.move_id.line_ids.filtered(
                        lambda x: x.account_id.id == default_account_id
                    ):
                        line.write({'name': name})
            
            status_message = f'Payment created successfully. Payment ID: {payment.name}, Amount: {payment_amount}, Memo: {name}'
            _logger.info(f"Payment created for order feed {self.id}: {status_message}")
            
            # Update feed message to show success
            self.message = f"{status_message}<br/>{self.message or ''}"
            
        except Exception as e:
            status = False
            status_message = f'Error processing payment: {str(e)}'
            _logger.error(f"Error in process_payment_without_invoice for feed {self.id}: {e}", exc_info=True)
            
            # Update feed message to show error
            self.message = f"<span style='color: red;'>{status_message}</span><br/>{self.message or ''}"
        
        

