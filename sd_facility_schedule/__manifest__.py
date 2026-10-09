{
    'name': 'Facility Workstation Scheduling',
    'version': '20.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Concrete employee assignments to workstations',
    'author': 'SD',
    'license': 'LGPL-3',
    'depends': ['hr', 'sd_facility'],
    'data': [
        'security/sd_facility_schedule_security.xml',
        'security/ir.access.csv',
        'views/sd_facility_assignment_views.xml',
        'views/sd_facility_schedule_menus.xml',
    ],
    'installable': True,
    'application': False,
}
