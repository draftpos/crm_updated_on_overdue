# -*- coding: utf-8 -*-
from odoo import models, api

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def _touch_leads(self, lead_ids):
        if lead_ids:
            self.env.cr.execute(
                "UPDATE crm_lead SET write_date = NOW() AT TIME ZONE 'UTC', write_uid = %s WHERE id IN %s",
                (self.env.uid, tuple(set(lead_ids)),)
            )
            self.env['crm.lead'].browse(lead_ids).invalidate_recordset(['write_date', 'write_uid'])

    @api.model_create_multi
    def create(self, vals_list):
        activities = super().create(vals_list)
        lead_ids = []
        for act in activities:
            if act.res_model == 'crm.lead' and act.res_id:
                lead_ids.append(act.res_id)
                if act.date_deadline:
                    lead = self.env['crm.lead'].browse(act.res_id)
                    if lead.exists():
                        open_acts = lead.activity_ids.filtered(lambda a: a.date_deadline)
                        earliest_date = min(open_acts.mapped('date_deadline')) if open_acts else act.date_deadline
                        if lead.custom_next_contact_date != earliest_date:
                            lead.with_context(skip_ensure_activity=True).sudo().write({'custom_next_contact_date': earliest_date})
        self._touch_leads(lead_ids)
        return activities

    def write(self, vals):
        res = super().write(vals)
        lead_ids = [act.res_id for act in self if act.res_model == 'crm.lead' and act.res_id]
        if 'date_deadline' in vals:
            for act in self:
                if act.res_model == 'crm.lead' and act.res_id:
                    lead = self.env['crm.lead'].browse(act.res_id)
                    if lead.exists():
                        open_acts = lead.activity_ids.filtered(lambda a: a.date_deadline)
                        if open_acts:
                            earliest_date = min(open_acts.mapped('date_deadline'))
                            if lead.custom_next_contact_date != earliest_date:
                                lead.with_context(skip_ensure_activity=True).sudo().write({'custom_next_contact_date': earliest_date})
        self._touch_leads(lead_ids)
        return res

    def unlink(self):
        lead_ids = [act.res_id for act in self if act.res_model == 'crm.lead' and act.res_id]
        res = super().unlink()
        if lead_ids:
            for lead in self.env['crm.lead'].browse(lead_ids).exists():
                remaining = lead.activity_ids.filtered(lambda a: a.date_deadline)
                if remaining:
                    min_date = min(remaining.mapped('date_deadline'))
                    if lead.custom_next_contact_date != min_date:
                        lead.with_context(skip_ensure_activity=True, skip_next_contact_check=True).sudo().write({'custom_next_contact_date': min_date})
                else:
                    if lead.custom_next_contact_date:
                        lead.with_context(skip_ensure_activity=True, skip_next_contact_check=True).sudo().write({'custom_next_contact_date': False})
            self._touch_leads(lead_ids)
        return res
