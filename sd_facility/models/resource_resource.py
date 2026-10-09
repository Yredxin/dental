from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    # Ownership namespace, not another resource engine. Copy preserves this
    # marker so resource.mixin.copy_data can allocate a new dedicated resource.
    sd_facility_owned = fields.Boolean(string='Facility Resource', readonly=True)

    @api.constrains('sd_facility_owned', 'resource_type', 'user_id', 'company_id', 'calendar_id', 'active')
    def _check_facility_resource(self):
        for resource in self.filtered('sd_facility_owned'):
            if resource.resource_type != 'material' or resource.user_id or not resource.company_id:
                raise ValidationError(self.env._('Facility resources must be material, company-owned and have no user.'))
            if resource.calendar_id.company_id and resource.calendar_id.company_id != resource.company_id:
                raise ValidationError(self.env._('The working calendar must be shared or belong to the workstation company.'))
        # Fixed-ID integrity lookup only: read hidden/archived owners too, so
        # a direct Resource RPC cannot evade station checks through record rules.
        stations = self.env['sd.facility.station'].sudo().with_context(active_test=False).search([
            ('resource_id', 'in', self.ids),
        ])
        stations._check_facility_integrity()

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get('sd_facility_owned') for vals in vals_list):
            self._check_facility_management()
        return super().create(vals_list)

    def write(self, vals):
        self.check_access('write')
        if self.filtered('sd_facility_owned') or vals.get('sd_facility_owned'):
            self._check_facility_management()
        for resource in self.filtered('sd_facility_owned'):
            if 'sd_facility_owned' in vals and not vals['sd_facility_owned']:
                raise ValidationError(self.env._('Facility resource ownership cannot be removed.'))
            if 'company_id' in vals and vals['company_id'] != resource.company_id.id:
                raise ValidationError(self.env._('Facility resource company cannot be changed.'))
        if vals.get('sd_facility_owned') and any(not resource.sd_facility_owned for resource in self):
            raise ValidationError(self.env._('Existing resources cannot be converted into facility resources.'))
        return super().write(vals)

    def _check_facility_management(self):
        # HR/MRP may independently grant broad Resource permissions. They do
        # not authorize editing facility configuration through related fields.
        if not self.env.su and not self.env.user.has_group('sd_facility.sd_facility_group_manager'):
            raise AccessError(self.env._('Facility Manager permission is required for facility resources.'))
