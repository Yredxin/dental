# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class DentalPatient(models.Model):
    _name = 'dental.patient'
    _description = 'Dental Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'display_name'

    # Link to res.partner so the patient can be a customer for invoicing
    partner_id = fields.Many2one(
        'res.partner', string='Related Contact', required=True, ondelete='restrict',
        tracking=True,
    )
    code = fields.Char(string='Patient Code', readonly=True, copy=False, default=lambda s: _('New'))
    name = fields.Char(related='partner_id.name', store=True, readonly=False, tracking=True)
    display_name = fields.Char(compute='_compute_display_name_full', store=True)

    image_1920 = fields.Image(related='partner_id.image_1920', readonly=False)

    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], tracking=True)
    birth_date = fields.Date(string='Date of Birth', tracking=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=False)
    national_id = fields.Char(string='National ID')
    blood_type = fields.Selection([
        ('a_pos', 'A+'), ('a_neg', 'A-'),
        ('b_pos', 'B+'), ('b_neg', 'B-'),
        ('o_pos', 'O+'), ('o_neg', 'O-'),
        ('ab_pos', 'AB+'), ('ab_neg', 'AB-'),
    ], string='Blood Type')
    marital_status = fields.Selection([
        ('single', 'Single'), ('married', 'Married'),
        ('widowed', 'Widowed'), ('divorced', 'Divorced'),
    ])
    occupation = fields.Char()

    phone = fields.Char(related='partner_id.phone', readonly=False)
    mobile = fields.Char(related='partner_id.mobile', readonly=False)
    email = fields.Char(related='partner_id.email', readonly=False)
    street = fields.Char(related='partner_id.street', readonly=False)
    city = fields.Char(related='partner_id.city', readonly=False)
    zip = fields.Char(related='partner_id.zip', readonly=False)
    country_id = fields.Many2one(related='partner_id.country_id', readonly=False)

    emergency_name = fields.Char()
    emergency_phone = fields.Char()
    emergency_relation = fields.Char()

    medical_history_ids = fields.One2many('dental.medical.history', 'patient_id', string='Medical History')
    allergies = fields.Text(help='Known allergies (penicillin, latex, anesthetics, etc.)')
    current_medications = fields.Text(help='Current daily medications.')
    chronic_diseases = fields.Text()
    smoker = fields.Boolean()
    pregnant = fields.Boolean()
    notes = fields.Html(string='Internal Notes')

    appointment_ids = fields.One2many('dental.appointment', 'patient_id', string='Appointments')
    treatment_plan_ids = fields.One2many('dental.treatment.plan', 'patient_id', string='Treatment Plans')
    prescription_ids = fields.One2many('dental.prescription', 'patient_id', string='Prescriptions')
    tooth_ids = fields.One2many('dental.tooth', 'patient_id', string='Odontogram')

    appointment_count = fields.Integer(compute='_compute_counts')
    treatment_plan_count = fields.Integer(compute='_compute_counts')
    prescription_count = fields.Integer(compute='_compute_counts')
    invoice_count = fields.Integer(compute='_compute_counts')
    total_invoiced = fields.Monetary(currency_field='currency_id', compute='_compute_counts')
    total_due = fields.Monetary(currency_field='currency_id', compute='_compute_counts')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint('UNIQUE(code)', 'Patient code must be unique!')

    @api.depends('name', 'code')
    def _compute_display_name_full(self):
        for rec in self:
            rec.display_name = '[%s] %s' % (rec.code or '-', rec.name or '')

    @api.depends('birth_date')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            if rec.birth_date:
                rec.age = relativedelta(today, rec.birth_date).years
            else:
                rec.age = 0

    def _compute_counts(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)
            rec.treatment_plan_count = len(rec.treatment_plan_ids)
            rec.prescription_count = len(rec.prescription_ids)
            invoices = self.env['account.move'].search([
                ('dental_patient_id', '=', rec.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel'),
            ])
            rec.invoice_count = len(invoices)
            rec.total_invoiced = sum(invoices.mapped('amount_total'))
            rec.total_due = sum(invoices.mapped('amount_residual'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals.get('code') == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('dental.patient') or _('New')
            if vals.get('partner_id'):
                self.env['res.partner'].browse(vals['partner_id']).is_dental_patient = True
        records = super().create(vals_list)
        for rec in records:
            rec._create_odontogram()
        return records

    def _create_odontogram(self):
        Tooth = self.env['dental.tooth']
        teeth = [quadrant * 10 + position for quadrant in (1, 2, 3, 4) for position in range(1, 9)]
        quadrant_labels = {1: '右上', 2: '左上', 3: '左下', 4: '右下'}
        position_labels = {
            1: '中切牙', 2: '侧切牙', 3: '尖牙', 4: '第一前磨牙',
            5: '第二前磨牙', 6: '第一磨牙', 7: '第二磨牙', 8: '第三磨牙',
        }
        for num in teeth:
            Tooth.create({
                'patient_id': self.id,
                'tooth_number': num,
                'name': quadrant_labels[num // 10] + position_labels[num % 10],
                'condition': 'healthy',
            })

    def action_open_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Appointments'),
            'res_model': 'dental.appointment',
            'view_mode': 'calendar,list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_open_treatment_plans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Treatment Plans'),
            'res_model': 'dental.treatment.plan',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_open_prescriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prescriptions'),
            'res_model': 'dental.prescription',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_open_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('dental_patient_id', '=', self.id), ('move_type', '=', 'out_invoice')],
            'context': {'default_move_type': 'out_invoice', 'default_dental_patient_id': self.id},
        }
