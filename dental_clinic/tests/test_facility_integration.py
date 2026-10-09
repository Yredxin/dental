from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


@tagged('facility')
class TestDentalFacilityIntegration(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reader = new_test_user(cls.env, login='dental_facility_read',
                                   groups='dental_clinic.group_dental_configuration_read')
        cls.manager = new_test_user(cls.env, login='dental_facility_manage',
                                    groups='dental_clinic.group_dental_configuration_write')

    def test_configuration_read(self):
        self.assertTrue(self.reader.has_group('sd_facility.sd_facility_group_read'))
        self.assertFalse(self.reader.has_group('sd_facility.sd_facility_group_manager'))
        self.env['sd.facility.space'].with_user(self.reader).search([])
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['sd.facility.space'].with_user(self.reader).create({'name': 'Denied'})

    def test_configuration_management(self):
        self.assertTrue(self.manager.has_group('sd_facility.sd_facility_group_manager'))
        Space = self.env['sd.facility.space'].with_user(self.manager)
        site = Space.create({'name': 'Dental clinic', 'type': 'facility'})
        floor = Space.create({'name': 'Dental floor', 'type': 'floor', 'parent_id': site.id})
        area = Space.create({'name': 'Dental area', 'type': 'area', 'parent_id': floor.id})
        station = self.env['sd.facility.station'].with_user(self.manager).create({'name': 'Dental position', 'space_id': area.id})
        station.write({'description': 'Managed'})
        station.action_archive()
        self.assertFalse(station.active)

    def test_facility_manager_does_not_escalate_dental(self):
        user = new_test_user(self.env, login='generic_facility_manager', groups='sd_facility.sd_facility_group_manager')
        self.assertFalse(user.has_group('base.group_system'))
        for capability in ('patient', 'appointment', 'clinical', 'employee', 'configuration'):
            self.assertFalse(user.has_group(f'dental_clinic.group_dental_{capability}_write'))

    def test_dental_menu_placement(self):
        self.assertEqual(self.env.ref('sd_facility.sd_facility_menu').parent_id,
                         self.env.ref('dental_clinic.menu_dental_config'))

    def test_capability_downgrade_removes_facility_management(self):
        self.manager.sudo()._apply_dental_capabilities({
            'patient': 'none', 'appointment': 'none', 'clinical': 'none',
            'employee': 'none', 'configuration': 'read'})
        self.assertFalse(self.manager.has_group('sd_facility.sd_facility_group_manager'))
        self.assertTrue(self.manager.has_group('sd_facility.sd_facility_group_read'))

    def test_employee_management_cannot_mutate_facility_resource(self):
        hr_user = new_test_user(self.env, login='facility_hr_boundary',
                                groups='dental_clinic.group_dental_employee_write')
        self.assertFalse(hr_user.has_group('sd_facility.sd_facility_group_manager'))
        Space = self.env['sd.facility.space'].with_user(self.manager)
        site = Space.create({'name': 'HR boundary site'})
        floor = Space.create({'name': 'Floor', 'type': 'floor', 'parent_id': site.id})
        area = Space.create({'name': 'Area', 'type': 'area', 'parent_id': floor.id})
        station = self.env['sd.facility.station'].with_user(self.manager).create({'name': 'Position', 'space_id': area.id})
        for vals in ({'name': 'Forbidden'}, {'active': False}, {'calendar_id': station.resource_calendar_id.id}):
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                station.resource_id.with_user(hr_user).write(vals)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['resource.resource'].with_user(hr_user).create({
                'name': 'Forbidden facility resource', 'sd_facility_owned': True, 'resource_type': 'material'})
