# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DentalAppointment(models.Model):
    _name = 'dental.appointment'
    _description = 'Dental Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start desc'
    _rec_name = 'name'

    name = fields.Char(required=True, readonly=True, copy=False, default=lambda s: _('New'), tracking=True)
    patient_id = fields.Many2one('dental.patient', required=True, tracking=True)
    practitioner_id = fields.Many2one('dental.practitioner', required=True, tracking=True)
    room_id = fields.Many2one('dental.room')
    treatment_ids = fields.Many2many('dental.treatment', string='Planned Treatments')
    plan_id = fields.Many2one('dental.treatment.plan', string='Related Plan',
                              domain="[('patient_id', '=', patient_id)]")

    start = fields.Datetime(required=True, default=fields.Datetime.now, tracking=True)
    stop = fields.Datetime(required=True,
                           default=lambda s: fields.Datetime.now() + timedelta(minutes=30),
                           tracking=True)
    duration = fields.Float(compute='_compute_duration', inverse='_inverse_duration', store=True)
    allday = fields.Boolean()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked-In'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('no_show', 'No-Show'),
    ], default='draft', tracking=True, group_expand='_expand_states')

    reason = fields.Text(string='Reason')
    notes = fields.Html()
    color = fields.Integer(related='practitioner_id.color', store=True)
    reminder_sent = fields.Boolean(default=False)

    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _check_dates = models.Constraint('CHECK(stop >= start)', 'End must be after start.')

    def _expand_states(self, states, domain):
        return [k for k, _v in self._fields['state'].selection]

    @api.depends('start', 'stop')
    def _compute_duration(self):
        for rec in self:
            if rec.start and rec.stop:
                rec.duration = (rec.stop - rec.start).total_seconds() / 3600.0
            else:
                rec.duration = 0.0

    def _inverse_duration(self):
        for rec in self:
            if rec.start and rec.duration:
                rec.stop = rec.start + timedelta(hours=rec.duration)

    @api.constrains('practitioner_id', 'start', 'stop')
    def _check_overlap(self):
        for rec in self:
            if not rec.practitioner_id or not rec.start or not rec.stop:
                continue
            overlap = self.search([
                ('id', '!=', rec.id),
                ('practitioner_id', '=', rec.practitioner_id.id),
                ('state', 'not in', ('cancel', 'no_show')),
                ('start', '<', rec.stop),
                ('stop', '>', rec.start),
            ], limit=1)
            if overlap:
                raise ValidationError(
                    _('Practitioner %(name)s already has an appointment in this time slot (%(other)s).')
                    % {'name': rec.practitioner_id.name, 'other': overlap.name}
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.appointment') or _('New')
        return super().create(vals_list)

    # Workflow
    def action_confirm(self):
        self.state = 'confirmed'

    def action_check_in(self):
        self.state = 'checked_in'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_no_show(self):
        self.state = 'no_show'

    def action_draft(self):
        self.state = 'draft'

    def action_send_reminder(self):
        template = self.env.ref('dental_clinic.mail_template_dental_appointment_reminder',
                                raise_if_not_found=False)
        for rec in self:
            if template and rec.patient_id.email:
                template.send_mail(rec.id, force_send=False)
                rec.reminder_sent = True
        return True
