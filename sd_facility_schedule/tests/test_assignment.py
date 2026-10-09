from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


@tagged('facility_schedule')
class TestAssignment(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(cls.env, login='schedule_manager',
                                    groups='sd_facility_schedule.sd_facility_schedule_group_manager')
        cls.reader = new_test_user(cls.env, login='schedule_reader',
                                   groups='sd_facility_schedule.sd_facility_schedule_group_read')
        cls.ordinary = new_test_user(cls.env, login='schedule_self', groups='base.group_user')
        cls.other_user = new_test_user(cls.env, login='schedule_other', groups='base.group_user')
        cls.portal = new_test_user(cls.env, login='schedule_portal', groups='base.group_portal')
        cls.system = new_test_user(cls.env, login='schedule_system', groups='base.group_system')
        cls.employee = cls.env['hr.employee'].sudo().create({
            'name': 'Doctor', 'company_id': cls.company.id, 'user_id': cls.ordinary.id})
        cls.other_employee = cls.env['hr.employee'].sudo().create({
            'name': 'Nurse', 'company_id': cls.company.id, 'user_id': cls.other_user.id})
        Space = cls.env['sd.facility.space'].sudo()
        site = Space.create({'name': 'Schedule clinic', 'company_id': cls.company.id})
        floor = Space.create({'name': 'Floor', 'type': 'floor', 'parent_id': site.id, 'company_id': cls.company.id})
        area = Space.create({'name': 'Area', 'type': 'area', 'parent_id': floor.id, 'company_id': cls.company.id})
        cls.station, cls.other_station = cls.env['sd.facility.station'].sudo().create([
            {'name': name, 'space_id': area.id, 'company_id': cls.company.id} for name in ('Chair 1', 'Chair 2')])
        cls.other_company = cls.env['res.company'].sudo().create({'name': 'Schedule other company'})
        cls.foreign_employee = cls.env['hr.employee'].sudo().create({
            'name': 'Foreign doctor', 'company_id': cls.other_company.id})
        site_b = Space.create({'name': 'Foreign clinic', 'company_id': cls.other_company.id})
        floor_b = Space.create({'name': 'Floor', 'type': 'floor', 'parent_id': site_b.id, 'company_id': cls.other_company.id})
        area_b = Space.create({'name': 'Area', 'type': 'area', 'parent_id': floor_b.id, 'company_id': cls.other_company.id})
        cls.foreign_station = cls.env['sd.facility.station'].sudo().create({
            'name': 'Foreign chair', 'space_id': area_b.id, 'company_id': cls.other_company.id})

    def _values(self, **overrides):
        return dict({
            'employee_id': self.employee.id, 'station_id': self.station.id,
            'start': '2026-10-12 09:00:00', 'stop': '2026-10-12 12:00:00',
            'company_id': self.company.id,
        }, **overrides)

    def _create(self, **overrides):
        return self.env['sd.facility.assignment'].with_user(self.manager).create(self._values(**overrides))

    def _denied(self, operation, exception=(ValidationError, IntegrityError)):
        with mute_logger('odoo.sql_db'), self.assertRaises(exception), self.env.cr.savepoint():
            operation()
            self.env.flush_all()

    def test_planned(self):
        assignment = self._create()
        self.assertEqual(assignment.assignment_type, 'planned')
        self.assertFalse(assignment.reason)

    def test_temporary(self):
        assignment = self._create(assignment_type='temporary', reason='Emergency coverage')
        self.assertEqual(assignment.assignment_type, 'temporary')

    def test_temporary_reason_required(self):
        for reason in (False, '', '   ', '\t\n'):
            self._denied(lambda: self._create(assignment_type='temporary', reason=reason))

    def test_reason_write(self):
        assignment = self._create()
        self._denied(lambda: assignment.write({'assignment_type': 'temporary'}))
        assignment.write({'assignment_type': 'temporary', 'reason': 'Coverage'})
        self._denied(lambda: assignment.write({'reason': False}))

    def test_zero_interval(self):
        self._denied(lambda: self._create(stop='2026-10-12 09:00:00'))

    def test_reversed_interval(self):
        self._denied(lambda: self._create(stop='2026-10-12 08:00:00'))

    def test_invalid_interval_write(self):
        assignment = self._create()
        self._denied(lambda: assignment.write({'start': '2026-10-12 13:00:00'}))

    def test_other_station_overlap(self):
        self._create()
        self._denied(lambda: self._create(station_id=self.other_station.id,
                                         start='2026-10-12 10:00:00', stop='2026-10-12 11:00:00'))

    def test_same_station_overlap(self):
        self._create()
        self._denied(lambda: self._create(start='2026-10-12 09:30:00', stop='2026-10-12 10:30:00'))

    def test_containing_overlap(self):
        self._create()
        self._denied(lambda: self._create(start='2026-10-12 08:00:00', stop='2026-10-12 13:00:00'))

    def test_adjacent(self):
        self._create()
        self._create(station_id=self.other_station.id, start='2026-10-12 12:00:00', stop='2026-10-12 15:00:00')
        self._create(start='2026-10-12 08:00:00', stop='2026-10-12 09:00:00')

    def test_overlap_across_types(self):
        self._create()
        self._denied(lambda: self._create(assignment_type='temporary', reason='Coverage',
                                         start='2026-10-12 10:00:00', stop='2026-10-12 11:00:00'))

    def test_batch_overlap(self):
        self._denied(lambda: self.env['sd.facility.assignment'].with_user(self.manager).create([
            self._values(), self._values(station_id=self.other_station.id)]))

    def test_write_overlap(self):
        self._create()
        second = self._create(start='2026-10-12 12:00:00', stop='2026-10-12 15:00:00')
        self._denied(lambda: second.write({'start': '2026-10-12 11:00:00'}))

    def test_employee_write_overlap(self):
        self._create()
        second = self._create(employee_id=self.other_employee.id)
        self._denied(lambda: second.write({'employee_id': self.employee.id}))

    def test_write_self_exclusion(self):
        assignment = self._create()
        assignment.write({'stop': '2026-10-12 13:00:00'})
        assignment.write({'reason': 'Updated'})

    def test_archive_does_not_block(self):
        assignment = self._create()
        assignment.action_archive()
        self.assertFalse(assignment.active)
        self._create()
        self._denied(assignment.action_unarchive)

    def test_multiple_employees(self):
        self._create()
        self._create(employee_id=self.other_employee.id)

    def test_multiple_employees_partial_overlap(self):
        self._create()
        self._create(employee_id=self.other_employee.id, start='2026-10-12 11:00:00', stop='2026-10-12 14:00:00')

    def test_company_employee(self):
        self._denied(lambda: self.env['sd.facility.assignment'].sudo().create(
            self._values(employee_id=self.foreign_employee.id)))

    def test_company_station(self):
        self._denied(lambda: self.env['sd.facility.assignment'].sudo().create(
            self._values(station_id=self.foreign_station.id)))

    def test_company_assignment(self):
        self._denied(lambda: self.env['sd.facility.assignment'].sudo().create(
            self._values(company_id=self.other_company.id)))

    def test_company_write(self):
        assignment = self._create()
        self._denied(lambda: assignment.sudo().write({'company_id': self.other_company.id}))
        self._denied(lambda: assignment.sudo().write({'station_id': self.foreign_station.id}))
        self._denied(lambda: assignment.sudo().write({'employee_id': self.foreign_employee.id}))

    def test_inactive_station(self):
        self.station.sudo().action_archive()
        self._denied(self._create)
        archived = self._create(active=False)
        self._denied(archived.action_unarchive)

    def test_calendars_unchanged_outside_hours(self):
        employee_calendar = self.employee.sudo().resource_calendar_id
        station_calendar = self.station.sudo().resource_calendar_id
        employee_attendances = employee_calendar.attendance_ids.read()
        station_attendances = station_calendar.attendance_ids.read()
        self._create(start='2026-10-11 01:00:00', stop='2026-10-11 03:00:00')
        self.assertEqual(self.employee.sudo().resource_calendar_id, employee_calendar)
        self.assertEqual(self.station.sudo().resource_calendar_id, station_calendar)
        self.assertEqual(employee_calendar.attendance_ids.read(), employee_attendances)
        self.assertEqual(station_calendar.attendance_ids.read(), station_attendances)

    def test_own_only(self):
        own = self._create()
        other = self._create(employee_id=self.other_employee.id)
        Model = self.env['sd.facility.assignment'].with_user(self.ordinary)
        self.assertEqual(Model.search([('id', 'in', (own | other).ids)]).ids, own.ids)
        self.assertEqual(own.with_user(self.ordinary).read(['employee_id', 'station_id'])[0]['id'], own.id)
        self._denied(lambda: other.with_user(self.ordinary).read(), AccessError)
        self.assertEqual(own.with_user(self.ordinary).read(['station_id'])[0]['station_id'][1], 'Chair 1')

    def test_ordinary_mutations_denied(self):
        assignment = self._create().with_user(self.ordinary)
        self._denied(lambda: self.env['sd.facility.assignment'].with_user(self.ordinary).create(self._values()), AccessError)
        for operation in (lambda: assignment.write({'reason': 'Denied'}), assignment.action_archive, assignment.unlink):
            self._denied(operation, AccessError)

    def test_read_manager(self):
        assignments = self._create() | self._create(employee_id=self.other_employee.id)
        Model = self.env['sd.facility.assignment'].with_user(self.reader)
        self.assertEqual(set(Model.search([('id', 'in', assignments.ids)]).ids), set(assignments.ids))
        self._denied(lambda: Model.create(self._values()), AccessError)
        for operation in (lambda: assignments.with_user(self.reader).write({'reason': 'Denied'}),
                          assignments.with_user(self.reader).action_archive, assignments.with_user(self.reader).unlink):
            self._denied(operation, AccessError)

    def test_manager_mutations(self):
        assignment = self._create()
        assignment.write({'reason': 'Correction'})
        assignment.action_archive()
        self._denied(assignment.unlink, AccessError)
        self.assertFalse(self.manager.has_group('base.group_system'))
        self.assertFalse(self.manager.has_group('base.group_erp_manager'))
        self._denied(lambda: self.ordinary.with_user(self.manager).write({
            'group_ids': [Command.link(self.env.ref('base.group_system').id)]}), AccessError)

    def test_portal(self):
        assignment = self._create().with_user(self.portal)
        Model = self.env['sd.facility.assignment'].with_user(self.portal)
        for operation in (lambda: Model.search([]), lambda: assignment.read(),
                          lambda: Model.create(self._values()), lambda: assignment.write({'reason': 'Denied'}),
                          assignment.unlink):
            self._denied(operation, AccessError)
        menu = self.env.ref('sd_facility_schedule.sd_facility_assignment_menu_my')
        self.assertFalse(menu.sudo().group_ids & self.portal.sudo().all_group_ids)

    def test_system(self):
        Model = self.env['sd.facility.assignment'].with_user(self.system)
        assignment = Model.create(self._values())
        assignment.write({'reason': 'Administration'})
        assignment.action_archive()
        self._denied(assignment.unlink, AccessError)

    def test_allowed_company_scope(self):
        assignment = self.env['sd.facility.assignment'].sudo().create(self._values(
            company_id=self.other_company.id, employee_id=self.foreign_employee.id,
            station_id=self.foreign_station.id))
        Model = self.env['sd.facility.assignment'].with_user(self.manager)
        self.assertFalse(Model.search([('id', '=', assignment.id)]))
        self._denied(lambda: assignment.with_user(self.manager).read(), AccessError)

    def test_current_company_employee(self):
        self.ordinary.sudo().write({'company_ids': [Command.link(self.other_company.id)]})
        self.foreign_employee.sudo().write({'user_id': self.ordinary.id})
        own = self._create()
        foreign = self.env['sd.facility.assignment'].sudo().create(self._values(
            company_id=self.other_company.id, employee_id=self.foreign_employee.id,
            station_id=self.foreign_station.id))
        Model = self.env['sd.facility.assignment'].with_user(self.ordinary)
        self.assertEqual(Model.with_context(allowed_company_ids=[self.company.id, self.other_company.id]).search(
            [('id', 'in', (own | foreign).ids)]).ids, own.ids)
        self.assertEqual(Model.with_context(allowed_company_ids=[self.other_company.id, self.company.id]).search(
            [('id', 'in', (own | foreign).ids)]).ids, foreign.ids)

    def test_menu_scope(self):
        own_menu = self.env.ref('sd_facility_schedule.sd_facility_assignment_menu_my').id
        all_menu = self.env.ref('sd_facility_schedule.sd_facility_assignment_menu').id
        visible = self.env['ir.ui.menu'].with_user(self.ordinary)._visible_menu_ids()
        self.assertIn(own_menu, visible)
        self.assertNotIn(all_menu, visible)
        self.assertIn(all_menu, self.env['ir.ui.menu'].with_user(self.reader)._visible_menu_ids())

    def test_archive_controls_match_write_access(self):
        Model = self.env['sd.facility.assignment']
        # Alternate identities to catch view metadata leaking through caches.
        for user, readonly in ((self.manager, False), (self.reader, True),
                               (self.ordinary, True), (self.system, False), (self.reader, True)):
            model = Model.with_user(user)
            fields = model.fields_get(['active'], ['readonly'])
            self.assertEqual(fields['active']['readonly'], readonly)
            views = model.get_views([(False, 'list'), (False, 'form')])
            self.assertEqual(views['models']['sd.facility.assignment']['fields']['active']['readonly'], readonly)
