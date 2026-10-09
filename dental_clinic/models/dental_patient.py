# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class DentalPatient(models.Model):
    _name = 'dental.patient'
    _description = 'Dental Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'display_name'

    # The existing patient form includes its avatar. No other partner fields
    # belong to this facade, especially financial/company/security settings.
    _patient_contact_fields = (
        'name', 'phone', 'mobile', 'email', 'street', 'city', 'zip',
        'country_id', 'image_1920',
    )
    _patient_demographic_fields = (
        'gender', 'birth_date', 'national_id', 'marital_status', 'occupation',
        'emergency_name', 'emergency_phone', 'emergency_relation',
    )
    _patient_clinical_fields = (
        'blood_type', 'allergies', 'current_medications', 'chronic_diseases',
        'smoker', 'pregnant', 'notes', 'medical_history_ids', 'tooth_ids',
        'treatment_plan_ids', 'prescription_ids',
    )

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

    appointment_ids = fields.One2many('dental.appointment', 'patient_id', string='Appointments',
                                      groups='dental_clinic.group_dental_appointment_read')
    treatment_plan_ids = fields.One2many('dental.treatment.plan', 'patient_id', string='Treatment Plans',
                                        groups='dental_clinic.group_dental_clinical_read')
    prescription_ids = fields.One2many('dental.prescription', 'patient_id', string='Prescriptions',
                                      groups='dental_clinic.group_dental_clinical_read')
    tooth_ids = fields.One2many('dental.tooth', 'patient_id', string='Odontogram')

    can_repair_contact = fields.Boolean(compute='_compute_can_repair_contact')
    appointment_count = fields.Integer(compute='_compute_appointment_count',
                                        groups='dental_clinic.group_dental_appointment_read')
    treatment_plan_count = fields.Integer(
        compute='_compute_treatment_plan_count',
        groups='dental_clinic.group_dental_clinical_read',
    )
    prescription_count = fields.Integer(
        compute='_compute_prescription_count',
        groups='dental_clinic.group_dental_clinical_read',
    )
    invoice_count = fields.Integer(
        compute='_compute_invoice_totals',
        groups='account.group_account_invoice,account.group_account_readonly',
    )
    total_invoiced = fields.Monetary(
        currency_field='currency_id', compute='_compute_invoice_totals',
        groups='account.group_account_invoice,account.group_account_readonly',
    )
    total_due = fields.Monetary(
        currency_field='currency_id', compute='_compute_invoice_totals',
        groups='account.group_account_invoice,account.group_account_readonly',
    )
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint('UNIQUE(code)', 'Patient code must be unique!')

    @api.depends_context('uid')
    def _compute_can_repair_contact(self):
        allowed = self.env.su or self.env.user._has_full_dental_management()
        for rec in self:
            rec.can_repair_contact = allowed

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

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)

    @api.depends('treatment_plan_ids')
    def _compute_treatment_plan_count(self):
        for rec in self:
            rec.treatment_plan_count = len(rec.treatment_plan_ids)

    @api.depends('prescription_ids')
    def _compute_prescription_count(self):
        for rec in self:
            rec.prescription_count = len(rec.prescription_ids)

    def _compute_invoice_totals(self):
        # Accounting field groups and the caller's normal ACL/company rules
        # remain authoritative; clinical counters never enter this compute.
        totals = {
            patient.id: (count, amount, residual)
            for patient, count, amount, residual in self.env['account.move']._read_group(
                [('dental_patient_id', 'in', self.ids),
                 ('move_type', '=', 'out_invoice'), ('state', '!=', 'cancel')],
                ['dental_patient_id'], ['__count', 'amount_total:sum', 'amount_residual:sum'],
            )
        }
        for rec in self:
            rec.invoice_count, rec.total_invoiced, rec.total_due = totals.get(rec.id, (0, 0, 0))

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access('create')
        contact_defaults = {
            name: self.env.context[f'default_{name}']
            for name in self._patient_contact_fields
            if f'default_{name}' in self.env.context
        }
        contact_values = []
        patient_values = []
        for vals in vals_list:
            vals = dict(vals)
            self._check_patient_field_write(set(vals) | {
                name for name in self._patient_demographic_fields + self._patient_clinical_fields
                if f'default_{name}' in self.env.context
            })
            contact = {**contact_defaults, **{
                name: vals.pop(name) for name in self._patient_contact_fields if name in vals
            }}
            self._check_contact_maintenance(contact)
            contact_values.append(contact)
            if not vals.get('code') or vals.get('code') == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('dental.patient') or _('New')
            patient_values.append(vals)
        # Related-field defaults must not invoke the ordinary partner inverse
        # before the patient exists and its effective write access is checked.
        context = {
            key: value for key, value in self.env.context.items()
            if key not in {f'default_{name}' for name in self._patient_contact_fields}
        }
        records = super(DentalPatient, self.with_context(context)).create(patient_values)
        # Only mark contacts linked by successfully access-checked patient
        # creation. Keep contact read/company restrictions, and elevate just
        # this fixed flag; never forward caller values or defaults under sudo.
        partners = records.partner_id
        partners.check_access('read')
        partners.with_context({}).sudo().write({'is_dental_patient': True})
        for rec, contact in zip(records, contact_values):
            rec._write_patient_contact(contact)
            rec._create_odontogram()
        return records

    def write(self, vals):
        self.check_access('write')
        self._check_patient_field_write(vals)
        if ('partner_id' in vals and not self.env.su
                and not self.env.user._has_full_dental_management()
                and any(rec.partner_id.id != vals['partner_id'] for rec in self)):
            raise AccessError(self.env._('Only a Dental Manager may repair a patient contact link.'))
        contact = {name: vals[name] for name in self._patient_contact_fields if name in vals}
        self._check_contact_maintenance(contact)
        result = super().write({name: value for name, value in vals.items() if name not in contact})
        self._write_patient_contact(contact)
        return result

    def _check_patient_field_write(self, names):
        if self.env.su:
            return
        names = set(names)
        if (names.intersection(self._patient_clinical_fields)
                and not self.env.user.has_group('dental_clinic.group_dental_clinical_write')):
            raise AccessError(self.env._('Clinical patient updates require Dental Clinical Read/Write.'))
        if (names.intersection(self._patient_demographic_fields)
                and not self.env.user.has_group('dental_clinic.group_dental_patient_write')):
            raise AccessError(self.env._('Patient demographic maintenance requires Patient Management Read/Write.'))

    def _check_contact_maintenance(self, values):
        if values and not self.env.su and not self.env.user.has_group('dental_clinic.group_dental_patient_write'):
            raise AccessError(self.env._('Patient contact maintenance requires Patient Management Read/Write.'))
        for name in values:
            if name not in self._patient_contact_fields:
                raise AccessError(self.env._('This contact field is not allowed through the patient.'))
            self.check_field_access(self._fields[name], 'write')

    def _write_patient_contact(self, values):
        if not values:
            return
        self.check_access('write')
        self._check_contact_maintenance(values)
        partners = self.partner_id
        partners.check_access('read')
        # Elevation must not bypass the standard protection of user accounts
        # or let a name change synchronize bank-holder data without its ACL.
        # Match Odoo's internal-account protection. Portal identity contact
        # values are maintained here without touching login/password/groups.
        users = partners.with_context(active_test=False).user_ids.filtered(lambda user: user._is_internal())
        if users:
            users.check_access('write')
        if 'name' in values:
            banks = partners.bank_ids
            if banks:
                banks.check_access('write')
        # Fixed model, access-checked patient links and exact scalar whitelist.
        # Discard caller context; never forward patient vals or x2many commands.
        contact = {name: values[name] for name in self._patient_contact_fields if name in values}
        address = {name: contact.pop(name) for name in ('street', 'city', 'zip', 'country_id') if name in contact}
        contact_partner = partners.with_context({}).sudo()
        if contact:
            contact_partner.write(contact)
        if address:
            # Odoo's own narrow address updater uses ORM write without its
            # hierarchy synchronization: only the patient's linked contacts
            # change, never their parent company's or sibling addresses.
            contact_partner._update_address(address)

    def _create_odontogram(self):
        self.ensure_one()
        self.check_access('write')
        # Patient creation is already access-checked. Only these fixed FDI
        # child values run elevated; discard caller defaults and never pass
        # patient create values or relational commands into this operation.
        Tooth = self.env['dental.tooth'].with_context({}).sudo()
        teeth = [quadrant * 10 + position for quadrant in (1, 2, 3, 4) for position in range(1, 9)]
        quadrant_labels = {1: '右上', 2: '左上', 3: '左下', 4: '右下'}
        position_labels = {
            1: '中切牙', 2: '侧切牙', 3: '尖牙', 4: '第一前磨牙',
            5: '第二前磨牙', 6: '第一磨牙', 7: '第二磨牙', 8: '第三磨牙',
        }
        Tooth.create([{
            'patient_id': self.id,
            'tooth_number': num,
            'name': quadrant_labels[num // 10] + position_labels[num % 10],
            'condition': 'healthy',
        } for num in teeth])

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
