# DENTAL-AUTH-01-R1 independent authenticated acceptance

Historical result: **PASS**, 2026-10-09. A separate agent used actual seven-role
cookie-authenticated HTTP sessions against isolated `sd_dental_dev`. The human
request, case ledger and frozen matrix supplied the oracle. Implementation tests
and sudo ORM calls were not acceptance proof. No credentials/tokens were stored.

## Accepted results

| Measure | Count |
| --- | ---: |
| Accepted HTTP requests, including authentication/setup | 903 |
| Expected and actual AccessError denials | 376 |
| Positive responses | 527 |
| Actual model CRUD cells | 336 |
| Value-level assertions | 97 |
| Final unauthorized permits / other failures | 0 / 0 |

The CRUD matrix exercised 12 models x seven actors x four operations against
valid synthetic records. Positive responses alone did not prove group values,
contact flags, healthy/exact 32 teeth or unchanged Portal-user authorization;
those properties had explicit returned-value assertions.

Patient registration passed for Frontdesk/Manager/System with both existing and
new contacts; denied for Portal/Nurse/Warehouse/Dentist. Contact-field whitelist,
demographic/clinical separation, direct generic Contact write/delete, relink
repair, company restrictions and configuration/product boundaries passed.
Nested x2many operations 0-6, caller defaults, forged uid/su/context flags and
user/group escalation were tested. System's private odontogram RPC call was
denied with unchanged patient/contact/tooth snapshots. Invoice-wizard CRUD used
a valid journal without generating invoices. Common fixtures were preserved.

## Disclosed oracle and harness corrections

Two early expectations incorrectly denied native internal IAP account creation
and non-secret metadata read. Both pinned and installed native source grant
those operations to Internal User; tokens and administration remain restricted.
The corrected oracle verified all non-System account write/delete/token and
service-management denials. No Dental permission was widened; no enrichment,
provider, credit, reminder or invitation operation was sent.

All historical runs contained 1,587 attempts/1,586 responses, including one
sandbox preflight refusal, 57 malformed/invalid-fixture calls and the two IAP
oracle mismatches. These were disclosed and excluded from the accepted set.
Corrected slots, valid fixtures and supported method signatures were rerun.
The accepted set has no malformed denial or expected-ALLOW AccessError.

Original request/response evidence, summaries, case mappings and detailed report
are preserved outside Git in
`D:\Code\odoo\.tmp\authorization-final-20261009`. They are not committed raw
artifacts. The final cumulative independent gate is documented separately in
[AUTH02 acceptance](DENTAL_AUTH_02_INDEPENDENT_ACCEPTANCE.md).
