# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalPrescriptionLine(models.Model):
    _name = 'dental.prescription.line'
    _description = 'Prescription Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    prescription_id = fields.Many2one('dental.prescription', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Medicine',
                                 domain=[('type', '=', 'consu')])
    name = fields.Char(string='Medicine Name', required=True)
    dosage = fields.Char(help='e.g. 500mg')
    frequency = fields.Char(help='e.g. 3 times a day')
    duration = fields.Char(help='e.g. 7 days')
    quantity = fields.Float(default=1.0)
    instructions = fields.Text()
