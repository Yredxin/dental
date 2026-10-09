# DENTAL-AUTH-02 acceptance ledger

Oracle: `DENTAL_AUTH_02_CAPABILITY_MODEL.md` and the human AUTH02 specification.
Scope: isolated localhost development only; no production/NAS, Core or composition
changes. Human review approved the final cumulative implementation commit.
Existing AUTH01 evidence is archived outside Git; all AUTH02 raw output stays
outside Git in `D:\Code\odoo\.tmp\auth02`.

## Model ACL oracle

R = read, C = create, U = write, D = physical delete. Administrative and clinical
patient fields are guarded separately even when generic write is available.
"Full management" means all five capabilities RW (负责人 / System).

| Model | Read capability | Mutation capability | Delete |
| --- | --- | --- | --- |
| dental.patient | Patient R or Clinical R | Patient RW: C/admin U; Clinical RW: clinical U | Full management |
| dental.medical.history | Patient R or Clinical R | Clinical RW: CU | Full management |
| dental.tooth | Patient R or Clinical R | Clinical RW: U; fixed 32-child initialization after patient creation; full management C | Full management |
| dental.appointment | Appointment R | Appointment RW: CU/actions | Full management |
| dental.treatment.plan | Clinical R | Clinical RW: CU/actions | Full management |
| dental.treatment.plan.line | Clinical R | Clinical RW: CU | Full management |
| dental.prescription | Clinical R | Clinical RW: CU/actions | Full management |
| dental.prescription.line | Clinical R | Clinical RW: CU | Full management |
| dental.practitioner | Patient/Appointment/Clinical/Configuration R (shared selectors) | Configuration RW: CU | Configuration RW |
| dental.room | Patient/Appointment/Clinical/Configuration R (shared selectors) | Configuration RW: CU | Configuration RW |
| dental.treatment | Patient/Appointment/Clinical/Configuration R (shared selectors) | Configuration RW: CU, native Product Manager synchronization | Configuration RW |
| dental.invoice.wizard | Full management | Full management: CU; accounting remains separately required | Full management |
| dental.permission.profile | Configuration R | Configuration RW: CU/archive | Not granted by business capability |
| dental.permission.apply (transient) | Configuration RW, native transient ownership | Configuration RW: CU, fixed-group application only | Native transient lifecycle |
| res.partner | Existing native read | Patient RW: create only where Dental flag is True; fixed contact facade after patient write checks | No new grant |
| hr.employee.public | Native Internal User directory read; Employee R exposes app | No new mutation | No new grant |
| hr.employee | Native public-field fallback for R; private fields HR Officer only | Employee RW -> HR Officer native CU/archive | Native HR Officer, constraints preserved |

Clinical company restrictions remain on appointments, plans, prescriptions and
their lines/wizard. Profile application requires an existing internal staff user
in an allowed company. A business Manager cannot modify a System target.

## Execution cases

