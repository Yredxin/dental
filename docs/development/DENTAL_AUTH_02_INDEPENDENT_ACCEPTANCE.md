# DENTAL-AUTH-02 independent acceptance

Result: **PASS**, 2026-10-09, isolated `sd_dental_dev` at
`http://127.0.0.1:18069`. A separate acceptance agent/session started after the
implementation validation gates passed. It used real Chrome and authenticated
XML-RPC/HTTP, without reading or editing implementation/repository-test source.
Only disposable fixtures were changed; no production/NAS/Core/composition access.

## Authenticated results

**265/265 valid checks passed:** 134 allowed, 131 correctly denied, zero
unexpected permits/errors. Includes 96 actual Mixed A/B CRUD cells, independent
capability boundaries, all five default presets, custom preset management,
native form onchange payloads, unrelated-group preservation, manual overrides,
employee C/R/U/archive/D and private-field limits, patient contact facade,
flag/exact 32 FDI teeth, direct contact/relink/clinical denials, Portal backend,
and forged groups/levels/private methods/System/other-company target attempts.
Rejected changes were followed by persistence/group-preservation reads.

After the implementation review closed the native HR invitation RPC gap, the
independent session reran affected denial checks after upgrade/restart. Eight
actors (Manager, isolated Employee RW, Frontdesk, Nurse, Warehouse, Dentist,
Portal and Mixed B) received AccessError for empty-record invitation calls;
Manager JSON-RPC also returned the exact AccessError class. Empty IDs guarantee
no invitation/email path even if the check regresses. No System/admin invitation
was invoked. User count stayed 21; the disposable employee's account link stayed
empty and contact/archive state unchanged.

Two superseded harness setup assertions remain explicitly invalidated in raw
evidence: profile_id-only transient creation does not simulate native form
onchange; multi_company is not a stable single-company preservation sentinel.
Actual onchange/form payloads and unrelated multi_currency checks replaced them.
Neither was an implementation defect or ignored unauthorized permit.

## Real Chrome results

**13 composite scenarios passed**, supported by 15 screenshots and a final
post-restart Manager menu/employee-list/Logout recheck:

- All six internal review accounts: My Subscription absent; Preferences opens,
  Help remains, Logout returns to login. Native Help navigation exercised once.
- Manager native Employees create, edit, archive and list; forbidden general
  Contacts/Dashboards/Apps/Settings absent.
- Chinese native System authorization: five independent selectors with
  无/只读/读写; no primary legacy Dental role selector; exact Chinese presets.
- Manager applied 护士 to disposable staff; System manually raised Appointment
  to RW. Persistence verified exact five levels, preserved multi_currency and
  successful appointment creation, without continuous preset enforcement.
- Frontdesk created a new linked contact/patient through the actual form,
  edited demographics and viewed all 32 teeth; flag/FDI verified independently.
- Mixed A edited demographics while clinical fields stayed read only; Mixed B
  edited clinical content while demographics stayed read only and the employee
  public directory had no New action. Saved values verified through RPC.

Mandatory Chinese flows passed. Optional separate English acceptance was not
run. No invitation/email action was sent. Original AUTH01 clinical records were
preserved; additional named review fixtures are disposable.

Raw report, JSON checks, harnesses and screenshots remain outside Git under
`D:\Code\odoo\.tmp\auth02\independent`. No passwords or raw captures are stored
in this permanent report. No unresolved technical acceptance findings.
