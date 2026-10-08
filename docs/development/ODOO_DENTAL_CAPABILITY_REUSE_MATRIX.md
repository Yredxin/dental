# Odoo 20 / SD Dental capability reuse matrix

Source inspection date: 2026-10-08 (Asia/Shanghai). **32 areas reviewed**: the 31
requested initial categories plus an explicitly deferred clinical-visit area.
This is a decision framework and source inventory, not a future schema design
or permission to implement any row.

## Evidence scope and decision vocabulary

- Odoo Community reference: `D:/odoo-sd/odoo20-clean`, branch `20.0`, commit
  `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`. Odoo paths below are relative to this
  checkout. Its clean status and actual implementations were inspected. This
  reference is not asserted to be the exact source commit of the runtime image.
- Dental: `D:/Code/odoo/dental`, branch `port/odoo20-demo`, commit
  `d2c766a498d523f704ac95303b1227c1fd40a551`. Dental paths below are repository-relative.
- SD: `D:/Code/odoo/odoo-sd`, branch `main`, commit
  `bf6d30035701159f968f8c5901b38d186fa48521`. Actual `addons/` contains only
  `README.md`; **no SD addon implementation exists there**. Existing deployment
  changes were read only and are not capabilities attributed to an SD addon.
- Dental's manifest directly depends on `base`, `mail`, `contacts`, `product`,
  `account`, `calendar`. Presence in Odoo source does **not** establish that an
  optional module is installed or configured in the development database. No
  live database capability audit was performed.

Every strategy cell is exactly one of `USE`, `CONFIGURE`, `EXTEND`, `WRAP`, `NEW`,
`DEFER`. Prefer `USE -> CONFIGURE -> EXTEND -> WRAP -> NEW`; `DEFER` means a
separate audit/design decision is needed, not permission for a new capability.
Recommendations apply to the named area, not automatically to all related
future features. Evidence IDs identify actual inspected files and symbols below.

## Initial matrix

