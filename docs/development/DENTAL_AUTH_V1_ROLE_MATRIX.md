# Dental V1 authorization oracle

Task: DENTAL-AUTH-01. Date: 2026-10-09 (Asia/Shanghai).

Status: **Human approved for formal closure with AUTH02**. This is the historical AUTH01 oracle, not the final group implementation. AUTH02 replaces roles with five independent capabilities and gives Frontdesk plan/prescription read through Clinical Read. See [the final capability model](DENTAL_AUTH_02_CAPABILITY_MODEL.md).
This is the independent test oracle for the authorization matrix. See the
[verification and review report](DENTAL_AUTH_01_AUDIT.md).

## Actors and groups

| Actor | Identity / group | Responsibility |
| --- | --- | --- |
| Patient | `dental.patient.partner_id`, external identity with `base.group_portal` | External patient; no Dental backend access in V1 |
| Frontdesk | `dental_clinic.group_dental_receptionist` | Administrative patient and appointment work |
| Nurse | `dental_clinic.group_dental_nurse` | Read clinical context |
| Warehouse | `dental_clinic.group_dental_warehouse` | Reserved role; no current Dental access |
| Dentist | `dental_clinic.group_dental_user` | Clinical work; appointments read-only |
| Manager | `dental_clinic.group_dental_manager` | All Dental business capabilities and configuration |
| System Administrator | `base.group_system` | Standard Odoo administration plus Dental Manager |

Arrows mean "implies":

```text
base.group_system -> Dental Manager -> Frontdesk
                                   -> Nurse
                                   -> Warehouse
                                   -> Dentist
                                   -> product.group_product_manager
```

The four capability roles are independent and imply standard internal-user
identity. Manager does not imply System Administrator. Existing Frontdesk,
Dentist and Manager external IDs are preserved. The legacy explicit
`base.user_admin` membership is removed; its Dental authority comes from
`base.group_system`. Portal patients are not internal Dental employees.

## Model permissions

C = create, R = read, U = update, D = delete, `-` = no access.
These are effective permissions for users having only the indicated role and
necessary standard identity. Unrelated application roles must not mask failures.

| Model | Portal | Frontdesk | Nurse | Warehouse | Dentist | Manager | System Admin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `dental.patient` | - | CRU | R | - | RU | CRUD | CRUD |
| `dental.medical.history` | - | R | R | - | CRU | CRUD | CRUD |
| `dental.practitioner` | - | R | R | - | R | CRUD | CRUD |
| `dental.room` | - | R | R | - | R | CRUD | CRUD |
| `dental.tooth` | - | R | R | - | RU | CRUD | CRUD |
| `dental.treatment` | - | R | R | - | R | CRUD | CRUD |
| `dental.treatment.plan` | - | - | R | - | CRU | CRUD | CRUD |
| `dental.treatment.plan.line` | - | - | R | - | CRU | CRUD | CRUD |
| `dental.appointment` | - | CRU | R | - | R | CRUD | CRUD |
| `dental.prescription` | - | - | R | - | CRU | CRUD | CRUD |
| `dental.prescription.line` | - | - | R | - | CRU | CRUD | CRUD |
| `dental.invoice.wizard` | - | - | - | - | - | CRUD | CRUD |

Group-less restrictions cover all CRUD on appointments, treatment plans and
prescriptions, their lines through the parent company, and invoice wizards
through the plan company. Optional empty companies remain shared. Patient,
medical history, tooth and catalog models have no company field and remain
shared; this task adds no company schema.

Only Manager (and therefore System Admin) receives the explicitly approved
standard Product Manager capability because treatments maintain backing service
products. No Dental role receives accounting or Contact Manager authority.
Invoice-wizard CRUD tests supply a valid journal explicitly. Full invoicing
requires separately configured standard accounting permissions.

## Menu visibility

V = visible; `-` = hidden. Selector read access does not expose configuration
menus. Hidden menus do not replace model permissions.

| Surface | Portal | Frontdesk | Nurse | Warehouse | Dentist | Manager | System Admin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Patients | - | V | V | - | V | V | V |
| Appointments / Calendar / Today | - | V | V | - | V | V | V |
| Treatment Plans | - | - | V | - | V | V | V |
| Prescriptions | - | - | V | - | V | V | V |
| Standalone Odontogram menu | - | - | V | - | V | V | V |
| Patient Odontogram tab | - | V | V | - | V | V | V |
| Dental Configuration, including practitioner/room/treatment | - | - | - | - | - | V | V |
| Apps / technical Settings | - | - | - | - | - | - | V |
| Generic Contacts / Dashboards root apps | - | - | - | - | - | - | V |

Source-backed Apps exception: auto-installed `base_install_request` replaces
the standard Apps menu restriction with `base.group_user_regular`. Dental
restores `base.menu_management` to `base.group_system` using addon XML, as
permitted by the task. No Settings override or Odoo Core change is needed.
A separate later upgrade of `base_install_request` can replace this configuration
again; reapply the Dental module update after such an upgrade.

The invoice menu additionally requires normal `account.move` read access via
Odoo's action-model menu filtering. Empty Billing parents are not reachable.
Plain Dental Manager/System Admin roles alone do not gain accounting rights.

## Form and action boundaries

