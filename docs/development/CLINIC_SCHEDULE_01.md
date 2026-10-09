# CLINIC-SCHEDULE-01: employee workstation scheduling

Candidate date: 2026-10-09 (Asia/Shanghai). No commit or push authorized.
Baseline: `port/odoo20-demo`, local and fetched remote
`00b6eee266782b2f7a0620ee923858f9273f9165`; clean initial worktree.
CLINIC-SPACE-01 is accepted. Pinned Community reference:
`D:/odoo-sd/odoo20-clean`, `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`.
The isolated development image is `odoo:20.0-20260926`; its source is not
asserted to have the pinned reference SHA.

## Source-backed reuse audit

Requirement: employee + workstation + concrete start/stop datetime.

- USE: `hr.employee` (`addons/hr/models/hr_employee.py`) is the common staff
  identity, with native Resource and user relationships. No practitioner link.
- USE: existing `sd.facility.station` is the Resource-backed operational
  workstation identity. Existing `sd_facility` remains HR-independent.
- USE: `resource.calendar` and `resource.calendar.attendance`
  (`addons/resource/models/`) describe normal availability, including recurrent
  and dated attendances. Their interval/collision APIs do not represent a
  concrete employee-to-station placement. Neither employee nor station
  availability is changed or used as a rejection rule.
- NEW: `sd.facility.assignment`. `hr.employee.location`
  (`addons/hr/models/hr_employee_location.py`) has `date`, `employee_id`, and
  `hr.work.location`, with one exception per employee/date, not intraday
  workstation intervals. `hr.version` stores effective employment records and
  contract dates, not operational placements. `hr.attendance` records actual
  check-in/out, not planned workstation assignments. `calendar.event` has
  meetings, partner attendees and notification/recurrence semantics without
  employee/station identity or the required privacy and exclusivity.
  Odoo 20 Community `hr_work_entry` derives work-entry intervals from calendars
  and time rules (`models/hr_version.py`, `hr_time_rule.py`); its
  `hr.user.work.entry.employee` is a personal calendar filter, with no time span
  or station. Resource Calendar Leaves represent time off/working-time
  exceptions, not employee-to-station placement.
- CONFIGURE: native Odoo 20 `ir.access` permission/restriction rows, group
  implications, list/form/search actions, archive and translation mechanisms.
  This pinned version unifies the older ACL/record-rule models in `ir.access`.
- EXTEND: Dental Employee Management group implications, preserving the five
  AUTH02 capabilities and existing capability application mechanism.

Searches across pinned Community addons, current Dental, `sd_facility` and
composition `D:/Code/odoo/odoo-sd/addons` found no matching model. The composition
addon directory contains only its README. No Enterprise Planning inspected.
Constraint extension point: `odoo/orm/table_objects.py:Constraint`, with native
EXCLUDE usage in `addons/l10n_fr_pdp/models/account_edi_proxy_user.py` and
serialized ORM collision checking in Resource Calendar Attendance inspected.
Decision: PROCEED under the human-approved single implementation task.

## Model and lifecycle

Generic addon `sd_facility_schedule` depends exactly on `hr`, `sd_facility`.
Assignment fields: `employee_id`, `station_id`, `start`, `stop`,
`assignment_type`, `reason`, `company_id`, `active`, plus native ORM identity,
display and audit fields. Required employee/station references use restrict
foreign keys. `_check_company_auto`, checked relations and exact-company
server constraints prohibit cross-company placement, including related companies.

Planned (`正式排班`) is a normal manager-created schedule, with optional reason.
Temporary (`临时排班`) is exceptional placement and requires a nonblank reason.
The future workspace action can collect a reason as part of its constrained
creation; it is not implemented here and does not justify a self-create grant.

Intervals are UTC datetimes displayed in the user's timezone, with `stop > start`.
Active assignments for the same employee cannot overlap, irrespective of type,
station or area. Adjacent intervals are valid. Different employees may share a
station during identical or partially overlapping intervals.

