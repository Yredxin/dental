# Cumulative AUTH01/AUTH02 committed file scope

Human-approved implementation on `port/odoo20-demo`, relative to accepted parent
`2d3b6c8a023fd59ad71fee1fb80cb660d9d8dfbf`.

The final scope is **27 source/test files and nine permanent documents**. The
complete source manifest is in
[AUTH02 acceptance](DENTAL_AUTH_02_ACCEPTANCE_CASES.md#complete-cumulative-changed-source-manifest).
Source bytes were preserved during final commit preparation; tests were rerun.

## Permanent documentation

- `DENTAL_AUTH_V1_ROLE_MATRIX.md`: historical AUTH01 oracle, explicitly superseded
  by AUTH02's capability model.
- `DENTAL_AUTH_01_ACCEPTANCE_CASES.md`: concise 31-category/seven-role ledger.
- `DENTAL_AUTH_01_AUDIT.md`: reuse, containment and historical review summary.
- `DENTAL_AUTH_01_CHANGED_FILES.md`: this cumulative scope.
- `DENTAL_AUTH_01_INDEPENDENT_ACCEPTANCE.md`: historical real-Chrome summary.
- `DENTAL_AUTH_01_RPC_ACCEPTANCE.md`: historical authenticated controls/results.
- `DENTAL_AUTH_02_CAPABILITY_MODEL.md`: final architecture and cumulative review.
- `DENTAL_AUTH_02_ACCEPTANCE_CASES.md`: final cases, matrix, validation and manifest.
- `DENTAL_AUTH_02_INDEPENDENT_ACCEPTANCE.md`: final independent acceptance.

## Excluded disposable evidence

All 175 initially dirty files were classified: 27 accepted source/test files,
nine permanent documents, and 139 disposable raw artifacts. The raw files
(logs, JSON responses/counts/schema, screenshots, DOM captures and one-off
upgrade harness) were moved outside Git to
`D:\Code\odoo\.tmp\authorization-final-20261009\raw`. Their SHA256 hashes were
verified after moving; original versions of the condensed documents and the
initial dirty-file inventory are retained beside that archive. AUTH02 raw
evidence remains under `D:\Code\odoo\.tmp\auth02`.

No raw acceptance output, disposable credentials, unrelated source, Core or
composition changes are included. The obsolete 158-file AUTH01 inventory and
historical source hashes remain in the external original-documentation archive;
they do not describe the final cumulative commit.
