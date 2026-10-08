# REUSE-AUDIT-01: Dental clinical workflow capability reuse audit

Date: 2026-10-08 (Asia/Shanghai). **REUSE-AUDIT-01 = READY.**
This is a source-backed, read-only design audit. READY means the audit is
complete; it does not approve implementation or settle the deferred design
decisions. **Schema: NOT YET AUTHORIZED.**

## 1. Executive summary

Preserve the current patient, practitioner, appointment, tooth, treatment,
planning and prescription objects. Reuse Odoo for identity, products, files,
messages, activities, scheduling UI, email, accounting, inventory and reports.
The principal weakness is the separation of intention from clinical fact:
scheduled time is not arrival time, a plan is not proof of performance, and a
mutable document with a `done` state is not a finalized clinical record.

The 24 decisions below are **USE 9, CONFIGURE 1, EXTEND 8, WRAP 0, NEW 0,
DEFER 6**. Examination requests and verified results are missing clinical
responsibilities, but existing diagnostic plan lines and clinical documents
remain possible extension targets. No NEW decision is proved necessary yet.
Visit representation, structured examination, actual execution, examination
request/result representation and finalized visit records require human decisions. No `dental.encounter`
model is assumed or authorized.

### Preflight and evidence boundary

| Check | Verified evidence |
| --- | --- |
| Dental root | `D:/Code/odoo/dental`, verified with `git rev-parse --show-toplevel`. |
| Branch | `port/odoo20-demo`. |
| HEAD | Exactly `e56ffa41b6f3243d2208618c883f99c796e3a895`, the accepted SKILL-FOUNDATION-01 closure commit. |
| Initial worktree | Clean, including untracked files; no staged changes. |
| Business-source tree | `HEAD:dental_clinic` = `8c9a743ce8b1aa16284eff74f45b2b43b3e29d01`. |
| Skills | All five installed project skills were opened and applied. Accepted fresh Codex 0.138.0 `skills/list(forceReload=true)` evidence records all five enabled, `scope=repo`, no errors. Current local validation passed: 23 official files, five skills, 145 references and pinned-source comparison. This audit reuses the accepted discovery record; it does not claim another fresh harness scan. |
| Odoo reference | `D:/odoo-sd/odoo20-clean`, branch `20.0`, HEAD `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`; clean, verified with read-only Git status. |
| Dental manifest | `dental_clinic`, version `20.0.1.0.0`; direct dependencies `base`, `mail`, `contacts`, `product`, `account`, `calendar`. |
| SD source | `D:/Code/odoo/odoo-sd`, HEAD `bf6d30035701159f968f8c5901b38d186fa48521`; `addons/` contains only `README.md`, no implemented SD addons. Existing deployment changes were left untouched. |

Sources: [manifest](D:/Code/odoo/dental/dental_clinic/__manifest__.py),
[accepted discovery](D:/Code/odoo/dental/docs/development/ODOO_AGENT_SKILLS_DISCOVERY.json),
[skill verification](D:/Code/odoo/dental/docs/development/ODOO_AGENT_SKILLS_VERIFICATION.md),
[local validator](D:/Code/odoo/dental/docs/development/verify_agent_skills.py),
[existing capability matrix](D:/Code/odoo/dental/docs/development/ODOO_DENTAL_CAPABILITY_REUSE_MATRIX.md).
The matrix remains unchanged. Its Dental revision precedes the skills-only
closure commit; its business-source evidence remains applicable. Its broader
area decisions are refined here for the individual clinical responsibilities,
not treated as implementation permission or silently corrected.

The source snapshot's exact equivalence to the runtime Docker image remains
unestablished and NON-BLOCKING, as accepted at foundation closure. Source
availability does not prove that optional addons are installed or configured.
No database was accessed, no Odoo process or business action was run, and no
external provider/API call was made. The waived authentication failure
(`invalid_api_key`) remains NON-BLOCKING and was not retried.

Method: inspect all Dental models, wizard, access data, relevant views/reports
and their callers; compare the matrix; search local Community source and SD
addons; read the actual standard implementations closest to each requirement.
Negative findings are bounded to these local revisions, not Enterprise, OCA,
other private addons or the entire Odoo ecosystem. Model-name/description text
searches across `addons/` and `odoo/addons/` were supplemented by inspection of
calendar, project, event, survey and website-visitor semantics [O02, O03].

Guidance applied: `sd-odoo-dental`; `odoo-guidelines` ORM, fields, security,
stable changes, XML and reports sections; `odoo-web-guidelines` JavaScript
extension guidance; `odoo-security` access, field exposure and public-method
checks; `odoo-review` revision pinning, callers and counterexample review.
This is not a full security certification or runtime integration test.
The user explicitly requests DEFER as an allowed classification; that request
takes precedence over the project skill's narrower five-class audit vocabulary.

## 2. Current model map

