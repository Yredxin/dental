from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SdFacilityAssignment(models.Model):
    _name = 'sd.facility.assignment'
    _description = 'Workstation Assignment'
    _rec_name = 'employee_id'
    _order = 'start, employee_id, id'
    _check_company_auto = True

    employee_id = fields.Many2one(
        'hr.employee', required=True, index=True, check_company=True,
        ondelete='restrict', domain="[('company_id', '=', company_id)]")
    station_id = fields.Many2one(
        'sd.facility.station', string='Workstation', required=True, index=True,
        check_company=True, ondelete='restrict',
        domain="[('company_id', '=', company_id), ('active', '=', True)]")
    start = fields.Datetime(string='Start Time', required=True, index=True)
    stop = fields.Datetime(string='End Time', required=True)
    assignment_type = fields.Selection(
        [('planned', 'Planned'), ('temporary', 'Temporary')],
        required=True, default='planned')
    reason = fields.Text()
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company, index=True)
    active = fields.Boolean(default=True)

    _interval_positive = models.Constraint(
        'CHECK(stop > start)', 'End time must be after start time.')
    _temporary_reason = models.Constraint(
        "CHECK(assignment_type != 'temporary' OR NULLIF(BTRIM(reason), '') IS NOT NULL)",
        'Temporary assignments require a reason.')
    # Both operands use built-in range GiST operators. The singleton employee
    # range tests identity without installing the btree_gist extension.
    # Half-open time ranges allow adjacency; archived rows do not participate.
    _employee_no_overlap = models.Constraint(
        """EXCLUDE USING gist (
            int8range(employee_id::bigint, employee_id::bigint, '[]') WITH &&,
            tsrange(start, GREATEST(start, stop), '[)') WITH &&
        ) WHERE (active IS TRUE)""",
        'An employee cannot have overlapping active assignments.')

    @api.constrains('employee_id', 'station_id', 'company_id')
    def _check_assignment_company(self):
        for assignment in self:
            if (assignment.company_id != assignment.employee_id.company_id
                    or assignment.company_id != assignment.station_id.company_id):
                raise ValidationError(self.env._(
                    'Assignment, employee and workstation must belong to the same company.'))

    @api.constrains('assignment_type', 'reason')
    def _check_temporary_reason(self):
        for assignment in self:
            if assignment.assignment_type == 'temporary' and not (assignment.reason or '').strip():
                raise ValidationError(self.env._('Temporary assignments require a reason.'))

    @api.constrains('start', 'stop')
    def _check_interval(self):
        for assignment in self:
            if assignment.stop <= assignment.start:
                raise ValidationError(self.env._('End time must be after start time.'))

    @api.constrains('station_id', 'active')
    def _check_active_station(self):
        if any(assignment.active and not assignment.station_id.active for assignment in self):
            raise ValidationError(self.env._('Active assignments require an active workstation.'))

    @api.model_create_multi
    def create(self, vals_list):
        # ORM updates are deferred. Flush earlier archives/interval edits before
        # INSERT so the exclusion constraint sees the current transaction state.
        self.flush_model(['employee_id', 'start', 'stop', 'active'])
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if {'employee_id', 'start', 'stop', 'active'} & vals.keys():
            # Enforce exclusion during the call, including unarchive, rather
            # than leaving a deferred failure for an unrelated later query.
            self.flush_recordset(['employee_id', 'start', 'stop', 'active'])
        return result

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        result = super().fields_get(allfields, attributes)
        # Native form/list archive menus inspect field metadata, not model ACLs.
        # Keep active readable, but hide mutation controls from read-only users.
        active = result.get('active', {})
        if 'readonly' in active and not self.has_access('write'):
            active['readonly'] = True
        return result

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type='form', **options):
        key = super()._get_view_cache_key(view_id, view_type, **options)
        return key + (self.has_access('write'),)