Protection is database-level: native `models.Constraint` declares a partial
GiST exclusion on a singleton `int8range` of the employee ID and half-open
`tsrange(start, greatest(start, stop), '[)')`, only for active rows. Built-in
range operators require no PostgreSQL extension. `greatest` prevents reversed
input from failing in range construction before the positive-interval CHECK.
The constraint handles create, batch create, write and unarchive, including
concurrent transactions and records hidden by access rules, without a search
or sudo. [PostgreSQL range constraints](https://www.postgresql.org/docs/18/rangetypes.html#RANGETYPES-CONSTRAINT)
describe the native exclusion mechanism. ORM constraints also validate positive
intervals and nonblank temporary reasons.
Create flushes pending interval/archive changes before insert; interval or active
writes flush their affected rows so validation happens during the ORM call.

Archived assignments do not block placement. Reactivation checks overlap and
requires an active station. Active create/change of station requires an active
station; subsequently archiving a station preserves historical assignment rows.
All routine roles, including non-superuser System Administrators, lack unlink
permission. Native archive/unarchive is the operational correction mechanism.

## Security and UI

Internal users receive read permission only where
`employee_id == user.employee_id.id`. Native HR resolves `user.employee_id` in
the current active company (`addons/hr/models/res_users.py`,
`_compute_company_employee`). A global all-CRUD restriction intersects this with
allowed companies. Multiple employee records do not widen self scope; switching
the active company selects that company's employee. A user without an employee
sees no assignments. Menu/action filters are conveniences, not authorization.

Schedule Read can read all assignments in allowed companies. Schedule Manager
adds create/write/archive, without deletion or user/group administration.
System Administrator implies Schedule Manager. Portal/public have no grant.
Dental Employee Management NONE uses ordinary self access; READ implies Schedule
Read; READ/WRITE implies Schedule Manager. No sixth capability is introduced.
Generic roles do not imply Dental authority or HR mutation rights.

Schedule Read can read workstation metadata in allowed companies to select
stations. Ordinary users retain no direct Station grant; native Many2one
serialization supplies the station name from their authorized assignment.
This grants no facility/resource mutation, hierarchy management or other employee
assignment access. Native HR public-directory fallback supplies employee display
names without granting private HR access.

Native list-first menus: My Schedule (`我的排班`) for internal users and
All Schedules (`全部排班`) for Schedule Read/Manager. ACLs determine edit/create
controls. Native archive controls also use `active` field metadata; `fields_get`
marks it read-only without model write access, with a corresponding native view
cache key. Server ACLs remain the mutation boundary. Columns: employee,
workstation, start, stop, type, reason, company.
Filters: Today, Next 7 Days, My Schedule, Planned, Temporary, Archived; group
by employee/station/company. Today and next seven calendar days use local
midnight boundaries converted to UTC, and include intervals intersecting the
window. No hierarchy data is duplicated for grouping. No chatter or workflow.

## Future contract and scope

DENTAL-WORKSPACE-01 may resolve native user -> current-company employee ->
active assignment where `start <= now < stop` -> station. Exclusivity guarantees
at most one current placement. A future constrained temporary selection must
validate identity, company, reason, time and overlap; ordinary generic CRUD
remains denied. The current task grants no such method or workspace access.

Deferred: workspace/login selection, queues/calling, appointment/room routing,
practitioner migration, recurrence/templates, automatic allocation, calendar/
Gantt/graphics, patient Portal work. Appointment, dental.room and
dental.practitioner models are untouched. Odoo Core, production/NAS and
composition source are untouched.

## Verification ledger

Passed: 35 generic scheduling tests, 4 Dental scheduling integration tests,
35 existing Facility tests, 6 existing Dental Facility integration tests and
all 60 AUTH01/AUTH02 tests (140 required tests). Final no-demo clean composition
also runs two native Web checks: 142 total, zero failures/errors. Standalone
`sd_facility_schedule` installs without Dental and its final rerun passes all
35 scheduling tests, zero failures/errors.

Accepted-baseline upgrade passes the required suite in both the existing
`sd_dental_dev` and an isolated restored clone. Final UI correction rerun on
`sd_dental_dev` passes all 140 tests. Existing data hashes match across
16 models (including employees/versions, resources and 11 clinical models), all
21 user identities and their original group memberships. Existing development
Facility tables were empty; the baseline clone additionally contains a facility,
floor, area and dedicated Station/Resource, whose data also survive upgrade.
The local development service is restarted and healthy. Backup includes the
original database and filestore. No production/NAS access.

`odoo-security`: complete sweep and access review; fixed domains enforce self
scope and all-operation company restrictions. Generic/Dental group implications
and downgrade behavior verified. No new runtime sudo, direct SQL execution,
custom business RPC/controller, dynamic domain construction, file/eval/HTML/secret
surface or group administration. Native static SQL declarations contain no
interpolated values. No unresolved material finding.

`odoo-review`: all candidate files mapped and reviewed in the local baseline
checkout. Init/model Python: structure/imports/naming, fields/ORM/constraints,
batch/performance, translation/comments. Manifests: dependencies/load order.
Tests: fixtures, post-install collection, behavioral boundaries, expected-error
savepoints. Security: access rows/groups and the security skill. XML: native
list/form/search/action/menu and record conventions. PO/docs: static translation
and scoped evidence. Stable-version guidance read; this task explicitly
authorizes the new feature, while existing Dental edits are only dependency,
group integration and test registration. Web skill read; no static/assets
changes. No unresolved blocking finding. Python/XML/PO checks and tracked plus
untracked whitespace checks pass.

Independent acceptance: PASS on the final candidate, with no source changes by
the acceptance agent. All 60 authenticated RPC checks pass using real ordinary,
READ, RW, Portal and System identities, including known-ID privacy, forbidden
mutations, company scope, overlap, adjacency, shared Stations, archive/reactivation,
inactive Stations and privilege-escalation negatives. Browser checks pass for
own-only menus/records, READ controls, RW planned/temporary creation and archive,
Portal exclusion, local-date filter boundaries, Facility management and existing
Dental patient/appointment/room pages. Fresh-origin role switching from READ to
RW and back, then ordinary access, preserves the correct controls and privacy.
The read-only archive-menu defect discovered during acceptance was corrected;
the added regression, all 140 required tests, authenticated checks and rendered
browser rerun pass. No unresolved source, security or UI defect.
Raw harnesses/logs remain outside Git under `D:/Code/odoo/.tmp/clinic-schedule-01`.

Status: **CLINIC-SCHEDULE-01 = READY FOR HUMAN REVIEW**. Remaining human review:
Chinese terminology, list/form usability, planned versus temporary workflow and
the usefulness of the next-seven-days filter. No commit or push; no Workspace
or Queue implementation.
