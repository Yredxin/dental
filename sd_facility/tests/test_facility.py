from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


@tagged('facility')
class TestFacility(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env, login='facility_manager', groups='sd_facility.sd_facility_group_manager',
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.reader = new_test_user(
            cls.env, login='facility_reader', groups='sd_facility.sd_facility_group_read',
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.ordinary = new_test_user(cls.env, login='facility_ordinary', groups='base.group_user')
        cls.portal = new_test_user(cls.env, login='facility_portal', groups='base.group_portal')
        cls.system = new_test_user(
            cls.env, login='facility_system', groups='base.group_system',
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.Space = cls.env['sd.facility.space'].with_user(cls.manager)
        cls.Station = cls.env['sd.facility.station'].with_user(cls.manager)
        cls.site = cls.Space.create({'name': 'Clinic', 'type': 'facility'})
        cls.floor = cls.Space.create({'name': 'Ground', 'type': 'floor', 'parent_id': cls.site.id})
        cls.area = cls.Space.create({'name': 'Room', 'type': 'area', 'parent_id': cls.floor.id})
        cls.nested = cls.Space.create({'name': 'Bay', 'type': 'area', 'parent_id': cls.area.id})
        cls.station = cls.Station.create({'name': 'Position', 'space_id': cls.nested.id})
        cls.other_company = cls.env['res.company'].sudo().create({'name': 'Other legal company'})
        cls.other_site = cls.env['sd.facility.space'].sudo().create({
            'name': 'Other clinic', 'company_id': cls.other_company.id, 'type': 'facility'})
        cls.other_floor = cls.env['sd.facility.space'].sudo().create({
            'name': 'Other floor', 'company_id': cls.other_company.id,
            'type': 'floor', 'parent_id': cls.other_site.id})
        cls.other_area = cls.env['sd.facility.space'].sudo().create({
            'name': 'Other area', 'company_id': cls.other_company.id,
            'type': 'area', 'parent_id': cls.other_floor.id})

    def _callSetUp(self):
        super()._callSetUp()
        # BaseCommon rebinds fixture recordsets to its independent test user.
        self.Space = self.env['sd.facility.space'].with_user(self.manager)
        self.Station = self.env['sd.facility.station'].with_user(self.manager)
        for name in ('site', 'floor', 'area', 'nested', 'station'):
            setattr(self, name, getattr(self, name).with_user(self.manager))

    def _denied(self, operation, exception=ValidationError):
        with mute_logger('odoo.sql_db'), self.assertRaises(exception), self.env.cr.savepoint():
            operation()

    def test_tree_paths(self):
        self.assertEqual(self.nested.parent_path, f'{self.site.id}/{self.floor.id}/{self.area.id}/{self.nested.id}/')
        self.assertEqual(self.nested.complete_name, 'Clinic / Ground / Room / Bay')
        self.assertEqual(self.Space.search([('id', 'child_of', self.area.id)]), self.area | self.nested)
        self.assertEqual(set(self.Space.search([('id', 'parent_of', self.nested.id)]).ids),
                         set((self.site | self.floor | self.area | self.nested).ids))

    def test_multiple_sites_and_positions(self):
        site = self.Space.create({'name': 'Second site', 'type': 'facility'})
        self.assertFalse(site.parent_id)
        second = self.Station.create({'name': 'Second position', 'space_id': self.nested.id})
        self.assertNotEqual(second.resource_id, self.station.resource_id)

    def test_hierarchy_path_cannot_be_forged(self):
        self._denied(lambda: self.area.write({'parent_path': ''}))
        self._denied(lambda: self.Space.create({'name': 'Forged', 'parent_path': '999/'}))

    def test_invalid_parent_matrix(self):
        for kind, parent in [('facility', self.site), ('facility', self.floor), ('facility', self.area),
                             ('floor', self.floor), ('floor', self.area), ('area', self.site)]:
            with self.subTest(kind=kind, parent=parent.type):
                self._denied(lambda: self.Space.create({'name': 'Invalid', 'type': kind, 'parent_id': parent.id}))

    def test_missing_parent(self):
        for kind in ('floor', 'area'):
            self._denied(lambda: self.Space.create({'name': 'Invalid', 'type': kind}))

    def test_cycle(self):
        self._denied(lambda: self.area.write({'parent_id': self.nested.id}), UserError)

    def test_cross_company_parent(self):
        self._denied(lambda: self.Space.sudo().create({
            'name': 'Invalid', 'type': 'floor', 'company_id': self.company.id,
            'parent_id': self.other_site.id}))

    def test_legal_company_parent_still_forbidden(self):
        subsidiary = self.env['res.company'].sudo().create({'name': 'Subsidiary', 'parent_id': self.company.id})
        site = self.Space.sudo().create({'name': 'Subsidiary site', 'company_id': subsidiary.id})
        self._denied(lambda: self.Space.sudo().create({
            'name': 'Invalid', 'type': 'floor', 'company_id': self.company.id, 'parent_id': site.id}))

    def test_company_immutable(self):
        self._denied(lambda: self.area.sudo().write({'company_id': self.other_company.id}))
        self._denied(lambda: self.station.sudo().write({'company_id': self.other_company.id}))

    def test_type_checks_archived_children(self):
        self.station.action_archive()
        self.nested.action_archive()
        self._denied(lambda: self.area.write({'type': 'facility', 'parent_id': False}))

    def test_type_checks_archived_stations(self):
        self.station.action_archive()
        self._denied(lambda: self.nested.write({'type': 'floor', 'parent_id': self.site.id}))

    def test_bottom_up_archive(self):
        self._denied(lambda: self.area.action_archive())
        self._denied(lambda: self.nested.action_archive())
        self.station.action_archive()
        self.nested.action_archive()
        self.area.action_archive()
        self.floor.action_archive()
        self.site.action_archive()
        self.assertFalse(self.station.resource_id.active)
        self.assertFalse(self.Space.search([('id', '=', self.site.id)]))
        self.assertTrue(self.Space.with_context(active_test=False).search([('id', '=', self.site.id)]))

    def test_unarchive_requires_active_ancestry(self):
        self.station.action_archive()
        self.nested.action_archive()
        self._denied(lambda: self.station.action_unarchive())
        self._denied(lambda: self.Station.create({'name': 'Invalid', 'space_id': self.nested.id}))
        self.nested.action_unarchive()
        self.station.action_unarchive()
        self.assertTrue(self.station.resource_id.active)

    def test_reparent_under_archived_floor(self):
        floor = self.Space.create({'name': 'Closed floor', 'type': 'floor', 'parent_id': self.site.id})
        floor.action_archive()
        self._denied(lambda: self.area.write({'parent_id': floor.id}))

    def test_station_requires_area(self):
        for space in (self.site, self.floor):
            self._denied(lambda: self.Station.create({'name': 'Invalid', 'space_id': space.id}))

    def test_station_same_company(self):
        self._denied(lambda: self.Station.sudo().create({
            'name': 'Invalid', 'company_id': self.company.id, 'space_id': self.other_area.id}))

    def test_station_other_allowed_company_default_calendar(self):
        self.manager.sudo().company_ids = [Command.set((self.company | self.other_company).ids)]
        Station = self.Station.with_context(allowed_company_ids=[self.company.id, self.other_company.id])
        station = Station.create({
            'name': 'Other company position', 'company_id': self.other_company.id,
            'space_id': self.other_area.id})
        self.assertEqual(station.company_id, self.other_company)
        self.assertEqual(station.resource_calendar_id, self.other_company.sudo().resource_calendar_id)
        self.assertEqual(station.resource_id.resource_type, 'material')

    def test_material_resource(self):
        self.assertTrue(self.station.resource_id.exists())
        self.assertEqual(self.station.resource_id.resource_type, 'material')
        self.assertFalse(self.station.resource_id.user_id)
        self.assertEqual(self.station.resource_id.company_id, self.station.company_id)

    def test_stable_resource(self):
        resource = self.station.resource_id
        self.station.write({'name': 'Renamed', 'description': 'Updated', 'sequence': 20})
        self.assertEqual(self.station.resource_id, resource)
        self.assertEqual(resource.name, 'Renamed')
        other = self.Station.create({'name': 'Other', 'space_id': self.area.id})
        self._denied(lambda: self.station.write({'resource_id': other.resource_id.id}))

    def test_exclusive_resource(self):
        self._denied(lambda: self.Station.create({
            'name': 'Duplicate', 'space_id': self.nested.id, 'resource_id': self.station.resource_id.id}), IntegrityError)

    def test_no_external_resource_adoption(self):
        for kind in ('user', 'material'):
            resource = self.env['resource.resource'].sudo().create({'name': 'External', 'resource_type': kind})
            self._denied(lambda: self.Station.create({
                'name': 'Invalid', 'space_id': self.area.id, 'resource_id': resource.id}))

    def test_copy_allocates_resource(self):
        self.station.code = 'POSITION'
        copy = self.station.copy()
        self.assertNotEqual(copy.resource_id, self.station.resource_id)
        self.assertFalse(copy.code)
        self.assertEqual(copy.resource_id.resource_type, 'material')

    def test_calendar_same_company(self):
        calendar = self.env['resource.calendar'].sudo().create({'name': 'Availability', 'company_id': self.company.id})
        self.station.resource_calendar_id = calendar
        self.assertEqual(self.station.resource_id.calendar_id, calendar)

    def test_calendar_shared(self):
        calendar = self.env['resource.calendar'].sudo().create({'name': 'Shared', 'company_id': False})
        self.station.resource_calendar_id = calendar
        self.assertEqual(self.station.resource_id.calendar_id, calendar)

    def test_calendar_foreign_denied(self):
        calendar = self.other_company.sudo().resource_calendar_id
        self._denied(lambda: self.station.sudo().write({'resource_calendar_id': calendar.id}))
        self._denied(lambda: self.station.resource_id.sudo().write({'calendar_id': calendar.id}))

    def test_direct_resource_invariants(self):
        for vals in ({'resource_type': 'user'}, {'user_id': self.manager.id},
                     {'company_id': self.other_company.id}, {'sd_facility_owned': False}):
            self._denied(lambda: self.station.resource_id.sudo().write(vals))

    def test_direct_resource_unarchive_denied(self):
        self.station.action_archive()
        self.nested.action_archive()
        self._denied(lambda: self.station.resource_id.write({'active': True}))

    def test_reader_security(self):
        for record, values in ((self.site, {'name': 'Forbidden', 'type': 'facility'}),
                               (self.station, {'name': 'Forbidden', 'space_id': self.area.id})):
            record = record.with_user(self.reader)
            self.assertTrue(record.read(['name']))
            self._denied(lambda: record.create(values), AccessError)
            self._denied(lambda: record.write({'name': 'Forbidden'}), AccessError)
            self._denied(lambda: record.unlink(), AccessError)

    def test_manager_cru_no_delete(self):
        self.site.write({'description': 'Managed'})
        station = self.Station.create({'name': 'Managed', 'space_id': self.area.id})
        station.action_archive()
        self.assertFalse(station.active)
        self._denied(lambda: station.unlink(), AccessError)

    def test_portal_and_ordinary_denied(self):
        for user in (self.portal, self.ordinary):
            for model, values in ((self.Space, {'name': 'Denied', 'type': 'facility'}),
                                  (self.Station, {'name': 'Denied', 'space_id': self.area.id})):
                self._denied(lambda: model.with_user(user).search([]), AccessError)
                self._denied(lambda: model.with_user(user).create(values), AccessError)

    def test_system_management(self):
        site = self.Space.with_user(self.system).create({'name': 'System site', 'type': 'facility'})
        site.write({'description': 'System'})
        site.action_archive()
        self.assertFalse(site.active)

    def test_company_access_all_operations(self):
        self._denied(lambda: self.other_site.with_user(self.manager).read(['name']), AccessError)
        self._denied(lambda: self.other_site.with_user(self.manager).write({'name': 'Denied'}), AccessError)
        self._denied(lambda: self.Space.create({
            'name': 'Denied', 'type': 'facility', 'company_id': self.other_company.id}), AccessError)

    def test_manager_no_general_resource_authority(self):
        external = self.env['resource.resource'].sudo().create({'name': 'Human'})
        self._denied(lambda: external.with_user(self.manager).write({'name': 'Denied'}), AccessError)
        self._denied(lambda: self.env['resource.resource'].with_user(self.manager).create({'name': 'Denied'}), AccessError)
        self._denied(lambda: self.station.resource_id.unlink(), AccessError)

    def test_deletion_restrict_and_cleanup(self):
        self._denied(lambda: self.nested.sudo().unlink(), IntegrityError)
        resource = self.station.resource_id
        self._denied(lambda: resource.sudo().unlink(), IntegrityError)
        self.station.sudo().unlink()
        self.assertFalse(resource.exists())

    def test_code_uniqueness(self):
        self.site.code = 'SITE'
        self._denied(lambda: self.Space.create({'name': 'Duplicate', 'type': 'facility', 'code': 'SITE'}), IntegrityError)
        self.station.code = 'STATION'
        self._denied(lambda: self.Station.create({'name': 'Duplicate', 'space_id': self.area.id, 'code': 'STATION'}), IntegrityError)
