from odoo import fields, models

from .res_users import CAPABILITIES


LEVELS = [('none', 'None'), ('read', 'Read'), ('write', 'Read/Write')]


class DentalPermissionProfile(models.Model):
    _name = 'dental.permission.profile'
    _description = 'Dental Permission Profile'
    _order = 'name, id'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    patient_level = fields.Selection(LEVELS, string='Patient Management', required=True, default='none')
    appointment_level = fields.Selection(LEVELS, string='Appointment Management', required=True, default='none')
    clinical_level = fields.Selection(LEVELS, string='Dental Clinical', required=True, default='none')
    employee_level = fields.Selection(LEVELS, string='Employee Management', required=True, default='none')
    configuration_level = fields.Selection(LEVELS, string='Dental Configuration', required=True, default='none')

    def _get_capability_levels(self):
        self.ensure_one()
        self.check_access('read')
        return {name: self[f'{name}_level'] for name in CAPABILITIES}
