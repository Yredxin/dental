from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


CAPABILITIES = ('patient', 'appointment', 'clinical', 'employee', 'configuration')
FIELDS = [f'dental_{name}_level' for name in CAPABILITIES]


@tagged('admin_ia')
class TestAdminInformationArchitecture(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        groups = {
            'ordinary': 'base.group_user',
            'read': 'dental_clinic.group_dental_employee_read',
            'write': 'dental_clinic.group_dental_employee_write',
            'configuration': 'dental_clinic.group_dental_configuration_write',
            'manager': 'dental_clinic.group_dental_manager',
            'system': 'base.group_system',
            'portal': 'base.group_portal',
        }
        cls.actors = {role: new_test_user(
            cls.env, login=f'admin_ia_{role}', groups=group,
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
            for role, group in groups.items()}
        cls.employee = cls.env['hr.employee'].sudo().create({
            'name': 'Inline permission employee', 'user_id': cls.actors['ordinary'].id,
            'company_id': cls.company.id})
        cls.no_user = cls.env['hr.employee'].sudo().create({
            'name': 'Employee without account', 'company_id': cls.company.id})
        cls.profile = cls.env.ref('dental_clinic.permission_profile_nurse')

    def _apply(self, employee=None, actor='write', profile=None):
        employee = (employee if employee is not None else self.employee).with_user(self.actors[actor])
        # Match the native object button: save/read, then evaluate its context.
        [saved] = employee.web_save({'dental_permission_profile_id': (profile or self.profile).id}, {
            'dental_permission_profile_id': {'fields': {'display_name': {}}}})
        profile_id = saved['dental_permission_profile_id']['id']
        self.env.invalidate_all()  # The button RPC has a fresh request cache.
        return employee.with_context(dental_permission_profile_id=profile_id).action_apply_dental_profile()

    def test_native_button_save_retains_selection_without_applying(self):
        employee = self.employee.with_user(self.actors['write'])
        before = self._levels()
        [saved] = employee.web_save({'dental_permission_profile_id': self.profile.id}, {
            'dental_permission_profile_id': {'fields': {'display_name': {}}}})
        self.assertEqual(saved['dental_permission_profile_id']['id'], self.profile.id)
        self.assertEqual(self._levels(), before)
        self.env.invalidate_all()
        self.assertFalse(employee.dental_permission_profile_id)

    def _levels(self):
        self.employee.invalidate_recordset(FIELDS)
        employee = self.employee.with_user(self.actors['write'])
        return tuple(employee[name] for name in FIELDS)

    def test_inline_preset_then_manual_customization(self):
        self._apply()
        self.assertEqual(self._levels(), ('read', 'read', 'read', 'none', 'none'))
        employee = self.employee.with_user(self.actors['write'])
        with Form(employee, view='hr.view_employee_form') as form:
            form.dental_appointment_level = 'write'
        self.assertEqual(self._levels(), ('read', 'write', 'read', 'none', 'none'))
        self.assertTrue(self.env['dental.appointment'].with_user(self.actors['ordinary']).has_access('create'))
        self.env.invalidate_all()
        self.assertEqual(self._levels(), ('read', 'write', 'read', 'none', 'none'))
        self.assertFalse(employee.dental_permission_profile_id)

    def test_preset_changes_archive_and_delete_do_not_resync(self):
        profile = self.env['dental.permission.profile'].sudo().create({
            'name': 'One-time preset', 'patient_level': 'read', 'appointment_level': 'read'})
        self._apply(profile=profile)
        self.employee.with_user(self.actors['write']).write({'dental_appointment_level': 'write'})
        expected = ('read', 'write', 'none', 'none', 'none')
        profile.write({'patient_level': 'write', 'appointment_level': 'none'})
        self.assertEqual(self._levels(), expected)
        profile.action_archive()
        self.assertEqual(self._levels(), expected)
        profile.unlink()
        self.assertEqual(self._levels(), expected)

    def test_selector_is_never_a_stored_relation(self):
        employee = self.employee.with_user(self.actors['write'])
        employee.write({'dental_permission_profile_id': self.profile.id})
        employee.invalidate_recordset(['dental_permission_profile_id'])
        self.assertFalse(employee.dental_permission_profile_id)
        self._apply()
        for model in ('hr.employee', 'res.users'):
            for field in self.env[model]._fields.values():
                self.assertFalse(field.store and field.relational
                                 and field.comodel_name == 'dental.permission.profile')
        for name in FIELDS:
            self.assertFalse(self.env['hr.employee']._fields[name].store)

    def test_no_account_form_and_values(self):
        employee = self.no_user.with_user(self.actors['write'])
        self.assertFalse(employee.dental_has_internal_user)
        self.assertEqual(tuple(employee[name] for name in FIELDS), ('none',) * 5)
        with Form(employee, view='hr.view_employee_form'):
            pass
        employee.write({'name': 'Still usable without account'})
        self.assertFalse(employee.user_id)

    def test_no_account_application_and_write_denied(self):
        with self.assertRaises(ValidationError):
            self._apply(employee=self.no_user)
        with self.assertRaises(ValidationError):
            self.no_user.with_user(self.actors['write']).write({'dental_patient_level': 'write'})
        self.assertFalse(self.no_user.user_id)

    def test_employee_creation_cannot_configure_permissions(self):
        with self.assertRaises(AccessError):
            self.env['hr.employee'].with_user(self.actors['write']).create({
                'name': 'Rejected account authority', 'user_id': self.actors['ordinary'].id,
                'dental_configuration_level': 'write'})

    def test_native_employee_creation_without_account_remains_usable(self):
        with Form(self.env['hr.employee'].with_user(self.actors['write']), view='hr.view_employee_form') as form:
            form.name = 'Native employee without account'
        self.assertFalse(form.record.user_id)

    def test_read_manager_has_directory_but_no_permission_mutation(self):
        employee = self.employee.with_user(self.actors['read'])
        self.assertTrue(employee.read(['name']))
        with self.assertRaises(AccessError):
            employee.read(FIELDS)
        with self.assertRaises(AccessError):
            employee.write({'dental_patient_level': 'write'})
        with self.assertRaises(AccessError):
            self._apply(actor='read')
        with self.assertRaises(AccessError):
            employee.with_context(dental_permission_profile_id=self.profile.id).action_apply_dental_profile()

    def test_ordinary_cannot_manage_own_or_other_permissions(self):
        for employee in (self.employee, self.no_user):
            with self.subTest(employee=employee.id), self.assertRaises(AccessError):
                self._apply(employee=employee, actor='ordinary')
        with self.assertRaises(AccessError):
            self.employee.with_user(self.actors['ordinary']).write({'dental_patient_level': 'write'})
        with self.assertRaises(AccessError):
            self.employee.with_user(self.actors['ordinary']).with_context(
                dental_permission_profile_id=self.profile.id).action_apply_dental_profile()

    def test_portal_denied(self):
        with self.assertRaises(AccessError):
            self._apply(actor='portal')
        with self.assertRaises(AccessError):
            self.employee.with_user(self.actors['portal']).read(FIELDS)
        self.assertFalse(self.env['dental.permission.profile'].with_user(self.actors['portal']).has_access('read'))

    def test_employee_manager_reads_but_cannot_manage_definitions(self):
        for role in ('read', 'write'):
            profile = self.profile.with_user(self.actors[role])
            self.assertTrue(profile.read(['name', 'patient_level']))
            with self.assertRaises(AccessError):
                profile.write({'patient_level': 'write'})
            with self.assertRaises(AccessError):
                profile.action_archive()
            with self.assertRaises(AccessError):
                profile.copy()

    def test_configuration_and_system_manage_definitions(self):
        for role in ('configuration', 'system'):
            profile = self.env['dental.permission.profile'].with_user(self.actors[role]).create({
                'name': 'Authorized definition'})
            profile.write({'patient_level': 'read'})
            profile.action_archive()

    def test_system_can_manage_employee(self):
        self._apply(actor='system')
        self.assertEqual(self._levels(), ('read', 'read', 'read', 'none', 'none'))

    def test_unrelated_groups_preserved_through_employee_path(self):
        user = self.actors['ordinary']
        user.sudo().write({'group_ids': [Command.link(self.env.ref(xmlid).id) for xmlid in (
            'base.group_multi_currency', 'hr.group_hr_user', 'account.group_account_readonly')]})
        before = set(user.group_ids.ids)
        self._apply()
        self.employee.with_user(self.actors['write']).write({'dental_appointment_level': 'write'})
        self.assertTrue(before <= set(user.group_ids.ids))
        self.assertFalse(user.has_group('base.group_system'))

    def test_arbitrary_group_and_level_injection_denied(self):
        employee = self.employee.with_user(self.actors['write'])
        with self.assertRaises(ValidationError):
            employee.write({'dental_patient_level': 'base.group_system'})
        with self.assertRaises(ValueError), self.cr.savepoint():
            employee.write({'group_ids': [Command.link(self.env.ref('base.group_system').id)]})
        for role in ('write', 'manager'):
            caller = self.actors[role]
            for target in (caller, self.actors['ordinary']):
                with self.subTest(role=role, target=target.id), self.assertRaises(AccessError):
                    target.with_user(caller).write({
                        'group_ids': [Command.link(self.env.ref('base.group_system').id)]})
            self.assertFalse(caller.has_group('base.group_system'))
            self.assertFalse(caller.has_group('base.group_erp_manager'))

    def test_invalid_preset_input_denied(self):
        for value in (False, 'base.group_system', [self.profile.id], -1, 999999999):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.employee.with_user(self.actors['write']).with_context(
                    dental_permission_profile_id=value).action_apply_dental_profile()

    def test_system_target_protected_from_managers(self):
        employee = self.env['hr.employee'].sudo().create({
            'name': 'System target', 'user_id': self.actors['system'].id, 'company_id': self.company.id})
        for role in ('write', 'manager'):
            with self.subTest(role=role), self.assertRaises(AccessError):
                self._apply(employee=employee, actor=role)
        self._apply(employee=employee, actor='system')
        self.assertTrue(self.actors['system'].has_group('base.group_system'))

    def test_self_downgrade_is_atomic(self):
        employee = self.env['hr.employee'].sudo().create({
            'name': 'Self managed employee', 'user_id': self.actors['write'].id,
            'company_id': self.company.id})
        employee.with_user(self.actors['write']).write(dict.fromkeys(FIELDS, 'none'))
        self.assertFalse(self.actors['write'].has_group('dental_clinic.group_dental_employee_write'))
        self.assertFalse(self.actors['write'].has_group('base.group_system'))

    def test_foreign_company_employee_denied(self):
        company = self.env['res.company'].sudo().create({'name': 'Other IA clinic'})
        user = new_test_user(self.env, login='admin_ia_foreign', groups='base.group_user',
                             company_id=company.id, company_ids=[Command.set(company.ids)])
        employee = self.env['hr.employee'].sudo().create({
            'name': 'Foreign target', 'company_id': company.id, 'user_id': user.id})
        with self.assertRaises(AccessError):
            self._apply(employee=employee)

    def test_employee_only_helper_requires_linked_employee(self):
        with self.assertRaises(AccessError):
            self.actors['configuration'].with_user(self.actors['write'])._apply_dental_capabilities(
                dict.fromkeys(CAPABILITIES, 'read'))

    def test_menu_acceptance_matrix(self):
        xmlids = (
            'dental_clinic.menu_dental_root', 'hr.menu_hr_root', 'sd_facility.sd_facility_menu',
            'dental_clinic.menu_dental_permission_root',
            'sd_facility_schedule.sd_facility_assignment_menu_my',
            'sd_facility_schedule.sd_facility_assignment_menu',
            'dental_clinic.menu_dental_permission_profiles',
            'dental_clinic.menu_dental_permission_apply')
        expected = {
            'ordinary': (False, True, False, False, True, False, False, False),
            'read': (False, True, False, True, True, True, True, False),
            'write': (False, True, False, True, True, True, True, False),
            'manager': (True, True, True, True, True, True, True, False),
            'system': (True, True, True, True, True, True, True, False),
            'portal': (False,) * 8,
        }
        for role, flags in expected.items():
            if role == 'portal':
                with self.assertRaises(AccessError):
                    self.env['ir.ui.menu'].with_user(self.actors[role]).load_menus(debug=False)
                continue
            visible = self.env['ir.ui.menu'].with_user(self.actors[role])._visible_menu_ids()
            for xmlid, flag in zip(xmlids, flags):
                with self.subTest(role=role, xmlid=xmlid):
                    self.assertEqual(self.env.ref(xmlid).id in visible, flag)
        self.assertFalse(self.env.ref('sd_facility.sd_facility_menu').parent_id)
        self.assertEqual(self.env.ref('sd_facility_schedule.sd_facility_schedule_menu').parent_id,
                         self.env.ref('hr.menu_hr_root'))
        children = self.env['ir.ui.menu'].sudo().search([
            ('parent_id', '=', self.env.ref('dental_clinic.menu_dental_config').id)])
        self.assertEqual(set(children.ids), {self.env.ref(f'dental_clinic.menu_dental_config_{name}').id
                                            for name in ('treatments', 'practitioners', 'rooms')})

    def test_chinese_space_navigation(self):
        self.env['res.lang'].sudo()._activate_lang('zh_CN')
        self.env['ir.module.module'].sudo()._load_module_terms(['sd_facility'], ['zh_CN'])
        Menu = self.env['ir.ui.menu'].sudo().with_context(lang='zh_CN')
        root = self.env.ref('sd_facility.sd_facility_menu').with_context(lang='zh_CN')
        self.assertEqual(root.name, '空间')
        self.assertFalse(root.parent_id)
        expected = {
            'sd_facility_space_menu_facility': '院址',
            'sd_facility_space_menu_floor': '楼层',
            'sd_facility_space_menu_area': '区域',
            'sd_facility_station_menu': '工作位',
        }
        self.assertEqual(set(root.child_id.ids), {
            self.env.ref(f'sd_facility.{xmlid}').id for xmlid in expected})
        for xmlid, label in expected.items():
            with self.subTest(xmlid=xmlid):
                self.assertEqual(self.env.ref(f'sd_facility.{xmlid}').with_context(lang='zh_CN').name, label)
        self.assertEqual(Menu.search([
            ('parent_id', '=', False), ('name', 'in', ['空间', '诊所设施', 'Space', 'Facilities'])]), root)
        menus = Menu.with_user(self.actors['manager']).load_menus(debug=False)
        self.assertEqual(menus[root.id]['name'], '空间')

    def test_native_view_and_chinese_permissions(self):
        self.env['res.lang'].sudo()._activate_lang('zh_CN')
        self.env['ir.module.module'].sudo()._load_module_terms(
            ['dental_clinic', 'sd_facility', 'sd_facility_schedule'], ['zh_CN'])
        self.env.invalidate_all()
        Model = self.env['hr.employee'].with_user(self.actors['write']).with_context(lang='zh_CN')
        view = Model.get_view(self.env.ref('hr.view_employee_form').id, 'form')
        arch = etree.fromstring(view['arch'])
        page = arch.xpath('//page[@name="dental_work_permissions"]')[0]
        self.assertEqual(page.get('string'), '工作权限')
        self.assertEqual(page.xpath('.//button[@name="action_apply_dental_profile"]')[0].get('string'), '应用模板')
        self.assertEqual(Model.fields_get(['dental_permission_profile_id'])[
            'dental_permission_profile_id']['string'], '权限模板')
        self.assertEqual(len(page.xpath('.//field[@widget="radio"]')), 5)
        fields = Model.fields_get(FIELDS)
        for name in FIELDS:
            self.assertEqual(tuple(fields[name]['selection']), (('none', '无'), ('read', '只读'), ('write', '读写')))
        for role in ('ordinary', 'read'):
            view = self.env['hr.employee'].with_user(self.actors[role]).get_view(
                self.env.ref('hr.view_employee_form').id, 'form')
            self.assertNotIn('dental_work_permissions', view['arch'])

    def test_chinese_profile_labels_and_validation(self):
        self.env['res.lang'].sudo()._activate_lang('zh_CN')
        self.env['ir.module.module'].sudo()._load_module_terms(['dental_clinic'], ['zh_CN'])
        Model = self.env['dental.permission.profile'].with_user(self.actors['write']).with_context(lang='zh_CN')
        for view_type in ('list', 'form'):
            view = Model.get_view(self.env.ref(
                f'dental_clinic.dental_permission_profile_view_{view_type}').id, view_type)
            arch = etree.fromstring(view['arch'])
            self.assertEqual(arch.xpath('//field[@name="name"]')[0].get('string'), '模板名称')
        self.assertEqual(self.env.ref('dental_clinic.menu_dental_permission_profiles').with_context(
            lang='zh_CN').name, '权限模板')
        employee = self.employee.with_user(self.actors['write']).with_context(lang='zh_CN')
        with self.assertRaisesRegex(ValidationError, '^请先选择权限模板。$'):
            employee.action_apply_dental_profile()
        self.profile.sudo().action_archive()
        with self.assertRaisesRegex(ValidationError, '^请选择启用的权限模板。$'):
            employee.with_context(dental_permission_profile_id=self.profile.id).action_apply_dental_profile()
