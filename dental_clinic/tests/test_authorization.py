from ast import literal_eval
from contextlib import closing
from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import Form, tagged
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


# Independent oracle: docs/development/DENTAL_AUTH_02_CAPABILITY_MODEL.md.
# Each role exercises real ORM CRUD for all twelve models (48 cells).
MODEL_MATRIX = {
    'dental.patient': ('cru', 'r', '', 'ru'),
    'dental.medical.history': ('r', 'r', '', 'cru'),
    'dental.practitioner': ('r', 'r', '', 'r'),
    'dental.room': ('r', 'r', '', 'r'),
    'dental.tooth': ('r', 'r', '', 'ru'),
    'dental.treatment': ('r', 'r', '', 'r'),
    'dental.treatment.plan': ('r', 'r', '', 'cru'),
    'dental.treatment.plan.line': ('r', 'r', '', 'cru'),
    'dental.appointment': ('cru', 'r', '', 'r'),
    'dental.prescription': ('r', 'r', '', 'cru'),
    'dental.prescription.line': ('r', 'r', '', 'cru'),
    'dental.invoice.wizard': ('', '', '', ''),
}
ROLE_GROUPS = {
    'frontdesk': 'base.group_user,dental_clinic.group_dental_patient_write,dental_clinic.group_dental_appointment_write,dental_clinic.group_dental_clinical_read',
    'nurse': 'base.group_user,dental_clinic.group_dental_patient_read,dental_clinic.group_dental_appointment_read,dental_clinic.group_dental_clinical_read',
    'warehouse': 'base.group_user',
    'dentist': 'base.group_user,dental_clinic.group_dental_patient_read,dental_clinic.group_dental_appointment_read,dental_clinic.group_dental_clinical_write',
    'manager': 'base.group_user,dental_clinic.group_dental_patient_write,dental_clinic.group_dental_appointment_write,dental_clinic.group_dental_clinical_write,dental_clinic.group_dental_employee_write,dental_clinic.group_dental_configuration_write',
    'system': 'base.group_system',
    'portal': 'base.group_portal',
}


