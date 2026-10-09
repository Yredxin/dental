# ADMIN-IA-01: clinic administration navigation and work permissions

Accepted cumulative change: ADMIN-IA-01, R1 and R2. Human review approved the
implementation and final independent browser acceptance. Baseline parent:
`913e30787983849e64defe72294870c5f905d496`, branch `port/odoo20-demo`.

## Navigation

The four relevant peer applications are 牙科, 员工, 空间 and 权限.

- Dental configuration retains 治疗项目目录, 执业牙医 and legacy 诊室/牙椅.
- Space contains 院址, 楼层, 区域 and 工作位, using existing Facility actions.
  Upgrade clears its former Dental parent; the generic addon is an application.
- Employees contains 排班 → 我的排班 / 全部排班. Internal users retain their
  own scheduling entry; existing access and company/self rules determine scope.
- Permissions contains 权限模板. The former standalone Apply menu is inactive;
  its wizard remains compatible with existing callers. The list/form name label
  is 模板名称. Separately authorized native Odoo applications remain available.

## Employee work permissions

The native employee form adds 工作权限 for Employee Management RW and System
administrators. It shows the linked login, a template selector, 应用模板 and
five 无 / 只读 / 读写 controls: 患者管理, 预约管理, 牙科临床, 员工管理,
牙科配置. Employees without an internal login receive an explanatory message
and have no capability editor or template application.

Templates are one-time presets. Applying saves immediately and reloads; later
manual changes use normal Save. The Nurse preset is read/read/read/none/none.
Changing Appointment to read/write persists across reload. The selector is
computed and non-stored, clears on a new request, and creates no live Profile
binding. Actual user groups remain the sole permission authority.

R2 retains the selected non-stored value in native Employee.write so web_save
returns it before the object button evaluates its context. The action then
validates the selected profile and reuses the existing AUTH02 capability helper.
No custom JavaScript, stored permission matrix or alternate authority engine
is introduced.

Employee READ uses the native public directory and cannot apply or edit
capabilities. Ordinary employees have no permission management. Employee RW
checks accessible linked employees, actor authority and native employee access.
AUTH02 retains internal-user, company and protected-System-target checks. Its
existing scoped sudo accepts only fixed Dental group commands; arbitrary group
IDs, levels and caller context are never forwarded. Unrelated memberships and
native System authority are preserved. Permission definition management remains
restricted to Configuration RW/System.

## Upgrade and translation requirements

Pinned Community reference inspected:
`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`.
Local regression runtime: `odoo:20.0-20260926`; its source SHA is not asserted.

R1 diagnosed native translation import preserving existing Chinese values by
default. Existing databases with old menu/view translations require the supported
translation-overwrite option. Stop the local application for upgrade and restart
afterwards to reload Python translations:

```sh
odoo server -c /etc/odoo/odoo.conf -d sd_dental_dev \
  -u dental_clinic,sd_facility,sd_facility_schedule --i18n-overwrite \
  --without-demo=True --stop-after-init --no-http --max-cron-threads=0
```

PO/POT entries retain the native extraction markers needed for Python messages.
There is no custom translation loader, direct translation SQL or Core patch.
Native unrelated English labels remain outside this task's accepted scope.

## Verification and acceptance

The accepted cumulative suite covers AUTH01/AUTH02, Facility and Dental
integration, Schedule and Dental integration, 25 ADMIN-IA cases, translation
regressions and two native Web wrappers. The wrappers execute five native
view_button_hook cases for each desktop/mobile preset, without skips.

The full suite is selected with:

```text
dental_auth,facility,facility_schedule,admin_ia,/web:WebSuite.test_unit_desktop[@web/views/view_button_hook],/web:MobileWebSuite.test_unit_mobile[@web/views/view_button_hook]
```

Independent real Chrome acceptance passed on upgraded `sd_dental_dev` and clean
`admin_ia_r2_release`, including five fresh credential logins, navigation,
Nurse application, manual override/reload, no-login/READ/ordinary/System behavior
and narrow RPC security checks. Evidence and account handoffs remain outside Git.
The clean browser uses localhost separately from the upgraded host to avoid
session-cookie collisions; browser automatic translation is excluded from
terminology acceptance.

The former logout HTTP 405 finding was an acceptance-method false positive.
Pinned Odoo20 logout accepts POST only. Its native menu posts the CSRF token and
redirects; actual rendered-menu logout works for all reviewed roles. Direct GET
returns the expected 405 and is not a valid browser UX logout test.

Before final commit, the complete suite passed on both databases: 167 tests
each, zero failures/errors/skips, including both native Web presets. Post-push
verification is recorded in the closure report outside Git. No browser evidence,
temporary harness files or credentials belong in this commit.

## Scope

AUTH is extended through its existing boundary, not redesigned. Facility and
Schedule business models, Appointment and legacy dental.room are unchanged.
No room migration, Workspace, Queue, account provisioning, Odoo Core changes
or production/NAS operations are included. DENTAL-WORKSPACE-01 is deferred.
