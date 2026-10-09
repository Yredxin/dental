from odoo import api, fields, models

from odoo.addons.dental_clinic.models.dental_permission_profile import LEVELS
from odoo.addons.dental_clinic.models.res_users import CAPABILITIES


class DentalPermissionApply(models.TransientModel):
    _name = 'dental.permission.apply'
    _description = 'Apply Dental Permission Profile'

    user_id = fields.Many2one('res.users', string='Staff User', required=True,
                              domain="[('share', '=', False), ('company_ids', 'in', context.get('allowed_company_ids', []))]")
    profile_id = fields.Many2one('dental.permission.profile', string='Permission Profile')
    patient_level = fields.Selection(LEVELS, string='Patient Management', required=True, default='none')
    appointment_level = fields.Selection(LEVELS, string='Appointment Management', required=True, default='none')
    clinical_level = fields.Selection(LEVELS, string='Dental Clinical', required=True, default='none')
    employee_level = fields.Selection(LEVELS, string='Employee Management', required=True, default='none')
    configuration_level = fields.Selection(LEVELS, string='Dental Configuration', required=True, default='none')

    @api.onchange('user_id')
    def _onchange_user_id(self):
        self.profile_id = False
        if self.user_id:
            self.update({f'{name}_level': level for name, level in
                         self.user_id._get_dental_capability_levels().items()})

    @api.onchange('profile_id')
    def _onchange_profile_id(self):
        if self.profile_id:
            self.update({f'{name}_level': level for name, level in
                         self.profile_id._get_capability_levels().items()})

    def action_apply(self):
        self.ensure_one()
        self.check_access('write')
        # The selections are authoritative, so a chosen preset can be adjusted
        # before applying. The private user helper revalidates every boundary.
        self.user_id._apply_dental_capabilities({name: self[f'{name}_level'] for name in CAPABILITIES})
        return {'type': 'ir.actions.act_window_close'}
