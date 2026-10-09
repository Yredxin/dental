# DENTAL-AUTH-01 authorization review

AUTH01 and AUTH02 are human approved for formal closure in one cumulative
implementation commit. Accepted parent:
`2d3b6c8a023fd59ad71fee1fb80cb660d9d8dfbf`, branch `port/odoo20-demo`.
This concise historical AUTH01 review replaces duplicated execution transcripts;
[AUTH02](DENTAL_AUTH_02_CAPABILITY_MODEL.md) defines the final capability model.

## Reuse and implementation

Pinned Community source `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` and installed
Odoo `20.0-20260926` were inspected. No SD implementation beyond its README or
sibling Enterprise checkout was available. Native groups, `ir.access`, field
groups, form-view selection and product backing records were reused.

- Patient/contact registration uses a fixed Dental primary Contact form. A
  narrow `res.partner._get_view` extension restores its name widget to plain
  char after native partner autocomplete; generic Contact forms are unchanged.
  Registration requires no enrichment call, IAP Manager or broad Contact role.
- The patient model is the controlled contact facade. Effective patient write
  authority and the administrative capability gate precede scalar whitelist
  synchronization. Clinical authority alone cannot maintain demographics.
- Patient counters are split so readable patient forms do not force forbidden
  appointment/clinical/accounting reads. No unrelated Accounting permission is
  granted to fix computation side effects.
- Clinical fields, indirect relations and caller defaults are guarded on the
  server. Company restrictions cover every relevant CRUD operation.
- Generic Contacts/Dashboards roots are System-only. Menu hiding does not claim
  a global prohibition of native model reads.
- Manager's Product Manager reuse supports treatment backing products; ordinary
  clinical/Frontdesk/Nurse/Warehouse roles receive no such grant.

## Elevation review

All three AUTH01 sites were reviewed twice, including callers/context/targets:

| Site | Containment |
| --- | --- |
| Contact flag after successful patient creation | Linked contact only; fixed `is_dental_patient=True`; normal read gate; empty context |
| Patient contact synchronization | Linked contact only; fixed contact/avatar scalar whitelist; normal internal-account/bank-holder checks; no arbitrary values, child commands or hierarchy propagation |
| Private odontogram initialization | Access-checked patient; fixed 32 healthy adult FDI children; empty context; caller commands/defaults excluded |

Private helpers are not remotely callable, even by System. Direct generic
Contact write/delete, unauthorized relink, clinical write and technical/group
escalation remain denied. Portal-linked contact editing does not change login,
password, groups, active state or company authority.

## Review and validation

AUTH01 R1: 31 automated tests, 336 effective seven-role CRUD cells, clean install
and exact accepted-source upgrade passed; all 11 clinical snapshots preserved.
Independent acceptance passed 217 cases and 903 accepted HTTP requests.
Early malformed harness calls and native-IAP oracle errors were disclosed and
excluded from accepted totals; no ACL was widened to make them pass.

The final cumulative suite has **60 tests, zero failures/errors, 912 actual
Dental CRUD cells**. Fresh installation, exact committed-parent upgrade and
development upgrade passed. Final independent AUTH02 acceptance passed 265
authenticated checks and 13 Chrome scenarios. The native HR invitation RPC gap
found in AUTH02 review was closed and independently rechecked.

`odoo-security` and `odoo-review`: PASS, no unresolved material findings.
Guidelines read: imports/naming/translation, ORM/context/computes/transactions,
fields, XML, access rights, tests, performance, stable changes, manifest/module
structure, comments; web JavaScript/assets; project reuse policy. The final
per-file mapping and fourth elevation site are recorded in AUTH02's review.

Core/composition source, production/NAS and deferred features were not changed.
Native IAP internal account create/non-secret metadata read remains standard;
non-System write/delete/token and service-management denials passed. Existing
accounting workflows still require native accounting authority. Raw evidence and
the original reports are retained outside Git under
`D:\Code\odoo\.tmp\authorization-final-20261009`.
