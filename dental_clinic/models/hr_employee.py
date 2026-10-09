from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .dental_permission_profile import LEVELS
from .res_users import CAPABILITIES


PERMISSION_GROUPS = 'dental_clinic.group_dental_employee_write,base.group_system'
CAPABILITY_FIELDS = {f'dental_{name}_level': name for name in CAPABILITIES}


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Non-stored form inputs. User groups remain the only permission state.
    dental_permission_profile_id = fields.Many2one(
        'dental.permission.profile', string='Permission Profile',
        compute='_compute_dental_permission_profile_id', readonly=False,
        groups=PERMISSION_GROUPS)
    dental_has_internal_user = fields.Boolean(
        compute='_compute_dental_capabilities', groups=PERMISSION_GROUPS)
    dental_user_login = fields.Char(
        string='Login', compute='_compute_dental_capabilities', groups=PERMISSION_GROUPS)
    dental_patient_level = fields.Selection(
        LEVELS, string='Patient Management', compute='_compute_dental_capabilities',
        readonly=False, groups=PERMISSION_GROUPS)
    dental_appointment_level = fields.Selection(
        LEVELS, string='Appointment Management', compute='_compute_dental_capabilities',
        readonly=False, groups=PERMISSION_GROUPS)
    dental_clinical_level = fields.Selection(
        LEVELS, string='Dental Clinical', compute='_compute_dental_capabilities',
        readonly=False, groups=PERMISSION_GROUPS)
    dental_employee_level = fields.Selection(
        LEVELS, string='Employee Management', compute='_compute_dental_capabilities',
        readonly=False, groups=PERMISSION_GROUPS)
    dental_configuration_level = fields.Selection(
        LEVELS, string='Dental Configuration', compute='_compute_dental_capabilities',
        readonly=False, groups=PERMISSION_GROUPS)

    @api.depends('user_id')
    def _compute_dental_permission_profile_id(self):
        self.dental_permission_profile_id = False

    @api.depends('user_id', 'user_id.login', 'user_id.all_group_ids')
    def _compute_dental_capabilities(self):
        for employee in self:
            user = employee.user_id
            internal = bool(user and user._is_internal() and not user.has_group('base.group_portal'))
            employee.dental_has_internal_user = internal
            employee.dental_user_login = user.login if user else False
            levels = user._get_dental_capability_levels() if internal else dict.fromkeys(CAPABILITIES, 'none')
            for field_name, capability in CAPABILITY_FIELDS.items():
                employee[field_name] = levels[capability]

    def _check_dental_permission_management(self):
        if not self.env.su and not (
                self.env.user.has_group('dental_clinic.group_dental_employee_write')
                or self.env.user.has_group('base.group_system')):
            raise AccessError(self.env._('Employee Management Read/Write is required.'))
        self.check_access('read')
        self.check_access('write')
        if any(not employee.user_id for employee in self):
            raise ValidationError(self.env._('This employee has no system login account.'))

    @api.model_create_multi
    def create(self, vals_list):
        employee_vals_list = []
        for vals in vals_list:
            if vals.get('dental_permission_profile_id') or any(
                    vals[key] not in (False, 'none') for key in CAPABILITY_FIELDS if key in vals):
                raise AccessError(self.env._('Save the employee before configuring work permissions.'))
            # Native form defaults may include the empty computed matrix.
            # Discard those inputs; creation never applies user capabilities.
            employee_vals_list.append({key: value for key, value in vals.items()
                                       if key not in CAPABILITY_FIELDS and key != 'dental_permission_profile_id'})
        return super().create(employee_vals_list)

    def write(self, vals):
        permission_fields = set(CAPABILITY_FIELDS) & vals.keys()
        if not permission_fields and 'dental_permission_profile_id' not in vals:
            return super().write(vals)
        self._check_dental_permission_management()
        # Handle all five facade inputs in one call, including a self-downgrade.
        # Separate inverses could lose authority midway or read protected siblings.
        employee_vals = {key: value for key, value in vals.items()
                         if key not in CAPABILITY_FIELDS}
        result = super().write(employee_vals)
        self._check_dental_permission_management()
        if permission_fields:
            for employee in self:
                levels = employee.user_id._get_dental_capability_levels()
                levels.update({CAPABILITY_FIELDS[key]: vals[key] for key in permission_fields})
                employee.user_id._apply_dental_capabilities(levels)
            self.invalidate_recordset(list(CAPABILITY_FIELDS))
        # Native object buttons save/reload before evaluating their context.
        # Let ORM cache the non-stored selector for that web_save response.
        # A later request computes False; no employee/user profile is stored.
        return result

    def action_apply_dental_profile(self):
        self.ensure_one()
        self._check_dental_permission_management()
        profile_id = self.env.context.get('dental_permission_profile_id')
        if type(profile_id) is not int or profile_id <= 0:
            raise ValidationError(self.env._('Choose a permission profile first.'))
        profile = self.env['dental.permission.profile'].browse(profile_id).exists()
        if not profile or not profile.active:
            raise ValidationError(self.env._('Choose an active permission profile.'))
        self.user_id._apply_dental_capabilities(profile._get_capability_levels())
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_send_invitation(self):
        # Match the native Invite button's administration gate over RPC too:
        # HR Officer employee maintenance must not provision user accounts.
        if not self.env.user.has_group('base.group_erp_manager'):
            raise AccessError(self.env._("Only user administrators may invite employee users."))
        self.check_access('write')
        return super().action_send_invitation()
