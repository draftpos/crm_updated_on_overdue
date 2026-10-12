/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";

export class CrmLeadFormController extends FormController {
    async save(params) {
        const record = this.model.root;
        const saved = await super.save(params);
        if (saved && record.resModel === "crm.lead" && record.resId) {
            // Do not popup activity schedule if lead already has a scheduled site visit
            const hasOpenSiteVisit = ['open', 'rescheduled'].includes(record.data.site_visit_state);
            const siteVisitRecords = record.data.site_visit_ids && record.data.site_visit_ids.records;
            const hasSiteVisits = Boolean(hasOpenSiteVisit || (siteVisitRecords && siteVisitRecords.length > 0));

            // If lead is active and has no next contact date AND no site visit, pop up Activity Schedule
            if (record.data.active && !record.data.custom_next_contact_date && !hasSiteVisits) {
                await this.actionService.doAction({
                    type: "ir.actions.act_window",
                    name: "Schedule an Activity",
                    res_model: "mail.activity.schedule",
                    view_mode: "form",
                    views: [[false, "form"]],
                    target: "new",
                    context: {
                        active_model: "crm.lead",
                        active_id: record.resId,
                        active_ids: [record.resId],
                        dialog_size: "large",
                    },
                }, {
                    onClose: async () => {
                        await record.load();
                    },
                });
            }
        }
        return saved;
    }
}

export const crmLeadFormView = {
    ...formView,
    Controller: CrmLeadFormController,
};

registry.category("views").add("crm_lead_form", crmLeadFormView);
