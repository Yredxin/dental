# REUSE-AUDIT-FACILITY-01: Clinic spatial / workstation foundation

Audit date: 2026-10-09 (Asia/Shanghai). Mode: AUDIT / DESIGN ONLY.

## 1. Executive conclusion

**REUSE-AUDIT-FACILITY-01 = COMPLETE.** This concludes the source-backed audit,
not implementation approval. The recommended architecture is ready for human
design acceptance and a separately scoped CLINIC-SPACE-01 task. No addon source,
migration, runtime database, production/NAS, or Odoo Core was changed. No modules
were installed, and no commit or push was made.

Recommend **one generic addon, `sd_facility`, with two business models**:

- `sd.facility.space`: one company-isolated physical tree, using standard ORM
  `parent_id`, `_parent_store`, indexed `parent_path`, and `active`. Types:
  `facility`, `floor`, `area`. A physical facility/site root is necessary to
  represent the requested company -> facility -> floor -> nested areas sequence.
- `sd.facility.station`: the actual work position, linked to an area, inheriting
  `resource.mixin`, with an exclusively owned **material** `resource.resource`.
  Employees retain separate human resources. Reuse `resource.calendar` for
  working availability; do not mistake it for an employee/station assignment.

Do not inherit `stock.location`, `stock.warehouse`, `mrp.workcenter`,
`restaurant.floor`, `restaurant.table`, or `hr.work.location` as the clinic
foundation. Their business meanings, callers, or dependencies are incompatible.
Adapt the Stock tree pattern and the MRP material-resource composition pattern.
The POS floor-plan geometry/history code is a credible future adaptation source,
but its complete editor/service is coupled to POS. No POS dependency or copying
is recommended now.

Keep `dental.room` and `dental.appointment.room_id` unchanged until the facility
foundation and an explicit legacy mapping exist. Later migrate bookings to a
generic station; retain room compatibility for old records/integrations during
the transition. Reuse the Dental treatment catalog for an initial Dental-specific
station-to-service mapping, not as a universal examination capability engine.

### Baseline and evidence limits

| Check | Verified result |
| --- | --- |
| Dental repository | `D:/Code/odoo/dental` |
| Fetch | `git fetch --all --prune` succeeded before baseline verification. The sandboxed attempt failed to initialize DNS; the authorized network retry succeeded. |
| Branch | `port/odoo20-demo` |
| Local HEAD | `3a7f17f2f76e5256a0e20481ac39ffadca7a556c` |
| Fetched `origin/port/odoo20-demo` | `3a7f17f2f76e5256a0e20481ac39ffadca7a556c` |
| Equality / accepted baseline | Both match the required accepted commit. |
| Initial worktree | Clean: empty `git status --porcelain=v1`. |
| Requested Odoo path | `D:/Code/odoo/odoo` does not exist on this machine. |
| Actual pinned Odoo checkout | `D:/odoo-sd/odoo20-clean`, already documented in the accepted capability matrix and previous workflow audit; branch `20.0`, HEAD `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`; clean. This checkout was read directly, not reconstructed from old reports. |
| Odoo release evidence | `odoo/release.py`: `version_info = (20, 0, 0, FINAL, 0, '')`. Findings apply to this exact source revision. |
| SD composition checkout | `D:/Code/odoo/odoo-sd`, HEAD `bf6d30035701159f968f8c5901b38d186fa48521`. `addons/` contains only `README.md`; no existing implemented SD facility addon was found. |
| Runtime qualification | No live database or installation audit. Local source availability does not establish module installation or equivalence to the runtime image. |
| Authorized document | Task section 20 requests this Markdown document if governance allows documentation. The five project skills contain no prohibition on this audit artifact; implementation remains prohibited. |

Applied project skills: `odoo-guidelines`, `odoo-web-guidelines`, `odoo-security`,
`odoo-review`, `sd-odoo-dental`. Guidelines read: Fields; Recordsets/domains/context;
Computes/onchange/constraints; Methods/extension points; Transactions/exceptions;
Access rights; Manifest; Batch ORM calls/performance conventions; JavaScript
feature organization and extension; Assets. The review used pinned sources and
traced consumers. Security conclusions concern the facility reuse boundary;
this is not a fresh certification of all Dental or POS security.

The user-requested vocabulary includes ADAPT/DEFER/REJECT. These describe
adaptation, postponement, and exclusions, not implementation authority. For
project-policy purposes, ADAPT of a pattern means WRAP of that pattern, while
the genuinely absent facility business representation is separately NEW.
Missing evidence was not used to justify NEW.

## 2. Existing Odoo candidates

Evidence IDs below identify directly inspected files and methods. Odoo paths are
relative to the exact pinned Odoo checkout in section 1. Dental paths are relative
to the accepted Dental checkout. Line anchors are navigation starts, not ranges.

### O01: POS Restaurant models and persistence

`addons/pos_restaurant/models/pos_restaurant.py:24` defines `restaurant.floor`
with `pos.load.mixin`, POS configurations, table children, sequence, archive flag,
and `floor_plan_layout = fields.Json(copy=False)`. `restaurant.table` at line 118
has table number/seats, floor, table grouping parent/side, active, and layout JSON.
Its parent is a restaurant table-grouping relationship, not a floor/area tree.
Neither model declares a standalone clinic `company_id` isolation mechanism.
Deletion/archive behavior checks POS sessions and draft orders.

`addons/pos_restaurant/models/pos_config.py:14` declares stored settings JSON and
computed `floor_plan` JSON. `_compute_floor_plan` (175) combines active floors'
layout with active tables' layout and IDs. `get_floor_plan` (195) returns this
plan separately from loaded business records. The JS restoration fills name,
table number, and seats from those records when absent from the layout.

`save_floor_plan` (208), `_save_floor_plan_floor` (249),
`_save_floor_plan_table` (311), and `_split_layout_server_data` (330) are the
persistence seam. Floor `name` and table `table_number`/`seats` are explicit
business keys; other non-excluded values become layout. Omitted active floors
and tables are deactivated, with POS operational checks. The config notifies
`FLOOR_PLAN_UPD` across related POS configurations.

Image handling: supported formats include SVG, PNG, JPEG, GIF, WebP in
`pos_restaurant.py:13`. `add_floor_plan_image` (83) decodes data, detects MIME,
uses attachment checksum/name matching, and initially links the upload to
`restaurant.floor` with `res_id=0`. Saving binds new attachments to the floor,
copies images reused across floors, and strips transport-only `newImages`.
`_gc_embeddings` (106) removes unattached uploads older than one day. These are
useful design precedents, not a clinic-safe upload API to transplant unchanged.

