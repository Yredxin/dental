from odoo import models
from odoo.exceptions import AccessError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_send_invitation(self):
        # Match the native Invite button's administration gate over RPC too:
        # HR Officer employee maintenance must not provision user accounts.
        if not self.env.user.has_group('base.group_erp_manager'):
            raise AccessError(self.env._("Only user administrators may invite employee users."))
        self.check_access('write')
        return super().action_send_invitation()
