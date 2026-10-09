# DENTAL-AUTH-02 capability model

Baseline: `port/odoo20-demo`, accepted commit
`2d3b6c8a023fd59ad71fee1fb80cb660d9d8dfbf`. AUTH02 evolves the preserved AUTH01
candidate. Human review approved their final cumulative implementation commit;
raw evidence and original expanded reports are preserved outside Git.

## Reuse audit (PROCEED)

Pinned Community reference: `D:\odoo-sd\odoo20-clean`, commit
`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`. Runtime:
`odoo:20.0-20260926`, isolated `sd-odoo-dev`, `sd_dental_dev` only.
No existing SD addons were found in `odoo-sd/addons` beyond its README.

| Requirement | Classification | Inspected implementation / decision |
| --- | --- | --- |
| Independent capability selectors | CONFIGURE | `base/models/res_groups_privilege.py`, `res_groups.py` (`_get_view_group_hierarchy`, `_compute_disjoint_ids`), `base/views/res_users_views.xml`, Web `res_user_group_ids_field`. One privilege per domain; None is no group; RW implies R. Disjointness applies to user types, not independent privileges. These files match the installed runtime byte for byte. |
| Employee Read | USE | Native `hr.employee.public`, normal internal-user directory read. `hr.employee` private-field checks and public-read fallback inspected in the actual runtime. No private-HR read ACL added. |
| Employee RW | CONFIGURE | Native `hr.group_hr_user` (Officer), `hr/security/ir.access.csv`, `hr/views/hr_views.xml`, employee create/write/archive/unlink. Officer implies Internal User, not HR Administrator or System. `hr` is an authorized new dependency. Standard HR support models remain native. Runtime HR security/views match pinned files; employee source differs in badge validation, HR-responsible domain, leave interval and avatar fields, not the audited access fallback or CRUD paths. |
| Optional permission presets | EXTEND | Small `dental.permission.profile` and transient application form wrap fixed group assignments on native users. Explicitly authorized by AUTH02. No policy engine or employee master is needed. |
| Employee account invitation | EXTEND | Runtime `hr.employee.action_send_invitation` can call private sudo Light User creation without the `base.group_erp_manager` check on its native Invite button. Dental adds that exact native administration gate plus normal employee write access before delegation. Employee CRUD remains native; no account-provisioning workflow is added. |
| Hide subscription item | EXTEND | Native `mysubscription/static/src/user_menu.js` registers `mysubscription_user_menu` in Web `user_menuitems`. Dental asset removes that entry after importing the native module. `mysubscription` is a direct dependency for ordering. No Core patch. Runtime source matches; runtime manifest differs only in package metadata. |
| Existing patient security | EXTEND | Existing AUTH01 contact facade, field guards, three fixed elevation sites and split counters remain; their authority changes to capability groups. |

Rejected reinventions: custom authorization engine/editor, custom employee model,
arbitrary-group presets, Core JavaScript patches. Human decisions in AUTH02
authorize the profile schema, HR dependency and narrow Dental group application.

## Native authority

Exactly five `res.groups.privilege` records, each with Read and Read/Write
`res.groups`. Read/Write implies its own Read; no Dental domain implies another.
None means no group. Chinese labels use standard Odoo translations.

| Domain | zh_CN | Read/Write authority |
| --- | --- | --- |
| Patient Management | 患者管理 | Patient create and administrative/contact maintenance; clinical fields remain separately guarded |
| Appointment Management | 预约管理 | Appointment create/update/actions, no physical deletion |
| Dental Clinical | 牙科临床 | Existing clinician operations, no historical deletion |
| Employee Management | 员工管理 | Native HR Officer employee CRUD/archive and native constraints |
| Dental Configuration | 牙科配置 | Existing catalog/configuration, Product Manager reuse, permission presets and fixed Dental capability application |

Every Read group implies Internal User. Employee RW also implies HR Officer;
Configuration RW also implies Product Manager. System Administrator directly
implies all five RW groups. No business group implies System Administrator.
Portal remains external and receives none.

Native internal users retain Odoo's public employee-directory read baseline.
Employee None hides the Employees application for Dental-only users; it does not
remove unrelated native internal-user directory rights. Employee Read exposes
the public directory, never private HR fields.

## Default presets

| Profile | Patient | Appointment | Clinical | Employee | Configuration |
| --- | --- | --- | --- | --- | --- |
| 前台 | RW | RW | R | None | None |
| 护士 | R | R | R | None | None |
| 仓管 | None | None | None | None | None |
| 医生 | R | R | RW | None | None |
| 负责人 | RW | RW | RW | RW | RW |