Manifest: `pos_restaurant` depends on `point_of_sale`; its editor assets load in
`point_of_sale._assets_pos`. Its access rows are for POS user/manager groups.
Direct reuse would import restaurant/session/order semantics into facility work.

### O02: POS editor, geometry, history and callers

Directly inspected under `addons/pos_restaurant/static/src/app/`:

| Capability | Actual implementation | Assessment |
| --- | --- | --- |
| Service/store | `services/floor_plan/floor_plan_service.js:25`, `FloorPlanStore`; registry `pos_floor_plan` at 1021 | Reactive in-memory editor state, business-record restoration and serialization. `init(pos)`, `save`, refresh and update use POS config/data/models/device/IndexedDB. Adapt a new persistence boundary later. |
| Editor | `screens/floor_screen/floor_plan_editor/floor_plan_editor.js:40`, `FloorPlanEditor`; `floor_plan_editor.xml` | Owl component, selection, mouse/touch, handles and property controls. Extends POS `FloorPlanBase`; imports POS popup and Restaurant modules. No standalone reusable backend view is supplied. |
| Base and caller | `screens/floor_screen/floor_plan_base.js:6`; `hooks/floor_plan_hook.js`; `services/pos_store.js:1007` | Hook resolves `pos_floor_plan`; POS store initializes it and listens for `FLOOR_PLAN_UPD`. A clinic view must own its own service and loader. |
| Move / keyboard | Editor `operations/move.js:16`, `keydown-move.js` | Pointer movement, canvas limits, autoscroll, transformed bounds, keyboard motion; adapt DOM/handle contracts and policy. |
| Resize | `operations/resize.js:10`, `line-resize.js:15` | Rotated coordinate conversion, fixed anchors, minimum dimensions, aspect rules; line endpoint resize. Requires element/handle APIs. |
| Rotation | `operations/rotation.js:12` | Rotation around element center; special line behavior; 45-degree snap with 5-degree threshold. |
| Alignment snapping | Editor `utils/snapping.js:3`, `Snapping` | Bounds/centers/corners and viewport filtering, 5-pixel threshold, SVG guide lines. Currently snaps tables to tables and decorations to decorations; change categories for stations/areas. This is not a universal CAD/grid snapping engine. |
| Bounds/transforms | Service `utils/bounds_calculator.js:9`, `Matrix2D`, `calculateBoundsFromTransform`; `utils/utils.js` | Strong candidates for narrow adaptation. Imports/static asset paths still need decoupling. |
| Undo / redo | Service `utils/history.js:1`, `History`; store undo/redo/snapshot/transaction methods | Standalone 50-entry in-memory history utility; forward entries are discarded after an edit following undo. Store applies command/snapshot semantics. No persistent history/version engine. |
| Images / SVG | Service `elements/image.js`; `elements/floor.js` background; editor `utils/image.js`; O01 upload whitelist | Browser image loading and CSS/background or image assets; server attachment support. SVG is an image asset, not editable CAD geometry or an area polygon parser. |
| Text / labels | `elements/text.js`, `decor.js`, editor `operations/text_edit.js`, XML `t-out` | Text editing, decoration styling, plain labels. Preserve escaping and validate serialized style values in a later adaptation. |
| Lines / decorations | `elements/line.js`, `border_decor.js`, `decor.js`, element exports in `elements/index.js` | Lines, borders, basic shapes and image decorations; doors/plants/toilet SVG assets referenced by add-decor popup. Walls can be decorative lines, not a building topology engine. |
| Area polygons / CAD-DXF | Inspected element exports, shape constants and editor/service search | No area business model or polygon vertex editor/import pipeline found in these components. SVG support does not supply these missing capabilities. Defer a separate graphical audit. |

`FloorElement.raw` serializes UUID, left/top, width/height, rotation, scale and
shape. Floor raw data aggregates tables, decorations and background; table raw
data carries table business attributes. `FloorTable` additionally understands
restaurant parent tables, sides, seats and POS records. Use it as a design
reference for station elements; do not reuse table grouping as area membership.

### O03: Stock hierarchy, warehouse and ORM

`addons/stock/models/stock_location.py:13` uses `_parent_name='location_id'`,
`_parent_store=True`, indexed `parent_path`, parent/children relations,
`_check_company_auto=True`, `active`, recursive full names, and `child_of` /
`parent_of`. `_compute_warehouse_id` resolves the closest warehouse root using
ancestor paths. `usage='view'` is a virtual aggregating parent that cannot
directly contain products. This demonstrates that container nodes and actual
work/storage positions need distinct semantics; it is not a clinical area type.

Important divergences: company may be empty/shared; the model overrides
`_check_company_domain` with `models.check_company_domain_parent_of`, permitting
company-ancestor compatibility. Stock locations also own quants/moves/removal
and replenishment rules. `write` (225) rejects company changes, checks warehouse
and stock before archiving, and propagates active to descendants including
already archived records. `unlink` (270) deletes the searched subtree. Do not
copy these cascade policies blindly into a clinic tree.

`addons/stock/models/stock_warehouse.py:23` has required company, address partner,
view root and stock sublocations. `create` (114) creates locations, sequences,
picking types, routes and rules. Archive additionally updates related inventory
objects. A clinic site is not a warehouse, even if supplies are stored there.

Framework evidence: `odoo/orm/models.py:2423` / 4460 / 4484 / 4519 maintain parent
paths; `_has_cycle` is at 5116. `odoo/orm/domains.py:1872` implements parent-store
`child_of` as prefix matching of stored paths; `parent_of` at 1898 uses path IDs.
The operators include the seed node. `models.py:3339` / 3351 implement company
compatibility, and `action_archive` at 5273 simply writes the active field.
Recursive archive and all-path queue gates are not automatic ORM features.

### O04: Resource

`addons/resource/models/resource_resource.py:18` supplies name, active, company,
resource type (`user` = Human, `material` = Material), optional user, required
calendar, required timezone, and availability helpers. Calendar selection's
UI company domain is not a server-side station integrity guarantee.

`addons/resource/models/resource_mixin.py:10` is an abstract composition mixin,
not `_inherits` delegation. It declares required `resource_id` with
`ondelete='restrict'` and `bypass_search_access=True`; writable stored related
company/calendar and writable related timezone. `create` (30) batch-creates
missing resources using `_prepare_resource_values` (53); `copy_data` copies the
resources. It does **not** automatically define station name/active delegation,
force material type, enforce exclusive ownership, supply Resource CRUD grants,
or delete resources when the owning business record is deleted. No mixin
`write`/`unlink` override provides those lifecycle guarantees.

