from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SdFacilityStation(models.Model):
    _name = 'sd.facility.station'
    _description = 'Workstation'
    _inherit = 'resource.mixin'
    _order = 'sequence, name, id'
    _check_company_auto = True

    name = fields.Char(related='resource_id.name', store=True, readonly=False, required=True, precompute=True)
    code = fields.Char(copy=False)
    company_id = fields.Many2one(required=True)
    space_id = fields.Many2one(
        'sd.facility.space', string='Area', required=True, index=True,
        check_company=True, ondelete='restrict', domain="[('type', '=', 'area')]")
    resource_id = fields.Many2one(check_company=True)
    resource_calendar_id = fields.Many2one(required=True, check_company=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(related='resource_id.active', store=True, readonly=False, default=True)
    description = fields.Text()

    _resource_unique = models.Constraint('UNIQUE(resource_id)', 'Each workstation must own a different resource.')
    _code_unique = models.Constraint(
        'UNIQUE(company_id, code)', 'Workstation code must be unique within its company.')

    @api.constrains('space_id', 'resource_id', 'company_id', 'resource_calendar_id', 'active')
    def _check_facility_integrity(self):
        for station in self:
            resource = station.resource_id
            if station.space_id.type != 'area':
                raise ValidationError(self.env._('A workstation must belong to an area.'))
            if station.company_id != station.space_id.company_id or station.company_id != resource.company_id:
                raise ValidationError(self.env._('Workstation, area and resource must belong to the same company.'))
            if not resource.sd_facility_owned or resource.resource_type != 'material' or resource.user_id:
                raise ValidationError(self.env._('Workstations require dedicated facility material resources without a user.'))
            calendar = station.resource_calendar_id
            if not calendar or (calendar.company_id and calendar.company_id != station.company_id):
                raise ValidationError(self.env._('The working calendar must be shared or belong to the workstation company.'))
        self.filtered('active').space_id._check_active_ancestry()

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(vals) for vals in vals_list]
        company_ids = {vals.get('company_id') or self.env.company.id for vals in vals_list}
        calendars = {company.id: company.resource_calendar_id.id
                     for company in self.env['res.company'].browse(company_ids)}
        resource_ids = [vals['resource_id'] for vals in vals_list if vals.get('resource_id')]
        resource_calendars = {resource.id: resource.calendar_id.id
                              for resource in self.env['resource.resource'].browse(resource_ids)}
        for vals in vals_list:
            if 'resource_calendar_id' not in vals:
                # Prevent the mixin field's current-company default from
                # overwriting the requested company's Resource calendar.
                vals['resource_calendar_id'] = (
                    resource_calendars[vals['resource_id']] if vals.get('resource_id')
                    else calendars[vals.get('company_id') or self.env.company.id])
        return super().create(vals_list)

    def write(self, vals):
        self.check_access('write')
        if 'resource_id' in vals and any(station.resource_id.id != vals['resource_id'] for station in self):
            raise ValidationError(self.env._('Workstation resource identity cannot be replaced.'))
        if 'company_id' in vals and any(station.company_id.id != vals['company_id'] for station in self):
            raise ValidationError(self.env._('Workstation company cannot be changed. Create a new workstation instead.'))
        return super().write(vals)

    def unlink(self):
        # No facility role grants deletion. An authorized cleanup of an unused
        # station deletes its dedicated resource in the same ORM transaction.
        resources = self.resource_id
        result = super().unlink()
        resources.unlink()
        return result

    def _prepare_resource_values(self, vals, tz):
        values = super()._prepare_resource_values(vals, tz)
        values.update(resource_type='material', sd_facility_owned=True, active=vals.get('active', True))
        return values
