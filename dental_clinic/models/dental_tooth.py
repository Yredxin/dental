# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DentalTooth(models.Model):
    _name = 'dental.tooth'
    _description = 'Tooth (Odontogram entry)'
    _order = 'patient_id, tooth_number'

    patient_id = fields.Many2one('dental.patient', required=True, ondelete='cascade', index=True)
    tooth_number = fields.Integer(required=True, help='FDI numbering 11-48.')
    name = fields.Char(required=True)
    quadrant = fields.Selection([
        ('ur', 'Upper Right'), ('ul', 'Upper Left'),
        ('lr', 'Lower Right'), ('ll', 'Lower Left'),
    ], compute='_compute_quadrant', store=True)
    condition = fields.Selection([
        ('healthy', 'Healthy'),
        ('caries', 'Caries'),
        ('filled', 'Filled'),
        ('crown', 'Crown'),
        ('root_canal', 'Root Canal'),
        ('extracted', 'Extracted'),
        ('missing', 'Missing'),
        ('implant', 'Implant'),
        ('bridge', 'Bridge'),
        ('to_extract', 'To Extract'),
    ], default='healthy', required=True)
    surface = fields.Selection([
        ('o', 'Occlusal'), ('m', 'Mesial'), ('d', 'Distal'),
        ('b', 'Buccal'), ('l', 'Lingual'),
    ], help='Affected surface.')
    notes = fields.Text()
    last_treatment_date = fields.Date()

    _tooth_uniq = models.Constraint(
        'UNIQUE(patient_id, tooth_number)', 'A tooth number must be unique per patient.'
    )

    @api.depends('tooth_number')
    def _compute_quadrant(self):
        for rec in self:
            n = rec.tooth_number or 0
            if 11 <= n <= 18:
                rec.quadrant = 'ur'
            elif 21 <= n <= 28:
                rec.quadrant = 'ul'
            elif 31 <= n <= 38:
                rec.quadrant = 'll'
            elif 41 <= n <= 48:
                rec.quadrant = 'lr'
            else:
                rec.quadrant = False