Relevant APIs: mixin `_get_work_days_data_batch` (91), `_adjust_to_calendar`,
`_list_work_time_per_day`; resource `_get_unavailable_intervals` (155),
`_get_calendars_validity_within_period`, `_get_valid_work_intervals`,
`_get_resources_per_tz` (427). Calendar
`_attendance_intervals_batch` (287), `_leave_intervals_batch` (468),
`_work_intervals_batch` (525), `_unavailable_intervals_batch` (552),
`plan_hours` (764) are concrete lower-level scheduling helpers. Timezone-aware
inputs and batched resource-per-timezone mappings are part of these contracts.

`resource.calendar` supports fixed, variable (dated), and undefined calendars
in this revision. This differs from assumptions based on older Odoo versions.
Effective work intervals subtract absence intervals by default. A calendar is
working availability; it does not record who is assigned to which workstation.

`resource.calendar.leaves` has a single resource, start/end, name/reason,
calendar/company and `count_as = absence / working_time`. It lacks a second
employee/station identity and normal/substitution semantics. MRP deliberately
queries working-time leaves separately to detect reservations; ordinary
`_work_intervals_batch` does not automatically remove those reservations.

`addons/resource/__manifest__.py` depends on base/web. Its `security/ir.access.csv`
grants internal users resource **read**, with a company restriction over all
CRUD. HR and MRP separately grant their administrators resource CRUD. Therefore
inheriting the mixin alone is insufficient for a facility configurator to create,
rename or archive resources. `bypass_search_access` is not CRUD authorization.

### O05: MRP work centers and work orders

`addons/mrp/models/mrp_workcenter.py:22` uses `resource.mixin`,
`_check_company_auto`, writable related resource name/active, and checked working
calendar. `create` (305) forces default material resources. `write` (311) forwards
company changes. This is the closest architectural composition reference.

Its capacities at 84 / 437 / 627 are product/UoM parallel production capacities,
not a generic number of clinic staff or patient slots. Alternative centers at
74 and `_check_alternative_workcenter` are substitution candidates with company
checks. `working_state` (60 / 201) derives from productivity and work orders;
`done` there means in progress. Do not import those clinical state names.

`_get_first_available_slot` (348) combines working intervals and separate
`count_as='working_time'` leave reservations. `addons/mrp/models/mrp_workorder.py`
`_action_plan` evaluates primary/alternative centers, duration and blocking
work orders, chooses a finish time, and creates a calendar leave reservation.
Work-order start and finish are linked to reservation dates. This demonstrates
reuse of lower Resource intervals, not a ready employee/station schedule model.

Manifest depends on product, stock, resource. Direct MRP dependence brings
manufacturing, BOM, production and inventory behavior. Reuse Resource beneath
it; adapt only the ideas of material position, availability, alternative eligible
positions and reservations in separately audited future work.

### O06: HR work locations and employee identity

`addons/hr/models/hr_work_location.py:9` is company/address-based work context,
types home/office/other, with active and location number. It has no recursive
physical area hierarchy, work-position resource, capability or time interval.
`hr_employee.py:368` supplies weekday locations; `hr_employee_location.py:9`
provides dated employee exceptions with one exceptional location per employee
date. These can describe onsite/remote attendance context, but cannot distinguish
an 08:00-12:00 chair assignment from a 13:00 substitution on the same day.

`addons/hr/models/res_users.py:97` exposes current-company `employee_id`;
`_compute_company_employee` (282) selects employees using `env.company`, user
and company context. Reuse this identity resolution in a later workspace;
do not create a second employee identity system or depend on a global first
employee match. Employee `resource.mixin` / human resource remains separate.

### O07: Maintenance equipment

`addons/maintenance/models/maintenance.py:23` defines equipment categories and
category property definitions; `MaintenanceMixin` (69) supplies maintenance
team, technician, company, failure metrics and requests. Equipment (113) has
serial/model/vendor/warranty/cost/archive fields and maintenance history, with
category properties and assignment extension methods. Base equipment has no
station calendar or physical tree; categories are asset taxonomy, not service
capabilities. Its manifest depends on mail.

A dental chair/CBCT device is an equipment record when asset maintenance is
needed. A station is the work position where a device is used; equipment can be
replaced while station identity and history persist. A compressor/sterilizer may
serve an area/site or several stations without being a patient-routing station.
A later integration should extend equipment with checked site/space/station
placement links as appropriate. Do not force every equipment item into one
station, nor treat every station as one serialized asset. Shared serving links
and relocation history require separate business decisions.

### O08: Attachments and native access

`odoo/addons/base/models/ir_attachment.py:592` / 594 declares owner model/record,
company, public flag, binary content and MIME. Access checks at 648 / 671 verify
linked-record/field access, and unlinked uploads are restricted to their creator
or administrator. `_check_contents` (532) can force XML-like content, including
SVG, to text/plain depending on context and `ir.ui.view` write access. A POS MIME
whitelist alone does not establish safe or universally available SVG rendering.
Use standard filestore/attachment access, with private ownership and verified
company, rather than JSON base64 blobs or arbitrary privileged attachment reads.

Odoo 20 security uses `ir.access` permissions/restrictions. The inspected Resource,
HR, Restaurant and Dental access files use the operation/domain format. Do not
introduce legacy `ir.model.access` / `ir.rule` designs into this pinned version.

### D01: Current Dental and SD

Directly inspected `dental_clinic/models/dental_room.py:5`,
`dental_appointment.py:7`, `dental_practitioner.py:5`, `dental_treatment.py:5`,
`hr_employee.py`, room/appointment views, security access rows, demo room links,
treatment-plan-line consumers and current manifest.

Room is explicitly "Dental Room / Chair": name, code, sequence, description,
free-text equipment, active and color. It has no company, hierarchy, resource,
calendar or capabilities. Appointment's optional `room_id` (17) references it;
calendar/list/form/grouping and demo data consume the field. Appointment has a
company but no checked room relation. `_check_overlap` (64) checks practitioner
time overlap, not room/station occupancy, staff assignments or capacity, and is
not evidence of concurrent booking serialization.

