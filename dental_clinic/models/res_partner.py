# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Core removed the separate mobile field; keep the baseline Dental contact value.
    mobile = fields.Char(string='Mobile')

    is_dental_patient = fields.Boolean(string='Is Dental Patient')
    dental_patient_id = fields.One2many('dental.patient', 'partner_id', string='Patient Record')
