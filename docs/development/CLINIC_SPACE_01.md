# CLINIC-SPACE-01: facility and workstation foundation

Implementation date: 2026-10-09 (Asia/Shanghai).
Human review: **APPROVED**. Final commit and normal push authorized by the user.
Accepted design: `REUSE_AUDIT_FACILITY_01.md`, with the current task's explicit
overrides: delegated Facility Read/Manager groups and Dental implications; no
queue participation/inheritance fields. The generic addon is shipped alongside
Dental in this task's repository so the candidate and dependency are reviewable
together. No composition source or Odoo Core is changed.

## Baseline and reuse

Fetch succeeded. Branch `port/odoo20-demo`; local and fetched remote HEAD both
`1515646c10fa7e875880c51ab4a6a57a9c50e732`; initial worktree clean.
Pinned reference `D:/odoo-sd/odoo20-clean`, SHA
`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`, clean. Runtime verification uses the
existing isolated `odoo:20.0-20260926` development image; its source SHA is not
asserted to equal the reference SHA. Resource mixin creation/copy hooks were
inspected in both sources.

Reuse classification: physical space/station identities NEW under the accepted
audit; native parent-store tree pattern WRAP; Resource mixin EXTEND; calendars
and native backend UI USE; groups/access domains CONFIGURE. No existing SD addon
was found in the composition `addons/` directory. No Stock, MRP, Restaurant or
HR work-location business model is repurposed.

## Models and invariants

`sd_facility` depends directly only on `resource`; `dental_clinic` depends on
`sd_facility`. Exactly two new business models:

- `sd.facility.space`: `name`, optional company-unique `code` (`copy=False`),
  `type` (facility/floor/area), required immutable `company_id`, checked/restrict
  `parent_id`, inverse `child_ids`, ORM-owned indexed `parent_path`, stored
  recursive `complete_name`, direct inverse `station_ids`, `sequence`, `active`,
  `description`. Facility is a root; floor requires a facility parent; area
  requires a floor or area parent. Exact company equality includes legally
  related companies. Cycles use native ORM detection. Direct writes/creates
  supplying `parent_path` are rejected. Parent/type edits validate the resulting
  subtree and its stations, including archived records.
- `sd.facility.station`: writable stored Resource-related required `name`,
  optional company-unique `code` (`copy=False`), required immutable related
  `company_id`, checked/restrict required area `space_id`, unique checked
  required `resource_id`, checked required related `resource_calendar_id`,
  inherited `tz`, `sequence`, stored Resource-related `active`, `description`.
  A room-sized area may hold multiple independent stations. Facility/floor
  placement and cross-company placement are rejected server-side.

No independently writable facility/floor reference duplicates the tree.
Both models use `_check_company_auto` and all-operation company access domains.

## Resource integration and lifecycle

`resource.mixin._prepare_resource_values` supplies material type and the narrow
`resource.resource.sd_facility_owned` ownership marker. Standard mixin creation
and copy allocate resources; duplication creates a separate resource, while
ordinary station writes retain the same identity. Required stored related name
is precomputed so copies satisfy the database requirement. Supplied resources
must already be dedicated facility material resources without users; existing
human/MRP resources cannot be converted into that namespace. SQL uniqueness
prevents two stations sharing a resource, including concurrent attempts.

Station/resource company transfers, resource replacement, ownership removal,
human type or user binding are rejected. Calendars must be shared or belong to
the exact station company. Creation defaults to the requested company's calendar,
even when a different allowed company is currently active. Supplied dedicated
resources retain their calendar. Direct Resource writes enforce the same invariants
and revalidate owners. Facility-owned Resource creation/update explicitly
requires Facility Manager, even when an unrelated HR/MRP role independently
grants Resource CRUD. Native generic Resource read access remains unchanged;
no new human-resource mutation grant is added.

Business creation/writes use ordinary ACLs, without elevated mutation. The only
production `sudo()` is a fixed-resource-ID, read-only integrity lookup for hidden
or archived station owners; it returns no data to the caller and mutates nothing.

Archive is bottom-up: a space cannot be archived while a descendant space or
station remains active. Active create/reparent/unarchive requires all ancestors
active. Station archive updates its owned Resource; calendars and employees are
not archived. Reopening a parent does not automatically reopen descendants.
Normal roles have no delete grant. Restrict foreign keys protect hierarchy,
area and Resource references. An explicitly authorized unused-station cleanup
deletes the station and its dedicated Resource in the same transaction; future
operational consumers must add their own restrict/history and in-progress work
checks. No operational history framework is introduced now.

