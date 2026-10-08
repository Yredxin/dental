---
name: sd-odoo-dental
description: Apply SD Dental reuse-first architecture policy when assessing, designing, implementing, or reviewing features in the maintained Odoo 20 dental_clinic and SD addons. Require a source-backed reuse audit before feature implementation.
---

# SD Dental reuse policy

This skill defines project architecture and reuse policy only. For Odoo framework
implementation details, defer to the vendored official Odoo skills:

- [odoo-guidelines](../odoo-guidelines/SKILL.md): ORM, naming, fields, controllers,
  XML/view inheritance, QWeb, security, performance and tests.
- [odoo-web-guidelines](../odoo-web-guidelines/SKILL.md): JavaScript, Owl and assets.
- [odoo-review](../odoo-review/SKILL.md): code review.
- [odoo-security](../odoo-security/SKILL.md): security audit when applicable.

Read the relevant official sections for the task; do not duplicate or manually
edit those vendored rules. See [provenance](../../../docs/development/ODOO_AGENT_SKILLS.md)
and the [capability matrix](../../../docs/development/ODOO_DENTAL_CAPABILITY_REUSE_MATRIX.md).
Matrix recommendations are starting evidence, not feature authorization.

## REUSE FIRST

Before creating any new model, service, workflow, queue, notification mechanism,
inventory implementation, accounting object, attachment system, frontend
infrastructure or integration abstraction:

1. Search the actual pinned Odoo 20 Community source for an existing capability.
2. Search the current `dental_clinic` module.
3. Search existing SD addons, if any, including the composition repository's
   `addons/`. State explicitly when none exist.
4. Inspect implementations, callers, dependencies and extension points. Record
   source revisions and concrete files, model names, methods and XML IDs.
5. Classify each proposed capability as exactly one of the following, preferring
   the first sufficient option: `USE -> CONFIGURE -> EXTEND -> WRAP -> NEW`.
6. Only `NEW` authorizes building a new foundational capability, after the human
   design decision and a single scoped task. It is the last option, not the default.

| Classification | Meaning |
| --- | --- |
| USE | Use the existing capability and its standard APIs unchanged. |
| CONFIGURE | Satisfy the requirement with settings, records or supported configuration. |
| EXTEND | Add domain behavior through existing model, addon, view or widget extension points. |
| WRAP | Adapt an existing capability at a narrow boundary without duplicating its engine or data master. |
| NEW | Source evidence proves the required capability cannot be supplied by the preceding options. |

Missing evidence does not justify `NEW`. Mark the decision `BLOCKED` when required
source or dependencies are unavailable, or `DESIGN REVIEW REQUIRED` when the
business semantics or reuse choice need a human decision. `DEFER` in the matrix
means a decision was postponed; it is not an audit classification or permission
to implement.

## Required reuse audit

Complete this audit before implementing any new feature. Split a requirement
into capabilities when their reuse decisions differ. Explain why every earlier
option is insufficient for any `NEW` decision.

```text
REUSE AUDIT

Requirement:
<business requirement>

Existing Odoo capabilities:
- <model/module/service>

Existing Dental capabilities:
- <model/module/service>

Existing SD capabilities:
- <capability, or no existing addons found and paths searched>

Extension points inspected:
- <implementation, callers, dependencies and extension points>

Classification:
- <capability>: USE / CONFIGURE / EXTEND / WRAP / NEW

New capability actually required:
- <minimal justified gap, or none>

Rejected reinventions:
- <duplicated engine/data master avoided and why>

Evidence:
- <source revisions, files / model names / XML IDs / module names inspected>

Decision:
PROCEED / DESIGN REVIEW REQUIRED / BLOCKED
```

`PROCEED` means the audit supports the proposed approach; it does not bypass the
human decision or expand the authorized task. Do not begin implementation with
an incomplete audit, unresolved design decision or blocked evidence.

## Project boundaries

- **Odoo Core:** never modify it. Prefer configuration, inheritance, addon
  extension and standard framework APIs.
- **Dental Core:** `Yredxin/dental:dental_clinic` is our maintained Dental Core.
  Direct changes are appropriate for inherently dental clinical functionality:
  patients, appointments, clinical encounters, odontogram, diagnosis, treatment
  planning/execution, examination orders, prescriptions and clinical reports.
  Preserve existing data semantics where practical. Do not refactor solely for
  architectural purity. This is a placement policy, not a decision that any new
  clinical model is required.
- **Independent SD addons:** peripheral or cross-domain integrations normally
  stay separate, for example `sd_sms_aliyun`, `sd_wechat`, `sd_payment`, `sd_lab`,
  `sd_queue`, `sd_receipt_print`, `sd_display`, `sd_calling`, `sd_area` and
  `sd_medical_insurance`. These are placement examples, not existing addons or
  authorized work.

Clinical encounter / visit representation: requires separate reuse/design audit.
Do not infer that a `dental.encounter` model must be created.

## Reuse Odoo infrastructure

Confirm the APIs in the pinned source and the modules actually installed before
use. Prefer these existing capabilities wherever they satisfy the requirement:

| Area | Reuse target |
| --- | --- |
| Patient identity/contact | `res.partner` where applicable; preserve the existing `dental.patient.partner_id` link. |
| Users / employees | `res.users` / `hr.employee`; the clinical practitioner record is a separate existing concern. |
| Products, materials, medicines | `product.product` / `product.template`. |
| Inventory / purchasing | `stock.*` / `purchase.*`. |
| Accounting and receivables | `account.*`, including `account.move`. |
| Attachments | `ir.attachment` and the Odoo filestore. |
| Email / chatter / activities | `mail.*`, `mail.template` / `mail.thread` / `mail.activity`. |
| Calendar | `calendar.*`; inspect the existing Dental appointment and calendar view before changing representation. |
| Automation | `base_automation` where appropriate; inspect `base.automation` and `ir.cron`. |
| PDF reports | QWeb reports and `ir.actions.report`. |
| Security | Odoo groups and Odoo 20 `ir.access`, following the official security skills. |
| Frontend | Odoo Web, Owl and supported view/widget extension mechanisms. |
| SMS | Odoo SMS domain, queue and templates where appropriate; customize provider transport before considering a replacement subsystem. |

## Examples, not frozen architecture

**Dental consumable stock:** likely reuse `product.product`, `stock.move`,
`stock.location` and `stock.quant`. Product catalog, inventory engine and stock
ledger: `USE`. A treatment-to-consumable relation might need `EXTEND` or `NEW`,
but each capability must receive one classification after inspection. Actual
treatment consumption requires its own design audit. Reject a custom inventory
ledger, product master or stock quantity table unless a source-backed audit
proves necessity.

**Aliyun SMS:** likely `USE` or `EXTEND` Odoo SMS models, templates and queue;
provider transport may need `WRAP` or `NEW`. Inspect the actual queue dispatch
and provider-selection paths before deciding. Reject an independent notification
engine unless the audit proves it necessary. Do not send messages during an
audit or assume these examples authorize implementation.

## Review workflow

`IDEA -> REUSE AUDIT -> DESIGN DISCUSSION -> HUMAN DECISION -> SINGLE TASK ->
IMPLEMENTATION -> ODOO REVIEW -> SECURITY REVIEW where applicable -> TEST ->
HUMAN ACCEPTANCE -> NEXT TASK`

Prohibit `IDEA -> automatically create code`. A new idea starts an audit and
discussion, not implementation. A human-approved task may already contain the
required decision; record that authorization instead of requesting it again.
Keep implementation within that one task and stop before taking up the next.