| Requirement Area | Existing Odoo Capability | Existing Dental Capability | Recommended Strategy | Notes |
| --- | --- | --- | --- | --- |
| Users | `res.users`, delegated `res.partner` identity [O01](#o01-identity) | `dental.practitioner.user_id` [D01](#d01-patients-and-practitioners) | USE | Keep authentication and user identity in Odoo; a practitioner is an existing clinical record. |
| Employees | `hr.employee`, employee and resource mixins [O02](#o02-employees) | `dental.practitioner`; no `employee_id` or HR dependency [D01](#d01-patients-and-practitioners) | CONFIGURE | HR is optional. DESIGN REVIEW REQUIRED before choosing any practitioner-to-employee linkage; no migration now. |
| Contacts | `res.partner` [O01](#o01-identity) | `res.partner` extension and patient contact-related fields [D01](#d01-patients-and-practitioners) | USE | Preserve existing partner identity and Dental's compatibility `mobile` field. |
| Dental patients | Partner contact master [O01](#o01-identity) | `dental.patient`, required `partner_id`, clinical history [D01](#d01-patients-and-practitioners) | EXTEND | Extend the maintained patient record for approved clinical needs; no second contact master. |
| Appointments/calendar | `calendar.event`, Web calendar view [O03](#o03-calendar-and-work) | `dental.appointment`, `start`/`stop`, state actions, overlap constraint, calendar XML view [D02](#d02-appointments-and-messaging) | EXTEND | Appointment uses a calendar view, not `calendar.event` inheritance or synchronization. DESIGN REVIEW REQUIRED before adding synchronization or changing representation. |
| Activities/tasks | `mail.activity`, `mail.activity.mixin.activity_schedule`; `project.task` [O03](#o03-calendar-and-work) | Activity mixin on patient, appointment, plan, prescription [D01](#d01-patients-and-practitioners), [D03](#d03-clinical-catalog-and-planning), [D04](#d04-prescriptions) | USE | Use existing activities for follow-up; project tasks are optional and are not clinical visits. |
| Chatter | `mail.thread.message_post` [O04](#o04-mail) | Existing `mail.thread` inheritance and `<chatter/>` [D01](#d01-patients-and-practitioners), [D02](#d02-appointments-and-messaging) | USE | Use framework tracking/messages rather than a parallel conversation store. |
| Attachments/filestore | `ir.attachment`, `_storage`, `_filestore`, `_file_*` [O05](#o05-attachments) | Standard mail/thread attachment mechanisms available through existing inheritance; no separate attachment engine [D01](#d01-patients-and-practitioners) | USE | Keep attachment access and storage within Odoo. Clinical exposure rules need feature-level security review. |
| Products | `product.product`, `product.template` [O06](#o06-catalog-and-suppliers) | Treatment and prescription lines already link products [D03](#d03-clinical-catalog-and-planning), [D04](#d04-prescriptions) | USE | Avoid a second product master. |
| Services | Product `type='service'` [O06](#o06-catalog-and-suppliers) | `dental.treatment.product_id`; `create` creates a service and `write` synchronizes name/price [D03](#d03-clinical-catalog-and-planning) | USE | Reuse this existing service/billing link; do not redesign synchronization here. |
| Inventory | `stock.quant`, `stock.location`; product `is_storable` [O07](#o07-stock) | No stock dependency or inventory implementation in Dental [D00](#d00-module-scope) | CONFIGURE | Optional stock installation/settings are future work. DESIGN REVIEW REQUIRED for treatment consumption; catalog type alone does not establish tracked stock. |
| Stock movement | `stock.move`, `stock.move.line`, `stock.picking`; reservation/completion lifecycle [O07](#o07-stock) | No Dental stock moves or consumption hooks [D00](#d00-module-scope), [D03](#d03-clinical-catalog-and-planning) | USE | Reuse the movement engine. DESIGN REVIEW REQUIRED for clinical trigger, reversals, units and traceability; no custom stock ledger. |
| Purchasing | `purchase.order`, `purchase_stock._create_picking` [O08](#o08-purchasing) | No purchasing workflow [D00](#d00-module-scope) | CONFIGURE | Optional modules; reuse purchase/receipt integration rather than create a purchasing engine. |
| Suppliers | `res.partner`, `product.supplierinfo`, `seller_ids` [O01](#o01-identity), [O06](#o06-catalog-and-suppliers) | Existing patient partners are not a separate supplier system [D01](#d01-patients-and-practitioners) | USE | Configure vendor records and supplier prices; no independent supplier master. |
| Medicines | Product catalog and goods type [O06](#o06-catalog-and-suppliers) | `dental.prescription.line.product_id` restricted to `type='consu'`, plus free-text name, dose and instructions [D04](#d04-prescriptions) | EXTEND | DESIGN REVIEW REQUIRED for regulated medicine attributes or dispensing. Current product link is optional; no new medicine master or dispensing design now. |
| Email | `mail.template.send_mail`, `mail.mail`, email queue cron [O04](#o04-mail) | Appointment reminder template and `action_send_reminder(force_send=False)` [D02](#d02-appointments-and-messaging) | CONFIGURE | Configure templates/transport when authorized. Existing dev environment suppresses background delivery; no messages sent by this audit. |
| SMS | `sms.sms`, `sms.template`, `_process_queue`, `SmsApiBase`, provider selection [O09](#o09-sms) | No SMS dependency or provider; appointment reminder is email [D00](#d00-module-scope), [D02](#d02-appointments-and-messaging) | WRAP | DESIGN REVIEW REQUIRED for an Aliyun adapter. Inspect both `_split_by_api` and `_get_sms_api_class`; the queue explicitly supplies its API. Reuse SMS domain/templates/queue. |
| Automation | `base.automation`, server actions, `ir.cron` [O10](#o10-automation-and-jobs) | Existing state methods, no separate automation engine [D02](#d02-appointments-and-messaging), [D03](#d03-clinical-catalog-and-planning) | CONFIGURE | Configure automation where sufficient; no alternate rule engine. Optional module availability and execution rights must be checked. |
| Accounting | `account.move`, `account.move.line`, journals and payments [O11](#o11-accounting-and-payments) | Accounting dependency, patient totals, plan invoice links [D05](#d05-billing) | USE | Use the Odoo ledger and receivables; localization/setup remains a separate task. |
| Invoice/account.move | `account.move`, invoice lines and `action_post` [O11](#o11-accounting-and-payments) | Inherited Dental patient/plan fields; `dental.invoice.wizard.action_create_invoice` creates `out_invoice` [D05](#d05-billing) | EXTEND | Extend the existing invoice integration; no parallel invoice object. |
| Payment | `account.payment` versus online `payment.provider` / `payment.transaction` [O11](#o11-accounting-and-payments) | No Dental-specific payment integration [D05](#d05-billing) | DEFER | DESIGN REVIEW REQUIRED to distinguish recording/reconciliation from external provider transport; no payment implementation. |
| Reports/PDF | `ir.actions.report`, `report_action`, `_render_qweb_pdf` [O12](#o12-reports) | QWeb patient card, prescription and treatment-plan reports [D06](#d06-security-reports-and-frontend) | EXTEND | Extend existing reports using QWeb; no separate PDF engine. |
| Security | Odoo 20 `res.groups`, `res.groups.privilege`, `ir.access` permissions/restrictions [O13](#o13-security) | Receptionist/dentist/manager groups, `ir.access.csv`, appointment company restriction [D06](#d06-security-reports-and-frontend) | EXTEND | Follow official security skills; do not transplant older `ir.model.access`/`ir.rule` APIs. This inventory is not a security certification. |
| Frontend widgets/Owl | Registry, field components, calendar view and Owl [O14](#o14-web) | Standard form/list/calendar widgets and odontogram CSS only [D06](#d06-security-reports-and-frontend) | EXTEND | Extend supported Odoo UI mechanisms; no standalone frontend infrastructure or SVG odontogram implementation. |
| Queues/jobs if available | `ir.cron`, email and SMS domain queues [O04](#o04-mail), [O09](#o09-sms), [O10](#o10-automation-and-jobs) | No generic job queue addon in Dental or SD roots [D00](#d00-module-scope), [S01](#s01-sd-addons) | DEFER | DESIGN REVIEW REQUIRED for generic job guarantees. No `queue_job` or `job_queue` module found in the inspected roots; cron is not proof of a general durable job system. |
| Portal | `portal.mixin`, `CustomerPortal._document_check_access` [O15](#o15-portal-and-website) | Dental clinical models do not inherit `portal.mixin`; no Dental controllers [D00](#d00-module-scope) | DEFER | DESIGN REVIEW REQUIRED for patient identity, permissions and record exposure. Generic portal capability does not expose Dental records safely by default. |
| Website/H5 relevant capabilities | `website`, standard HTTP routes, portal and Web assets [O15](#o15-portal-and-website) | No Dental website/H5 flow; static module description is not a patient application [D00](#d00-module-scope) | DEFER | DESIGN REVIEW REQUIRED for use cases/authentication. A separate H5 stack is not pre-approved. |
| Dental tooth model | ORM/fields and existing view mechanisms [O14](#o14-web) | `dental.tooth`, patient/tooth unique constraint, FDI numbering and patient initialization [D07](#d07-teeth) | EXTEND | Preserve current numbering and patient relation where practical; no SVG work or new tooth model. |
| Treatment | Standard service product and billing [O06](#o06-catalog-and-suppliers) | `dental.treatment` clinical service catalog [D03](#d03-clinical-catalog-and-planning) | EXTEND | Catalog is not proof of a distinct treatment execution record. Execution semantics require separate design audit. |
| Treatment plan | Odoo mail/activity/currency/accounting infrastructure [O03](#o03-calendar-and-work), [O11](#o11-accounting-and-payments) | `dental.treatment.plan`, `.line`, states, tooth/treatment links, totals and invoicing flags [D03](#d03-clinical-catalog-and-planning) | EXTEND | Preserve current semantics. `action_done` marks lines done; do not equate that with a new execution schema or stock consumption. |
| Prescription | Products, mail/activity and QWeb [O06](#o06-catalog-and-suppliers), [O12](#o12-reports) | `dental.prescription`, `.line`, appointment link and print action [D04](#d04-prescriptions) | EXTEND | DESIGN REVIEW REQUIRED for any prescription redesign or dispensing changes; reuse the existing document first. |
| Clinical encounter / visit representation | Inspect framework and existing domain workflows in a separate audit | Existing appointment, plan and prescription relations [D02](#d02-appointments-and-messaging), [D03](#d03-clinical-catalog-and-planning), [D04](#d04-prescriptions) | DEFER | Clinical encounter / visit representation: requires separate reuse/design audit. No conclusion that `dental.encounter` must be created. |

## Inspected Odoo source evidence

### O01 Identity

`odoo/addons/base/models/res_users.py`: `res.users`, `_inherits` to `res.partner`
via `partner_id`; `odoo/addons/base/models/res_partner.py`: `res.partner` contact
fields. These are the identity/contact masters already consumed by Dental.

### O02 Employees

`addons/hr/models/hr_employee.py`: `hr.employee`, resource and mail mixins;
`addons/hr/__manifest__.py`: employee module dependencies. No HR dependency was
found in Dental's manifest; HR availability is source evidence, not installation evidence.

### O03 Calendar and work

`addons/calendar/models/calendar_event.py`: `calendar.event`, start/stop and mail
mixins; `addons/mail/models/mail_activity.py`: `mail.activity`;
`addons/mail/models/mail_activity_mixin.py`: `activity_schedule`;
`addons/project/models/project_task.py`: `project.task` and its mixins;
`addons/web/static/src/views/calendar/calendar_view.js`: calendar view registry.

### O04 Mail

`addons/mail/models/mail_thread.py`: `mail.thread.message_post`;
`addons/mail/models/mail_template.py`: `send_mail` with `force_send=False` default;
`addons/mail/models/mail_mail.py`: outgoing email implementation;
`addons/mail/data/ir_cron_data.xml`: `mail.ir_cron_mail_scheduler_action` calls
`process_email_queue(batch_size=1000)`.

### O05 Attachments

`odoo/addons/base/models/ir_attachment.py`: `ir.attachment`, `_storage`, `_filestore`,
`_file_fname`, `_file_read`, `_file_write`, `_full_path`. Actual file/DB storage and
filestore path construction were inspected, not inferred from the model name.

### O06 Catalog and suppliers

`addons/product/models/product_product.py`: `product.product`;
`addons/product/models/product_template.py`: `product.template`, `type` values
`consu`/`service`/`combo`, `is_storable`, `seller_ids`;
`addons/product/models/product_supplierinfo.py`: `product.supplierinfo.partner_id`.
`consu` means goods in this revision; inventory tracking is a separate flag.

### O07 Stock

`addons/stock/models/stock_location.py`: `stock.location`;
`addons/stock/models/stock_quant.py`: `stock.quant`, `_update_available_quantity`;
`addons/stock/models/stock_move.py`: `stock.move`, `_action_confirm`,
`_action_assign`, `_action_done` calling move-line completion;
`addons/stock/models/stock_picking.py`: `stock.picking`, `_action_done`;
`addons/stock/models/product.py`: stock-aware product behavior.
Private lifecycle methods are inspection evidence, not an instruction to bypass
standard workflows or write directly to quants.

### O08 Purchasing

`addons/purchase/models/purchase_order.py`: `purchase.order`, `button_confirm`;
`addons/purchase_stock/models/purchase_order.py`: `_create_picking`, order-line
`_create_stock_moves` call, move confirmation and assignment. This is an existing
purchase-to-stock integration.

### O09 SMS

`addons/sms/models/sms_sms.py`: `sms.sms`, `_split_by_api`, `_process_queue`,
`_send`, `_send_with_api`; `addons/sms/models/sms_template.py`: `sms.template`;
`addons/sms/tools/sms_api.py`: `SmsApiBase._send_sms_batch`, default IAP `SmsApi`;
`addons/sms/models/res_company.py`: `_get_sms_api_class`;
`addons/sms/data/ir_cron_data.xml`: `sms.ir_cron_sms_scheduler_action`.
In this snapshot `_split_by_api` yields `SmsApi(self.env)` directly and the queue
passes it through context. Overriding only the company's API selector would not
establish coverage of queued dispatch. Transport design must inspect both paths.

### O10 Automation and jobs

`addons/base_automation/models/base_automation.py`: `base.automation`, trigger
choices and `action_server_ids`;
`odoo/addons/base/models/ir_cron.py`: `ir.cron`, `_process_jobs` and batching.
Directory/file searches of Odoo `addons/`, Dental and SD addon roots found no
`queue_job` or `job_queue` module. This is bounded negative evidence, not a claim
that no third-party job addon exists elsewhere.

### O11 Accounting and payments

`addons/account/models/account_move.py`: `account.move`, `move_type`, invoice lines,
`action_post` and `_post`; `addons/account/models/account_move_line.py`:
`account.move.line`; `addons/account/models/account_payment.py`: `account.payment`;
`addons/payment/models/payment_provider.py`: `payment.provider`;
`addons/payment/models/payment_transaction.py`: `payment.transaction` and
post-processing. Accounting payments and external provider transactions are
distinct existing capabilities, not a reason to invent another ledger.

### O12 Reports

`odoo/addons/base/models/ir_actions_report.py`: `ir.actions.report`,
`_render_qweb_pdf`, `report_action`. Dental report actions select `qweb-pdf`.

### O13 Security

`odoo/addons/base/models/res_groups.py`: `res.groups`;
`odoo/addons/base/models/ir_access.py`: `ir.access`, `operation`, `group_id`,
`domain`, computed permission/restriction `kind`. Dental's group privilege and
access records match this Odoo 20 mechanism. Detailed review follows the official
security skill; this inventory does not assess every grant or RPC method.

### O14 Web

`addons/web/static/src/core/registry.js`;
`addons/web/static/src/views/fields/char/char_field.js`: `CharField` extends Owl
`Component`, `registry.category("fields").add("char", ...)`;
`addons/web/static/src/views/calendar/calendar_view.js`: view registration.
Use the official web guidelines for supported extension details at this revision.

### O15 Portal and website

`addons/portal/models/portal_mixin.py`: `portal.mixin`, access token/URL and
`_get_share_url`; `addons/portal/controllers/portal.py`:
`CustomerPortal._document_check_access`;
`addons/website/models/website.py`: `website`;
`addons/website/controllers/main.py`: website routes and authentication;
`addons/website/__manifest__.py`: website/Web/portal dependencies.

## Inspected Dental and SD source evidence

### D00 Module scope

`dental_clinic/__manifest__.py`, `models/__init__.py` and a complete module file
inventory. Direct dependencies and assets were read; there is no Dental stock,
purchase, SMS, website, HR or generic-job implementation or controller directory
in this baseline. Transitive Odoo dependencies are not a Dental clinical feature.

### D01 Patients and practitioners

`dental_clinic/models/dental_patient.py`: `dental.patient`, contact-related fields,
mail/activity mixins, clinical relations and `_create_odontogram`;
`dental_clinic/models/res_partner.py`: `is_dental_patient`, `dental_patient_id`,
compatibility `mobile`; `dental_clinic/models/dental_practitioner.py`: `user_id`,
clinical speciality and license fields, no employee link;
`dental_clinic/views/dental_patient_views.xml`: standard widgets and chatter.

### D02 Appointments and messaging

`dental_clinic/models/dental_appointment.py`: model, start/stop, state actions,
`_check_overlap`, `plan_id`, `treatment_ids`, `action_send_reminder`;
`dental_clinic/views/dental_appointment_views.xml`:
`view_dental_appointment_calendar`, `date_start="start"`, `date_stop="stop"`;
`dental_clinic/data/mail_template_data.xml`:
`dental_clinic.mail_template_dental_appointment_reminder` (referenced by the method).

### D03 Clinical catalog and planning

`dental_clinic/models/dental_treatment.py`: product relation, `create` and `write`;
`dental_clinic/models/dental_treatment_plan.py`: mail/activity mixins, workflow,
`action_done`, invoice relations and invoice wizard action;
`dental_clinic/models/dental_treatment_plan_line.py`: tooth/treatment relations,
quantity, price, state, schedule and invoiced flag. These were read as existing
semantics, not proposals for treatment execution.

### D04 Prescriptions

`dental_clinic/models/dental_prescription.py`: patient, practitioner and
`appointment_id`, confirmation and `action_print`;
`dental_clinic/models/dental_prescription_line.py`: optional product relation,
required free-text name, dosage/frequency/duration/quantity/instructions.

### D05 Billing

`dental_clinic/models/account_move.py`: inherited patient/plan links;
`dental_clinic/wizards/dental_invoice_wizard.py`: `action_create_invoice`, product
invoice lines, `move_type='out_invoice'`, partner/journal and plan linkage;
`dental_clinic/models/dental_patient.py`: invoice totals and residuals.

### D06 Security reports and frontend

`dental_clinic/security/dental_security.xml`: Dental privilege/groups,
`rule_dental_appointment_user` as `ir.access`;
`dental_clinic/security/ir.access.csv`: `operation` grants;
`dental_clinic/report/dental_reports.xml`: three `qweb-pdf` actions;
`dental_clinic/views/dental_patient_views.xml` and
`dental_clinic/views/dental_appointment_views.xml`: standard widgets/chatter;
`dental_clinic/__manifest__.py`: only `static/src/css/odontogram.css` in backend
assets. The static file inventory contains no custom JS/Owl component.

### D07 Teeth

`dental_clinic/models/dental_tooth.py`: patient relation, FDI `tooth_number`,
condition/surface, `_compute_quadrant` and unique patient/tooth constraint;
`dental_clinic/models/dental_patient.py`: `_create_odontogram` generates adult
FDI teeth for each new patient. No new odontogram design is proposed.

### S01 SD addons

`D:/Code/odoo/odoo-sd/addons/README.md` and complete directory inventory: no SD
addon source is present. Names such as `sd_sms_aliyun` and `sd_payment` in the
policy are examples of placement for future approved integrations.

## Areas requiring a later human design decision

Employee/practitioner linkage; appointment/calendar synchronization; treatment
consumption and stock movement triggers; medicine/dispensing semantics; SMS
provider transport; payment flow; generic job guarantees; clinical portal/H5
exposure; treatment execution; prescription redesign; clinical encounter / visit
representation. Each needs its own source-backed reuse audit and scoped human
decision. None of these decisions or implementations is made by this matrix.
