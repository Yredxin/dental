# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DentalTreatmentPlan(models.Model):
    _name = 'dental.treatment.plan'
    _description = 'Dental Treatment Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(required=True, readonly=True, copy=False, default=lambda s: _('New'), tracking=True)
    patient_id = fields.Many2one('dental.patient', required=True, ondelete='restrict', tracking=True)
    practitioner_id = fields.Many2one('dental.practitioner', required=True, tracking=True)
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    expected_end_date = fields.Date()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', tracking=True)
    line_ids = fields.One2many('dental.treatment.plan.line', 'plan_id', string='Treatments', copy=True)
    notes = fields.Html()
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    total_amount = fields.Monetary(currency_field='currency_id', compute='_compute_total', store=True)
    invoiced_amount = fields.Monetary(currency_field='currency_id', compute='_compute_invoiced')
    invoice_ids = fields.Many2many('account.move', string='Invoices', copy=False)
    invoice_count = fields.Integer(compute='_compute_invoiced')

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('subtotal'))

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.amount_total')
    def _compute_invoiced(self):
        for rec in self:
            valid = rec.invoice_ids.filtered(lambda m: m.state != 'cancel')
            rec.invoiced_amount = sum(valid.mapped('amount_total'))
            rec.invoice_count = len(rec.invoice_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.treatment.plan') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Add at least one treatment line.'))
            rec.state = 'confirmed'

    def action_start(self):
        self.state = 'in_progress'

    def action_done(self):
        for rec in self:
            rec.line_ids.filtered(lambda l: l.state != 'done').state = 'done'
            rec.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def action_create_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Invoice'),
            'res_model': 'dental.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_plan_id': self.id, 'default_patient_id': self.patient_id.id},
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
        }
