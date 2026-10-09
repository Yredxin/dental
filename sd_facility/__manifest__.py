{
    'name': 'Facility Management',
    'version': '20.0.1.0.0',
    'category': 'Administration',
    'summary': 'Company-owned facilities, floors, areas and resource-backed workstations',
    'license': 'LGPL-3',
    'author': 'SD',
    'depends': ['resource'],
    'data': [
        'security/sd_facility_security.xml',
        'security/ir.access.csv',
        'views/sd_facility_space_views.xml',
        'views/sd_facility_station_views.xml',
        'views/sd_facility_menus.xml',
    ],
    'application': True,
    'installable': True,
}
