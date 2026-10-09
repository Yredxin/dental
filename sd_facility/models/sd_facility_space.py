from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SdFacilitySpace(models.Model):
    _name = 'sd.facility.space'
    _description = 'Facility Space'
    _parent_store = True
    _parent_name = 'parent_id'
    _rec_name = 'complete_name'
    _order = 'sequence, name, id'
    _check_company_auto = True

    name = fields.Char(required=True)
    code = fields.Char(copy=False)
    type = fields.Selection([
        ('facility', 'Facility'), ('floor', 'Floor'), ('area', 'Area'),
    ], required=True, default='facility')
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company, index=True)
    parent_id = fields.Many2one(
        'sd.facility.space', string='Parent Space', index=True,
        check_company=True, ondelete='restrict')
    child_ids = fields.One2many('sd.facility.space', 'parent_id', string='Direct Child Spaces')
    parent_path = fields.Char(index=True, readonly=True)
    complete_name = fields.Char(compute='_compute_complete_name', store=True, recursive=True)
    station_ids = fields.One2many('sd.facility.station', 'space_id', string='Direct Workstations')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()

    _code_unique = models.Constraint(
        'UNIQUE(company_id, code)', 'Space code must be unique within its company.')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for space in self:
            space.complete_name = (
                f'{space.parent_id.complete_name} / {space.name}' if space.parent_id else space.name)

    @api.constrains('parent_id', 'type', 'company_id', 'active')
    def _check_hierarchy(self):
        if self._has_cycle():
            raise ValidationError(self.env._('Facility spaces cannot form a recursive cycle.'))
        for space in self:
            parent = space.parent_id
            if space.type == 'facility' and parent:
                raise ValidationError(self.env._('A facility must be a root space.'))
            if space.type == 'floor' and (not parent or parent.type != 'facility'):
                raise ValidationError(self.env._('A floor must belong directly to a facility.'))
            if space.type == 'area' and (not parent or parent.type not in ('floor', 'area')):
                raise ValidationError(self.env._('An area must belong to a floor or another area.'))
            if parent and parent.company_id != space.company_id:
                raise ValidationError(self.env._('Parent and child spaces must belong to the same company.'))
        self.filtered('active')._check_active_ancestry()

    @api.model_create_multi
    def create(self, vals_list):
        if any('parent_path' in vals for vals in vals_list):
            raise ValidationError(self.env._('The space hierarchy path is managed by Odoo.'))
        return super().create(vals_list)

    def write(self, vals):
        self.check_access('write')
        if 'parent_path' in vals:
            raise ValidationError(self.env._('The space hierarchy path is managed by Odoo.'))
        if 'company_id' in vals and any(space.company_id.id != vals['company_id'] for space in self):
            raise ValidationError(self.env._('Space company cannot be changed. Create a new space instead.'))
        result = super().write(vals)
        if {'parent_id', 'type', 'active'} & vals.keys():
            # Archived descendants still constrain structural edits. ORM paths
            # supply the subtree; no separate hierarchy engine is needed.
            descendants = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
            descendants._check_hierarchy()
            stations = self.env['sd.facility.station'].with_context(active_test=False).search([
                ('space_id', 'in', descendants.ids),
            ])
            stations._check_facility_integrity()
        return result

    def _check_active_ancestry(self):
        ancestor_ids = {int(item) for space in self for item in (space.parent_path or '').split('/') if item}
        ancestors = self.with_context(active_test=False).browse(ancestor_ids)
        if any(not ancestor.active for ancestor in ancestors):
            raise ValidationError(self.env._('Active spaces and workstations require active ancestors. Archive children first.'))
