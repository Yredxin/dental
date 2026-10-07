# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DentalTreatment(models.Model):
    _name = 'dental.treatment'
    _description = 'Dental Treatment / Service Catalog'
    _order = 'category, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    category = fields.Selection([
        ('preventive', 'Preventive'),
        ('restorative', 'Restorative'),
        ('endodontic', 'Endodontic'),
        ('periodontic', 'Periodontic'),
        ('prosthetic', 'Prosthetic'),
        ('orthodontic', 'Orthodontic'),
        ('surgical', 'Surgical'),
        ('cosmetic', 'Cosmetic'),
        ('diagnostic', 'Diagnostic'),
        ('other', 'Other'),
    ], default='preventive', required=True)
    duration = fields.Float(string='Default Duration (h)', default=0.5)
    description = fields.Text()
    product_id = fields.Many2one(
        'product.product', string='Linked Product/Service',
        domain=[('type', '=', 'service')],
        help='Used for invoicing. Auto-created if empty.',
    )
    price = fields.Float(string='Standard Price', default=0.0)
    requires_tooth = fields.Boolean(string='Tooth-Specific', default=True)
    active = fields.Boolean(default=True)
    color = fields.Integer()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.product_id:
                product = self.env['product.product'].create({
                    'name': rec.name,
                    'type': 'service',
                    'list_price': rec.price,
                    'default_code': rec.code or False,
                })
                rec.product_id = product.id
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.product_id and ('price' in vals or 'name' in vals):
                rec.product_id.write({
                    'list_price': rec.price,
                    'name': rec.name,
                })
        return res
