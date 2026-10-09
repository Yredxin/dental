from odoo import Command, api, models
from odoo.exceptions import AccessError, ValidationError


CAPABILITIES = ('patient', 'appointment', 'clinical', 'employee', 'configuration')
LEGACY_PRESETS = {
    'receptionist': ('write', 'write', 'read', 'none', 'none'),
    'nurse': ('read', 'read', 'read', 'none', 'none'),
    'warehouse': ('none',) * 5,
    'user': ('read', 'read', 'write', 'none', 'none'),
    'manager': ('write',) * 5,
}


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _get_dental_capability_levels(self):
        self.ensure_one()
        return {
            name: next((level for level in ('write', 'read')
                        if self.has_group(f'dental_clinic.group_dental_{name}_{level}')), 'none')
            for name in CAPABILITIES
        }

    def _has_full_dental_management(self):
        self.ensure_one()
        return all(self.has_group(f'dental_clinic.group_dental_{name}_write')
                   for name in CAPABILITIES)

    def _apply_dental_capabilities(self, levels):
        self.ensure_one()
        caller = self.env.user
        if not self.env.su and not caller.has_group('dental_clinic.group_dental_configuration_write'):
            raise AccessError(self.env._('Dental Configuration Read/Write is required.'))
        if set(levels) != set(CAPABILITIES) or any(
                level not in ('none', 'read', 'write') for level in levels.values()):
            raise ValidationError(self.env._('Only the five Dental capability levels are accepted.'))
        self.check_access('read')
        if not self._is_internal() or self.has_group('base.group_portal'):
            raise AccessError(self.env._('Dental capabilities can only be applied to internal staff.'))
        if not self.company_ids & self.env.companies:
            raise AccessError(self.env._('The staff member must belong to an allowed company.'))
        if (not self.env.su and not caller.has_group('base.group_system')
                and self.has_group('base.group_system')):
            raise AccessError(self.env._('Only a System Administrator may adjust another System Administrator.'))
        managed = self.env['res.groups'].browse([
            self.env.ref(f'dental_clinic.group_dental_{name}_{level}').id
            for name in CAPABILITIES for level in ('read', 'write')
        ] + [self.env.ref(f'dental_clinic.group_dental_{name}').id for name in LEGACY_PRESETS])
        commands = [Command.unlink(group.id) for group in self.group_ids & managed]
        commands += [Command.link(self.env.ref(f'dental_clinic.group_dental_{name}_{level}').id)
                     for name, level in levels.items() if level != 'none']
        # Internal identity survives removal of an old compatibility aggregator.
        commands.append(Command.link(self.env.ref('base.group_user').id))
        # Manager has no general user-write authority. Elevate only fixed link /
        # unlink commands for these ten capability and five compatibility groups
        # on this access-checked internal staff user. Never forward RPC vals,
        # arbitrary group IDs, nested create/update commands or caller context.
        self.with_context({}).sudo().write({'group_ids': commands})

    @api.model
    def _migrate_legacy_dental_groups(self):
        # Upgrade-only ORM migration; not an RPC endpoint or a live preset sync.
        if not self.env.su:
            raise AccessError(self.env._('Dental legacy migration requires module installation authority.'))
        legacy = {name: self.env.ref(f'dental_clinic.group_dental_{name}') for name in LEGACY_PRESETS}
        users = self.with_context(active_test=False).search([
            ('group_ids', 'in', [group.id for group in legacy.values()]),
        ])
        for user in users:
            assigned = [name for name, group in legacy.items() if group in user.group_ids]
            levels = user._get_dental_capability_levels()
            rank = {'none': 0, 'read': 1, 'write': 2}
            for name in assigned:
                for capability, level in zip(CAPABILITIES, LEGACY_PRESETS[name]):
                    if rank[level] > rank[levels[capability]]:
                        levels[capability] = level
            user._apply_dental_capabilities(levels)

    def action_apply_dental_permission_profile(self):
        self.ensure_one()
        self.check_access('read')
        if not self.env.user.has_group('dental_clinic.group_dental_configuration_write'):
            raise AccessError(self.env._('Dental Configuration Read/Write is required.'))
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Apply Dental Permission Profile'),
            'res_model': 'dental.permission.apply', 'view_mode': 'form', 'target': 'new',
            'context': {'default_user_id': self.id},
        }
