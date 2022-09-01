# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class SaleOrderAttachements(models.Model):
    _inherit = "sale.order"

    @api.one
    def _compute_attachements(self):
        '''
            This function computes the number of attachement documents for a given sale order.
        '''
        attachements = self.env['ir.attachment']

        for record in self:
            record.attachements_count = attachements.search_count(
                [('res_model', '=', 'sale.order'), ('res_id', '=', record.id)])






    @api.multi
    def attachement_document_action(self):
        '''This function returns an action that display attahcements generated from a given sale order.'''
        return {
            'name': _('Sale order attachements'),
            'view_mode': 'tree,form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('res_model', '=', 'sale.order'),('res_id', '=', self.id)],
        }

    attachements_count = fields.Integer(compute='_compute_attachements', string='Attachements')