AUTH02 explicitly gives 前台 read-only plans and prescriptions through Clinical
Read. Profiles are mutable normal records, not continuously synchronized policy.
Applying replaces only direct Dental capability/compatibility groups and keeps
unrelated groups. Manual overrides remain effective. Manager application is
limited to existing internal staff in allowed companies and excludes System
Administrator targets. No user-account provisioning or arbitrary group input.

The native user form exposes the five independent selectors and an optional
Apply Dental Permission Profile action. A narrow Dental application form also
lets Configuration RW users adjust only those five levels for staff.

## Compatibility and deletion

Legacy role XML IDs remain hidden compatibility aggregators without a primary
privilege selector. Upgrade migrates direct legacy assignments to the equivalent
capabilities and removes those old assignments. It runs only on remaining legacy
memberships, so subsequent upgrades preserve manual capability changes.

Existing Manager/System Dental deletion and contact-repair exceptions require
all five RW capabilities. This is the same effective combination as 负责人,
without a sixth capability or legacy role as an authority source. A single RW
capability does not grant those exceptions. Ordinary patient and appointment RW
remain CRU; clinical history RW remains CRU and tooth RW remains RU.

## Validation

Execution results and complete model ACL mapping are recorded in
`DENTAL_AUTH_02_ACCEPTANCE_CASES.md`. Raw logs, snapshots, backups, browser
captures and disposable harnesses stay outside Git in `D:\Code\odoo\.tmp\auth02`.

## Cumulative security and Odoo review

Reviewed the live worktree against accepted HEAD above, including untracked
source/tests, in both rules and merits passes. All five project skills were
discoverable and applied. No sibling Enterprise checkout or SD implementation
was available; all available Community/Dental/SD consumers were searched.
Legacy XML IDs and public method signatures are preserved. This is the explicitly
authorized AUTH02 feature/schema change on the project's Odoo 20 port branch.

| Changed files (complete source manifest in acceptance ledger) | Guidelines mapped/read |
| --- | --- |
| Manifest | Manifest, module structure, stable changes, comments |
| Model/wizard Python and their imports | Python imports/naming/translation, ORM/context/computes/transactions/methods, fields, performance, security, stable changes, comments |
| Security XML/CSV | Access rights, fields, XML/data, company restrictions, security, stable changes, comments |
| Views and profile data | XML/data/inheritance anchors, fields/groups, security, stable changes, comments |
| User-menu JavaScript | Web JavaScript feature organization/registry extension, assets, security, stable changes |
| Tests | Tests, Python, ORM, fields, access rights/security, stable changes, comments |
| POT/PO and documentation | Translation/field/XML contracts, stable changes, project reuse policy and audit evidence |

Every production elevation site was reviewed twice, including its public caller,
normal-user gates, target scope, forwarded values/context and x2many behavior:

| Site | Allowed operation and boundary |
| --- | --- |
| Patient create: fixed partner flag | Successfully created patients' linked contacts, normal contact read check, only `is_dental_patient=True`, empty context |
| Patient contact facade | Effective patient write + Patient RW, linked contacts only, nine scalar contact/avatar fields; internal-account and bank-holder normal write checks; no hierarchy propagation or arbitrary patient values |
| Private odontogram initializer | Access-checked patient, fixed 32 FDI children/healthy values, empty context; no caller child commands |
| Private Dental capability application | Configuration RW caller; readable internal staff in allowed company; Manager cannot target System; unlink only managed memberships and link only fixed capability IDs/Internal User; no arbitrary commands, groups, user fields or caller context |

Sweeps found no production raw SQL, eval/deserialization, file operations,
controllers, HTML injection sinks or added credentials. Existing public workflow
actions retain normal ORM enforcement; new wizard action checks transient write
authority and the private user helper revalidates authorization. Native user/group
and technical-administration boundaries were checked with normal ORM and
independent authenticated negative requests.

Security review: PASS, no unresolved material findings. Odoo review: PASS, no
blocking findings. Remaining native implications are intentionally additive:
unrelated groups are preserved even if an administrator separately configured
them to imply Dental capabilities; presets cannot negate native Odoo authority.

Closed review finding (judgement / public RPC authorization): native HR's
employee invitation method exposed account provisioning to the newly reused HR
Officer permission. The additive Dental `hr.employee` override now rejects
callers without native user-administration authority before accessing the
employee or provisioning helper, and checks employee write access for allowed
administrators. Its API/signature and native return/delegation remain intact;
all available addons consumers were checked. The regression test proves every
business role, both mixed users and isolated Employee RW are denied before the
helper, and native System delegation remains available using a mocked helper
without creating an account or sending mail. This fix adds no sudo.

Guidelines read: module_structure, manifest, python, orm, fields, xml, security,
performance, tests, stable, comments; Web javascript/assets; odoo-security;
odoo-review; sd-odoo-dental and the project reuse matrix.
