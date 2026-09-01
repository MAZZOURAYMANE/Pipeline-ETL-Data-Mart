from odoo import models, fields,api

class CommissionCRUI(models.Model):
    _name = 'commission.crui'
    _description = 'Commission CRUI'

    name = fields.Char(string="Nom de la commission", required=True)
    date_passage = fields.Datetime(string="Date de passage", required=True)
    membre_ids = fields.Many2many('res.partner', string="Membres de la commission")
    dossier_id = fields.Many2one('dossier', string="Dossier concerné", ondelete="cascade")
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.dossier_id:
            res.dossier_id.date_passage = res.date_passage
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'date_passage' in vals and self.dossier_id:
            self.dossier_id.date_passage = vals['date_passage']
        return res