| ID | Case and pass condition | Result |
| --- | --- | --- |
| CAP-01 | Five native privileges; exactly R/RW groups; RW implies own R; no cross-domain or System implication; Portal none; legacy selector empty | PASS (60-test suite) |
| CAP-02 | Each of five domains independently assigned at R and RW; effective writes and forbidden adjacent operations checked | PASS (60-test suite) |
| PRE-01 | Exact 前台/护士/仓管/医生/负责人 defaults; application yields expected groups and internal identity | PASS (60-test suite) |
| PRE-02 | Custom preset CU; Configuration R read only; lower capabilities denied; no arbitrary group field/value accepted | PASS (60-test suite) |
| PRE-03 | Apply replaces only direct Dental-managed groups; unrelated group and System/internal identity preserved | PASS (60-test suite) |
| PRE-04 | Apply 护士, manually raise Appointment to RW; profile edits/upgrades do not revert manual override | PASS (60-test suite) |
| MIX-01 | Mixed A (Patient RW, Appointment RW, Clinical R) executes all 48 Dental CRUD cells with expected denials | PASS (60-test suite) |
| MIX-02 | Mixed B (Patient R, Appointment R, Clinical RW, Employee R) executes 48 CRUD cells plus employee public read | PASS (60-test suite) |
| REG-01 | All 31 adapted AUTH01 tests, including 336 seven-role CRUD cells, retained and passing | PASS (60-test suite) |
| REG-02 | Frontdesk actual contact registration + patient creation, exact 32 FDI teeth/flag; contact whitelist/avatar/demographics; direct contact edit/delete/relink denied | PASS (60-test suite) |
| REG-03 | Clinical server guards, company restrictions, workflow buttons, reminder rollback, accounting counters, Portal backend, Product Manager boundary | PASS (60-test suite) |
| REG-04 | Patient-only view reads do not compute forbidden appointment/clinical/accounting counters | PASS (60-test suite) |
| EMP-01 | Employee R public list/read allowed; private fields/C/U/archive/D denied | PASS (60-test suite) |
| EMP-02 | Employee RW and Manager native employee C/R/U/archive/D pass for unreferenced disposable employee; native constraints remain | PASS (60-test suite) |
| SEC-01 | Manager self-System/technical groups, unrelated user-group changes, arbitrary res.groups operations denied | PASS (60-test suite) |
| SEC-02 | Forged group IDs/levels, profile injection, private-helper RPC, Portal/System/other-company target bypass denied | PASS (60-test suite) |
| UI-01 | zh_CN System user form shows 患者管理/预约管理/牙科临床/员工管理/牙科配置 with 无/只读/读写; no primary legacy role dropdown | PASS (independent Chrome) |
| UI-02 | All six internal profiles: My Subscription absent; Preferences/Help where native/Logout retained; English checked if practical | PASS (independent Chrome; optional English not separately run) |
| UI-03 | Contacts/Dashboards/Apps/Technical hidden for non-System; employee and mixed-user menus match capabilities | PASS (independent Chrome/RPC) |
| UI-04 | Manager uses real Employees UI to create, edit, archive and list; Dental preset application and manual adjustment work | PASS (independent Chrome/RPC) |
| MIG-01 | Exact accepted HEAD -> candidate; synthetic clinical rows/hashes preserved; legacy users mapped, no old assignments | PASS (exact snapshots) |
| MIG-02 | Existing AUTH01 dev -> candidate; before/after hashes for all 11 clinical models equal; seven users/lang preserved and mapped | PASS (exact snapshots) |
| INS-01 | Fresh install without demo produces groups/profiles/translations and full passing tests | PASS (60 tests) |
| REV-01 | Full cumulative odoo-security (all sudo reviewed twice), odoo-review, diff whitespace check | PASS |
| IND-01 | Separate independent Chrome + authenticated negative acceptance after implementation validation; no unexpected permits | PASS (13 Chrome scenarios, 265 authenticated checks including final HR guard supplement) |
| SEC-03 | Native HR invitation RPC requires user administration before account creation/helper; employee management alone denied; System delegation preserved without mail/account side effects | PASS (60-test suite; independent denial supplement) |

## Browser / authenticated acceptance procedure

Use review accounts `auth01.frontdesk`, `.nurse`, `.warehouse`, `.dentist`,
`.manager`, `.system`, `.portal` at `http://127.0.0.1:18069`, database
`sd_dental_dev`. Mixed accounts are supplied at execution time. Credentials are
disposable and supplied separately; never store passwords in this ledger.

1. Authenticate each user; check business menus, editable/read-only forms and
   generic app boundaries. Portal must fail direct backend clinical operations.
2. Frontdesk registers a synthetic contact/patient through Dental; verify flag,
   exactly 32 teeth, allowed contact editing and denied clinical writes.
3. Verify default profiles and both mixed users through authenticated ORM
   requests; use at least one mixed user in Chrome.
4. Manager creates/edits/archives an employee in Chrome, lists employees, and
   cannot access technical admin. Do not bypass native dependencies for deletes.
5. Manager applies a preset to a disposable existing internal staff user; verify
   unrelated direct group remains. System manually changes Appointment to RW
   and verifies the native independent selectors; no profile auto-reversion.
6. Forge self System/ERP Manager, unrelated user-group changes, arbitrary group
   records, unknown profile/wizard group fields/levels, private-helper RPC and
   Portal/System targets. Every unauthorized request must fail and preserve groups.
7. Inspect zh_CN System user permissions and profile names. Check user menu in
   six internal sessions and English: subscription absent, native retained items
   function. Log out successfully.

Record genuine failures, fix only implementation defects, rerun affected
automated gates, then rerun independent acceptance. No human review handoff with
known technical failures.

## Automated and upgrade results

- Final suite: **60 tests, 0 failures, 0 errors**. The 31 AUTH01 tests remain;
  AUTH02 adds 29 tests. Effective Dental CRUD cells: **912** (336 seven-role,
  96 mixed, 480 across ten isolated capability levels), plus contact, employee,
  workflow, field, company, profile and escalation assertions.