@tagged('dental_auth')
class TestDentalAuthorization(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role_users = {
            role: new_test_user(
                cls.env, login=f'dental_auth_{role}', groups=group,
                company_id=cls.company.id,
                company_ids=[Command.set(cls.company.ids)],
            )
            for role, group in ROLE_GROUPS.items()
        }
        cls.patient = cls.env['dental.patient'].create({'partner_id': cls.partner.id})
        cls.practitioner = cls.env['dental.practitioner'].create({'name': 'Auth practitioner'})
        cls.room = cls.env['dental.room'].create({'name': 'Auth room'})
        cls.treatment = cls.env['dental.treatment'].create({'name': 'Auth treatment', 'price': 25})
        cls.plan = cls.env['dental.treatment.plan'].create({
            'patient_id': cls.patient.id, 'practitioner_id': cls.practitioner.id,
        })
        cls.prescription = cls.env['dental.prescription'].create({
            'patient_id': cls.patient.id, 'practitioner_id': cls.practitioner.id,
        })
        cls.journal = cls.env['account.journal'].create({
            'name': 'Auth sales', 'code': 'AUTH', 'type': 'sale', 'company_id': cls.company.id,
        })
        # Reserve one valid FDI slot for direct create tests.
        cls.patient.tooth_ids.filtered(lambda tooth: tooth.tooth_number == 11).unlink()
        cls.portal_patient = cls.env['dental.patient'].create({
            'partner_id': cls.role_users['portal'].partner_id.id,
        })

    def _values(self, model):
        clinical = {'patient_id': self.patient.id, 'practitioner_id': self.practitioner.id}
        return {
            'dental.patient': {'partner_id': self.partner.id},
            'dental.medical.history': {'patient_id': self.patient.id, 'title': 'Auth history'},
            'dental.practitioner': {'name': 'Auth independent practitioner'},
            'dental.room': {'name': 'Auth independent room'},
            'dental.tooth': {'patient_id': self.patient.id, 'tooth_number': 11, 'name': 'FDI 11'},
            'dental.treatment': {'name': 'Auth independent service', 'price': 10},
            'dental.treatment.plan': dict(clinical),
            'dental.treatment.plan.line': {'plan_id': self.plan.id, 'treatment_id': self.treatment.id},
            'dental.appointment': {
                **clinical, 'room_id': self.room.id,
                'start': '2030-01-01 08:00:00', 'stop': '2030-01-01 08:30:00',
            },
            'dental.prescription': dict(clinical),
            'dental.prescription.line': {'prescription_id': self.prescription.id, 'name': 'Auth medicine'},
            'dental.invoice.wizard': {
                'plan_id': self.plan.id, 'patient_id': self.patient.id, 'journal_id': self.journal.id,
            },
        }[model]

    def _exercise(self, role, model, operation):
        user = self.role_users[role]
        Model = self.env[model].with_user(user)
        self.assertFalse(Model.env.su, 'Role checks must never run as superuser')
        if operation == 'c':
            record = Model.create(self._values(model))
            self.assertTrue(record.id)
        else:
            # Elevated fixture setup is independent of the operation being tested.
            record = self.env[model].sudo().create(self._values(model)).with_user(user)
            field = {
                'dental.patient': 'allergies' if role in ('dentist', 'mixed_b', 'isolated_clinical') else 'occupation', 'dental.medical.history': 'title',
                'dental.tooth': 'condition', 'dental.treatment.plan': 'notes',
                'dental.treatment.plan.line': 'description', 'dental.appointment': 'reason',
                'dental.prescription': 'diagnosis', 'dental.invoice.wizard': 'invoice_date',
            }.get(model, 'name')
            if operation == 'r':
                self.assertEqual(len(record.read([field], load=None)), 1)
            elif operation == 'u':
                value = {
                    'condition': 'caries', 'invoice_date': '2030-01-02',
                    'notes': '<p>Updated by role</p>',
                }.get(field, 'Updated by role')
                self.assertTrue(record.write({field: value}))
                actual = record[field].isoformat() if field == 'invoice_date' else record[field]
                self.assertEqual(actual, value)
            else:
                self.assertTrue(record.unlink())
                self.assertFalse(record.sudo().exists())

    def _assert_crud_matrix(self, role):
        index = {'frontdesk': 0, 'nurse': 1, 'warehouse': 2, 'dentist': 3}.get(role)
        for model, roles in MODEL_MATRIX.items():
            allowed = 'crud' if role in ('manager', 'system') else '' if role == 'portal' else roles[index]
            for operation in 'crud':
                with self.subTest(role=role, model=model, operation=operation):
                    orm_operation = {'c': 'create', 'r': 'read', 'u': 'write', 'd': 'unlink'}[operation]
                    self.assertEqual(
                        self.env[model].with_user(self.role_users[role]).has_access(orm_operation),
                        operation in allowed,
                    )
                    # Roll back every cell, including permitted deletes and pre-ACL
                    # create side effects; at most 48 savepoints in each test.
                    with closing(self.cr.savepoint()):
                        if operation in allowed:
                            self._exercise(role, model, operation)
                        else:
                            with self.assertRaises(AccessError):
                                self._exercise(role, model, operation)

    def test_frontdesk_crud_matrix(self):
        self._assert_crud_matrix('frontdesk')

    def test_nurse_crud_matrix(self):
        self._assert_crud_matrix('nurse')

    def test_warehouse_crud_matrix(self):
        self._assert_crud_matrix('warehouse')

    def test_dentist_crud_matrix(self):
        self._assert_crud_matrix('dentist')

    def test_manager_crud_matrix(self):
        self._assert_crud_matrix('manager')

    def test_system_crud_matrix(self):
        self._assert_crud_matrix('system')

    def test_portal_crud_matrix(self):
        self._assert_crud_matrix('portal')

    def test_group_semantics(self):
        expected = {
            'frontdesk': ('write', 'write', 'read', 'none', 'none'),
            'nurse': ('read', 'read', 'read', 'none', 'none'),
            'warehouse': ('none',) * 5,
            'dentist': ('read', 'read', 'write', 'none', 'none'),
            'manager': ('write',) * 5, 'system': ('write',) * 5,
            'portal': ('none',) * 5,
        }
        for role, user in self.role_users.items():
            for name, level in zip(('patient', 'appointment', 'clinical', 'employee', 'configuration'), expected[role]):
                with self.subTest(role=role, capability=name):
                    self.assertEqual(user.has_group(f'dental_clinic.group_dental_{name}_read'), level != 'none')
                    self.assertEqual(user.has_group(f'dental_clinic.group_dental_{name}_write'), level == 'write')
            self.assertEqual(user.has_group('base.group_system'), role == 'system')
            self.assertEqual(user.has_group('base.group_portal'), role == 'portal')
            self.assertEqual(user.has_group('base.group_user'), role != 'portal')
            self.assertEqual(user.has_group('product.group_product_manager'), role in ('manager', 'system'))
            for legacy in ('receptionist', 'nurse', 'warehouse', 'user', 'manager'):
                self.assertFalse(user.has_group(f'dental_clinic.group_dental_{legacy}'))
            if role != 'system':
                self.assertFalse(user.has_group('base.group_erp_manager'))
                self.assertFalse(user.has_group('account.group_account_invoice'))
                self.assertFalse(self.env['account.move'].with_user(user).has_access('create'))

    def test_menu_visibility(self):
        administrative = {
            'menu_dental_root', 'menu_dental_dashboard', 'menu_dental_patients_top',
            'menu_dental_patients', 'menu_dental_appointments_top',
            'menu_dental_appointments_calendar', 'menu_dental_appointments_list',
            'menu_dental_appointments_today',
        }
        clinical = {'menu_dental_odontogram', 'menu_dental_clinical_top', 'menu_dental_plans', 'menu_dental_prescriptions'}
        config = {'menu_dental_config', 'menu_dental_config_treatments', 'menu_dental_config_practitioners', 'menu_dental_config_rooms'}
        for role, user in self.role_users.items():
            Menu = self.env['ir.ui.menu'].with_user(user)
            if role == 'portal':
                with self.assertRaises(AccessError):
                    Menu.load_menus(debug=True)
                visible = set()
            else:
                candidates = Menu._visible_menu_ids(debug=True)
                # Match load_menus' removal of orphan menus whose parent app
                # is hidden; technical debug nodes alone are not reachable.
                visible = {
                    menu.id for menu in Menu.browse(candidates)
                    if all(int(parent) in candidates for parent in menu.parent_path.split('/') if parent)
                }
            expected = set()
            if role not in ('warehouse', 'portal'):
                expected |= administrative
            if role in ('frontdesk', 'nurse', 'dentist', 'manager', 'system'):
                expected |= clinical
            if role in ('manager', 'system'):
                expected |= config
            for menu in administrative | clinical | config:
                with self.subTest(role=role, menu=menu):
                    self.assertEqual(self.env.ref(f'dental_clinic.{menu}').id in visible, menu in expected)
            for menu in ('base.menu_management', 'base.menu_administration', 'base.menu_custom', 'contacts.menu_contacts', 'spreadsheet_dashboard.spreadsheet_dashboard_menu_root'):
                with self.subTest(role=role, menu=menu):
                    self.assertEqual(self.env.ref(menu).id in visible, role == 'system')
            if role in ('warehouse', 'portal'):
                all_dental = self.env['ir.ui.menu'].sudo().search([('id', 'child_of', self.env.ref('dental_clinic.menu_dental_root').id)])
                self.assertFalse(set(all_dental.ids) & visible)

    def _arch(self, role, model, xmlid, view_type='form'):
        result = self.env[model].with_user(self.role_users[role]).get_view(
            view_id=self.env.ref(f'dental_clinic.{xmlid}').id, view_type=view_type,
        )
        return etree.fromstring(result['arch'])

    def test_patient_view_visibility_and_reads(self):
        clinical_fields = {'medical_history_ids', 'allergies', 'tooth_ids', 'treatment_plan_ids', 'prescription_ids'}
        for role in ('frontdesk', 'nurse', 'dentist', 'manager', 'system'):
            arch = self._arch(role, 'dental.patient', 'view_dental_patient_form')
            names = set(arch.xpath('//field/@name'))
            for name in clinical_fields:
                self.assertIn(name, names)
            self.assertTrue(arch.xpath('//button[@name="action_open_appointments"]'))
            for name in ('action_open_treatment_plans', 'action_open_prescriptions'):
                self.assertTrue(arch.xpath(f'//button[@name="{name}"]'))
            self.assertEqual(bool(arch.xpath('//button[@name="action_open_invoices"]')), False)
            # Read exactly the root fields the client requests, including each
            # visible counter, with no elevated or accounting fixture role.
            fields = {node.get('name') for node in arch.xpath('//field[not(ancestor::field)]')}
            result = self.patient.with_user(self.role_users[role]).read(sorted(fields), load=None)
            self.assertEqual(len(result), 1)
            if role == 'nurse':
                self.assertEqual(arch.get('edit').lower(), 'false')
        for role in ('warehouse', 'portal'):
            with self.assertRaises(AccessError):
                self._arch(role, 'dental.patient', 'view_dental_patient_form')

    def test_write_button_visibility(self):
        cases = (
            ('dental.appointment', 'view_dental_appointment_form', {'frontdesk', 'manager', 'system'},
             ('action_confirm', 'action_check_in', 'action_done', 'action_no_show', 'action_send_reminder', 'action_cancel', 'action_draft')),
            ('dental.treatment.plan', 'view_dental_treatment_plan_form', {'dentist', 'manager', 'system'},
             ('action_confirm', 'action_start', 'action_done', 'action_cancel', 'action_draft')),
            ('dental.prescription', 'view_dental_prescription_form', {'dentist', 'manager', 'system'},
             ('action_confirm', 'action_cancel', 'action_draft')),
        )
        for model, view, writers, buttons in cases:
            for role in ('frontdesk', 'nurse', 'dentist', 'manager', 'system'):
                if not self.env[model].with_user(self.role_users[role]).has_access('read'):
                    with self.assertRaises(AccessError):
                        self._arch(role, model, view)
                    continue
                arch = self._arch(role, model, view)
                for button in buttons:
                    with self.subTest(role=role, button=button, model=model):
                        self.assertEqual(bool(arch.xpath(f'//button[@name="{button}"]')), role in writers)
                if model == 'dental.treatment.plan':
                    self.assertEqual(bool(arch.xpath('//button[@name="action_create_invoice"]')), False)
                if model == 'dental.prescription':
                    self.assertTrue(arch.xpath('//button[@name="action_print"]'))
                if role not in writers:
                    self.assertEqual(arch.get('edit').lower(), 'false')
                    self.assertEqual(arch.get('create').lower(), 'false')
                    self.assertEqual(arch.get('delete').lower(), 'false')

    def test_frontdesk_patient_creation_and_fixed_teeth(self):
        Patient = self.env['dental.patient'].with_user(self.role_users['frontdesk'])
        patients = Patient.with_context(default_condition='caries').create([
            {'partner_id': self.partner.id}, {'partner_id': self.partner.id},
        ])
        expected = {quadrant * 10 + position for quadrant in (1, 2, 3, 4) for position in range(1, 9)}
        for patient in patients:
            self.assertTrue(patient.partner_id.is_dental_patient)
            teeth = patient.sudo().tooth_ids
            self.assertEqual(len(teeth), 32)
            self.assertEqual(set(teeth.mapped('tooth_number')), expected)
            self.assertEqual(set(teeth.mapped('condition')), {'healthy'})
            self.assertFalse(any(teeth.mapped('notes')))
            self.assertTrue(all(teeth.mapped('name')))
            self.assertTrue(all(teeth.mapped('quadrant')))
            self.assertEqual(patient.appointment_count, 0)
            self.assertEqual(len(teeth.with_user(Patient.env.user).read(['condition'])), 32)
            for operation in ('write', 'unlink'):
                with self.assertRaises(AccessError):
                    if operation == 'write':
                        teeth.with_user(Patient.env.user).write({'condition': 'caries'})
                    else:
                        teeth.with_user(Patient.env.user).unlink()
        with self.assertRaises(AccessError), self.cr.savepoint():
            Patient.create({
                'partner_id': self.partner.id,
                'tooth_ids': [Command.create({'tooth_number': 11, 'name': 'Injected', 'condition': 'caries'})],
            })
        with self.assertRaises(AccessError), self.cr.savepoint():
            patients[0].write({'tooth_ids': [Command.update(patients[0].sudo().tooth_ids[0].id, {'condition': 'caries'})]})

    def test_contact_flag_does_not_grant_general_partner_authority(self):
        user = self.role_users['frontdesk']
        self.assertFalse(user.has_group('base.group_partner_manager'))
        partner = self.env['res.partner'].sudo().create({'name': 'Auth contact flag boundary'})
        patient = self.env['dental.patient'].with_user(user).create({'partner_id': partner.id})
        self.assertTrue(partner.is_dental_patient)
        self.assertEqual(len(patient.sudo().tooth_ids), 32)
        with self.assertRaises(AccessError):
            partner.with_user(user).write({'name': 'Denied general contact edit'})
        with self.assertRaises(AccessError):
            partner.with_user(user).unlink()

    def test_native_patient_contact_creation_workflow(self):
        user = self.role_users['frontdesk']
        arch = self._arch('frontdesk', 'dental.patient', 'view_dental_patient_form')
        selector = arch.xpath('//field[@name="partner_id"]')[0]
        context = literal_eval(selector.get('context'))
        self.assertEqual(context['default_is_dental_patient'], True)
        self.assertEqual(selector.get('readonly'), 'id and not can_repair_contact')
        Partner = self.env['res.partner'].with_user(user)
        # Same normal-user quick-create RPC and context as the existing UI.
        partner_id, label = Partner.with_context(**context).name_create('Auth new UI patient')
        partner = Partner.browse(partner_id)
        self.assertTrue(label)
        self.assertTrue(partner.is_dental_patient)
        with Form(self.env['dental.patient'].with_user(user), view='dental_clinic.view_dental_patient_form') as form:
            form.partner_id = partner
            form.name = 'Auth UI patient identity'
            form.phone = '021-12345678'
            form.email = 'patient@example.invalid'
        patient = form.record
        self.assertEqual(patient.partner_id, partner)
        self.assertEqual(partner.name, 'Auth UI patient identity')
        self.assertEqual(partner.phone, '021-12345678')
        self.assertEqual(partner.email, 'patient@example.invalid')
        self.assertEqual(len(patient.sudo().tooth_ids), 32)
        for values in ({'name': 'Denied generic contact'}, {'name': 'Denied false flag', 'is_dental_patient': False}):
            with self.assertRaises(AccessError), self.cr.savepoint():
                Partner.create(values)
        with self.assertRaises(AccessError), self.cr.savepoint():
            Partner.with_context(**context).create({'name': 'Denied overridden flag', 'is_dental_patient': False})
        with self.assertRaises(AccessError):
            partner.write({'phone': 'Denied direct update'})
        with self.assertRaises(AccessError):
            partner.unlink()

    def test_registration_dialog_avoids_iap(self):
        user = self.role_users['frontdesk']
        arch = self._arch('frontdesk', 'dental.patient', 'view_dental_patient_form')
        context = literal_eval(arch.xpath('//field[@name="partner_id"]')[0].get('context'))
        view = self.env.ref(context['form_view_ref'])
        Partner = self.env['res.partner'].with_user(user).with_context(**context)
        dialog = etree.fromstring(Partner.get_view(view_id=view.id, view_type='form')['arch'])
        self.assertEqual(dialog.xpath('//field[@name="name"]')[0].get('widget'), 'char')
        self.assertFalse(dialog.xpath('//*[@widget="field_partner_autocomplete" or @widget="res_partner_many2one"]'))
        self.assertFalse(self.env['iap.account'].with_user(user).has_access('write'))
        with patch.object(type(self.env['iap.account']), 'get', side_effect=AssertionError('Dental registration must not use IAP')):
            with Form(Partner, view=view) as contact_form:
                contact_form.name = 'Auth dialog new patient'
                contact_form.email = 'dialog@example.invalid'
            partner = contact_form.record
            with Form(self.env['dental.patient'].with_user(user), view='dental_clinic.view_dental_patient_form') as patient_form:
                patient_form.partner_id = partner
        self.assertTrue(partner.is_dental_patient)
        self.assertEqual(len(patient_form.record.tooth_ids), 32)
        # Paid/company enrichment remains unchanged in the ordinary form.
        generic = etree.fromstring(Partner.get_view(view_id=self.env.ref('base.view_partner_form').id, view_type='form')['arch'])
        self.assertTrue(generic.xpath('//field[@name="name" and @widget="field_partner_autocomplete"]'))

    def test_all_role_registration_boundary(self):
        for role, user in self.role_users.items():
            with self.subTest(role=role), closing(self.cr.savepoint()):
                Partner = self.env['res.partner'].with_user(user).with_context(default_is_dental_patient=True)
                Patient = self.env['dental.patient'].with_user(user)
                if role in ('frontdesk', 'manager', 'system'):
                    partner = Partner.create({'name': 'Auth role registration'})
                    patient = Patient.create({'partner_id': partner.id})
                    self.assertTrue(patient.partner_id.is_dental_patient)
                    self.assertEqual(len(patient.tooth_ids), 32)
                else:
                    with self.assertRaises(AccessError):
                        Partner.create({'name': 'Denied role registration'})
                    with self.assertRaises(AccessError):
                        Patient.create({'partner_id': self.partner.id})

    def test_frontdesk_readonly_clinical_surface(self):
        user = self.role_users['frontdesk']
        patient = self.patient.with_user(user)
        values = {
            'blood_type': 'a_pos', 'allergies': 'Latex', 'chronic_diseases': 'Synthetic',
            'current_medications': 'Synthetic', 'smoker': True, 'pregnant': True,
            'notes': '<p>Clinical</p>',
        }
        self.patient.sudo().write(values)
        self.assertEqual(patient.read(list(values))[0]['allergies'], 'Latex')
        self.assertTrue(patient.tooth_ids.read(['tooth_number', 'name', 'condition']))
        history = self.env['dental.medical.history'].sudo().create({'patient_id': patient.id, 'title': 'Readable history'})
        self.assertEqual(history.with_user(user).title, 'Readable history')
        for name, value in values.items():
            with self.subTest(field=name), self.assertRaises(AccessError), self.cr.savepoint():
                patient.write({name: value})
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.env['dental.patient'].with_user(user).create({'partner_id': self.partner.id, name: value})
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.env['dental.patient'].with_user(user).with_context(**{f'default_{name}': value}).create({'partner_id': self.partner.id})
        for name in ('medical_history_ids', 'tooth_ids', 'treatment_plan_ids', 'prescription_ids'):
            with self.subTest(relation=name), self.assertRaises(AccessError), self.cr.savepoint():
                patient.write({name: [Command.clear()]})
        for operation in ('create', 'write', 'unlink'):
            with self.subTest(history_operation=operation), self.assertRaises(AccessError), self.cr.savepoint():
                if operation == 'create':
                    self.env['dental.medical.history'].with_user(user).create({'patient_id': patient.id, 'title': 'Denied'})
                elif operation == 'write':
                    history.with_user(user).write({'title': 'Denied'})
                else:
                    history.with_user(user).unlink()
        arch = self._arch('frontdesk', 'dental.patient', 'view_dental_patient_form')
        for name in values.keys() | {'tooth_ids', 'medical_history_ids'}:
            nodes = arch.xpath(f'//field[@name="{name}" and not(ancestor::field)]')
            self.assertTrue(nodes, name)
            self.assertTrue(all(node.get('readonly') == '1' for node in nodes), name)

    def test_demographic_maintenance_role_boundary(self):
        values = {'gender': 'other', 'birth_date': '1995-01-01', 'national_id': 'AUTH01',
                  'marital_status': 'single', 'occupation': 'Synthetic', 'emergency_name': 'Review',
                  'emergency_phone': '123', 'emergency_relation': 'Other'}
        for role in ('frontdesk', 'manager', 'system'):
            self.patient.with_user(self.role_users[role]).write(values)
        for role in ('dentist', 'nurse', 'warehouse', 'portal'):
            for name, value in values.items():
                with self.subTest(role=role, field=name), self.assertRaises(AccessError), self.cr.savepoint():
                    self.patient.with_user(self.role_users[role]).write({name: value})
        self.patient.with_user(self.role_users['dentist']).write({'allergies': 'Dentist clinical update'})

    def test_portal_linked_contact_facade(self):
        portal = self.role_users['portal']
        before = {'login': portal.login, 'groups': portal.group_ids.ids, 'active': portal.active}
        patient = self.portal_patient.with_user(self.role_users['frontdesk'])
        patient.write({'name': 'Auth maintained Portal patient', 'email': 'portal.patient@example.invalid',
                       'phone': '12345', 'mobile': '67890', 'street': 'Portal patient street'})
        self.assertEqual(portal.sudo().partner_id.name, 'Auth maintained Portal patient')
        self.assertEqual(portal.sudo().partner_id.email, 'portal.patient@example.invalid')
        self.assertEqual({'login': portal.login, 'groups': portal.group_ids.ids, 'active': portal.active}, before)
        self.assertFalse(portal.with_user(self.role_users['frontdesk']).has_access('write'))
        with self.assertRaises(AccessError):
            portal.with_user(self.role_users['frontdesk']).write({'login': 'Denied'})
        with self.assertRaises(AccessError):
            portal.partner_id.with_user(self.role_users['frontdesk']).write({'email': 'Denied'})

    def test_contact_facade_whitelist_and_role_boundary(self):
        values = {
            'name': 'Auth maintained patient', 'phone': '021-87654321',
            'mobile': '13800000000', 'email': 'updated@example.invalid',
            'street': '1 Patient Street', 'city': 'Shanghai', 'zip': '200000',
            'country_id': self.env.ref('base.cn').id, 'image_1920': False,
        }
        for role in ('frontdesk', 'manager', 'system'):
            patient = self.patient.with_user(self.role_users[role])
            patient.write(values)
            for name, value in values.items():
                actual = patient.partner_id[name]
                if name == 'image_1920':
                    self.assertFalse(actual)
                else:
                    self.assertEqual(actual.id if name == 'country_id' else actual, value)
            self.assertEqual(patient.name, values['name'])
            self.assertIn(values['name'], patient.display_name)
            if role != 'system':
                self.assertFalse(patient.env.user.has_group('base.group_partner_manager'))
                with self.assertRaises(AccessError):
                    patient.partner_id.write({'phone': 'Denied direct update'})
        for role in ('dentist', 'nurse', 'warehouse'):
            user = self.role_users[role]
            for name, value in values.items():
                with self.subTest(role=role, field=name), self.assertRaises(AccessError), self.cr.savepoint():
                    self.patient.with_user(user).write({name: value})
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.env['res.partner'].with_user(user).create({'name': 'Denied role contact', 'is_dental_patient': True})
            with self.assertRaises(AccessError):
                self.patient.partner_id.with_user(user).write({'phone': 'Denied direct role edit'})
        for role in ('dentist', 'nurse'):
            arch = self._arch(role, 'dental.patient', 'view_dental_patient_form')
            for name in values:
                nodes = arch.xpath(f'//field[@name="{name}" and not(ancestor::field)]')
                self.assertTrue(nodes, name)
                self.assertTrue(all(node.get('readonly') in ('1', 'True', 'true') for node in nodes), name)

    def test_contact_facade_rejects_extra_fields_and_relink(self):
        patient = self.patient.with_user(self.role_users['frontdesk'])
        partner = patient.partner_id
        before = partner.phone
        for field in ('vat', 'is_company', 'company_id', 'parent_id', 'bank_ids', 'is_dental_patient'):
            with self.subTest(field=field), self.assertRaises(ValueError), self.cr.savepoint():
                patient.write({'phone': 'Must roll back', field: False})
            self.assertEqual(partner.phone, before)
        other = self.env['res.partner'].sudo().create({'name': 'Auth repair target', 'is_dental_patient': True})
        for role in ('frontdesk', 'dentist'):
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.patient.with_user(self.role_users[role]).write({'partner_id': other.id, 'phone': 'Denied relink'})
            self.assertEqual(self.patient.sudo().partner_id, partner)
        for role in ('manager', 'system'):
            self.patient.with_user(self.role_users[role]).write({'partner_id': other.id})
            self.assertEqual(self.patient.sudo().partner_id, other)

    def test_contact_facade_checks_effective_patient_write(self):
        self.env['ir.access'].sudo().create({
            'name': 'Auth denied patient contact facade',
            'model_id': self.env['ir.model']._get_id('dental.patient'),
            'operation': 'u', 'domain': f"[('id', '!=', {self.patient.id})]",
        })
        partner = self.patient.sudo().partner_id
        before = partner.phone
        with self.assertRaises(AccessError):
            self.patient.with_user(self.role_users['frontdesk']).write({'phone': 'Denied by record domain'})
        self.assertEqual(partner.phone, before)

    def test_contact_values_on_batch_patient_creation(self):
        partners = self.env['res.partner'].sudo().create([{'name': 'Auth batch one'}, {'name': 'Auth batch two'}])
        patients = self.env['dental.patient'].with_user(self.role_users['frontdesk']).with_context(default_phone='default phone').create([
            {'partner_id': partners[0].id, 'name': 'Auth batch renamed one', 'phone': 'explicit phone'},
            {'partner_id': partners[1].id, 'name': 'Auth batch renamed two'},
        ])
        self.assertEqual(partners.mapped('name'), ['Auth batch renamed one', 'Auth batch renamed two'])
        self.assertEqual(partners.mapped('phone'), ['explicit phone', 'default phone'])
        for patient in patients:
            self.assertTrue(patient.partner_id.is_dental_patient)
            self.assertEqual(len(patient.sudo().tooth_ids), 32)

    def test_contact_facade_does_not_propagate_to_other_contacts(self):
        Partner = self.env['res.partner'].sudo()
        parent = Partner.create({'name': 'Auth parent company', 'is_company': True, 'street': 'Original parent'})
        linked = Partner.create({'name': 'Auth linked person', 'parent_id': parent.id})
        sibling = Partner.create({'name': 'Auth sibling person', 'parent_id': parent.id})
        child = Partner.create({'name': 'Auth child address', 'parent_id': linked.id})
        snapshots = {partner.id: partner.street for partner in parent | sibling | child}
        patient = self.env['dental.patient'].with_user(self.role_users['frontdesk']).create({'partner_id': linked.id})
        patient.write({'street': 'Only patient address', 'city': 'Shanghai'})
        self.assertEqual(linked.street, 'Only patient address')
        self.assertEqual(linked.city, 'Shanghai')
        for partner in parent | sibling | child:
            self.assertEqual(partner.street, snapshots[partner.id])

    def test_contact_facade_preserves_user_and_bank_authority(self):
        user = self.role_users['frontdesk']
        protected_user = self.role_users['dentist'].sudo()
        patient = self.env['dental.patient'].with_user(user).create({'partner_id': protected_user.partner_id.id})
        before = protected_user.partner_id.email
        with self.assertRaises(AccessError), self.cr.savepoint():
            patient.write({'email': 'Denied account takeover@example.invalid'})
        self.assertEqual(protected_user.partner_id.email, before)
        partner = self.env['res.partner'].sudo().create({'name': 'Auth bank-linked patient'})
        bank = self.env['res.partner.bank'].sudo().create({'partner_id': partner.id, 'account_number': 'AUTH01-1234'})
        bank_patient = self.env['dental.patient'].with_user(user).create({'partner_id': partner.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            bank_patient.write({'name': 'Denied bank-holder synchronization'})
        self.assertEqual(partner.name, 'Auth bank-linked patient')
        self.assertEqual(bank.partner_id, partner)

    def test_counters_preserve_accounting_boundary(self):
        user = self.role_users['frontdesk']
        patient = self.patient.with_user(user)
        self.env['dental.appointment'].with_user(user).create(self._values('dental.appointment'))
        self.assertEqual(patient.appointment_count, 1)
        self.assertFalse(self.env['account.move'].with_user(user).has_access('read'))
        fields = patient.fields_get()
        self.assertEqual(patient.treatment_plan_count, 1)
        self.assertEqual(patient.prescription_count, 1)
        for name in ('invoice_count', 'total_invoiced', 'total_due'):
            self.assertNotIn(name, fields)
            with self.assertRaises(AccessError):
                patient.read([name])
        for role in ('nurse', 'dentist', 'manager'):
            clinical_patient = self.patient.with_user(self.role_users[role])
            self.assertEqual(clinical_patient.treatment_plan_count, 1)
            self.assertEqual(clinical_patient.prescription_count, 1)
            self.assertEqual(clinical_patient.appointment_count, 1)
            with self.assertRaises(AccessError):
                clinical_patient.read(['total_due'])
        accountant = new_test_user(
            self.env(su=True), login='dental_auth_accountant',
            groups=ROLE_GROUPS['manager'] + ',account.group_account_invoice',
        )
        invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id,
            'journal_id': self.journal.id, 'dental_patient_id': self.patient.id,
        })
        accounting_patient = self.patient.with_user(accountant)
        self.assertEqual(accounting_patient.invoice_count, 1)
        self.assertEqual(accounting_patient.total_invoiced, invoice.amount_total)
        self.assertEqual(accounting_patient.total_due, invoice.amount_residual)
        for model, view, button in (
            ('dental.patient', 'view_dental_patient_form', 'action_open_invoices'),
            ('dental.treatment.plan', 'view_dental_treatment_plan_form', 'action_create_invoice'),
        ):
            arch = etree.fromstring(self.env[model].with_user(accountant).get_view(
                view_id=self.env.ref(f'dental_clinic.{view}').id, view_type='form',
            )['arch'])
            self.assertTrue(arch.xpath(f'//button[@name="{button}"]'))

    def test_manager_product_maintenance_boundary(self):
        for role in ('manager', 'system'):
            user = self.role_users[role]
            treatment = self.env['dental.treatment'].with_user(user).create({'name': f'{role} service', 'price': 25})
            self.assertEqual(treatment.product_id.type, 'service')
            treatment.write({'name': f'{role} renamed', 'price': 50})
            self.assertEqual(treatment.product_id.name, f'{role} renamed')
            self.assertEqual(treatment.product_id.list_price, 50)
        for role in ('frontdesk', 'nurse', 'warehouse', 'dentist'):
            with self.assertRaises(AccessError):
                self.env['product.product'].with_user(self.role_users[role]).create({'name': 'Denied', 'type': 'service'})

    def test_workflow_actions_enforce_orm_permissions(self):
        appointment = self.env['dental.appointment'].sudo().create(self._values('dental.appointment'))
        for role in ('frontdesk', 'manager', 'system'):
            record = appointment.with_user(self.role_users[role])
            for action, state in (
                ('action_confirm', 'confirmed'), ('action_check_in', 'checked_in'),
                ('action_done', 'done'), ('action_no_show', 'no_show'),
                ('action_cancel', 'cancel'), ('action_draft', 'draft'),
            ):
                getattr(record, action)()
                self.assertEqual(record.state, state)
        for role in ('nurse', 'dentist', 'warehouse', 'portal'):
            for action in ('action_confirm', 'action_check_in', 'action_done', 'action_no_show', 'action_cancel', 'action_draft'):
                with self.assertRaises(AccessError):
                    getattr(appointment.with_user(self.role_users[role]), action)()
        self.env['dental.treatment.plan.line'].sudo().create(self._values('dental.treatment.plan.line'))
        for role in ('dentist', 'manager', 'system'):
            plan = self.plan.with_user(self.role_users[role])
            for action, state in (('action_confirm', 'confirmed'), ('action_start', 'in_progress'), ('action_done', 'done'), ('action_cancel', 'cancel'), ('action_draft', 'draft')):
                getattr(plan, action)()
                self.assertEqual(plan.state, state)
            prescription = self.prescription.with_user(self.role_users[role])
            for action, state in (('action_confirm', 'confirmed'), ('action_cancel', 'cancel'), ('action_draft', 'draft')):
                getattr(prescription, action)()
                self.assertEqual(prescription.state, state)
        for model, record, actions in (
            ('dental.treatment.plan', self.plan, ('action_confirm', 'action_start', 'action_done', 'action_cancel', 'action_draft')),
            ('dental.prescription', self.prescription, ('action_confirm', 'action_cancel', 'action_draft')),
        ):
            for role in ('frontdesk', 'nurse', 'warehouse', 'portal'):
                for action in actions:
                    with self.subTest(role=role, model=model, action=action), self.assertRaises(AccessError):
                        getattr(record.with_user(self.role_users[role]), action)()

    def test_reminder_permission_and_transaction_boundary(self):
        appointment = self.env['dental.appointment'].sudo().create(self._values('dental.appointment'))
        appointment.patient_id.email = 'auth-patient@example.invalid'
        template = self.env.ref('dental_clinic.mail_template_dental_appointment_reminder')
        # No mail is delivered. Synthetic queue records test the existing
        # write boundary, including rollback of pre-write template effects.
        def queue_fixture_mail(*args, **kwargs):
            return self.env['mail.mail'].sudo().create({
                'subject': 'Auth reminder rollback', 'body_html': '<p>Auth fixture</p>',
                'email_to': 'nobody@example.invalid',
            }).id

        with patch.object(type(template), 'send_mail', side_effect=queue_fixture_mail) as send_mail:
            for role in ('frontdesk', 'manager', 'system'):
                record = appointment.with_user(self.role_users[role])
                record.action_send_reminder()
                self.assertTrue(record.reminder_sent)
            for role in ('nurse', 'dentist', 'warehouse', 'portal'):
                before = self.env['mail.mail'].sudo().search_count([('subject', '=', 'Auth reminder rollback')])
                with self.assertRaises(AccessError), self.cr.savepoint():
                    appointment.with_user(self.role_users[role]).action_send_reminder()
                self.assertEqual(self.env['mail.mail'].sudo().search_count([('subject', '=', 'Auth reminder rollback')]), before)
            self.assertTrue(send_mail.called)

    def test_portal_arbitrary_and_own_backend_records_denied(self):
        user = self.role_users['portal']
        for patient in (self.patient, self.portal_patient):
            with self.assertRaises(AccessError):
                patient.with_user(user).read(['name'])
        with self.assertRaises(AccessError):
            self.env['dental.patient'].with_user(user).search([])

    def test_company_restrictions_cover_children_and_operations(self):
        company = self.env['res.company'].sudo().create({'name': 'Auth other company'})
        for model in ('dental.appointment', 'dental.treatment.plan', 'dental.prescription'):
            values = {**self._values(model), 'company_id': company.id}
            record = self.env[model].sudo().create(values)
            for role in ('frontdesk', 'nurse', 'dentist', 'manager', 'system'):
                actor = record.with_user(self.role_users[role]).with_context(allowed_company_ids=self.company.ids)
                create_values = dict(values)
                if model == 'dental.appointment':
                    create_values.update(start='2030-01-02 08:00:00', stop='2030-01-02 08:30:00')
                with self.assertRaises(AccessError), self.cr.savepoint():
                    self.env[model].with_env(actor.env).create(create_values)
                with self.assertRaises(AccessError):
                    actor.read(['name'])
                with self.assertRaises(AccessError):
                    actor.write({'state': 'cancel'})
                with self.assertRaises(AccessError):
                    actor.unlink()
                if self.env[model].with_env(actor.env).has_access('read'):
                    self.assertNotIn(record.id, self.env[model].with_env(actor.env).search([]).ids)
                else:
                    with self.assertRaises(AccessError):
                        self.env[model].with_env(actor.env).search([])
            child_model, inverse = {
                'dental.treatment.plan': ('dental.treatment.plan.line', 'plan_id'),
                'dental.prescription': ('dental.prescription.line', 'prescription_id'),
            }.get(model, (None, None))
            if child_model:
                child_values = {**self._values(child_model), inverse: record.id}
                child = self.env[child_model].sudo().create(child_values)
                with self.assertRaises(AccessError), self.cr.savepoint():
                    self.env[child_model].with_user(self.role_users['manager']).create(child_values)
                with self.assertRaises(AccessError):
                    child.with_user(self.role_users['manager']).read(['id'])
                with self.assertRaises(AccessError):
                    child.with_user(self.role_users['manager']).write({'sequence': 20})
                with self.assertRaises(AccessError):
                    child.with_user(self.role_users['manager']).unlink()