Practitioner is an existing clinical professional with user, specialty and
license fields; no employee/resource/company linkage. Current Dental **does**
depend on `hr` (the older matrix's manifest summary is superseded), and extends
employee invitation authorization, but that does not establish a practitioner
to employee relationship.

Treatment is a service catalog with diagnostic category, default duration,
optional tooth specificity, linked billing service product and price. Creating a
treatment auto-creates a service product when absent; name/price changes update
that product. It is not an independent taxonomy of non-billable operational
capabilities, imaging protocols, examination orders/results or staff credentials.

No implemented SD addon source is present in the composition `addons/` directory.

## 3. Reuse classification matrix

Each row classifies the specified capability, not blanket reuse of its addon.

| Model / capability | Class | Decision and evidence |
| --- | --- | --- |
| `res.company` | USE | Existing ownership/security boundary. Multiple physical facilities may belong to one company; do not manufacture companies per room/site. O03/O04/D01. |
| Existing company calendars | CONFIGURE | Reuse appropriate existing hours/timezone; new station calendars only where actual working patterns differ. O04. |
| Stock location tree **pattern** | ADAPT | Standard parent store/path/operators, recursive names and checked relationships; no stock dependency. O03. |
| `stock.location` as clinic space | REJECT | Stock ledger/usage/shared-company semantics and lifecycle coupling. O03. |
| `stock.warehouse` as clinic facility | REJECT | Automatically creates inventory routes/types/locations; wrong site semantics. O03. |
| `resource.resource` | USE | Dedicated material resource per station; separate human resources per employee. O04/O05. |
| `resource.mixin` | EXTEND | Inherit and complete material default, name/active, required company, ownership/lifecycle/security invariants. Do not duplicate its creation/copy engine. O04. |
| `resource.calendar` and interval helpers | USE | Working availability and timezone arithmetic, with exact pinned method contracts. O04. |
| `resource.calendar.leaves` for downtime | USE | Later standard absences; not a paired employee/station assignment master. O04. |
| Employee/station scheduling representation | DEFER | Neither work calendars nor HR locations express the requested assignment. Audit scheduling engines/modules separately before a NEW assignment decision. O04/O05/O06. |
| `hr.work.location` as area/station/schedule | REJECT | Work-address/remote context and daily exceptions, not nested physical positions or timed staffing. O06. |
| `mrp.workcenter` directly | REJECT | Manufacturing state/capacity/work-order dependencies. O05. |
| MRP material-resource composition pattern | ADAPT | Reuse lower-level Resource, not MRP code/dependency. O05. |
| `maintenance.equipment` / categories | EXTEND | Optional future asset catalog with placement/serving links; retain equipment identity. No integration now. O07. |
| `restaurant.floor` / `restaurant.table` directly | REJECT | POS loaders/configurations/session/order/grouping semantics; no clinic area/company foundation. O01. |
| POS floor-plan persistence split | ADAPT | Business ORM records separate from layout JSON and attachments; replace save/load endpoint and destructive omission semantics. O01. |
| POS floor-plan editor/service | ADAPT | Selective later extraction behind clinic store/model adapters, not dependency/import of complete service. O02. |
| POS bounds/move/resize/rotation/snapping | ADAPT | Concrete algorithms exist; remove Restaurant imports, table categories, DOM assumptions where necessary. O02. |
| POS `History` utility | USE | Algorithm reusable; local extraction/licensing review later. Store application layer still needs adaptation. O02. |
| POS text/line/image/decor elements | ADAPT | Rendering/interaction precedents; no existing area polygon editor. O02. |
| `ir.attachment` | USE | Standard file ownership, access and filestore; extension-specific upload validation later. O08. |
| Physical site/floor/recursive-area master | NEW | No sufficient model among audited candidates without changing its business master or importing irrelevant engines. Use standard ORM infrastructure. O01/O03/O06/D01. |
| Generic station business record | NEW | Resource alone lacks spatial/routing position; existing rooms/tables/equipment/workcenters carry incompatible meanings. Compose Resource, do not clone it. |
| `dental.room` now | USE | Preserve accepted booking behavior and data until mapping is reviewed. D01. |
| `dental.room` transition facade | WRAP | Later explicit station mapping for resolvable legacy records; eventual retirement after consumers migrate. D01. |
| `dental.appointment.room_id` integration | DEFER | Later EXTEND booking with checked station and staged migration; no model change now. D01. |
| `dental.practitioner` | USE | Preserve clinical professional identity. Employee binding later is EXTEND, not replacement. D01/O06. |
| `dental.treatment` catalog | USE | Adequate master for initial concrete Dental services, including catalogued diagnostic services. D01. |
| Dental station service mapping | EXTEND | Later station `treatment_ids` in Dental integration, using existing treatments. Do not put Dental fields in generic foundation. |
| Broad capability / examination engine | DEFER | Examination protocols/orders/results, non-billable capabilities and qualifications need their own audit; no NEW engine justified now. |
| Area polygons / CAD-DXF import | DEFER | Additional graphical capabilities require a separate scoped reuse audit; absent from inspected POS floor-plan elements. O02. |
| Queue engine / calling / workspace | DEFER | Foundation supports references; no operational engine authorized or supplied by this audit. |

For the two NEW business records, USE/CONFIGURE cannot express the stated
facility/routing identities with existing masters. EXTEND/WRAP of rooms, work
locations, equipment, stock locations, restaurant tables or work centers would
retain conflicting meanings, dependency or identity constraints. The minimal
gap is two physical business records composed with existing ORM and Resource,
not a new tree engine, resource/calendar engine, file system or workflow engine.

## 4. Recommended addon boundary

| Boundary | Assessment |
| --- | --- |
| Put foundation in `dental_clinic` | Easy initial wiring, but couples all scheduling, queue, display and graphical users to clinical/patient/billing dependencies. Reject for generic foundation. |
| One new `sd_facility` | Recommended. Own generic physical tree/stations and standard backend configuration. Resource integration is part of that foundation. |
| Multiple immediate addons | Premature: no implemented queue, scheduling, graphics or equipment bridge yet. Do not create empty micro-addons. |

Use the composition repository's `addons/sd_facility` in a future implementation
task, subject to its task baseline. Keep this audit artifact in Dental's requested
documentation path. Clinical integration can later extend station/appointment
inside maintained Dental Core with a dependency pointing **Dental -> Facility**.
Foundation must never depend on Dental. Split an optional integration addon only
when it has real independent consumers or an optional installation need.

Future HR scheduling and Maintenance/Stock integration can live above Facility
when those stages are authorized. This is boundary direction, not authorization
to create those addons now.

## 5. Recommended minimum data model

This is a proposed contract, not an implemented schema.

```text
res.company
  -> sd.facility.space(type=facility)   one root per physical site
       -> sd.facility.space(type=floor)
            -> sd.facility.space(type=area)
                 -> sd.facility.space(type=area) ...
                 -> sd.facility.station
                      -> resource.resource(type=material)
                           -> resource.calendar
```

### Space

| Field | Proposed contract |
| --- | --- |
| `name` | Required display name. |
| `code` | Optional stable human identifier; copy disabled. Use a company-wide unique nonempty code if supplied. |
| `sequence` | Backend ordering. |
| `company_id` | Required, indexed, default current company; actual owner, never shared/empty. Immutable after creation. |
| `type` | Required selection: facility / floor / area. Facility means physical site, not a legal company. |
| `parent_id` | Same-model checked relation; indexed, restrict deletion. Required logically for floor/area, forbidden for facility. |
| `child_ids` | Standard inverse. Areas may contain both child areas and stations. |
| `parent_path` | Indexed Char, ORM-managed, readonly; `_parent_store=True`, `_parent_name='parent_id'`. |
| `complete_name` | Stored recursive full name for unambiguous selectors and backend navigation. |
| `active` | Standard archive field, default true. |
| `allow_shared_queue_inheritance` | Boolean, default false, copy disabled, meaningful only on areas. It expresses participation permission along the path; it creates no queue. |
| `station_ids` | Inverse of station `space_id`, direct children only; label accordingly. |

Do not add queue records, coordinates, background uploads, employee assignments,
capability masters, or custom history. Facility address can later link to
`res.partner` if site-address operations require it; it is not needed to establish
site identity today. Multiple facilities in one company are supported immediately.

Validation: a facility has no parent; a floor has a facility parent; an area has
a floor or area parent. No floors inside areas, facilities inside facilities, or
cross-company parents. Check cycles through the exact ORM API. A station must
belong to an area; model a physical room as an area, allowing several stations.
Use a ground-floor area for reception rather than creating a special exception.
Type changes must not invalidate any child/station, including archived children.
Parent/type edits must validate the whole affected subtree, not only the edited
record's current UI domain. Do not persist a second independent site or floor
foreign key that can diverge from the tree; compute it later if needed.

### Station

| Field | Proposed contract |
| --- | --- |
| `name` | Required writable stored related `resource_id.name`, following MRP composition. |
| `code` | Optional company-wide unique nonempty code; copy disabled. |
| `sequence` | Backend ordering. |
| `space_id` | Required area relation; indexed, `check_company=True`, restrict deletion. |
| `resource_id` | Inherited required Resource relation; unique per station, readonly in normal forms; checked company, restrict deletion. No arbitrary employee/workcenter resource reuse. |
| `company_id` | Strengthen mixin writable stored related company to required. Single source is resource company. Validate against area and freeze ownership after creation. |
| `resource_calendar_id` | Mixin related working calendar; checked, required. Accept the same company or an intentionally shared company-less calendar; reject another company's calendar. |
| `tz` | Inherited writable related timezone; keep native timezone values. |
| `active` | Writable stored related `resource_id.active`, default true. |
| `queue_enabled` | Boolean, default false, copy disabled; technical participation permission only. |

No employee owner field on the station and no station `resource.user_id` login
binding. A work position is not its current occupant. No generic station category,
capacity, alternative list or equipment text field is required initially.

### Company isolation, Resource integrity and security

- Enable `_check_company_auto=True` on both business models, with checked parent,
  area, resource and calendar relations. Required company prevents shared physical
  nodes. Do not copy Stock's parent-company compatibility override. Add exact
  equality validation for space/station/resource company; standard compatibility
  alone accepts shared records for some comodels.
- Use group-less `ir.access` company restrictions for **all CRUD** on both models:
  `[('company_id', 'in', company_ids)]`. Checked foreign keys and access restrictions
  solve different problems; both are required. UI domains do not enforce RPC.
- Smallest initial configuration authority: existing `base.group_system`, with
  create/read/update on spaces/stations, and read for `base.group_user` under
  company restrictions. No routine delete grant. No portal/public grants and no
  HR role needed merely to configure a station. A delegated facility role can be
  designed when required; do not imply Dental configuration permissions imply
  HR administration or generic facility authority.
- Provide explicit create/read/update Resource permissions for that system
  configuration role, bounded to material resources with no user and an allowed,
  nonempty company. Do not grant human-resource CRUD to general clinic users or
  rely on HR/MRP's unrelated grants. System configurators already own broad system
  configuration duties; a future delegated facility-manager role needs a narrower
  resource ownership design before it receives these permissions. Use ordinary
  ORM permission paths; no blanket sudo wrapper around mixin creation or writes.
- Force material type through `_prepare_resource_values` (or the verified MRP
  default context pattern), then validate actual supplied resources as well.
  Ensure one station per resource and reject human/user-linked resources. Normal
  create/copy should let the mixin allocate/copy an owned resource; disallow
  arbitrary supplied IDs from attaching an employee/MRP resource.
- Guard direct writes on station-owned `resource.resource` too: a raw Resource
  RPC must not change its company/type/user or calendar to violate station/area
  invariants. A narrow addon extension to that existing model is part of the
  integration, not a third business master. Company-related recomputation does
  not by itself revalidate every child relationship.
- Company transfers should create a new station/site and archive the old one;
  do not mutate historical ownership. Future appointment/task/schedule foreign
  keys require checked company and operational validation at their own boundary.
- Validate active ancestry before creating/unarchiving/moving active records.
  Keep state changes atomic. Future queue/graphical public RPC methods must check
  caller authority, record access/company, all requested IDs and payload keys.

### Archive and deletion

Use standard `active` / `action_archive` / archived search. For the initial
foundation, **block archiving a space with any active descendant space/station**;
require bottom-up archive. This is smaller and predictable compared with copying
Stock's recursive archive and restoring previously archived descendants on undo.
Block unarchiving a child/station under an inactive ancestor. Check archived
records when validating ownership and structural changes.

Station archive writes its owned material resource's active flag; it does not
archive an employee, equipment, or calendar. Exclude archived records from new
assignment/routing but preserve references and ordinary historical reads.
Future operational modules must protect scheduled/in-progress work before archive.

Restrict deletion via parent/area/resource relations; prefer archive once history
exists. No delete grant in initial configuration. If a later cleanup operation
allows deletion of an unused leaf/station, it must check all operational references
and explicitly handle the owned resource after deleting the station. The mixin
does not garbage-collect it. Do not add custom tombstones/version/history engines.

## 6. Space tree decision

Recommend Option B, one space model, extended with a physical **facility root**.
The two-type candidate (floor/area only) omits an explicit required site identity.
The third type satisfies that requirement without a third model or a second tree.

| Criterion | A: separate floor + area models | B: one typed space tree |
| --- | --- | --- |
| ORM simplicity | Areas need parent-area and floor links, with propagation/consistency logic. Facility still needs representation. | One parent relation and standard parent store; station points to one area. |
| Validation | Model separation encodes floor/area distinction but duplicated links require checks. | Explicit parent/type transition checks; straightforward permitted-parent matrix. |
| Hierarchy queries | `child_of` only solves the area portion; separate floor/site traversal. | One ORM tree supports descendant/ancestor scope across sites/floors/areas. |
| Graphics | Convenient floor model but area elements need separate integration. | Filter type=floor for canvases; area geometries and station references derive from the same tree. |
| Company isolation | Rules/checks for each model and every relation. | One space rule plus station/resource checks; fewer independent relations. |
| Multi-site | Extra facility entity/links anyway. | Facility roots support several sites per company immediately. |
| Nested areas | Works but needs separate floor consistency on moves. | Native recursive areas; direct station children can coexist. |
| UI usability | Separate menus naturally distinct. | Filtered facility/floor/area actions provide the same usability over one model; full-name selector removes ambiguity. |
| Migration cost | More cross-model mappings; later common-space routing needs reconciliation. | One space reference for pool targets and geometry, one station reference for direct targets. |
| Security | More ACLs and relations; type separation does not replace record access. | Fewer masters; enforce target type server-side, not merely filtered menus. |
| Extensibility | Floor-specific fields explicit; new levels often add links/models. | Type-scoped behavior/fields possible; add levels only when business need is accepted. |

A separate facility entity would become worthwhile for substantial site-specific
operations (independent licenses, address management, building assets), not merely
to hold the root name today. Do not create different models just to match menu
labels. Do not model floors as queue pools: only areas are legal pool targets.

## 7. Workstation/resource decision

**Directly inherit `resource.mixin` in `sd.facility.station`.** Use a dedicated
material resource and native working calendar from the outset. This is preferable
to a free-form room field now and a disruptive resource migration next stage.
It follows the MRP composition pattern through the lower Resource addon.

Alternatives rejected: using a bare `resource.resource` as the station would mix
generic human/material resources with clinic-specific physical membership and
permissions; copying its calendar/availability fields duplicates an engine;
hand-maintaining a new Many2one lifecycle without the mixin discards verified
batch creation/copy and helper APIs. `_inherits` is unnecessary.

The lifecycle gaps in O04 remain explicit implementation obligations: force
material type, delegate name/active, constrain supplied resources/ownership and
company/calendar, provide CRUD paths, and protect direct resource changes. Copy
must allocate a new resource, reset unique code and leave queue participation
disabled pending configuration. No employee's resource is shared with a station.
Do not expose MRP efficiency/capacity fields as clinical scheduling semantics.

## 8. Queue compatibility

Foundation supports later target fields naturally:

| Routing mode | Future target contract |
| --- | --- |
| DIRECT | `station_id`, same company, active station/ancestry, queue participation and service/assignment eligibility where applicable. Resolve a specific dentist's scheduled station at the relevant time. |
| POOL | `space_id` constrained to an area, plus required service. Later claim by an eligible descendant station. No floor/site polymorphism or alternate room model needed. |

A future task must select the applicable target mode and validate target
exclusivity. Actual queue ownership, claim locks, priority and fairness remain
deferred. Hierarchy permission is not an assignment, reservation or capability.

Define eligibility for area A, station S and service R as:

```text
S belongs to A's descendant area tree (A included)
AND S.queue_enabled
AND S satisfies R
AND every area from A through S.space_id, INCLUDING A and S.space_id,
    allows shared queue inheritance
AND S and the complete physical ancestry are active and in the target company
```

Site/floor nodes are not area gates; their activity/company still applies.
For A=true -> B=false -> C=true -> S=true, A cannot reach S. C can manage its
own pool because C-to-S does not include B. A service/category label on A does
not grant a capability to S. Station directly in A also checks A's flag.

Efficient future evaluation: retrieve descendant areas with ORM `child_of`,
collect the disallowing area IDs in that scope, and exclude stations whose
`space_id` is `child_of` any of those blocking areas. Fetch active/capability-
eligible stations in batches, with explicit company and ancestor checks. An
alternative is batched path-ID inspection over prefetched areas. Neither
requires a custom closure table or per-station recursive SQL query.

**Counterexample:** `('space_id','child_of',A)` plus a flag on S's immediate area
will wrongly admit S below B=false. `child_of` encodes ancestry only. Standard
`active_test` also does not test every ancestor's flag/activity. Keep any future
eligibility cache scoped to the root and invalidate on reparent, active, gate,
station and capability changes; no cache is needed now.

Moving or redrawing a station on a canvas must never silently change its
business area membership. A business reparent operation is separate and checked.

## 9. Scheduling compatibility

Resource-backed stations support the next stage without changing station
identity. Availability is the intersection of station working intervals,
employee availability and the authorized assignment interval, then adjusted
for reservations/conflicts defined by that later scheduling feature.

The expected employee + station + start/end + normal/substitution + reason is
**not** already supplied by `resource.mixin`, a working calendar, a work-location
weekday field, or a single-resource calendar leave. Do not implement it here.
The next audit must inspect installed/licensed scheduling candidates before
concluding a new assignment model is necessary. This Community-source audit
does not claim Enterprise Planning was reviewed.

Preserve the distinction between staffing assignment and patient reservation.
One staff shift does not mean a station is occupied by one patient for the whole
shift. MRP's working-time leave convention illustrates reservation bookkeeping,
but ordinary availability helpers do not treat that convention as a universal
busy-slot engine. Do not copy manufacturing leaves/work orders as staff shifts.

Later use strict start < end, half-open intervals, UTC storage with resource
timezone-aware calculations, same-company employees/stations, substitution
precedence, and concurrency-safe conflict enforcement. Capacity/concurrent staff
and cross-site travel need business decisions. No mutable station employee field
or assignments inside layout JSON.

Workspace compatibility: use current-company `res.users.employee_id`, then
find the authorized current assignment and enter that station's workspace.
On missing assignment, an authorized temporary selection/substitution can reuse
the same station ID. It should persist a reviewed temporary assignment rather
than changing station ownership. Define authorization and ambiguity handling
later. Shared device login and identifying the actual acting employee are separate
future concerns; a layout click must not grant clinical permissions.

## 10. Future graphical architecture

No graphical fields/editor/uploads are in CLINIC-SPACE-01. The identity/tree split
is sufficient for later graphical extensions without a redesign of routing IDs.

| Owner | BUSINESS DATA | Future LAYOUT DATA |
| --- | --- | --- |
| Facility root | Site identity, company, active, child floors | Normally no canvas; optional site presentation settings if genuinely needed. |
| Floor space | Name, parent facility, company, active | Versioned layout schema (format version, not history engine), canvas/viewBox dimensions, unit/scale transform, background attachment reference and placement, decorations/walls and view defaults. |
| Area space | Name, parent, company, active, inheritance permission | Polygon/outline points and label placement expressed in its derived floor coordinates; one canonical owner for area geometry. |
| Station | Stable identity, area membership, resource/calendar, active, queue participation; later service mapping | Icon/shape, position/size, rotation, visual label offsets/layer; derived floor coordinates, not a second independently writable floor membership. |
| `ir.attachment` | Owner model/record, company/access metadata, MIME/file content | SVG/raster background or decoration assets; optional original CAD/DXF and converted safe SVG attached to the floor. No duplicated file store. |
| Runtime projection | Assignment, queue/task/occupancy and clinical access stay in their own business records | Display overlays fetched from authorized business APIs; never authoritative saved occupancy/status inside geometry. |

Recommended later persistence: floor-owned scene metadata/decorations, area-owned
polygon JSON, station-owned placement JSON, and floor-owned background attachments.
Load assembles a projection using business IDs. Avoid a second writable copy of
area/station geometry inside a floor scene; separate scene models only if actual
multi-layout/version requirements appear. Stable ORM IDs determine identity;
client UUIDs identify unsaved graphical elements. Use one floor coordinate system
so nested business areas do not require nested transform arithmetic.

Names, containment, company, capability and lifecycle are business data. Position,
rotation, polygon vertices and wall/label decorations are layout data. A room may
be an area polygon containing two independent station elements. Polygon overlap
or containment is visual evidence, not automatic permission to reparent or route.

POS comparison: keep its separate ORM business records / layout JSON / attachment
content, reconstructed by a loader. Replace `pos.config` settings owner with floor
settings and its save/load endpoint with facility-specific authorized methods.
Unlike POS's omitted table/floor deactivation, omission/deleting a graphic should
remove its placement or decoration only. Business archive is an explicit operation
with history checks. Whitelist geometry keys and bounds instead of accepting all
unrecognized JSON keys as layout.

Future extraction strategy:

1. Pin source/license provenance and review source changes again at that task.
   No copied POS code is introduced by this audit.
2. Adapt small geometry/bounds/history and operation modules into the facility
   graphical feature, retaining required attribution and local assets. Remove
   `@pos_restaurant` imports/static paths and table-specific snapping rules.
3. Give a clinic store explicit load/save/attachment interfaces. Use standard
   Odoo Web/Owl hooks/registry/dialog/UI and an appropriate backend view/client
   action; replace POS popup, loaders, sessions, orders, devices, IndexedDB and
   websocket assumptions rather than importing a POS store.
4. Build station/area adapters and polygon support only after a dedicated reuse
   decision; keep text/lines/decorations separate from clinical business models.
5. Treat undo/redo as transient editing transactions. Ordinary write metadata
   and concurrency protection suffice initially; no custom persistent history.
6. Reuse private attachments with MIME/size validation, ownership/company checks,
   escaped text and safe styles. Review SVG content/serving policy explicitly;
   native `_check_contents` may make an upload text/plain for a non-privileged
   configurator. Do not bypass it or render arbitrary inline SVG/HTML. CAD/DXF
   conversion is a separately audited importer and outputs inert/sanitized assets.

## 11. Dental integration/migration

Answers to the required room questions:

| Question | Recommendation |
| --- | --- |
| Remain now? | Yes. Preserve accepted data and appointment behavior. |
| Become foundation? | No. Its room/chair mixture and missing company/resource/tree semantics are inadequate. |
| Compatibility facade? | Yes, temporarily where a reviewed mapping exists. Do not create a parallel long-term resource engine. |
| Migrate appointment to generic workstation? | Yes, in a separately authorized integration task, using checked `station_id` and keeping room history during transition. |
| Eventually retire room? | Retire from new operational configuration after consumers and legacy mappings are accepted; remove the model/field only in a later compatibility-breaking migration. |
| Can migration wait? | Yes for the unchanged accepted app. This does not provide new station scheduling/occupancy/company isolation meanwhile. New workflows must wait for a valid station mapping. |

The legacy name does not prove whether a record is a physical room, a single
chair, or several chairs. Classify actual records before mapping: chair-like
records may map to one station; room-like records map to one area and potentially
several stations. Never guess the workstation for historical bookings of a
multi-station room. Preserve unresolved legacy `room_id` until a human resolution.

A transition can extend room with an optional station link only for unambiguous
cases, while retaining a separate reviewed area mapping for true rooms. New
appointment `station_id` becomes the authoritative operational target; define
conflict behavior during dual-field coexistence and prevent divergent updates.
Do not build an automatic facade that silently turns one room into one station.
Recheck all appointment views/calendar filters, demo/imports, access profiles
and external consumers before any retirement. Operational references must use
restrict/history-preserving lifecycle, and station bookings need their own
reservation constraints, beyond current practitioner overlap checks.

Capability result:

- **USE** `dental.treatment` as the initial concrete Dental service catalog.
  **EXTEND** the Dental integration with station `treatment_ids` and checked
  selection rules later. A normal/endodontic/cleaning service can be mapped when
  actually represented by treatment records. Category is coarse taxonomy, not
  permission inherited by every station in an area.
- A billable CBCT/imaging service can be represented in that catalog (diagnostic,
  with appropriate tooth specificity), but configuration must recognize its
  automatic billing-product creation and price/name synchronization.
- **DEFER** broader examination capabilities. Protocol/device constraints,
  acquisition versus interpretation, order/result workflows, modalities and
  non-billable capabilities challenge the treatment/product coupling. This audit
  makes no **NEW** capability-engine recommendation. It does not create dummy
  priced treatments merely to tag operational equipment.
- Practitioner remains the clinical professional; use existing employee/user
  infrastructure for staffing, with a reviewed practitioner/employee binding
  later. HR manifest dependency alone supplies no such binding today.

## 12. Dependencies

**Recommended initial direct manifest dependencies: `['resource']`.**
Its inspected manifest already requires base and web. This follows the project
manifest rule to declare directly used addons rather than list base redundantly.
If a later graphical feature directly imports Web JS APIs, explicitly add `web`
at that stage. Generic backend views alone do not justify POS or HR dependencies.

| Candidate | Class for foundation | Exact disposition |
| --- | --- | --- |
| `base` | REQUIRED | ORM, company, attachments and security; already implicit/transitive. Do not redundantly add to proposed direct list. |
| `web` | REQUIRED | Native backend runtime supplied by Resource's dependency. OPTIONAL FUTURE direct dependency when own Web JS/assets/API usage begins. |
| `resource` | REQUIRED | Direct dependency for mixin/resource/calendars. |
| `hr` | OPTIONAL FUTURE | Staffing/workspace integration above foundation; no initial dependency. Dental currently already requires it independently. |
| `maintenance` | OPTIONAL FUTURE | Real equipment integration above foundation, not an initial field/dependency. |
| `dental_clinic` | DO NOT DEPEND | Reverse integration direction: Dental may depend on Facility later. |
| `point_of_sale` | DO NOT DEPEND | No POS configurations, loaders, orders or assets in foundation. |
| `pos_restaurant` | DO NOT DEPEND | Future selective adaptation does not require installing Restaurant. |
| `stock` | DO NOT DEPEND | Tree pattern uses ORM, not stock models. OPTIONAL FUTURE only in an actual inventory-placement bridge. |
| `mrp` | DO NOT DEPEND | Architectural reference only; Resource is sufficient underlying dependency. |

Do not add mail, calendar (meetings), generic queue/scheduling engines or graphical
libraries without their own direct requirement. `resource.calendar` comes from
Resource, not the Calendar meeting addon.

## 13. Deferred issues

Deferred work: scheduling-engine reuse selection and assignment representation;
station patient reservations/concurrent conflicts; direct/pool queue models and
claim atomicity; calling/displays; login workspace and temporary assignment;
staff credentials and generic examinations; equipment/stock links; site address
details; graphical layout version/units/polygons/import/security; legacy room
data mapping and eventual migrations. None was implemented here.

Only genuinely unresolved business decisions for later stages:

| Decision | Why a human answer is needed |
| --- | --- |
| Legacy room meaning per record | A physical multi-chair room cannot map to a single station without changing meaning; source cannot identify the intended chair for historical bookings. |
| Concurrent staffing/patient use | Decide whether one station can have multiple employees and/or concurrent patients, and substitution precedence. This determines scheduling conflicts, not the physical schema. |
| Service granularity | Decide whether the initial mapping is concrete billable treatments or additional non-billable service/protocol categories; treatment creation currently has billing side effects. |
| Temporary station choice authority | Decide who may select/substitute, approval requirements and how to handle no/multiple assignments; login identity alone grants no station permission. |
| Equipment relationship semantics | Decide fixed placement versus shared serving relationships where maintenance/inventory integration is requested. |

Architecture recommendations are explicit; no open human choice between
floor/area schemas, no permission request to write this audit, and no claim that
the next implementation has been authorized. Defaults proposed here (queue flags
false, system configuration, bottom-up archive) can be accepted or changed in
that future scoped task without blocking this completed audit.

## 14. Proposed CLINIC-SPACE-01 implementation scope

**Proposal only. Do not begin under REUSE-AUDIT-FACILITY-01.**

Smallest maintainable implementation, in the future authorized composition
checkout, is one addon `sd_facility`, direct dependency Resource, with:

1. **Exactly two new business models and the fields in section 5.** Space:
   name/code/sequence/company/type/parent/children/parent_path/complete_name/
   active/inheritance flag/direct stations. Station: related Resource name and
   active, code/sequence/space/resource/company/calendar/timezone/queue flag.
   No background/layout JSON or upload API yet. No additional facility/floor/
   area/capability/schedule/queue/history business models.
2. **Small Resource integration extension:** material defaults and owned-resource
   validation, name/active lifecycle, mixin copy reuse and uniqueness; checked
   area/company/calendar invariants also protected against direct owned Resource
   writes. No changes to Core. Freeze cross-company transfers, reject cycles and
   illegal parents/types, reject active children below inactive ancestry, and
   enforce bottom-up archive with restrict references.
3. **Standard backend views/actions only:** filtered Facility, Floors, Areas
   `list,form` actions on the one space model; Workstations `list,form` action.
   One Facilities menu with those four entries. Search views: name/code,
   company/type/parent or space, active/archived; appropriate company and
   parent/space groupings. Forms show full-name ancestry, direct children/direct
   stations, type-appropriate inheritance flag, and Resource calendar/timezone.
   Full-name area selector; no custom tree widget, canvas, workspace, dashboard,
   calendar assignment view, station switching or operational task screen.
4. **Native Odoo 20 `ir.access`:** company restrictions for all CRUD, internal
   read and system-configuration create/update, explicit bounded material
   Resource create/update authority. No clinical data exposed, general human
   Resource edit grants, unrelated role changes, routine delete or public access.
5. **Required acceptance checks for those invariants:** two companies (including
   related legal companies), two physical sites per company, nested mixed
   area/station children, cycle/type/reparent checks including archived records,
   material/resource exclusivity/copy, Resource CRUD under intended roles,
   direct Resource RPC mutation, calendar/company mismatch, archive/unarchive
   ordering, and restrict references. Include two stations in one room area.
   Verify standard tree queries include the root. Queue eligibility scenarios
   are future logic requirements; do not implement an eligibility engine simply
   to test it now.

Excluded from that proposal: Dental room/appointment modification or migration;
treatment capability fields; employee/practitioner binding; scheduling,
reservations, workspace, treatment/examination/task/visit/queue/calling flows;
Maintenance/Inventory/MRP/POS installations or integration; graphical code or
POS copying; custom history and production deployment.

The architecture supports the requested sequence: physical identities first;
then employee/station scheduling; login workspace; treatment/examination task
flow; full appointment/check-in/visit flow; and graphical representation later.
Supporting those references is not a claim that their business logic exists.

Verification for this audit: Dental baseline matched after fetch; the documented
pinned Odoo reference was clean; source implementations, callers, manifests and
relevant access contracts were inspected. Final review is limited to the single
new documentation artifact. No runtime tests are claimed for unimplemented
models. STOP after this document and final report; no CLINIC-SPACE-01 work starts.
