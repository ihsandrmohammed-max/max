# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.tools import float_compare, float_is_zero, date_utils, email_split, html_escape, is_html_empty

from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')


class IncluseFeesProduct(models.Model):
    _inherit = 'product.product'

    include_fees = fields.Boolean('Include Fees')


class AccountInvoice(models.Model):
    _inherit = 'account.journal'

    is_fee = fields.Boolean('Consider Account Fees in Entries')
    fee_account_id = fields.Many2one('account.account', 'Fees Account')
    percentage = fields.Float('Percentage', digits="Bank Fees", )
    extra_fees = fields.Float('Extra Fees', digits="Bank Fees")
    tax_fees = fields.Float('Tax Fees')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    paid_amount = fields.Float('Paid Amount', readonly=True)

    @api.onchange('amount', 'payment_type')
    def onchange_amount(self):
        if self.amount or self.payment_type:
            if self.payment_type == 'inbound':
                self.paid_amount = self.amount
            else:
                self.paid_amount = -1 * self.amount

    def old00_prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        res = super(AccountPayment, self)._prepare_move_line_default_vals()
        fees_data = []
        total_fees_amount = 0.0
        fees_amount = 0.0
        extra_fees = 0.0
        tax_fees_amount = 0.0

        if self.journal_id.is_fee and self.journal_id.percentage:
            fees_account_id = self.journal_id.fee_account_id.id if self.journal_id.fee_account_id else False
            total_fees_amount = (self.amount * self.journal_id.percentage) / 100
            extra_fees = self.journal_id.extra_fees
            _logger.info(f"Total bank fee to distribute: {total_fees_amount}")
            product_fees = total_fees_amount
            tax_fees_amount = (product_fees * self.journal_id.tax_fees) / 100
            product_fees = product_fees

            fees_amount = product_fees

            fee_line_vals = {
                'name': f'Bank Fees Amount {fees_amount}',
                'date_maturity': self.date,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'account_id': fees_account_id,
                'payment_id': self.id,
            }
            extra_fees_line = {
                'name': f'Extra Fees Amount {extra_fees}',
                'date_maturity': self.date,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'account_id': fees_account_id,
                'payment_id': self.id,
            }

            tax_fees_line = {
                'name': f'Tax Fees Amount {tax_fees_amount}',
                'date_maturity': self.date,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'account_id': fees_account_id,
                'payment_id': self.id,
            }

            if self.payment_type == 'inbound':
                fee_line_vals.update({'debit': fees_amount, 'credit': 0.0})
                extra_fees_line.update({'debit': extra_fees, 'credit': 0.0})
                tax_fees_line.update({'debit': tax_fees_amount, 'credit': 0.0})
            else:
                fee_line_vals.update({'debit': 0.0, 'credit': product_fees})
                extra_fees_line.update({'debit': 0.0, 'credit': extra_fees})
                tax_fees_line.update({'credit': tax_fees_amount, 'debit': 0.0})

            fees_data.append(fee_line_vals)
            fees_data.append(extra_fees_line)
            fees_data.append(tax_fees_line)

        account_credit = self.env['account.payment.method.line'].sudo().search(
            [('id', '=', self.payment_method_line_id.id)], limit=1)
        account_id = account_credit.payment_account_id.id

        liquidity_amount_currency = round(self.amount - (fees_amount + extra_fees + tax_fees_amount), 2)

        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )

        res[0]['account_id'] = account_id
        res[0]['amount_currency'] = liquidity_balance if liquidity_balance > 0.0 else -liquidity_balance

        if self.payment_type == 'inbound':
            res[0]['debit'] = liquidity_balance if liquidity_balance > 0.0 else 0.0
        else:
            res[0]['credit'] = liquidity_balance if liquidity_balance > 0.0 else 0.0
            res[0]['amount_currency'] = -1 * res[0]['amount_currency']

        res += fees_data
        return res


    def old01_prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        _logger.info("=== START _prepare_move_line_default_vals ===")
        _logger.info(
            "Payment ID: %s | Amount: %s | Type: %s | Journal: %s | Date: %s",
            self.id, self.amount, self.payment_type, self.journal_id.name, self.date
        )

        res = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals, force_balance)
        _logger.debug("Initial move lines from super(): %s", res)

        company_currency = self.company_id.currency_id
        comp_cur_id = company_currency.id

        fees_data = []
        base_fees = 0.0
        extra_fees = 0.0
        tax_fees = 0.0
        total_fees = 0.0

        _logger.info("Checking journal fee configuration...")
        if self.journal_id.is_fee and (self.journal_id.percentage or self.journal_id.extra_fees):
            _logger.info("Journal has fee configuration enabled.")
            fees_account_id = self.journal_id.fee_account_id.id if self.journal_id.fee_account_id else False
            base_fees = (self.amount * (self.journal_id.percentage or 0.0)) / 100.0
            extra_fees = float(self.journal_id.extra_fees or 0.0)
            tax_fees = (base_fees * (self.journal_id.tax_fees or 0.0)) / 100.0
            total_fees = round(base_fees + extra_fees + tax_fees, 6)
            _logger.info(
                "Fees calculated -> base: %.6f | extra: %.6f | tax: %.6f | total: %.6f",
                base_fees, extra_fees, tax_fees, total_fees
            )

            if fees_account_id:
                for label, amount in [
                    ("Bank Fees", base_fees),
                    ("Extra Fees", extra_fees),
                    ("Tax Fees", tax_fees),
                ]:
                    if not amount:
                        continue
                    amt_rounded = round(amount, 2)
                    fee_line = {
                        'name': f'{label}: {amt_rounded}',
                        'date_maturity': self.date,
                        'partner_id': self.partner_id.id if self.partner_id else False,
                        'account_id': fees_account_id,
                        'payment_id': self.id,
                        'currency_id': comp_cur_id,
                        'amount_currency': amt_rounded if self.payment_type == 'inbound' else -amt_rounded,
                    }
                    if self.payment_type == 'inbound':
                        fee_line.update({'debit': amt_rounded, 'credit': 0.0})
                    else:
                        fee_line.update({'debit': 0.0, 'credit': amt_rounded})
                    fees_data.append(fee_line)
                    _logger.debug("Prepared fee line: %s", fee_line)

        _logger.info("Fetching payment method line and liquidity account...")
        account_pm_line = None
        if self.payment_method_line_id:
            account_pm_line = self.env['account.payment.method.line'].sudo().search(
                [('id', '=', self.payment_method_line_id.id)], limit=1)
        account_id = account_pm_line.payment_account_id.id if account_pm_line else (
            res[0].get('account_id') if res else None)
        _logger.info("Selected liquidity account_id: %s", account_id)

        liquidity_amount_currency = round(self.amount - total_fees, 6)
        _logger.info("Liquidity amount_currency (payment currency) after fees: %.6f", liquidity_amount_currency)

        liquidity_company_amount = round(self.currency_id._convert(
            liquidity_amount_currency, company_currency, self.company_id, self.date
        ), 6)
        _logger.info("Liquidity company amount (converted): %.6f", liquidity_company_amount)

        # Ensure there are initial lines from super()
        if not res or not isinstance(res, list) or len(res) < 2:
            _logger.warning("Unexpected structure from super(): res=%s", res)

        # Adjust first line (liquidity) and ensure all lines have company currency id
        if res and isinstance(res, list) and len(res) >= 1:
            main_line = res[0]
            main_line['account_id'] = account_id
            main_line['currency_id'] = comp_cur_id
            # amount_currency must reflect company currency when company currency == payment currency
            # we keep amount_currency as company currency amount because company and payment currency are same scenario in your case
            main_line['amount_currency'] = liquidity_amount_currency
            if self.payment_type == 'inbound':
                main_line['debit'] = round(liquidity_company_amount, 2)
                main_line['credit'] = 0.0
            else:
                main_line['credit'] = round(liquidity_company_amount, 2)
                main_line['debit'] = 0.0
                main_line['amount_currency'] = -main_line.get('amount_currency', 0.0)
            _logger.debug("Adjusted liquidity line: %s", main_line)

        # Force company currency on all original lines (to avoid Odoo internal reconversion surprises)
        for idx, line in enumerate(res):
            line['currency_id'] = comp_cur_id
            # ensure amount_currency sign matches debit/credit when company currency used
            # If company currency is same as payment currency, amount_currency should equal debit-credit (company amount)
            # We'll leave amount_currency as is for original second line (counterpart), but force the type if missing
            if 'debit' in line and 'credit' in line:
                balance = round((line.get('debit', 0.0) - line.get('credit', 0.0)), 2)
                line['amount_currency'] = balance
            _logger.debug("Normalized original line %s: %s", idx, line)

        # Append fee lines (already set to company currency)
        res += fees_data
        _logger.debug("Merged lines (liquidity + counterpart + fees): %s", res)

        # Calculate totals in company currency
        total_debit = round(sum(float(line.get('debit', 0.0)) for line in res), 6)
        total_credit = round(sum(float(line.get('credit', 0.0)) for line in res), 6)
        diff = round(total_debit - total_credit, 6)
        _logger.info("Totals -> Debit: %.6f | Credit: %.6f | Diff: %.6f", total_debit, total_credit, diff)

        # If imbalance small, add rounding adjustment line with correct signs
        if abs(diff) > 0.000001:
            _logger.warning("Detected imbalance (diff=%.6f). Preparing adjustment.", diff)
            adj_amount = round(abs(diff), 2)  # round adjustment to cents
            # Build adjustment line in company currency
            # If diff > 0 => Debit > Credit => need a credit adjustment (amount_currency negative)
            # If diff < 0 => Credit > Debit => need a debit adjustment (amount_currency positive)
            if diff > 0:
                adj_line = {
                    'name': f'Rounding Adjustment ({diff:.6f})',
                    'date_maturity': self.date,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'account_id': account_id,
                    'currency_id': comp_cur_id,
                    # amount_currency must be negative for credit line
                    'amount_currency': -adj_amount,
                    'debit': 0.0,
                    'credit': adj_amount,
                }
            else:
                adj_line = {
                    'name': f'Rounding Adjustment ({diff:.6f})',
                    'date_maturity': self.date,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'account_id': account_id,
                    'currency_id': comp_cur_id,
                    # amount_currency must be positive for debit line
                    'amount_currency': adj_amount,
                    'debit': adj_amount,
                    'credit': 0.0,
                }
            _logger.info("Adding adjustment line: %s", adj_line)
            res.append(adj_line)

            # recompute totals after adjustment
            total_debit = round(sum(float(line.get('debit', 0.0)) for line in res), 6)
            total_credit = round(sum(float(line.get('credit', 0.0)) for line in res), 6)
            _logger.info("Totals after adjustment -> Debit: %.6f | Credit: %.6f", total_debit, total_credit)

        _logger.info("=== END _prepare_move_line_default_vals ===")
        return res

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        _logger.info("=== START _prepare_move_line_default_vals ===")
        _logger.info(
            "Payment ID: %s | Amount: %s | Type: %s | Journal: %s | Date: %s",
            self.id, self.amount, self.payment_type, self.journal_id.name, self.date
        )

        res = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals, force_balance)
        _logger.debug("Initial move lines from super(): %s", res)

        company_currency = self.company_id.currency_id
        comp_cur_id = company_currency.id

        fees_data = []
        base_fees = 0.0
        extra_fees = 0.0
        tax_fees = 0.0
        total_fees = 0.0

        _logger.info("Checking journal fee configuration...")
        if self.journal_id.is_fee and (self.journal_id.percentage or self.journal_id.extra_fees):
            _logger.info("Journal has fee configuration enabled.")
            fees_account_id = self.journal_id.fee_account_id.id if self.journal_id.fee_account_id else False
            base_fees = (self.amount * (self.journal_id.percentage or 0.0)) / 100.0
            extra_fees = float(self.journal_id.extra_fees or 0.0)
            tax_fees = (base_fees * (self.journal_id.tax_fees or 0.0)) / 100.0
            total_fees = round(base_fees + extra_fees + tax_fees, 6)
            _logger.info(
                "Fees calculated -> base: %.6f | extra: %.6f | tax: %.6f | total: %.6f",
                base_fees, extra_fees, tax_fees, total_fees
            )

            if fees_account_id:
                for label, amount in [
                    ("Bank Fees", base_fees),
                    ("Extra Fees", extra_fees),
                    ("Tax Fees", tax_fees),
                ]:
                    if not amount:
                        continue
                    amt_rounded = round(amount, 2)
                    fee_line = {
                        'name': f'{label}: {amt_rounded}',
                        'date_maturity': self.date,
                        'partner_id': self.partner_id.id if self.partner_id else False,
                        'account_id': fees_account_id,
                        'payment_id': self.id,
                        'currency_id': comp_cur_id,
                        'amount_currency': amt_rounded if self.payment_type == 'inbound' else -amt_rounded,
                    }
                    if self.payment_type == 'inbound':
                        fee_line.update({'debit': amt_rounded, 'credit': 0.0})
                    else:
                        fee_line.update({'debit': 0.0, 'credit': amt_rounded})
                    fees_data.append(fee_line)
                    _logger.debug("Prepared fee line: %s", fee_line)

        _logger.info("Fetching payment method line and liquidity account...")
        account_pm_line = None
        if self.payment_method_line_id:
            account_pm_line = self.env['account.payment.method.line'].sudo().search(
                [('id', '=', self.payment_method_line_id.id)], limit=1)
        account_id = account_pm_line.payment_account_id.id if account_pm_line else (
            res[0].get('account_id') if res else None)
        _logger.info("Selected liquidity account_id: %s", account_id)

        liquidity_amount_currency = round(self.amount - total_fees, 6)
        _logger.info("Liquidity amount_currency (payment currency) after fees: %.6f", liquidity_amount_currency)

        liquidity_company_amount = round(self.currency_id._convert(
            liquidity_amount_currency, company_currency, self.company_id, self.date
        ), 6)
        _logger.info("Liquidity company amount (converted): %.6f", liquidity_company_amount)

        if not res or not isinstance(res, list) or len(res) < 2:
            _logger.warning("Unexpected structure from super(): res=%s", res)

        if res and isinstance(res, list) and len(res) >= 1:
            main_line = res[0]
            main_line['account_id'] = account_id
            main_line['currency_id'] = comp_cur_id
            main_line['amount_currency'] = liquidity_amount_currency
            if self.payment_type == 'inbound':
                main_line['debit'] = round(liquidity_company_amount, 2)
                main_line['credit'] = 0.0
            else:
                main_line['credit'] = round(liquidity_company_amount, 2)
                main_line['debit'] = 0.0
                main_line['amount_currency'] = -main_line.get('amount_currency', 0.0)
            _logger.debug("Adjusted liquidity line: %s", main_line)

        for idx, line in enumerate(res):
            line['currency_id'] = comp_cur_id
            if 'debit' in line and 'credit' in line:
                balance = round((line.get('debit', 0.0) - line.get('credit', 0.0)), 2)
                line['amount_currency'] = balance
            _logger.debug("Normalized original line %s: %s", idx, line)

        res += fees_data
        _logger.debug("Merged lines (liquidity + counterpart + fees): %s", res)

        total_debit = round(sum(float(line.get('debit', 0.0)) for line in res), 6)
        total_credit = round(sum(float(line.get('credit', 0.0)) for line in res), 6)
        diff = round(total_debit - total_credit, 6)
        _logger.info("Totals -> Debit: %.6f | Credit: %.6f | Diff: %.6f", total_debit, total_credit, diff)

        if abs(diff) > 0.000001:
            _logger.warning("Detected imbalance (diff=%.6f). Adjusting existing line instead of creating new one.",
                            diff)
            target_line = None
            for line in res:
                if 'Bank' in line.get('name', '') or 'Liquidity' in line.get('name', ''):
                    target_line = line
                    break
            if not target_line:
                target_line = res[0]

            if diff > 0:
                target_line['debit'] = round(target_line.get('debit', 0.0) - abs(diff), 2)
                target_line['amount_currency'] = round(target_line['debit'] - target_line.get('credit', 0.0), 2)
                _logger.info("Reduced debit on line %s by %.6f", target_line.get('name'), diff)
            else:
                target_line['credit'] = round(target_line.get('credit', 0.0) - abs(diff), 2)
                target_line['amount_currency'] = round(target_line.get('debit', 0.0) - target_line['credit'], 2)
                _logger.info("Reduced credit on line %s by %.6f", target_line.get('name'), diff)

            total_debit = round(sum(float(line.get('debit', 0.0)) for line in res), 6)
            total_credit = round(sum(float(line.get('credit', 0.0)) for line in res), 6)
            _logger.info("Totals after inline adjustment -> Debit: %.6f | Credit: %.6f", total_debit, total_credit)

        _logger.info("=== END _prepare_move_line_default_vals ===")
        return res
