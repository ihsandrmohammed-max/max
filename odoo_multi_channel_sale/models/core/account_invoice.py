# -*- coding: utf-8 -*-

from odoo import models, fields, api
import itertools
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.ERROR)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    salla_so_id = fields.Char(string="Salla SO ID")

    def _invoice_paid_hook(self):
        from_webhook = self._context.get('from_webhook')
        if not from_webhook:
            self.wk_pre_confirm_paid()
        result = super(AccountInvoice, self)._invoice_paid_hook()
        if not from_webhook:
            self.wk_post_confirm_paid(result)
        return result

    def wk_get_invoice_order(self, invoice):
        data = map(
            lambda line_id: list(set(line_id.sale_line_ids.mapped('order_id'))),
            invoice.invoice_line_ids
        )
        return list(itertools.chain(*data))

    def wk_pre_confirm_paid(self):
        for invoice in self:
            for order_id in invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id'):
                mapping_ids = order_id.channel_mapping_ids
                if mapping_ids and mapping_ids[0].channel_id.state == 'validate' and mapping_ids[0].channel_id.active:
                    channel_id = mapping_ids[0].channel_id
                    if hasattr(channel_id, '%s_pre_confirm_paid' % channel_id.channel) and channel_id.sync_invoice and channel_id.state == 'validate':
                        getattr(channel_id, '%s_pre_confirm_paid' % channel_id.channel)(invoice, mapping_ids)

    def wk_post_confirm_paid(self, result):
        for invoice in self:
            for order_id in invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id'):
                mapping_ids = order_id.channel_mapping_ids
                if mapping_ids and mapping_ids[0].channel_id.state == 'validate' and mapping_ids[0].channel_id.active:
                    channel_id = mapping_ids[0].channel_id
                    if hasattr(channel_id, '%s_post_confirm_paid' % channel_id.channel) and channel_id.sync_invoice and channel_id.state == 'validate':
                        res = getattr(channel_id, '%s_post_confirm_paid' % channel_id.channel)(invoice, mapping_ids, result)
                        sync_vals = dict(
                        action_on='order_status',
                        ecomstore_refrence=mapping_ids[0].store_order_id,
                        odoo_id=mapping_ids[0].odoo_order_id,
                        action_type='export',
                    )
                        if res:
                            sync_vals['status'] = 'success'
                            sync_vals['summary'] = 'RealTime Order Status -> Invoiced'
                        else:
                            sync_vals['status'] = 'error'
                            sync_vals['summary'] = 'Invoicing at the ecommerce end was unsuccessful for the order.'
                        channel_id._create_sync(sync_vals)

    def old_action_update_payment_memo(self):
        for inv in self:
            # Update Payment Memo
            for y in inv.matched_payment_ids:
                y.write({'memo': inv.salla_so_id})
                y.move_id.write({'ref': inv.salla_so_id})
                default_account_id = y.move_id.journal_id.default_account_id.id
                for l in y.move_id.line_ids.filtered(lambda x: x.account_id.id == default_account_id):
                    l.write({'name': inv.salla_so_id})

                # Start get account from jornal
                # # For update line payment
                # for l in y.move_id.invoice_line_ids.filtered(lambda x: x.journal_id.type != 'cahe'):
                #     l.write({'name': inv.salla_so_id})
                # for l in y.move_id.line_ids:
                #     l.write({'name': inv.salla_so_id})

        #  Update Invoice Line Name
        # for line in inv.line_ids:
        #     line.write({'name': inv.salla_so_id})
        return True

    def action_update_payment_memo(self):
        for inv in self:
            _logger.info("🧾 [action_update_payment_memo] Start invoice: %s (ID: %s)", inv.name, inv.id)

            if not inv.salla_so_id:
                _logger.warning("⚠️ Invoice %s has no salla_so_id — skipping.", inv.name)
                continue

            # === Get all related payments ===
            payments = inv.matched_payment_ids or inv.reconciled_payment_ids

            # If both empty, try fetching reconciled payments manually
            if not payments and inv.is_invoice():
                try:
                    payments = inv._get_reconciled_payments()
                    _logger.debug("🔍 Retrieved %s payments using _get_reconciled_payments()", len(payments))
                except Exception:
                    _logger.debug("⚠️ _get_reconciled_payments() not available in this Odoo version")

            if not payments:
                _logger.warning("⚠️ Invoice %s has no linked payments — skipping.", inv.name)
                continue

            for pay in payments:
                if not pay.move_id:
                    _logger.warning("⚠️ Payment ID %s has no move_id", pay.id)
                    continue

                _logger.info("➡️ Updating payment ID: %s | Move: %s", pay.id, pay.move_id.name)

                pay.write({'memo': inv.salla_so_id})
                pay.move_id.write({'ref': inv.salla_so_id})

                journal = pay.move_id.journal_id
                if not journal:
                    _logger.warning("⚠️ No journal for payment move %s", pay.move_id.name)
                    continue

                default_account = journal.default_account_id
                if not default_account:
                    _logger.warning("⚠️ Journal '%s' has no default account", journal.name)
                    continue

                matched_lines = pay.move_id.line_ids.filtered(lambda l: l.account_id.id == default_account.id)
                _logger.debug("🔹 Found %s lines for account %s", len(matched_lines), default_account.name)

                for line in matched_lines:
                    old_name = line.name
                    line.write({'name': inv.salla_so_id})
                    _logger.info("✏️ Updated line ID %s | '%s' → '%s'", line.id, old_name, inv.salla_so_id)


            _logger.info("✅ Finished updating all payments for invoice: %s", inv.name)

        _logger.info("🎯 [action_update_payment_memo] Completed processing for %s invoice(s)", len(self))
        return True



    def action_fix_payments(self):
        for move in self:
            _logger.info("🔧 Starting payment fix for invoice: %s (ID: %s)", move.name, move.id)

            if move.state != 'posted':
                _logger.warning("Invoice %s is not posted. State: %s", move.name, move.state)
                raise UserError("You must post the invoice before fixing payments.")

            if move.payment_state == 'paid':
                _logger.info("Invoice %s already paid. Skipping.", move.name)
                raise UserError("The invoice is already paid.")

            payments = self.env['account.payment'].search([('memo', '=', move.name)])

            _logger.info("Found %s payment(s) for invoice %s", len(payments), move.name)

            if not payments:
                _logger.error("❌ No payments found for invoice %s (partner_id=%s, memo=%s)",
                              move.name, move.partner_id.id, move.name)
                raise UserError("No matching payments found for this invoice (based on partner and memo).")

            main_payment = payments[0]
            _logger.info("Selected main payment: %s (State: %s, Amount: %s)",
                         main_payment.name or main_payment.id,
                         main_payment.state,
                         main_payment.amount)

            if len(payments) > 1:
                _logger.warning("⚠️ Multiple payments found for invoice %s. Keeping the first, canceling others.",
                                move.name)
                for extra_payment in payments[1:]:
                    _logger.info("Processing extra payment: %s (State: %s)", extra_payment.id, extra_payment.state)
                    if extra_payment.state == 'posted':
                        extra_payment.action_cancel()
                        _logger.info("Canceled posted extra payment: %s", extra_payment.id)
                    elif extra_payment.state == 'draft':
                        extra_payment.unlink()
                        _logger.info("Deleted draft extra payment: %s", extra_payment.id)

            if main_payment.state == 'draft':
                _logger.info("Main payment is draft. Posting payment %s", main_payment.id)
                main_payment.action_post()
                _logger.info("✅ Main payment %s successfully posted.", main_payment.id)

            receivable_lines = move.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
            )
            payment_lines = main_payment.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
            )

            _logger.info("Invoice receivable lines: %s, Payment receivable lines: %s",
                         len(receivable_lines), len(payment_lines))

            if not receivable_lines or not payment_lines:
                _logger.warning("⚠️ Nothing to reconcile for invoice %s. Receivable or payment lines missing.",
                                move.name)
            else:
                _logger.info("Attempting reconciliation for invoice %s and payment %s", move.name, main_payment.id)
                (receivable_lines + payment_lines).reconcile()
                _logger.info("✅ Successfully reconciled payment %s with invoice %s", main_payment.id, move.name)

            move._compute_payment_state()
            _logger.info("🔄 Recomputed payment state for invoice %s. New state: %s", move.name, move.payment_state)

            _logger.info("🔄 Update Payment Memo")
            move.action_update_payment_memo()
            move.matched_payment_ids = [(6, 0, [main_payment.id])]

        _logger.info("🏁 Completed fixing payments for all selected invoices.")
        return True

