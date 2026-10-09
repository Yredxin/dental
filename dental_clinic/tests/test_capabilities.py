from contextlib import closing
from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import new_test_user

from .test_authorization import MODEL_MATRIX, TestDentalAuthorization


CAPABILITIES = ('patient', 'appointment', 'clinical', 'employee', 'configuration')
PRESETS = {
    'receptionist': ('write', 'write', 'read', 'none', 'none'),
    'nurse': ('read', 'read', 'read', 'none', 'none'),
    'warehouse': ('none',) * 5,
    'user': ('read', 'read', 'write', 'none', 'none'),
    'manager': ('write',) * 5,
}


@tagged('dental_auth')
class TestDentalCapabilities(TestDentalAuthorization):
    # Reuse fixtures/helpers; the AUTH01 class runs its 31 tests separately.
    allow_inherited_tests_method = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.capability_users = {}
        for capability in CAPABILITIES:
            for level in ('read', 'write'):
                cls.capability_users[capability, level] = new_test_user(
                    cls.env, login=f'dental_cap_{capability}_{level}',
                    groups=f'dental_clinic.group_dental_{capability}_{level}',
                    company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)],
                )
        cls.role_users = dict(cls.role_users)
        for name, groups in {
            'mixed_a': ('patient_write', 'appointment_write', 'clinical_read'),
            'mixed_b': ('patient_read', 'appointment_read', 'clinical_write', 'employee_read'),
        }.items():
            cls.role_users[name] = new_test_user(
                cls.env, login=f'dental_cap_{name}',
                groups=','.join(f'dental_clinic.group_dental_{group}' for group in groups),
                company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)],
            )
        cls.employee = cls.env['hr.employee'].sudo().create({
            'name': 'Dental public employee', 'company_id': cls.company.id,
        })

    def _apply(self, target, levels, caller=None, profile=None):
        caller = caller or self.role_users['manager']
        wizard = self.env['dental.permission.apply'].with_user(caller).create({
            'user_id': target.id,
            **{f'{name}_level': level for name, level in zip(CAPABILITIES, levels)},
            'profile_id': profile.id if profile else False,
        })
        wizard.action_apply()
        return wizard

    def _assert_levels(self, user, levels):
        user = user.with_user(user)
        self.assertFalse(user.env.su)
        for name, level in zip(CAPABILITIES, levels):
            self.assertEqual(user.has_group(f'dental_clinic.group_dental_{name}_read'), level != 'none')
            self.assertEqual(user.has_group(f'dental_clinic.group_dental_{name}_write'), level == 'write')

    def test_native_independent_privileges(self):
        for capability in CAPABILITIES:
            privilege = self.env.ref(f'dental_clinic.privilege_dental_{capability}')
            read = self.env.ref(f'dental_clinic.group_dental_{capability}_read')
            write = self.env.ref(f'dental_clinic.group_dental_{capability}_write')
            self.assertEqual(privilege.group_ids, read | write)
            self.assertIn(read, write.all_implied_ids)
            for level in ('read', 'write'):
                user = self.capability_users[capability, level]
                self.assertFalse(user.has_group('base.group_system'))
                self.assertFalse(user.has_group('base.group_erp_manager'))
                for other in CAPABILITIES:
                    if other != capability:
                        self.assertFalse(user.has_group(f'dental_clinic.group_dental_{other}_read'))
        self.assertFalse(self.env.ref('dental_clinic.privilege_dental').group_ids)
        for legacy in PRESETS:
            self.assertFalse(self.env.ref(f'dental_clinic.group_dental_{legacy}').privilege_id)

    def _isolated_capability_matrix(self, capability, level):
        # Independent oracle, including shared read-only selector records.
        expected = {}
        if capability in ('patient', 'appointment', 'clinical', 'configuration'):
            expected.update({name: 'r' for name in ('dental.practitioner', 'dental.room', 'dental.treatment')})
        if capability in ('patient', 'clinical'):
            expected.update({name: 'r' for name in ('dental.patient', 'dental.medical.history', 'dental.tooth')})
        if capability == 'clinical':
            expected.update({name: 'r' for name in ('dental.treatment.plan', 'dental.treatment.plan.line',
                                                    'dental.prescription', 'dental.prescription.line')})
        if capability == 'appointment':
            expected['dental.appointment'] = 'r'
        if level == 'write':
            if capability == 'patient':
                expected['dental.patient'] = 'cru'
            elif capability == 'appointment':
                expected['dental.appointment'] = 'cru'
            elif capability == 'clinical':
                expected.update({name: 'cru' for name in ('dental.medical.history', 'dental.treatment.plan',
                    'dental.treatment.plan.line', 'dental.prescription', 'dental.prescription.line')})
                expected.update({'dental.patient': 'ru', 'dental.tooth': 'ru'})
            elif capability == 'configuration':
                expected.update({name: 'crud' for name in ('dental.practitioner', 'dental.room', 'dental.treatment')})
        actor = f'isolated_{capability}'
        self.role_users = {**self.role_users, actor: self.capability_users[capability, level]}
        for model in MODEL_MATRIX:
            for operation in 'crud':
                with self.subTest(capability=capability, level=level, model=model, operation=operation), closing(self.cr.savepoint()):
                    if operation in expected.get(model, ''):
                        self._exercise(actor, model, operation)
                    else:
                        with self.assertRaises(AccessError):
                            self._exercise(actor, model, operation)

    def test_isolated_patient_read_matrix(self):
        self._isolated_capability_matrix('patient', 'read')

    def test_isolated_patient_write_matrix(self):
        self._isolated_capability_matrix('patient', 'write')

    def test_isolated_appointment_read_matrix(self):
        self._isolated_capability_matrix('appointment', 'read')

    def test_isolated_appointment_write_matrix(self):
        self._isolated_capability_matrix('appointment', 'write')

    def test_isolated_clinical_read_matrix(self):
        self._isolated_capability_matrix('clinical', 'read')

    def test_isolated_clinical_write_matrix(self):
        self._isolated_capability_matrix('clinical', 'write')

    def test_isolated_employee_read_matrix(self):
        self._isolated_capability_matrix('employee', 'read')

    def test_isolated_employee_write_matrix(self):
        self._isolated_capability_matrix('employee', 'write')

    def test_isolated_configuration_read_matrix(self):
        self._isolated_capability_matrix('configuration', 'read')

    def test_isolated_configuration_write_matrix(self):
        self._isolated_capability_matrix('configuration', 'write')

    def test_exact_default_profiles_and_application(self):
        target = self.role_users['warehouse']
        for name, levels in PRESETS.items():
            with self.subTest(profile=name):
                profile = self.env.ref(f'dental_clinic.permission_profile_{name}').with_user(self.role_users['manager'])
                self.assertEqual(tuple(profile[f'{cap}_level'] for cap in CAPABILITIES), levels)
                self._apply(target, levels, profile=profile)
                self._assert_levels(target, levels)
                self.assertFalse(target.has_group('base.group_system'))
                self.assertTrue(target._is_internal())

    def test_profile_isolation_and_manual_override(self):
        target = self.role_users['warehouse']
        unrelated = self.env.ref('base.group_multi_currency')
        target.sudo().write({'group_ids': [Command.link(unrelated.id)]})
        before = target.group_ids
        profile = self.env.ref('dental_clinic.permission_profile_nurse')
        self._apply(target, PRESETS['nurse'], profile=profile)
        self.assertIn(unrelated, target.group_ids)
        self.assertTrue(set(before.ids).issubset(target.group_ids.ids))
        target.sudo().write({'group_ids': [Command.link(self.env.ref('dental_clinic.group_dental_appointment_write').id)]})
        self._assert_levels(target, ('read', 'write', 'read', 'none', 'none'))
        self.assertTrue(self.env['dental.appointment'].with_user(target).has_access('create'))
        profile.sudo().write({'appointment_level': 'none'})
        self._assert_levels(target, ('read', 'write', 'read', 'none', 'none'))
        self.assertNotIn('profile_id', self.env['res.users']._fields)

    def test_custom_profile_and_form_application(self):
        manager = self.role_users['manager']
        profile = self.env['dental.permission.profile'].with_user(manager).create({
            'name': 'Custom clinic preset', 'patient_level': 'read',
            'clinical_level': 'write', 'employee_level': 'read',
        })
        profile.write({'appointment_level': 'read'})
        with Form(self.env['dental.permission.apply'].with_user(manager)) as form:
            form.user_id = self.role_users['warehouse']
            form.profile_id = profile
            self.assertEqual(form.clinical_level, 'write')
            form.appointment_level = 'write'
        form.record.action_apply()
        self._assert_levels(self.role_users['warehouse'], ('read', 'write', 'write', 'read', 'none'))

    def test_profile_acl_and_arbitrary_group_injection_denied(self):
        read_user = self.capability_users['configuration', 'read']
        profile = self.env.ref('dental_clinic.permission_profile_nurse')
        self.assertTrue(profile.with_user(read_user).read(['name']))
        with self.assertRaises(AccessError):
            profile.with_user(read_user).write({'patient_level': 'write'})
        for role in ('frontdesk', 'nurse', 'warehouse', 'dentist', 'portal'):
            with self.subTest(role=role), self.assertRaises(AccessError):
                self._apply(self.role_users['warehouse'], PRESETS['manager'], caller=self.role_users[role])
        for vals in ({'group_ids': [Command.link(self.env.ref('base.group_system').id)]},
                     {'configuration_level': 'base.group_system'}):
            with self.assertRaises(ValueError), self.cr.savepoint():
                profile.with_user(self.role_users['manager']).write(vals)
        with self.assertRaises(ValidationError):
            self.role_users['warehouse'].with_user(self.role_users['manager'])._apply_dental_capabilities({
                **dict(zip(CAPABILITIES, PRESETS['nurse'])), 'group_ids': [self.env.ref('base.group_system').id],
            })

    def test_manager_cannot_escalate_user_or_group_authority(self):
        manager = self.role_users['manager']
        target = self.role_users['warehouse']
        system = self.env.ref('base.group_system')
        before = {user.id: user.group_ids.ids for user in manager | target}
        for user in (manager, target):
            for vals in ({'group_ids': [Command.link(system.id)]}, {'role': 'group_system'},
                         {'group_ids': [Command.link(self.env.ref('base.group_erp_manager').id)]}):
                with self.subTest(user=user.id, vals=vals), self.assertRaises(AccessError), self.cr.savepoint():
                    user.with_user(manager).write(vals)
        with self.assertRaises(AccessError):
            system.with_user(manager).write({'implied_ids': [Command.link(self.env.ref('base.group_user').id)]})
        with self.assertRaises(AccessError):
            self.env['res.groups'].with_user(manager).create({'name': 'Forbidden arbitrary group'})
        with self.assertRaises(AccessError):
            self.role_users['system'].with_user(manager).action_apply_dental_permission_profile()
            self._apply(self.role_users['system'], PRESETS['warehouse'])
        for user in manager | target:
            self.assertEqual(user.group_ids.ids, before[user.id])
        self.assertFalse(manager.has_group('base.group_system'))

    def test_profile_rejects_portal_and_other_company_targets(self):
        with self.assertRaises(AccessError):
            self._apply(self.role_users['portal'], PRESETS['nurse'])
        company = self.env['res.company'].sudo().create({'name': 'Separate authorization clinic'})
        target = new_test_user(self.env, login='dental_cap_other_company', groups='base.group_user',
                               company_id=company.id, company_ids=[Command.set(company.ids)])
        with self.assertRaises(AccessError):
            self._apply(target, PRESETS['nurse'])

    def test_system_profile_application_preserves_system_authority(self):
        system = self.role_users['system']
        before = system.group_ids
        self._apply(system, PRESETS['warehouse'], caller=system)
        self.assertTrue(system.has_group('base.group_system'))
        self.assertTrue(set(before.ids).issubset(system.group_ids.ids))
        self._assert_levels(system, ('write',) * 5)

    def test_legacy_migration_and_repeat_upgrade(self):
        for name, expected in PRESETS.items():
            with self.subTest(legacy=name):
                target = new_test_user(self.env, login=f'dental_cap_legacy_{name}',
                                       groups=f'dental_clinic.group_dental_{name}',
                                       company_id=self.company.id, company_ids=[Command.set(self.company.ids)])
                self.env['res.users'].sudo()._migrate_legacy_dental_groups()
                self._assert_levels(target, expected)
                self.assertTrue(target._is_internal())
                for legacy in PRESETS:
                    self.assertFalse(target.has_group(f'dental_clinic.group_dental_{legacy}'))
                self._apply(target, PRESETS['warehouse'])
                self.env['res.users'].sudo()._migrate_legacy_dental_groups()
                self._assert_levels(target, PRESETS['warehouse'])

    def _mixed_matrix(self, role, index):
        for model, roles in MODEL_MATRIX.items():
            allowed = roles[index]
            for operation in 'crud':
                with self.subTest(user=role, model=model, operation=operation), closing(self.cr.savepoint()):
                    if operation in allowed:
                        self._exercise(role, model, operation)
                    else:
                        with self.assertRaises(AccessError):
                            self._exercise(role, model, operation)

    def test_mixed_a_effective_crud(self):
        self._mixed_matrix('mixed_a', 0)

    def test_mixed_b_effective_crud(self):
        self._mixed_matrix('mixed_b', 3)
        self.assertTrue(self.employee.with_user(self.role_users['mixed_b']).read(['name']))

    def test_patient_only_counters_and_field_boundaries(self):
        user = self.capability_users['patient', 'write']
        patient = self.patient.with_user(user)
        patient.write({'phone': 'Patient capability only', 'occupation': 'Administrative'})
        arch = etree.fromstring(patient.get_view(
            view_id=self.env.ref('dental_clinic.view_dental_patient_form').id, view_type='form')['arch'])
        names = {node.get('name') for node in arch.xpath('//field[not(ancestor::field)]')}
        self.assertTrue(patient.read(sorted(names), load=None))
        for name in ('appointment_count', 'treatment_plan_count', 'prescription_count', 'invoice_count'):
            self.assertNotIn(name, names)
            with self.assertRaises(AccessError):
                patient.read([name])
        self.assertFalse(patient.env['dental.appointment'].has_access('read'))
        with self.assertRaises(AccessError):
            patient.write({'allergies': 'Forbidden'})
        with self.assertRaises(AccessError):
            patient.write({'partner_id': self.role_users['portal'].partner_id.id})
        with self.assertRaises(AccessError):
            patient.unlink()

    def test_clinical_only_does_not_gain_contact_or_appointment_authority(self):
        user = self.capability_users['clinical', 'write']
        self.patient.with_user(user).write({'allergies': 'Clinical capability only'})
        with self.assertRaises(AccessError):
            self.patient.with_user(user).write({'phone': 'Forbidden'})
        with self.assertRaises(AccessError):
            self.patient.with_user(user).write({'occupation': 'Forbidden'})
        self.assertFalse(self.env['dental.appointment'].with_user(user).has_access('write'))
        self.assertFalse(self.env['dental.patient'].with_user(user).has_access('create'))

    def test_appointment_only_effective_mutation(self):
        user = self.capability_users['appointment', 'write']
        appointment = self.env['dental.appointment'].with_user(user).create(self._values('dental.appointment'))
        appointment.write({'reason': 'Appointment capability only'})
        appointment.action_confirm()
        self.assertEqual(appointment.state, 'confirmed')
        with self.assertRaises(AccessError):
            appointment.unlink()
        self.assertFalse(self.env['dental.patient'].with_user(user).has_access('write'))

    def test_configuration_only_product_boundary(self):
        read = self.capability_users['configuration', 'read']
        write = self.capability_users['configuration', 'write']
        self.assertTrue(self.treatment.with_user(read).read(['name']))
        with self.assertRaises(AccessError):
            self.treatment.with_user(read).write({'price': 22})
        treatment = self.env['dental.treatment'].with_user(write).create({'name': 'Configuration service', 'price': 22})
        treatment.write({'price': 33})
        self.assertEqual(treatment.product_id.list_price, 33)
        self.assertFalse(read.has_group('product.group_product_manager'))
        self.assertTrue(write.has_group('product.group_product_manager'))
        with self.assertRaises(AccessError):
            self.patient.with_user(write).unlink()
        with self.assertRaises(AccessError):
            self.patient.with_user(write).write({'partner_id': self.role_users['portal'].partner_id.id})

    def test_employee_read_public_directory_and_mutation_denials(self):
        user = self.capability_users['employee', 'read']
        public = self.env['hr.employee.public'].with_user(user).browse(self.employee.id)
        self.assertEqual(public.name, self.employee.name)
        self.assertTrue(self.employee.with_user(user).read(['name']))
        with self.assertRaises(AccessError):
            self.employee.with_user(user).read(['identification_id'])
        with self.assertRaises(AccessError):
            self.env['hr.employee'].with_user(user).create({'name': 'Forbidden employee'})
        for operation in ('write', 'action_archive', 'unlink'):
            with self.subTest(operation=operation), self.assertRaises(AccessError), self.cr.savepoint():
                if operation == 'write':
                    self.employee.with_user(user).write({'name': 'Forbidden edit'})
                elif operation == 'action_archive':
                    self.employee.with_user(user).action_archive()
                else:
                    self.employee.with_user(user).unlink()

    def test_employee_rw_native_crud_archive_and_system_boundary(self):
        for user in (self.capability_users['employee', 'write'], self.role_users['manager']):
            with self.subTest(user=user.id):
                employee = self.env['hr.employee'].with_user(user).create({
                    'name': 'Native Dental employee', 'company_id': self.company.id,
                })
                self.assertEqual(employee.name, 'Native Dental employee')
                employee.write({'name': 'Updated native employee'})
                employee.action_archive()
                self.assertFalse(employee.active)
                employee.unlink()
                self.assertFalse(employee.sudo().exists())
                self.assertTrue(user.has_group('hr.group_hr_user'))
                self.assertFalse(user.has_group('hr.group_hr_manager'))
                self.assertFalse(user.has_group('base.group_system'))
                with self.assertRaises(AccessError), self.cr.savepoint():
                    user.with_user(user).write({'group_ids': [Command.link(self.env.ref('base.group_system').id)]})

    def test_employee_invitation_requires_native_user_administration(self):
        employee = self.employee
        callers = [user for role, user in self.role_users.items() if role != 'system']
        callers.append(self.capability_users['employee', 'write'])
        with patch.object(type(employee), '_get_or_create_light_user') as provision:
            for user in callers:
                with self.subTest(user=user.login), self.assertRaises(AccessError):
                    employee.with_user(user).action_send_invitation()
            provision.assert_not_called()
        # Exercise the native administrator branch without creating an account
        # or sending mail. The native result is still the invitation notification.
        with patch.object(type(employee), '_get_or_create_light_user',
                          return_value=self.env['res.users']) as provision:
            result = employee.with_user(self.role_users['system']).action_send_invitation()
            provision.assert_called_once_with(invite=True)
            self.assertEqual(result['tag'], 'display_notification')

    def test_chinese_native_privileges_and_profiles(self):
        self.env['res.lang'].sudo()._activate_lang('zh_CN')
        self.env['ir.module.module'].sudo()._load_module_terms(['dental_clinic'], ['zh_CN'])
        self.env.invalidate_all()
        for name, label in zip(CAPABILITIES, ('患者管理', '预约管理', '牙科临床', '员工管理', '牙科配置')):
            privilege = self.env.ref(f'dental_clinic.privilege_dental_{name}').with_context(lang='zh_CN')
            self.assertEqual(privilege.name, label)
            self.assertEqual(privilege.placeholder, '无')
            self.assertEqual(self.env.ref(f'dental_clinic.group_dental_{name}_read').with_context(lang='zh_CN').name, '只读')
            self.assertEqual(self.env.ref(f'dental_clinic.group_dental_{name}_write').with_context(lang='zh_CN').name, '读写')
        for name, label in zip(PRESETS, ('前台', '护士', '仓管', '医生', '负责人')):
            profile = self.env.ref(f'dental_clinic.permission_profile_{name}').with_user(self.role_users['manager'])
            self.assertEqual(profile.with_context(lang='zh_CN').name, label)
