# -*- coding: utf-8 -*-
{
    'name': 'Dental Clinic Management',
    'version': '20.0.2.0.0',
    'category': 'Healthcare',
    'summary': 'Complete dental clinic management: patients, appointments, treatments, odontogram, prescriptions, billing.',
    'description': """
Dental Clinic Management for Odoo 20
=====================================
Features:
  * Patient files with medical history and allergies
  * Practitioners and rooms / dental chairs
  * Appointment scheduling (calendar)
  * Treatment catalog (services) and treatment plans
  * Interactive odontogram (32 teeth) with tooth conditions
  * Prescriptions with printable PDF
  * Native integration with Odoo Invoicing (no insurance)
  * Independent Dental capabilities and optional permission profiles
  * Demo data ready to test
""",
    'author': 'souhaibouadi',
    'website': 'https://github.com/souhaibouadi/dental',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'contacts',
        'product',
        'account',
        'calendar',
        # Native public employee directory / HR Officer authority.
        'hr',
        'sd_facility',
        'sd_facility_schedule',
        # Direct user-menu registry dependency and asset load ordering.
        'mysubscription',
        # Direct menu reference; account already auto-installs its dashboards.
        'spreadsheet_dashboard',
    ],
    'data': [
        # 1) Security
        'security/dental_security.xml',
        'security/dental_facility_security.xml',
        'security/dental_schedule_security.xml',
        'security/ir.access.csv',
        # 2) Master / configuration data
        'data/ir_sequence_data.xml',
        'data/dental_tooth_data.xml',
        'data/mail_template_data.xml',
        'data/dental_permission_profile_data.xml',
        # 3) Reports
        'report/report_paperformat.xml',
        'report/dental_prescription_template.xml',
        'report/dental_treatment_plan_template.xml',
        'report/dental_patient_card_template.xml',
        'report/dental_reports.xml',
        # 4) Views & actions FIRST (must be loaded before menus that reference them)
        'views/res_partner_views.xml',
        'views/dental_patient_views.xml',
        'views/dental_practitioner_views.xml',
        'views/dental_room_views.xml',
        'views/dental_treatment_views.xml',
        'views/dental_appointment_views.xml',
        'views/dental_treatment_plan_views.xml',
        'views/dental_tooth_views.xml',
        'views/dental_prescription_views.xml',
        'wizards/dental_invoice_wizard_views.xml',
        'views/dental_permission_profile_views.xml',
        'wizards/dental_permission_apply_views.xml',
        'views/res_users_views.xml',
        'views/hr_employee_views.xml',
        # 5) Menus LAST (they reference actions defined above)
        'views/dental_menus.xml',
        'views/dental_facility_menus.xml',
    ],
    'demo': [
        'demo/dental_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dental_clinic/static/src/css/odontogram.css',
            'dental_clinic/static/src/user_menu/user_menu.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