## Security and management UI

Facility Read implies internal identity and grants read only. Facility Manager
implies Facility Read and grants create/read/update/archive, without deletion
or System administration. Its Resource grant is restricted to facility-marked,
material, user-less resources in allowed companies. System Administrator implies
Facility Manager. No Portal/public grant exists.

Dental Configuration Read implies Facility Read; Dental Configuration Read/Write
implies Facility Manager. Implications never grant Dental capabilities to a
generic facility manager. AUTH02 remains the authority engine; no new Dental role
or profile synchronization is added. Capability downgrade is tested.

Native list/form/search actions provide Facilities, Floors, Areas and Workstations,
with archived filters, parent/area/company and calendar grouping. Full-name area
selectors disambiguate ancestry. The generic menu works independently; Dental
places it under its existing Configuration menu. Ordinary clinical users do not
gain facility configuration menus. A normal `zh_CN.po` translates all facility
terms, including Workstation/Workstations as `工作位`, facility type as `院址`,
floor as `楼层` and area as `区域`; no JavaScript is added.

## Compatibility and deferred work

`dental.room`, its records/views/menus, `dental.appointment` and `room_id` are
untouched. There is no appointment migration or inferred room-to-station mapping.
Stable station/resource IDs, the area reference, ORM `child_of`/`parent_of`,
calendar and timezone are the future integration hooks. Future scheduling,
queues and floor plans remain separate consumers of this foundation.

Deferred: employee assignments/substitution, patient reservations, workspace
selection, DIRECT/POOL queues, calling, Visit Flow/tasks, examination/treatment
capabilities, equipment/inventory, geometry/layout/SVG/CAD, graphical editor and
Portal patient flows. No queue flags, service mapping, coordinates or demo clinic
hierarchy are included.

## Verification and reviews

The reviewed candidate passes 41 new tests (35 generic and 6 Dental integration)
and all 60 existing AUTH01/AUTH02 authorization tests. Both no-demo Dental clean
installation and existing `sd_dental_dev` upgrade pass 101/101. Standalone
`sd_facility` clean installation without Dental passes its 35 generic tests.
Development preservation hashes match all stored data across 11 existing clinical
models, including 21 rooms and 18 appointments. All 21 original users and their
original group memberships are retained. Backup, hashed snapshots, harnesses and
raw logs remain outside Git in `D:/Code/odoo/.tmp/clinic-space-01`.

The existing image can log a healthcheck request racing shutdown of one-off test
servers after the successful suite summary (`cursor already closed`). The CLI
processes exit successfully; the restarted development service is healthy. This
is not an ignored test failure or a source change to Odoo Core.

`odoo-security`: all skill sweep patterns reviewed; company restrictions cover
CRUD, mutation grants are bounded, Resource related fields expose only owned
generic metadata, no public custom RPC/controller/file/SQL/HTML surface, and
Portal denial is tested. The forged-path and unrelated-HR Resource-write findings
were fixed and regression-tested. No unresolved material security finding.

`odoo-review`: all changed Python/init/manifest/test, access/group/menu/view and
translation/documentation files reviewed for rules and merits against the current
candidate plus pinned consumers. Guidelines read: module structure; manifest; Python imports,
naming/layout and translation; ORM recordsets/domains, constraints, extension
points and transactions; fields; XML/data; access rights; batch/performance;
tests; comments; stable-version scope. This explicitly authorized new addon is a
feature task, while existing Dental edits remain limited to integration. Web
skill read; no static/JavaScript/SCSS/assets changes. No blocking review finding.

Independent acceptance: PASS, a separate agent/session validated 96 independent
ORM scenarios and 18 authenticated HTTP scenarios, zero failures. It read live
metadata and the task oracle, not implementation or test source, and rolled back
all fixtures. This included hierarchy/path forgery, permissions and HR-only
Resource boundaries, company/calendar defaults, material ownership/copy,
archive/reopen/move, Chinese labels and existing Dental room/appointment/view
behavior. Its company-B default-calendar finding was fixed, regression-tested
and independently rechecked. No rendered browser pixels were inspected; MRP
was not installed, so a live MRP resource was not exercised. Unmarked external
material/human resource adoption is independently tested and rejected.

Final syntax/XML/translation checks and `git diff --check`: PASS. No pending
technical defect or required implementation gate remains.

Human review approved the terminology, management UI and clinic hierarchy.
Production/NAS access and starting CLINIC-SCHEDULE-01 remain outside this task.
