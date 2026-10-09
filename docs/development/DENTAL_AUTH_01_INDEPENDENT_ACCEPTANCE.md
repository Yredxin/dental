# DENTAL-AUTH-01-R1 independent browser acceptance

Historical result: **PASS**, 2026-10-09, isolated `sd_dental_dev` at
`http://127.0.0.1:18069`. Separate acceptance agents used seven actual zh_CN
role logins in real Google Chrome, live rendered UI and authenticated HTTP.
Implementation tests/conclusions were not used as acceptance proof.

## Results

196 UI role/category observations plus 21 RPC-only category rows produced
**217/217 PASS**, zero FAIL/NOT RUN. Counts represent observed categories, not
217 distinct mutations. The separate HTTP gate passed 903 accepted requests,
376 AccessError denials, 336 actual CRUD cells and 97 value assertions.

| Role | Browser result |
| --- | --- |
| Frontdesk | New/existing-contact registration saved; flag/exact 32 FDI verified independently; approved demographics and Portal-linked contact edits passed; populated clinical context read only; forbidden deletion/config/admin entries absent |
| Nurse | Patient/history/teeth/appointments/plans/prescriptions opened read only; creation/mutation/admin entries absent |
| Warehouse | Discuss/Calendar only; Dental absent; forced patient entry denied |
| Dentist | Demographics/contact read only; clinical/history/tooth and plan/RX operations saved; appointments read only; registration/config/admin entries absent |
| Manager | Registration/contact/clinical work and relink repair saved; disposable patient/appointment deletion and catalog operations passed; generic administrative apps absent |
| System | Dental workflows passed; Contacts/Dashboards/Apps/Settings opened; technical menu observed |
| Portal | Login landed on `/my`; backend entry redirected; no Dental backend UI |

Frontdesk executed both the native new-contact dialog and existing unmarked
contact selection. Independent reads verified each saved contact flag and its
own exact 32 teeth. Populated allergy/history/tooth values were reopened as read
only. Own HTTP cross-check made six requests, including two actual AccessError
denials for patient deletion and clinical mutation. Hidden controls alone were
not treated as server authorization proof.

Only disposable synthetic fixtures were mutated/deleted. Common fixtures were
preserved; Portal-linked contact edits were restored. No credentials/session
tokens, addon/Core/composition changes or production operations were involved.
Early oracle/harness corrections are summarized in the
[authenticated report](DENTAL_AUTH_01_RPC_ACCEPTANCE.md).

AUTH02 later supersedes the role implementation and adds Frontdesk plan/RX
read, independent capabilities and Employee management; see its
[final independent acceptance](DENTAL_AUTH_02_INDEPENDENT_ACCEPTANCE.md).
Original detailed reports, screenshots, DOM/JSON evidence and case mappings are
preserved outside Git in
`D:\Code\odoo\.tmp\authorization-final-20261009`.
