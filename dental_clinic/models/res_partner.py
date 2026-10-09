# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Core removed the separate mobile field; keep the baseline Dental contact value.
    mobile = fields.Char(string='Mobile')

    is_dental_patient = fields.Boolean(string='Is Dental Patient')
    dental_patient_id = fields.One2many('dental.patient', 'partner_id', string='Patient Record')

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        dental_view = self.env.ref('dental_clinic.res_partner_view_dental_registration', raise_if_not_found=False)
        if view_type == 'form' and dental_view and view.id == dental_view.id:
            # partner_autocomplete replaces every form's name widget in its
            # _get_view override. Only this Dental variant uses a plain text
            # input; it has no company enrichment/IAP requirement.
            for node in arch.xpath("//field[@name='name']"):
                node.set('widget', 'char')
        return arch, view