- Frontdesk sees editable administrative patient information and appointments.
  Medical Info and the patient Odontogram are visible read-only. Treatment Plans,
  Prescriptions and clinical stat buttons remain hidden. Appointment lifecycle/reminder buttons require Frontdesk membership.
- Nurse sees intended clinical areas for reading, without write buttons.
- Dentist sees clinical patient areas and treatment/prescription actions,
  without appointment management or invoice-wizard authority.
- Manager/System Admin see configuration and administrative/clinical actions.
- Invoice entry points require Manager plus standard accounting access.
  Create Invoice requires `account.group_account_invoice`; invoice stat buttons
  permit that group or `account.group_account_readonly`.
- Warehouse and Portal cannot access Dental clinical models or menus.

Frontdesk patient creation generates exactly the 32 adult FDI teeth (11-18,
21-28, 31-38, 41-48). Private initialization elevates only fixed healthy child
values and discards caller context defaults. Caller-supplied relational
commands retain normal ACL checks.

The fixed contact flag runs after normal patient creation and contact read
checks. The authorized contact facade separately permits name, phone, mobile,
email, street, city, zip, country_id and the existing UI's image_1920. Effective
patient write access, Frontdesk membership and field checks precede the exact
whitelisted partner synchronization, with caller context cleared. General
partner write/delete remains denied to Frontdesk. Dentist contact maintenance
is denied even though Dentist can update patient clinical fields.

Frontdesk may select partner_id on creation but cannot relink existing patients;
the form enforces this too. Manager/System retain explicit repair authority.
Contact fields/avatar are read-only for Dentist/Nurse. Address synchronization
uses the native narrow updater so parent/sibling/child contacts do not change.
Internal-user contact edits and bank-linked name changes additionally require
normal user/bank write authority before any elevation. Portal-linked contact
identity fields are maintained through the same fixed whitelist; login, password,
groups, activity and company authorization are never forwarded.

The native selector supplies default_is_dental_patient=True. Frontdesk has a
create-only res.partner permission with actual ORM domain
`[('is_dental_patient', '=', True)]`; Manager/System aggregate Frontdesk.
Unmarked/false-flag creation is denied. A caller can explicitly create a
Dental-marked contact under this approved ACL, without a UI-only security token.
No general partner write/delete or Contact Manager group follows from it.

Appointment, plan, prescription and accounting patient computations are split.
Clinical counters have clinical field groups; accounting aggregates have
standard accounting field groups and use normal ORM/company rules, without
elevation. Frontdesk patient form reads do not require accounting reads.

## Deferred boundaries

Reuse `base.group_portal` without adding a manifest dependency solely for that
group. No Portal pages/controllers or restricted "my data" backend access in
this task. Warehouse has no inventory implementation or clinical grants; no
`stock` or `product_expiry` installation/dependency. No workflow redesign.

The approved patient-contact facade resolves the prior related-write blocker.
Patient U permission alone does not grant contact maintenance: Frontdesk role
membership is also required, and arbitrary partner fields remain inaccessible
through the facade. No Portal, inventory or other deferred feature is added.

Clinical-page hiding is a UI boundary. This task does not add field-level
confidentiality for every existing clinical scalar on the otherwise readable
patient model.

## Acceptance evidence

PASS: 31 authorization test methods, including 336 actual ORM CRUD cells across
12 models and 7 actors; denied operations raise `AccessError`. Group semantics,
reachable menus, processed patient views/buttons, workflow smoke tests, fixed
teeth, contact/accounting/product boundaries, Portal denial and company
restrictions pass. The native new-contact quick-create plus patient Form save,
whitelist propagation, relink denial and hierarchy/user/bank boundaries pass.
Clean installation and exact accepted-source baseline upgrade pass; all 11
clinical-model snapshots are preserved. Independent authenticated HTTP acceptance
passes 336 CRUD cells and all targeted boundaries. Seven-role real Chrome
acceptance and all 217 case results PASS. See DENTAL_AUTH_01_INDEPENDENT_ACCEPTANCE.md
and DENTAL_AUTH_01_RPC_ACCEPTANCE.md for exact counts, evidence and rerun history.

## R1 human-approved field and application boundaries

Frontdesk administrative write fields: name, gender, birth_date, national_id,
marital_status, occupation, phone, mobile, email, street, city, zip, country_id,
emergency_name, emergency_phone, emergency_relation, image_1920. Dentist cannot
maintain these demographics/contact fields unless independently assigned Frontdesk.

Frontdesk reads blood_type, allergies, chronic_diseases, current_medications,
smoker, pregnant, clinical notes, existing medical histories and teeth. Writes
to these clinical scalars or medical_history_ids/tooth_ids/treatment_plan_ids/
prescription_ids are denied on create/write, including explicit context defaults.
Dentist clinical writes remain allowed. Nurse remains read-only.

The Dental Contact selector uses the native form_view_ref context to open
res_partner_view_dental_registration. Its name widget is restored to standard
char after partner_autocomplete's _get_view override, for this fixed view only.
No paid/company autocomplete or IAP rights are needed. The ordinary Contacts
form and global IAP behavior remain intact.

Generic Contacts and Dashboards root menus are restricted to base.group_system.
Discuss/Calendar remain standard. This is menu visibility, not a generic deny of
standard Contact reads or standard dashboard services. No added Contact/IAP/User/
Accounting role is used. A later standalone upgrade of an owning standard module
can reset its root menu groups; reapply -u dental_clinic afterward.
