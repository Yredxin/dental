from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


@tagged('facility_schedule')
class TestDentalScheduleIntegration(BaseCommon):
    def test_employee_read_mapping(self):
        user = new_test_user(self.env, login='dental_schedule_read', groups='dental_clinic.group_dental_employee_read')
        self.assertTrue(user.has_group('sd_facility_schedule.sd_facility_schedule_group_read'))
        self.assertFalse(user.has_group('sd_facility_schedule.sd_facility_schedule_group_manager'))
        self.env['sd.facility.assignment'].with_user(user).search([])
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['sd.facility.assignment'].with_user(user).create({})

    def test_employee_write_mapping(self):
        user = new_test_user(self.env, login='dental_schedule_rw', groups='dental_clinic.group_dental_employee_write')
        self.assertTrue(user.has_group('sd_facility_schedule.sd_facility_schedule_group_manager'))
        self.assertFalse(user.has_group('base.group_system'))
        self.assertFalse(user.has_group('base.group_erp_manager'))

    def test_capability_downgrade(self):
        user = new_test_user(self.env, login='dental_schedule_down', groups='dental_clinic.group_dental_employee_write')
        levels = dict(patient='none', appointment='none', clinical='none', employee='read', configuration='none')
        user.sudo()._apply_dental_capabilities(levels)
        self.assertTrue(user.has_group('sd_facility_schedule.sd_facility_schedule_group_read'))
        self.assertFalse(user.has_group('sd_facility_schedule.sd_facility_schedule_group_manager'))
        levels['employee'] = 'none'
        user.sudo()._apply_dental_capabilities(levels)
        self.assertFalse(user.has_group('sd_facility_schedule.sd_facility_schedule_group_read'))
        self.assertEqual(user._get_dental_capability_levels(), levels)

    def test_generic_manager_does_not_grant_dental(self):
        user = new_test_user(self.env, login='generic_schedule_boundary',
                             groups='sd_facility_schedule.sd_facility_schedule_group_manager')
        for capability in ('patient', 'appointment', 'clinical', 'employee', 'configuration'):
            self.assertFalse(user.has_group(f'dental_clinic.group_dental_{capability}_write'))
