# DENTAL-AUTH-01-R1 acceptance cases

Historical AUTH01 result: **217/217 PASS**, zero FAIL/NOT RUN, across seven
actors and 31 categories. Human approval now closes AUTH01 and AUTH02 together.
AUTH02's capability model supersedes the original role authority and gives
Frontdesk Clinical Read, including plans/prescriptions. Current behavior and
validation are in [AUTH02 acceptance](DENTAL_AUTH_02_ACCEPTANCE_CASES.md).

## Oracle and execution

The [V1 role matrix](DENTAL_AUTH_V1_ROLE_MATRIX.md) supplied the historical oracle.
Independent agents used actual role sessions in Chrome and authenticated HTTP
against isolated `sd_dental_dev`; implementation tests were not acceptance proof.
Case IDs are `R1-<role>-<category>` for Portal, Frontdesk, Nurse, Warehouse,
Dentist, Manager and System Administrator. Each category below passed for all
seven actors, including expected denials corroborated by AccessError.

| Category | Required boundary |
| --- | --- |
| A | Application switcher |
| B | Dental navigation |
| C | Patient list |
| D | Patient creation |
| E | Patient form read |
| F | Administrative patient update |
| G | Clinical patient update |
| H | Patient deletion |
| I | Existing-contact selection during registration |
| J | New contact through actual Dental registration dialog |
| K | Approved linked-contact edits, including Portal-linked contact |
| L | Unrelated direct Contact write |
| M | Direct Contact deletion |
| N | Existing-patient contact relink/Manager repair |
| O | Tooth read |
| P | Tooth write and nested-command attempts |
| Q | Medical information/history read |
| R | Medical information/history write and context/default injection |
| S | Appointment creation |
| T | Appointment read |
| U | Appointment update/workflow |
| V | Appointment deletion |
| W | Treatment-plan read |
| X | Treatment-plan mutation |
| Y | Prescription read |
| Z | Prescription mutation |
| AA | Configuration/catalog mutation |
| AB | Generic Contacts application visibility |
| AC | Generic Dashboards application visibility |
| AD | Technical/user/group administration |
| AE | Explicit forbidden transport operation/private helper |

Registration covered both an existing unmarked contact and the real browser
Create and edit dialog. Saved contacts received the Dental flag; each verified
patient had exactly 32 adult FDI teeth. Frontdesk contact/demographic edits and
populated clinical read-only views passed. Dentist clinical work, Nurse reads,
Warehouse/Portal denials and Manager/System repair/deletion passed. Hidden
menus/readonly controls were never substituted for server authorization checks.

## Results and evidence retention

- Seven actual Chrome logins; 196 UI role/category observations.
- The remaining 21 category rows were authenticated RPC-only controls.
- Independent HTTP: 903 accepted requests, 336 actual CRUD cells, 376 expected
  AccessError denials, 527 positive responses and 97 value assertions.
- Zero final unexpected permits or unresolved implementation failures.

See [browser summary](DENTAL_AUTH_01_INDEPENDENT_ACCEPTANCE.md) and
[HTTP summary](DENTAL_AUTH_01_RPC_ACCEPTANCE.md). The original detailed ledger,
raw JSON, screenshots, DOM captures, logs and one-off upgrade harness are
preserved outside Git in
`D:\Code\odoo\.tmp\authorization-final-20261009`, with an initial SHA256
inventory and hash-verified archival moves. No credentials are committed.