- Fresh no-demo install: `sd_dental_auth02_clean_60`, PASS with all 60 tests.
- Exact accepted commit archive -> `sd_dental_auth02_accepted_60` -> candidate:
  PASS with all 60 tests; all 11 stored clinical-model snapshots match exactly,
  including the synthetic patient's 32 teeth; legacy roles mapped and removed.
- Existing AUTH01 `sd_dental_dev` -> candidate: PASS with the then-complete
  49-test suite; all 11 clinical counts/hashes match exactly before/after;
  all seven account IDs/languages preserved. Final narrow HR invitation guard
  upgrade reran all 60 tests successfully; before/after hashes for all 11 models
  (including independent fixtures) and seven AUTH01 users/groups/languages are
  identical. Main Odoo and PostgreSQL services are healthy after restart.
- Preserved development baseline: 40 patients, 1,230 teeth, 14 appointments,
  19 medical histories, 22 plans/20 lines, 22 prescriptions/20 lines,
  18 practitioners, 19 rooms and 25 treatments. Independent acceptance adds
  clearly named disposable fixtures after the preservation comparison.
- `zh_CN` privilege names, placeholders, R/RW names and default profile names:
  standard Odoo translation import PASS. POT references accompany new PO terms.
- Both cumulative review passes PASS; four fixed elevation sites reviewed twice.
  `git diff --check` PASS. During final human-authorized commit preparation, 139 disposable AUTH01 artifacts were archived outside Git with verified hashes; original detailed documents were preserved there before condensation.
- Independent acceptance: **265/265** authenticated checks (134 allowed,
  131 correctly denied), zero unexpected permits/errors; **13** composite real
  Chrome scenarios and 96 mixed-user actual CRUD cells. Post-fix HR invitation
  RPC denied for eight business/external actors before native account creation;
  user count and employee account link stayed unchanged. No invitation email was
  sent. Details are in `DENTAL_AUTH_02_INDEPENDENT_ACCEPTANCE.md`.

## Complete cumulative changed-source manifest

All paths below are relative to the Dental repository. This includes both
tracked modifications and untracked source/tests, **27 files** total.

```text
dental_clinic/__manifest__.py
dental_clinic/data/dental_permission_profile_data.xml
dental_clinic/i18n/dental_clinic.pot
dental_clinic/i18n/zh_CN.po
dental_clinic/models/__init__.py
dental_clinic/models/dental_patient.py
dental_clinic/models/dental_permission_profile.py
dental_clinic/models/hr_employee.py
dental_clinic/models/res_partner.py
dental_clinic/models/res_users.py
dental_clinic/security/dental_security.xml
dental_clinic/security/ir.access.csv
dental_clinic/static/src/user_menu/user_menu.js
dental_clinic/tests/__init__.py
dental_clinic/tests/test_authorization.py
dental_clinic/tests/test_capabilities.py
dental_clinic/views/dental_appointment_views.xml
dental_clinic/views/dental_menus.xml
dental_clinic/views/dental_patient_views.xml
dental_clinic/views/dental_permission_profile_views.xml
dental_clinic/views/dental_prescription_views.xml
dental_clinic/views/dental_treatment_plan_views.xml
dental_clinic/views/res_partner_views.xml
dental_clinic/views/res_users_views.xml
dental_clinic/wizards/__init__.py
dental_clinic/wizards/dental_permission_apply.py
dental_clinic/wizards/dental_permission_apply_views.xml
```

Schema additions: persistent `dental.permission.profile` (name/active/five levels),
transient `dental.permission.apply` (staff/profile/five levels); standard HR
dependency schema. The only added patient field is non-stored
`can_repair_contact`; all 11 clinical stored schemas/data remain unchanged.

Permanent AUTH02 documentation is limited to the capability model, this ledger
and one concise independent acceptance report. No AUTH02 raw captures entered Git.


## Final human-approved commit preparation

AUTH01 and AUTH02 human review approved on 2026-10-09. Source bytes were frozen;
the full 60-test authorization suite was rerun before commit with zero
failures/errors. The authorized commit includes 27 source/test files and nine
concise permanent documents. Disposable raw artifacts and original expanded
reports are retained outside Git in
`D:\Code\odoo\.tmp\authorization-final-20261009`; final suite output remains
under `D:\Code\odoo\.tmp\auth02`. No credentials or raw acceptance files are
included. Post-commit verification checks parent/branch, exact file list, clean
worktree, whitespace and a full suite rerun on committed source.