| Existing object | Current responsibility and connections | Evidence |
| --- | --- | --- |
| `res.partner` + `dental.patient` | Partner owns contact identity. Patient requires `partner_id`, exposes related contact data, clinical background, appointments, plans, prescriptions and teeth. Partner has Dental flags/back-reference. No second contact master is needed. | [D01](#d01-patient-and-contact), [O01](#o01-identity) |
| `dental.practitioner` | Clinical name, speciality and license; optional `user_id` to `res.users`. Practitioner is not automatically an employee or the logged-in user. | [D02](#d02-practitioner-and-room), [O01](#o01-identity) |
| `dental.room` | Chair/room configuration. Appointment links a room; current overlap constraint checks practitioner, not room. | [D02](#d02-practitioner-and-room), [D03](#d03-appointment) |
| `dental.medical.history` | Dated patient background entry, type, description, optional practitioner. No encounter relationship or clinical sign-off lifecycle. | [D01](#d01-patient-and-contact) |
| `dental.tooth` | One current record per patient/FDI tooth, current condition, one surface, notes and manual last-treatment date. Patient creation initializes 32 adult teeth. | [D04](#d04-tooth-and-catalog) |
| `dental.treatment` | Treatment service catalog, duration, price, tooth requirement; links `product.product` and creates a service product if absent. | [D04](#d04-tooth-and-catalog), [O04](#o04-products-and-stock) |
| `dental.appointment` | Booking with patient, practitioner, room, scheduled interval, planned treatment tags and optional patient-filtered plan. Mail/activity mixins and calendar view. | [D03](#d03-appointment) |
| `dental.treatment.plan` + `.line` | Clinical proposal and scheduling plus commercial quantities/prices/discounts, mutable progress states and invoice flags/links. No independent performed-treatment event. | [D05](#d05-plan-and-plan-line) |
| `dental.prescription` + `.line` | Patient/practitioner document, optional appointment, free-text diagnosis, drug instructions and optional goods product. | [D06](#d06-prescription) |
| `dental.invoice.wizard` + inherited `account.move` | Draft customer invoices from selected plan lines; patient/plan links and patient totals. Accounting posting/payment stays in Odoo. | [D07](#d07-accounting-bridge), [O05](#o05-accounting) |
| Standard mail, attachments and reports | Existing mixins on patient, appointment, plan and prescription; three QWeb PDF reports. These provide infrastructure, not missing clinical semantics. | [D08](#d08-reports-and-access), [O06](#o06-files-mail-activities-and-history), [O07](#o07-reports-automation-and-security) |

The baseline defines 11 persistent Dental models, two existing-model
extensions (`res.partner`, `account.move`) and one transient invoice wizard.
No separate visit, examination request/result or execution model exists in
the inspected Dental module. No implemented SD addon supplies those roles.

## 3. Current workflow map

1. Create a patient linked to a partner; sequence the patient and initialize
   the adult odontogram. Clinical background remains on patient/history/tooth.
2. Book an appointment, choose practitioner/room, scheduled start/stop,
   optional plan and planned treatment tags. The practitioner overlap search
   rejects intersecting non-cancel/non-no-show appointments; it is not evidence
   of concurrent-booking safety or room collision control.
3. Appointment UI offers `draft -> confirmed -> checked_in -> done`, plus
   cancel/no-show/reset. The UI also permits confirmed appointments to become
   done without check-in and permits reset from done. Public action methods
   directly assign states; there is no server transition graph in those methods.
   Check-in records neither actual arrival time nor active treatment start.
4. Create a treatment plan and editable lines: treatment, tooth, prospective
   quantity/price, optional practitioner and scheduled date. Confirm only
   checks that a line exists; start sets `in_progress`.
5. `dental.treatment.plan.action_done` changes every non-done line to done,
   **including canceled lines**, then marks the plan done. This can happen
   without an appointment or individually documented performance. Line state
   and the invoice flag are editable in the plan form.
6. Create a prescription, optionally select an appointment, enter free-text
   diagnosis/drug instructions, confirm and print. Appointment/patient matching
   is not enforced by a model constraint in the inspected prescription model.
7. The invoice wizard initially selects non-invoiced, non-canceled plan lines,
   without requiring performed/done status. It creates a draft `out_invoice`,
   marks the lines invoiced and links the plan immediately. This is commercial
   processing, not proof of treatment, invoice posting or payment.
8. Staff can schedule standard activities, create another appointment, post
   chatter and attach files. There is no automatic clinical follow-up chain,
   finalized visit report, or treatment-triggered stock movement in this module.

These are static source observations [D01-D08], not actions executed against
the database. The distinction between UI restrictions and server behavior is
material to any later implementation.

## 4. Capability-by-capability reuse table

Each row has exactly one classification. USE covers the bounded current
responsibility, not every future clinical requirement. EXTEND identifies a
real existing extension target; DEFER identifies unresolved semantics. NEW
identifies a missing domain capability, with the earlier options examined in
section 7. None authorizes new source or a final schema.

Evidence IDs below resolve to module, model, field, method, actual XML ID and
source file in the appendix. N/A means the capability has no existing dedicated
model/method/XML ID; it is not a proposed identifier. Matrix area names in the
last column identify the prior recommendation reviewed for that row.

| # | Capability | Community source and existing Dental behavior | Real extension point / boundary | Class | Matrix area reviewed |
| --- | --- | --- | --- | --- | --- |
| 1 | Patient/contact | `res.partner`; `dental.patient.partner_id` and related phone/email/address [O01, D01]. | Use existing partner identity, patient clinical wrapper and patient form; preserve existing IDs. A patient-partner uniqueness policy is not established by the current relation. | USE | Contacts; Dental patients |
| 2 | Practitioner/user | `res.users.partner_id`; `dental.practitioner.user_id` optional, plus license/speciality [O01, D02]. | Use existing authentication and practitioner record. Do not replace it with an employee or infer clinician identity from the current session. | USE | Users; Employees |
| 3 | Appointment | Calendar renderer and `calendar.event`; Dental already has `start`, `stop`, patient, practitioner, room, plan and calendar XML [O02, D03]. | Keep `dental.appointment` for bookings and the existing Web calendar view. There is no `calendar.event` synchronization to preserve or assume. | USE | Appointments/calendar |
| 4 | Check-in / arrival | Event registration has attendance semantics; calendar has scheduled time, neither provides Dental arrival. Existing `action_check_in` only sets `checked_in` [O02, O03, D03]. | Extend the existing appointment state behavior. Define allowed transitions and actual-arrival evidence before claiming arrival tracking; preserve scheduled start/stop meaning. | EXTEND | Appointments/calendar; Automation |
| 5 | Clinical visit / encounter | `calendar.event`, `project.task`, `event.registration`, `survey.user_input` and website visits are not clinical episodes. Appointment lacks clinical episode/finalization semantics [O02, O03, D03]. | Decide cardinality, walk-ins, rescheduling and encounter ownership first. Extending appointment may suffice under a strict one-booking/one-visit policy; an independent clinical record may be justified otherwise. Dedicated XML ID/model: N/A. | DEFER | Clinical encounter / visit representation |
| 6 | Patient warnings / risk | Partner is identity, not a clinical risk record. Dental already stores allergies, medications, chronic disease, smoker/pregnancy and history [O01, D01, D08]. | Extend patient/appointment views and server-enforced field/access behavior around existing information. Current appointment form has no risk summary; do not expose all clinical data to reception by default. | EXTEND | Dental patients; Security; Frontend widgets/Owl |
| 7 | Tooth / odontogram data | Generic forms/views provide presentation. `dental.tooth` provides FDI number, condition, surface, notes and patient uniqueness [O02, D04]. | Use the current adult current-state chart. Per-visit findings, multiple surfaces and pediatric charts are separate requirements; no new chart engine or widget is justified by this audit. | USE | Dental tooth model; Frontend widgets/Owl |
| 8 | Clinical examination | Survey can collect structured answers; Dental has background entries, current teeth and appointment notes, no dated examination episode or sign-off [O03, D01, D03, D04]. | Decide whether narrative assessment suffices or tooth-level/time-bound observations are required; then assess extending existing clinical records versus using survey for collection. No dedicated examination XML ID/model: N/A. | DEFER | Dental patients; Clinical encounter / visit representation; Reports/PDF |
| 9 | Diagnosis | Product/service classification and survey answers are not diagnoses. Prescription already has free-text `diagnosis`; tooth condition/history are limited observations [O03, O04, D01, D04, D06]. | Extend the existing clinical-document/view context for an approved diagnosis responsibility. Patient/visit/tooth scope and any coding scheme remain decisions; a new diagnosis dictionary is not proved necessary. | EXTEND | Dental patients; Prescription |
| 10 | Treatment catalog | Odoo service product; Dental `dental.treatment.product_id`, `create`, `write`, price/duration/tooth flag [O04, D04]. | Use existing service catalog and product billing connection. Do not build another product master or infer that the diagnostic category supplies examination orders. | USE | Products; Services; Treatment |
| 11 | Treatment plan | Standard products/accounting can price services, but Dental already expresses clinical intention with patient, tooth, treatment, schedule, notes and totals [O04, O05, D05]. | Use the existing plan for its current mixed planning/quotation role; distinguish prospective lines from actual performance. No replacement plan model. | USE | Services; Treatment plan; Invoice/account.move |
| 12 | Treatment plan revision/change | Mail tracking and optional HTML history exist; plan lines remain editable, without approved revision relationships or snapshots [O06, D05]. | Extend existing plan change control; reuse mail tracking, including parent-directed line tracking where appropriate. HTML history only versions HTML content; it does not freeze relational lines or record clinical approval. | EXTEND | Treatment plan; Chatter; Security |
| 13 | Actual treatment execution | `stock.move` proves movement, `account.move` accounting, activity completion a task. Plan-line state/quantity/practitioner and scheduled date do not reliably prove performed treatment [O04-O06, D05, D07]. | Decide one execution per plan line versus repeated/partial/unplanned acts across visits. Only then choose extending plan lines or an independent execution responsibility. Existing dedicated execution API/XML ID: N/A. | DEFER | Treatment; Stock movement; Invoice/account.move |
| 14 | Examination order | Survey collects responses; activities schedule work. Diagnostic treatment/plan lines can already express a planned diagnostic service, but have no dedicated request lifecycle or result linkage [O03, O06, D04-D06]. | Decide whether extending a diagnostic plan line is sufficient or requests must exist independently of a priced plan. Reuse patient/practitioner/appointment context, catalog, activities and files. No dedicated clinical-order method/XML ID: N/A. | DEFER | Clinical encounter / visit representation; Treatment; Activities/tasks |
| 15 | Examination result | Survey answers and `ir.attachment` can hold values/files. Dental has no request-linked, clinically reviewed result lifecycle [O03, O06, D01, D06]. | Decide whether extending an existing clinical document with attributed findings/review is sufficient or multiple independently corrected results are required. Reuse attachments and, if suitable, survey input for collection. No dedicated result method/XML ID: N/A. | DEFER | Attachments/filestore; Dental patients; Reports/PDF |
| 16 | Prescription | Product/mail/report infrastructure plus existing patient/practitioner/appointment, diagnosis, advice and medicine lines [O04, O06, O07, D06]. | Use the existing basic prescription document and print action. Controlled prescribing, signing, dispensing and stronger context validation require separate approved scope; this USE is not a safety certification. | USE | Prescription; Reports/PDF |
| 17 | Medication/product relationship | Goods products already exist; prescription line has optional `product_id` and independent required name, dose, frequency, duration, quantity [O04, D06]. | Extend this existing bridge for agreed source consistency and selection rules. Goods are not automatically medicines or tracked inventory; no second medicine/product master. | EXTEND | Medicines; Products |
| 18 | Attachment / clinical files | `ir.attachment` storage and linked-record/field access; existing chatter accepts attachments [O06, D01, D03, D05, D06]. | Use standard attachment linkage, storage and access checks. Choose authorized clinical owner/exposure; an attachment alone is not a verified result or signed clinical record. | USE | Attachments/filestore; Security |
| 19 | Medical record / visit report | QWeb PDF/report engine exists. Dental prints patient card, plan and prescription, not a finalized visit record [O07, D08]. | Decide the authoritative visit content, responsible clinician, finalization and correction policy before extending reports. A current patient card is not a historical visit snapshot. Dedicated visit-report XML ID: N/A. | DEFER | Reports/PDF; Clinical encounter / visit representation |
| 20 | Follow-up / next appointment | Standard activity type, assignee and deadline; existing patient appointment action defaults the patient [O06, D01, D03]. | Configure a follow-up activity on an existing clinical document and use the current appointment action for the next booking. Automatic linkage/outcome escalation is outside this bounded manual workflow. | CONFIGURE | Activities/tasks; Appointments/calendar; Automation |
| 21 | Activities/tasks | `mail.activity.mixin.activity_schedule`, activity feedback, optional `project.task`; patient/appointment/plan/prescription already inherit the mixin [O03, O06, D01, D03, D05, D06]. | Use activities for assigned reminders/tasks. Completed activities are removed with a message posted; they are not durable performed-treatment records. No project/task subsystem is needed for basic follow-up. | USE | Activities/tasks |
| 22 | Chatter/audit trail | `mail.thread`, `mail.track.mixin`, `message_post` and optional `mail_tracking`; Dental tracks selected parent fields, not all line edits [O06, D05, D08]. | Extend clinically relevant coverage using standard tracking APIs, access controls and approved correction semantics. Chatter is not an immutable clinical-signature or complete audit guarantee. | EXTEND | Chatter; Security |
| 23 | Fees/accounting linkage | Odoo `account.move`/lines/posting; Dental wizard creates draft invoices and marks plan lines invoiced [O05, D07]. | Extend the existing bridge for server-side plan/patient/company/line consistency, repeat billing behavior and the future agreed billing basis. Keep posting, taxes, receivables and payment in Odoo. | EXTEND | Accounting; Invoice/account.move; Payment |
| 24 | Inventory/consumable linkage | `product.product`, `stock.move`, `.line`, `stock.location`, `stock.quant`; no Dental stock dependency or movement hook [O04, D04, D05, D07]. | Extend clinical-to-stock integration only after execution/consumption semantics and optional-module availability are decided. Reuse stock workflows for quantities, units, lots, locations and reversals. Never implement a parallel stock ledger. | EXTEND | Inventory; Stock movement; Purchasing |

### Explicit answers to the six design questions

**A. Clinical visit:** DESIGN REVIEW REQUIRED. No suitable ready-made clinical
encounter was found in this Community snapshot. That does not prove a new
Dental model is necessary. Calendar is a meeting, project is work assignment,
event attendance is event participation, survey is response collection and
website visit is browsing. Choose between extending appointment and an
independent clinical responsibility after agreeing business cardinality.

**B. Appointment:** adequate for booking; already has a basic arrival flag,
but no actual arrival evidence or server transition discipline. It has no
active-visit state or finalized clinical-record semantics. Using the present
`done` flag as all of these would overload its meaning. A later extension is
possible, conditional on the agreed one-booking/visit relationship and access
and correction lifecycle; it is not automatically the right representation.

**C. Plan:** a mixture of prospective clinical treatment, schedule, commercial
quotation and mutable progress flags. It is not an independent execution
record. Preserve its valid planning and pricing behavior; do not reinterpret
historical line status as performance evidence.

**D. Actual treatment:** no reliable dedicated representation currently exists.
Counterexample: mark a plan done before a visit; every non-done line becomes
done, even one previously canceled. No individually recorded actual time,
verified performer or outcome is required by that method. A line can also be
edited afterward. Scheduled date, intended practitioner, invoiced flag and
invoice payment do not repair this evidentiary gap. Representation is DEFER,
pending execution cardinality and correction decisions.

**E. Standard capabilities:** reuse `ir.attachment`; `mail.activity` and
`mail.activity.mixin`; `mail.thread`/tracking; `product.product`; standard
`stock.*`; standard `account.*`; Web calendar and, only if needed, linked
`calendar.event`; `mail.template`/mail queue; QWeb/`ir.actions.report`.
Section 5 gives concrete boundaries and APIs.

**F. Genuinely absent clinical responsibilities:** a dedicated diagnostic
request lifecycle, verified request-linked results, reliable actual performance
and a finalized visit record are missing. They are candidates for NEW only if
the agreed business requirements rule out the existing extension targets.
Whether they require new persistent objects rather than extensions remains unresolved.
Structured examination and diagnosis need agreed detail before any new
domain object can be justified. NEW does not mean new attachment, product,
survey, inventory, accounting, mail or workflow engines.

## 5. Odoo capabilities worth reusing

| Standard capability | Inspected reuse boundary | Availability / decision |
| --- | --- | --- |
| Contacts and login | `res.partner` contact master; `res.users` authentication/partner relation [O01]. | Base dependencies already declared. Clinical practitioner remains a distinct existing concern. |
| Calendar and frontend | Web `calendarView` registry serves arbitrary suitable business models. `calendar.event` additionally offers attendees, recurrence, alarms and linked-document fields [O02]. | Dental already declares calendar and uses its own booking calendar view. Synchronization is absent and needs a separate source-of-truth/privacy decision; reuse does not require migrating bookings to events. |
| Forms/questionnaires | Survey models and input/answer collection [O03]. | Optional addon, installation not verified. Suitable for collection only if the approved clinical examination fits; completion/scoring is not clinical verification. |
| Products | Product service/goods types, units and catalog [O04]. | Declared dependency. Keep existing treatment service and medicine product relationships; `consu` means Goods and `is_storable` separately means Track Inventory in this revision. |
| Inventory | Movement, move-line quantities/units/lots, locations and quants; inspected `_action_done` lifecycle [O04]. | Stock is not a direct Dental dependency. Private methods are evidence of engine behavior, not permission to bypass picking/movement workflows or directly update quants. |
| Accounting | Customer invoice/line, journal, tax, posting and payment state [O05]. | Account dependency declared. Dental should supply clinical/commercial linkage; Odoo should own the ledger. A created draft invoice is neither posted nor paid. |
| Clinical files | `ir.attachment.res_model/res_id/res_field`, filestore and `_compute_res_access` [O06]. | Standard capability. Link files to an approved secured owner; use `check_access`, not the deprecated `check` compatibility method. Do not set public exposure as a workaround. |
| Follow-up/tasks | `activity_schedule`, assignment/deadline and feedback [O06]. | Mixins already present. Configure manual follow-up before inventing automation; completion normally removes the activity and posts a message. |
| Chatter and changes | `message_post`, `tracking=True`, `mail.track.mixin._track_record` for changes on related records [O06]. | Existing parent mixins are reusable. In this snapshot `mail.tracking.value` belongs to optional `mail_tracking`; do not assume it is supplied/installed by `mail` alone. Standard tracking already renders values in message bodies. |
| Text history | `html.field.history.mixin._get_versioned_fields` and HTML revision retrieval [O06]. | Optional capability; bounded HTML history, not relational plan revision or clinical attestation. Consider only if prose versioning is actually required. |
| Email/reminders | `mail.template.send_mail(force_send=False)`, mail queue and its existing cron [O06]. | Dental reminder already queues mail. `reminder_sent=True` means the method queued it, not verified delivery. No email or notification sent during audit. |
| Reports | `ir.actions.report.report_action`, `_render_qweb_pdf`, existing QWeb templates [O07, D08]. | Reuse renderer and report actions; settle the authoritative clinical document before creating a visit report. Printing does not finalize or sign clinical content. |
| State/automation/security | Existing business methods, ORM constraints/access, Odoo 20 `ir.access`; optional `base.automation`, standard `ir.cron` [O07, D08]. | UI domains/button visibility are not server checks. Choose the smallest explicit business rule first; there is no proof that a generic new workflow engine is needed. |

## 6. Dental capabilities worth preserving

- Existing patient/contact identity and patient action domains; clinical history
  and warnings should be improved in place, not duplicated in a new contact table.
- Practitioner credentials and room records, without compulsory HR remodeling.
- Appointment booking identity, scheduled intervals, current calendar action
  and practitioner overlap behavior; any later change must preserve what the
  existing times and states mean to users.
- Existing FDI tooth identity, patient/tooth uniqueness and adult chart data.
  Keep current-state data distinct from any later historical observations.
- Treatment catalog/service product bridge and treatment plan/line relations.
  Preserve prospective quantities/prices instead of silently making them
  historical actual quantities.
- Prescription document, optional product linkage and existing report. Improve
  context/clinical rules through a scoped extension rather than replace it.
- The native account bridge, three QWeb reports, sequences and mail/activity
  inheritance. Resolve integration gaps without creating parallel masters.

Preservation is not acceptance of every current behavior. In particular, bulk
plan completion, editable progress/billing flags, inconsistent clinical links
and incomplete access/tracking coverage need explicitly scoped decisions.

## 7. Genuine gaps

### Examination request responsibility: missing lifecycle, representation DEFER (row 14)

Required responsibility: record a practitioner's diagnostic examination
request for a patient and distinguish its clinical purpose and disposition
from medication prescribing and administrative reminders. Potential
connections: existing patient, practitioner, appointment/approved visit
context, treatment/service catalog, plan line, activities and attachments.

USE already permits an intended diagnostic service to appear as a treatment
plan line, but does not supply a dedicated request lifecycle. CONFIGURE can
select diagnostic treatments and assign activities/questionnaires; this may
suffice for a deliberately simple process, but does not establish independent
request identity or clinical disposition. EXTEND has a real candidate in the
existing diagnostic plan line, linked to patient, treatment, practitioner,
scheduled date and state. It must be considered before NEW. If an examination
request must exist independently of a priced treatment plan, or support a
different clinical lifecycle, the plan-line representation may be insufficient.
Those requirements are not settled by this task. Medication prescription,
product master and current tooth condition are not interchangeable with a
request. Survey can collect associated information; WRAP could adapt a later
laboratory boundary, but neither supplies the local clinical responsibility.

A NEW responsibility becomes justified only after the simpler configured or
extended plan/document options are rejected against approved requirements.
No laboratory integration platform is needed for this audit.
**Schema: NOT YET AUTHORIZED.**

### Verified examination result responsibility: missing semantics, representation DEFER (row 15)

Required responsibility: associate received findings with the correct
request/patient and distinguish source receipt, practitioner review, accepted
outcome and subsequent correction. Potential connections: the approved
request representation, patient/visit context, practitioner, existing clinical
notes/history, attachments and optionally survey answers.

USE supplies files, narrative entries and answers, not verified clinical
result semantics. CONFIGURE can organize forms/tasks/files but does not make
survey completion or activity feedback clinical verification. EXTEND remains
plausible for attributed findings and review on an existing approved clinical
document; the audit cannot rule it out before request ownership and result
cardinality are agreed. Existing medical history has dated narrative and a
practitioner, but its current background-entry meaning is not automatically a
result-review lifecycle. Attachment storage should remain file infrastructure;
clinical metadata should not be confused with storage implementation.
WRAP might later import content, but cannot replace local attribution/review.

Multiple independently reviewed or corrected outcomes may justify NEW clinical
behavior beyond the current documents. An attachment-backed narrative may
instead be sufficient with a bounded extension. Request and result might share
an approved representation; no separate result model is inferred.
**Schema: NOT YET AUTHORIZED.**

### Actual treatment: missing evidence, representation DEFER (row 13)

Required responsibility: distinguish intended treatment from what was
performed, by whom and when, with clinically meaningful outcome/correction
and a clear connection to billing and consumption. Potential connections:
existing patient, practitioner, tooth, treatment, plan line, approved visit
context, prescription where applicable, invoice lines and stock movements.

Existing plan completion can mark canceled/unperformed work done; scheduled
date and intended quantity do not establish actual treatment. Standard
activities, invoices and stock movements document other kinds of events.
Nevertheless, a tightly constrained single-performance-per-plan-line process
could potentially EXTEND the existing line. Repeated, partial or unplanned
acts across visits may justify a NEW clinical responsibility. The audit does
not assume those cardinalities. **Schema: NOT YET AUTHORIZED.**

### Visit, examination, diagnosis and final record boundaries

Required responsibilities: group the clinical episode, retain time-bound
examination/diagnosis meaning, and distinguish draft clinical notes from an
accepted visit record and later corrections. Potential connections: existing
appointment, patient, practitioner, current teeth/history, plan, execution,
examination request/result, prescription and report.

Current mutable notes/background/current tooth condition and three printed
documents do not provide that combined lifecycle. Their absence is a gap,
not proof of a mandatory encounter or diagnosis model. Visit, examination and
visit report remain DEFER; diagnosis first targets an existing clinical
document extension, with coding/history detail undecided.
**Schema: NOT YET AUTHORIZED.**

### Existing bridges needing extension rather than replacement

Patient risks lack an appointment summary and require an explicit clinical
visibility policy. Plan changes lack agreed approval/revision semantics and
line tracking coverage. Prescription product/name consistency is unspecified.
Invoice selection is not a proof of performance and its public creation
method does not revalidate selected-line ownership, prior invoicing or
clinical billability. The `invoiced` flag is set on draft invoice creation;
repeated calls and cancellation/correction need an agreed policy. Dental has
no treatment-to-consumable bridge; execution triggers, units and reversal
meaning remain undecided. These are bounded EXTEND areas, not reasons for
new identity, accounting or stock engines [D01, D05-D08, O04-O07].

## 8. Ambiguous areas requiring human design decision

| Decision | Why it changes the reuse choice |
| --- | --- |
| Booking-to-visit cardinality; walk-ins; rescheduling; canceled booking with clinical work | Determines whether extending appointment can be sufficient or a clinical episode must survive independently. No final encounter schema follows from this audit. |
| Meaning and authority of check-in, active work, completion, reset and correction | A shared state field cannot truthfully stand for scheduling, treatment and final clinical sign-off without an agreed lifecycle. Repeated/multi-record actions need explicit semantics. |
| One plan line versus multiple actual acts, partial/unplanned work and multiple clinicians | Determines whether execution can extend plan lines or needs independent clinical facts. Never derive these facts from current done flags. |
| Clinical plan approval and revision versus quotation changes | Determines what must be preserved and who can change it. Standard tracking/prose history may help but do not automatically preserve approved relational content. |
| Examination versus diagnostic order versus questionnaire | Determines required result format, review responsibility and whether a simple narrative/attachment plus workflow is sufficient. Survey availability is not an examination policy. |
| Diagnosis patient/visit/tooth scope and whether coding is needed | Current diagnosis text is prescription-scoped. Do not choose a terminology master, dictionary or migration before this decision. |
| Risk visibility and practitioner responsibility | Reception currently has read access to patient/prescription and other clinical records. Sensitive patient fields have no field-level groups. Practitioner selection is not authorization or authenticated authorship. |
| Finalization/correction policy and visit report owner | Determines whether a live QWeb rendering is enough or accepted content must remain identifiable after subsequent changes. A PDF and a signature line do not establish attestation. |
| Medication source, permitted products and dispensing | Optional product and independent medicine name may diverge. A goods product alone proves neither drug suitability nor dispensed quantity. |
| Charging basis, draft/canceled invoices, duplicate requests and refunds | Current plans may be invoiced before execution. Decide deposits/planned charges versus performed charges before tying accounting to clinical completion. |
| Consumable trigger, actual quantity, lot/location, wastage and reversal | Clinical use, dispensing and purchase receipt are different events. Decide this before extending Dental-to-stock linkage or installing optional addons. |
| Calendar synchronization and clinical exposure | An appointment calendar view already works. Linked meetings would introduce attendee/visibility and source-of-truth decisions, not merely another UI. |

No decision above was silently made. No new model name, final field list,
relation cardinality, migration or integration abstraction is proposed.

## 9. Rejected reinventions

| Rejected proposal | Source-backed reason |
| --- | --- |
| New contact, user, service/product or medicine master | Existing partner/users and product catalog already supply identity and goods/services; Dental already links them [O01, O04, D01, D02, D04, D06]. |
| Custom file store or separate attachment database | `ir.attachment` already owns storage and secured document/field linkage [O06]. Clinical metadata is a different responsibility. |
| Custom reminders, conversation store or notification queue | Existing mail/activity/template/queue mechanisms cover these roles [O06, D03]. |
| Custom booking/calendar renderer or mandatory calendar migration | Existing Dental calendar view and Web calendar registry work on the appointment model [O02, D03]. Synchronization is a separate optional requirement. |
| Custom accounting ledger, invoice master or receivable balances | Native account moves/lines, posting/payment state and Dental bridge already exist [O05, D07]. Extend the clinical linkage. |
| Custom inventory ledger or direct quantity table | Standard stock moves, move lines, units, lots, locations and quants provide the movement engine [O04]. Only clinical consumption linkage is missing. |
| Generic workflow engine or speculative integration framework | Existing business state methods, ORM rules, activities, automation/server actions and cron have not been proved insufficient [O06, O07]. No current SD integration implementation requires an abstraction. |
| Automatically create `dental.encounter`, replace plan with project tasks, or treat event attendance as a visit | None resolves the unsettled clinical cardinality/finalization responsibility. Existing generic state labels do not establish clinical equivalence [O02, O03, D03, D05]. |
| Treat activity completion, plan done, invoice creation or stock movement as clinical performance | Each records a different responsibility, and current plan completion has an explicit unperformed/canceled-line counterexample [O04-O06, D05, D07]. |

## 10. Recommended smallest first implementation area

**A separately authorized EXTEND task for appointment check-in transition
consistency.** Preserve the current appointment and scheduled times. Agree
which existing source states can enter `checked_in`, who may perform the action
and whether a repeated check-in is idempotent or rejected. Enforce that rule
across authorized server entry paths, including direct writes/RPC, rather
than only button visibility. No new encounter or execution object is required
for this bounded improvement.

Why first: the existing `action_check_in` and form provide a concrete target,
and the current mismatch between visible buttons and direct state assignment
can be addressed without deciding all clinical-record semantics. The future
task should cover allowed/rejected transitions, repeated and multi-record
calls, ordinary receptionist/dentist access and preservation of scheduled
times. It must not claim to establish actual arrival timestamp evidence,
active treatment or finalized visit records. Those require separate scope.

This is a recommendation only. No implementation, test fixtures, model,
database change, migration or commit was created by this audit.

### Required reuse-audit decision record

```text
REUSE AUDIT
Requirement: Audit the 24 current Dental clinical workflow responsibilities.
Existing Odoo capabilities: O01-O07 below; standard identity, UI, products,
  stock, accounting, files, mail/activities, history, reports and automation.
Existing Dental capabilities: D01-D08 below; current maintained clinical models.
Existing SD capabilities: None in D:/Code/odoo/odoo-sd/addons (README.md only).
Extension points inspected: Existing model actions/constraints and callers,
  form/calendar/report XML, standard mixins, product/account/stock lifecycles.
Classification: Per-row decisions in section 4; no combined implementation class.
New capability actually required: Clinical request/result, performance and
  finalized-record semantics are missing; no NEW representation is proved
  necessary before the existing extension alternatives and business rules are decided.
Rejected reinventions: Section 9; no parallel infrastructure or data masters.
Evidence: Exact Dental/Odoo/SD revisions in section 1 and source appendix below.
Decision: DESIGN REVIEW REQUIRED for clinical representation and business rules.
  Audit deliverable READY; implementation NOT AUTHORIZED.
```

## Source evidence appendix

Dental paths below resolve to the accepted baseline. Odoo paths resolve to the
pinned local Community checkout. XML IDs are existing records, with their
module prefix; N/A is explicitly used for missing dedicated clinical objects.

### D01 Patient and contact

Module `dental_clinic`:
[dental_patient.py](D:/Code/odoo/dental/dental_clinic/models/dental_patient.py:8)
defines `dental.patient`, `partner_id`, related contact fields, allergies/current
medications/chronic diseases/smoker/pregnant, `medical_history_ids`, clinical
relations; `create`, `_create_odontogram`, `action_open_appointments`,
`action_open_prescriptions`, `_compute_counts`.
[res_partner.py](D:/Code/odoo/dental/dental_clinic/models/res_partner.py:6)
extends `res.partner` with `mobile`, `is_dental_patient`, `dental_patient_id`.
[dental_medical_history.py](D:/Code/odoo/dental/dental_clinic/models/dental_medical_history.py:6)
defines `dental.medical.history.patient_id/date/title/description/practitioner_id/kind`.
Its history is background entries, not an examination/encounter state machine.
[patient views](D:/Code/odoo/dental/dental_clinic/views/dental_patient_views.xml)
include clinical information and XML IDs
`dental_clinic.view_dental_patient_form`, `dental_clinic.action_dental_patient`.

### D02 Practitioner and room

Module `dental_clinic`:
[dental_practitioner.py](D:/Code/odoo/dental/dental_clinic/models/dental_practitioner.py:6)
defines `dental.practitioner.user_id`, `speciality`, `license_number`, appointment
relation and mail inheritance.
[dental_room.py](D:/Code/odoo/dental/dental_clinic/models/dental_room.py:6)
defines `dental.room` name/code/equipment. No dedicated clinical-execution method
is defined on either model. Their relationships, rather than a proposed HR
mapping, are the extension points.

### D03 Appointment

Module `dental_clinic`:
[dental_appointment.py](D:/Code/odoo/dental/dental_clinic/models/dental_appointment.py:8)
defines `dental.appointment.patient_id/practitioner_id/room_id/plan_id/treatment_ids`,
`start/stop/duration/state/reason/notes/reminder_sent/company_id`;
`_check_overlap`, duration compute/inverse, `action_confirm`, `action_check_in`
(line 92), `action_done`, cancellation/no-show/reset and `action_send_reminder`.
[appointment views](D:/Code/odoo/dental/dental_clinic/views/dental_appointment_views.xml:24)
contain button visibility and XML IDs `dental_clinic.view_dental_appointment_form`,
`dental_clinic.view_dental_appointment_calendar`,
`dental_clinic.action_dental_appointment`,
`dental_clinic.action_dental_appointment_calendar`.
[mail template](D:/Code/odoo/dental/dental_clinic/data/mail_template_data.xml)
defines `dental_clinic.mail_template_dental_appointment_reminder`.
No actual arrival/start/end or finalized clinical-record method is defined.

### D04 Tooth and catalog

Module `dental_clinic`:
[dental_tooth.py](D:/Code/odoo/dental/dental_clinic/models/dental_tooth.py:6)
defines `dental.tooth.patient_id/tooth_number/condition/surface/notes/last_treatment_date`,
patient/tooth uniqueness and `_compute_quadrant`.
[tooth views](D:/Code/odoo/dental/dental_clinic/views/dental_tooth_views.xml)
define `dental_clinic.view_dental_tooth_form`, `dental_clinic.action_dental_tooth`.
[dental_treatment.py](D:/Code/odoo/dental/dental_clinic/models/dental_treatment.py:6)
defines `dental.treatment.category/duration/product_id/price/requires_tooth`;
`create` generates service products, `write` synchronizes name/price to product.
[treatment views](D:/Code/odoo/dental/dental_clinic/views/dental_treatment_views.xml)
define `dental_clinic.view_dental_treatment_form`, `dental_clinic.action_dental_treatment`.
Neither a diagnostic category nor a manual last-treatment date supplies an
examination order, verified result or actual execution lifecycle.

### D05 Plan and plan line

Module `dental_clinic`:
[dental_treatment_plan.py](D:/Code/odoo/dental/dental_clinic/models/dental_treatment_plan.py:7)
defines `dental.treatment.plan.patient_id/practitioner_id/date/expected_end_date`,
`line_ids/state/notes/invoice_ids`; `action_confirm`, `action_start`,
`action_done` (line 62), reset/cancel and `action_create_invoice`.
[dental_treatment_plan_line.py](D:/Code/odoo/dental/dental_clinic/models/dental_treatment_plan_line.py:6)
defines `dental.treatment.plan.line.plan_id/patient_id/practitioner_id/treatment_id/tooth_id`,
`quantity/price_unit/discount/subtotal/state/scheduled_date/invoiced/note`;
`_onchange_treatment` and subtotal compute. Defaults assigned by onchange
are not a server-side invariant for all create/write paths.
[plan views](D:/Code/odoo/dental/dental_clinic/views/dental_treatment_plan_views.xml:18)
define `dental_clinic.view_dental_treatment_plan_form`, editable lines and state
buttons. Parent chatter does not automatically record every child edit.
No revision chain, verified performance or approved-content finalization API
is defined in these models.

### D06 Prescription

Module `dental_clinic`:
[dental_prescription.py](D:/Code/odoo/dental/dental_clinic/models/dental_prescription.py:6)
defines `dental.prescription.patient_id/practitioner_id/appointment_id/date`,
`diagnosis/advice/state/line_ids`; confirm/cancel/reset and `action_print`.
[dental_prescription_line.py](D:/Code/odoo/dental/dental_clinic/models/dental_prescription_line.py:6)
defines `.line.product_id` (optional, goods domain), required `name`, dosage,
frequency, duration, quantity and instructions. No dispensing/stock action.
[prescription views](D:/Code/odoo/dental/dental_clinic/views/dental_prescription_views.xml)
define `dental_clinic.view_dental_prescription_form`, editable lines and diagnosis.
The print action is `dental_clinic.action_report_dental_prescription` [D08].
No separate diagnosis model or examination-order/result API exists here.

### D07 Accounting bridge

Module `dental_clinic`:
[account_move.py](D:/Code/odoo/dental/dental_clinic/models/account_move.py:6)
extends `account.move` with `dental_patient_id`, `dental_plan_id`.
[dental_invoice_wizard.py](D:/Code/odoo/dental/dental_clinic/wizards/dental_invoice_wizard.py:7)
defines transient `dental.invoice.wizard.plan_id/patient_id/line_ids/journal_id/invoice_date`;
`_onchange_plan`, `action_create_invoice` (line 25). It checks selected lines
exist, patient partner and treatment product, then creates account move/lines
and marks selected lines invoiced. Its selection domain/onchange is not an
ownership/duplicate-invoicing validation inside the public creation method.
Patient invoice aggregation is in [D01]. Clinical execution/inventory links
and XML IDs for those missing responsibilities are N/A.

### D08 Reports and access

Module `dental_clinic`:
[dental_reports.xml](D:/Code/odoo/dental/dental_clinic/report/dental_reports.xml)
defines `dental_clinic.action_report_dental_patient_card`,
`dental_clinic.action_report_dental_treatment_plan`,
`dental_clinic.action_report_dental_prescription`, all `qweb-pdf`.
Their actual templates are
[patient card](D:/Code/odoo/dental/dental_clinic/report/dental_patient_card_template.xml),
[plan](D:/Code/odoo/dental/dental_clinic/report/dental_treatment_plan_template.xml),
[prescription](D:/Code/odoo/dental/dental_clinic/report/dental_prescription_template.xml).
They display current patient/chart data, prospective plan pricing and
prescription text respectively; no finalized-visit report is defined.
[dental_security.xml](D:/Code/odoo/dental/dental_clinic/security/dental_security.xml)
defines `dental_clinic.group_dental_receptionist`, `group_dental_user`,
`group_dental_manager` and `dental_clinic.rule_dental_appointment_user`
(an Odoo 20 `ir.access` company restriction, not legacy `ir.rule`).
[ir.access.csv](D:/Code/odoo/dental/dental_clinic/security/ir.access.csv)
contains actual CRUD grants; reception can read patient, plan/lines and
prescription/lines, while clinical patient fields have no `groups` restriction.
Only appointment has the inspected Dental company restriction. This finding
requires a later access design; it is not permission to widen rights.

### O01 Identity

Module `base`:
[res_partner.py](D:/odoo-sd/odoo20-clean/odoo/addons/base/models/res_partner.py:268)
defines `res.partner`, name/phone/email/contact identity;
[res_users.py](D:/odoo-sd/odoo20-clean/odoo/addons/base/models/res_users.py:174)
defines `res.users`, `partner_id`, `login`. Dedicated clinical methods/XML IDs:
N/A. Dental's existing partner/user fields are the integration points.

### O02 Calendar and Web

Module `calendar`:
[calendar_event.py](D:/odoo-sd/odoo20-clean/addons/calendar/models/calendar_event.py:97)
defines `calendar.event`, mail/activity mixins, start/stop/duration,
linked document `res_id/res_model_id/res_model/res_record` (lines 245-251),
attendees, recurrence and alarms; `_check_private_event_conditions` governs
meeting privacy. Scheduled meetings do not supply clinical verification.
Module `web`:
[calendar_view.js](D:/odoo-sd/odoo20-clean/addons/web/static/src/views/calendar/calendar_view.js:1)
registers `calendarView` using `registry.category("views").add("calendar", ...)`.
Frontend extension uses the existing view/registry; an Owl rewrite is not
required for this audit's capabilities. Dental calendar XML IDs are [D03].

### O03 Closest generic visit, work and examination candidates

Module `project`:
[project_task.py](D:/odoo-sd/odoo20-clean/addons/project/models/project_task.py:92)
defines `project.task`, assignment/stage/state/dates, `partner_id`, mail/activity
and HTML-history mixins; it is assigned work, not a clinical visit record.
Module `event`:
[event_event.py](D:/odoo-sd/odoo20-clean/addons/event/models/event_event.py:33)
defines scheduled `event.event`;
[event_registration.py](D:/odoo-sd/odoo20-clean/addons/event/models/event_registration.py:15)
defines `event.registration`, participant/partner, state and `action_attend_event`.
Event attendance is not Dental check-in or completed treatment.
Module `survey`:
[survey_survey.py](D:/odoo-sd/odoo20-clean/addons/survey/models/survey_survey.py:22)
defines `survey.survey` questions;
[survey_user_input.py](D:/odoo-sd/odoo20-clean/addons/survey/models/survey_user_input.py:19)
defines `survey.user_input.survey_id/partner_id/start_datetime/end_datetime/state/user_input_line_ids`.
Questionnaire answer/completion/scoring is not diagnostic request/result review.
Module `website`:
[website_visitor.py](D:/odoo-sd/odoo20-clean/addons/website/models/website_visitor.py:18)
defines `website.track.visit_datetime` and `website.visitor`: browsing visits,
not patient episodes. Dedicated clinical XML ID/method across these candidates:
N/A; none was identified as an off-the-shelf encounter or examination model.

### O04 Products and stock

Module `product`:
[product_product.py](D:/odoo-sd/odoo20-clean/addons/product/models/product_product.py)
defines `product.product`;
[product_template.py](D:/odoo-sd/odoo20-clean/addons/product/models/product_template.py:63)
defines `product.template.type` (Goods `consu`, Service `service`, Combo),
`is_storable` (line 127), `uom_id`. Module `stock`:
[stock_move.py](D:/odoo-sd/odoo20-clean/addons/stock/models/stock_move.py:18)
defines `stock.move.product_id/product_uom_qty/quantity/location_id/location_dest_id`,
confirmation/reservation and `_action_done` (line 2353);
[stock_move_line.py](D:/odoo-sd/odoo20-clean/addons/stock/models/stock_move_line.py:16)
defines `stock.move.line.product_id/uom_id/quantity/lot_id` and completion;
[stock_quant.py](D:/odoo-sd/odoo20-clean/addons/stock/models/stock_quant.py:21)
defines `stock.quant`, `_get_available_quantity`, `_update_available_quantity`;
[stock_location.py](D:/odoo-sd/odoo20-clean/addons/stock/models/stock_location.py)
defines `stock.location`. These are engine evidence, not APIs to call during
the audit. Dedicated Dental consumption XML ID/method: N/A.

### O05 Accounting

Module `account`:
[account_move.py](D:/odoo-sd/odoo20-clean/addons/account/models/account_move.py:82)
defines `account.move.state/move_type/invoice_line_ids/payment_state`, `_post`
(line 6134) and `action_post` (line 6821);
[account_move_line.py](D:/odoo-sd/odoo20-clean/addons/account/models/account_move_line.py)
defines accounting/invoice lines and product/quantity/price relationships.
Posting validates accounting documents and rights; it is not clinical sign-off.
Dental invoice action/caller and fields are [D05, D07], not a new ledger.

### O06 Files, mail, activities and history

Module `base`:
[ir_attachment.py](D:/odoo-sd/odoo20-clean/odoo/addons/base/models/ir_attachment.py:96)
defines `ir.attachment`, `_storage`, `_filestore`, `_file_write`,
`res_model/res_id/res_field` (lines 592-594), `_compute_res_access` (line 671).
Module `mail`:
[mail_thread.py](D:/odoo-sd/odoo20-clean/addons/mail/models/mail_thread.py:139)
defines `mail.thread` inheriting `mail.track.mixin`, tracking execution,
`message_post` (line 2256), attachment processing and rendering tracking values
into message bodies (line 2428);
[mail_track_mixin.py](D:/odoo-sd/odoo20-clean/addons/mail/models/mail_track_mixin.py:23)
defines tracked-field behavior and `_track_record` (line 298), expressly for
centralizing related-record/line changes on a parent;
[mail_message.py](D:/odoo-sd/odoo20-clean/addons/mail/models/mail_message.py)
defines `mail.message` document linkage and message content/access;
[mail_activity.py](D:/odoo-sd/odoo20-clean/addons/mail/models/mail_activity.py:24)
defines `mail.activity` document linkage and completed-activity removal/message
behavior;
[mail_activity_mixin.py](D:/odoo-sd/odoo20-clean/addons/mail/models/mail_activity_mixin.py:428)
defines `activity_schedule`, feedback and activity lifecycle integration;
[mail_template.py](D:/odoo-sd/odoo20-clean/addons/mail/models/mail_template.py:705)
defines `mail.template.send_mail` and queued dispatch semantics;
[mail cron](D:/odoo-sd/odoo20-clean/addons/mail/data/ir_cron_data.xml)
defines `mail.ir_cron_mail_scheduler_action` calling `process_email_queue`.
Module `mail_tracking`:
[mail_tracking_value.py](D:/odoo-sd/odoo20-clean/addons/mail_tracking/models/mail_tracking_value.py:5)
defines `mail.tracking.value`;
[manifest](D:/odoo-sd/odoo20-clean/addons/mail_tracking/__manifest__.py)
depends on mail, while its model extensions persist `tracking_value_ids`.
Module `html_editor`:
[html_field_history_mixin.py](D:/odoo-sd/odoo20-clean/addons/html_editor/models/html_field_history_mixin.py:10)
defines `html.field.history.mixin`, `_get_versioned_fields`, write-time patches,
bounded history and `html_field_history_get_content_at_revision`.
These standard primitives have no dedicated Dental execution/result XML ID.

### O07 Reports, automation and security

Module `base`:
[ir_actions_report.py](D:/odoo-sd/odoo20-clean/odoo/addons/base/models/ir_actions_report.py:37)
defines `ir.actions.report.report_name`, `_render_qweb_pdf` (line 677),
`report_action` (line 863);
[ir_cron.py](D:/odoo-sd/odoo20-clean/odoo/addons/base/models/ir_cron.py:101)
defines `ir.cron` and scheduled server-action processing;
[ir_access.py](D:/odoo-sd/odoo20-clean/odoo/addons/base/models/ir_access.py)
defines Odoo 20 `ir.access` operation/group/domain permission/restriction
mechanisms. Module `base_automation`:
[base_automation.py](D:/odoo-sd/odoo20-clean/addons/base_automation/models/base_automation.py:130)
defines `base.automation.model_id/trigger/action_server_ids` and rule processing.
Concrete Dental report/security XML IDs and UI callers are [D08]. No generic
clinical workflow-engine XML ID is claimed.

## Deliverable verification

- Created only this audit document. Existing matrix, installed skills and
  foundation verification/status files were not modified.
- No business source, Odoo Core, composition source, database, migrations,
  models, fixtures or runtime configuration changed; no notifications sent.
- Source links, cited Dental identifiers, table row count and single allowed
  classification per row checked locally. Classification total: 24.
- `git diff --check`: PASS. Because this document is untracked, its contents
  were also checked with `git -c core.autocrlf=false diff --no-index --check`.
- Final Dental branch/HEAD remain the accepted baseline; worktree contains
  only this new untracked document, with no staged changes. No commit made.

**STOP: no recommendation implemented and no next business task begun.**
