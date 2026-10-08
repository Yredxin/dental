# SKILL-FOUNDATION-01 verification

Date: 2026-10-08 (Asia/Shanghai). **SKILL-FOUNDATION-01 = READY.** The project owner
accepted the local discovery and integrity evidence below as sufficient and
waived the external OpenAI no-code dry run. Installation, actual harness
discovery and local validation are complete. No business implementation or global
skill installation was performed. The owner subsequently authorized one closure
commit containing only the 31 SKILL-FOUNDATION-01 files in this Dental repository.

## Closure decision

The project owner's closure decision accepts the following evidence:

- Fresh Codex 0.138.0 session and `skills/list(forceReload=true)`.
- All five repository-local skills discovered, enabled and returned with
  `scope=repo`, with no loading errors.
- Official skill file integrity: PASS.
- Relative-reference validation: PASS.
- No business-source changes and no Odoo Core changes.

The external OpenAI dry run is **WAIVED**. Do not attempt another external API
call or transmit private Dental/Odoo-SD repository content outside the local
development environment to validate agent skill discovery. The two limitations
recorded below are **NON-BLOCKING** and do not prevent this task's closure.

## Preflight evidence

Reported before repository writes:

| Repository | Branch / HEAD | Initial state |
| --- | --- | --- |
| `D:/Code/odoo/dental` | `port/odoo20-demo` / `d2c766a498d523f704ac95303b1227c1fd40a551` | Clean; exact accepted baseline. |
| `D:/Code/odoo/odoo-sd` | `main` / `bf6d30035701159f968f8c5901b38d186fa48521` | Existing ` M deployment/README.md` and `?? deployment/dev/`; preserved. |
| `D:/odoo-sd/odoo20-clean` | `20.0` / `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` | Clean, confirmed by read-only Git status outside the workspace sandbox; `skills/` exists. |

No existing `.agents/`, `.claude/`, `.codex/`, `AGENTS.md`, `CLAUDE.md` or `SKILL.md`
was found in either project. Odoo's existing skill directory was
`D:/odoo-sd/odoo20-clean/skills/`, with the four official skills. No Odoo project
agent instruction file or `.agents`/`.claude` directory was found. No applicable
parent `AGENTS.md` was found in `D:/`, `D:/Code`, `D:/Code/odoo` or `D:/odoo-sd`.

User skill roots already present were `C:/Users/Yredx/.agents/skills` and
`C:/Users/Yredx/.codex/skills`; the existing user
`C:/Users/Yredx/.codex/AGENTS.md` was empty. These were not modified. Bundled
plugin/system skills remain managed by the harness. No material instruction
conflict was found.

**NON-BLOCKING:** exact provenance equivalence between the pinned Odoo source
snapshot and the runtime Docker image has not yet been established. The
reference checkout is not asserted to match the exact runtime image commit.
This limitation is explicitly accepted by the closure decision. See
[source provenance](ODOO_AGENT_SKILLS.md).

## Byte integrity and reference validation

- All **23 official files**, including `README.md`, were copied completely and
  compared byte-for-byte to Git blobs in the recorded source commit.
- [SHA-256 manifest](ODOO_AGENT_SKILLS_SHA256.json) records every official path,
  checksum and Git blob ID. The installed and source file sets match exactly.
- All five `SKILL.md` files pass the bundled `skill-creator` `quick_validate.py`.
  Invoke Python with `-X utf8` on this Windows machine: the upstream security
  skill contains UTF-8 punctuation, and the validator otherwise uses the system
  GBK encoding. Official contents were preserved unchanged.
- The local validator passed **145 local reference checks**, covering Markdown
  paths and heading anchors across the
  installed skills and development documents, including the code-formatted
  sibling paths used by `odoo-review`.
- The matrix contains **32 capability areas**, each with one allowed strategy,
  and source files/model/method/XML-ID evidence. It defers the clinical visit
  representation to a separate reuse/design audit.

Reproduce byte/file/reference validation from Dental:

```powershell
python -X utf8 docs/development/verify_agent_skills.py --source D:/odoo-sd/odoo20-clean
Get-ChildItem -Directory .agents/skills | ForEach-Object {
    python -X utf8 C:/Users/Yredx/.codex/skills/.system/skill-creator/scripts/quick_validate.py $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "Skill validation failed" }
}
git diff --check
git diff --exit-code -- dental_clinic
git status --short --untracked-files=all
```

The helper requires only Python's standard library. The bundled skill validator
also requires PyYAML, available in the inspected Python environment. The helper
is read only; it does not install skills, update provenance or contact a model.

Before the closure commit, the completed changes were untracked, so whitespace was additionally
checked with `git -c core.autocrlf=false diff --no-index --check -- /dev/null <file>`
for each new file. Project-generated JSON evidence was normalized to LF; upstream
files were not normalized or rewritten.
Nothing was staged to make those validation results appear in a tracked diff.

## Actual fresh harness discovery: PASS

Started a new `codex app-server` process with `cwd=D:/Code/odoo/dental`, using the
existing Codex installation and normal user configuration. No catalog was
injected into the test. Exchanged:

```json
{"id":1,"method":"initialize","params":{"clientInfo":{"name":"skill-foundation-01-verifier","version":"1.0"}}}
{"method":"initialized","params":{}}
{"id":2,"method":"skills/list","params":{"cwds":["D:\\Code\\odoo\\dental"],"forceReload":true}}
```

The process identified itself as **Codex Desktop/0.138.0**. All expected skills
were returned from the Dental checkout with **`scope=repo`, `enabled=true`**:

- `odoo-guidelines`
- `odoo-web-guidelines`
- `odoo-security`
- `odoo-review`
- `sd-odoo-dental`

There were no Dental skill-loading errors or duplicate expected skill names.
The filtered actual response, including paths and descriptions, is saved in
[ODOO_AGENT_SKILLS_DISCOVERY.json](ODOO_AGENT_SKILLS_DISCOVERY.json). The test
process was terminated after collecting the response. No model inference was
needed for this discovery check.

The outer restricted shell could not initialize Codex's normal SQLite state, so
the same discovery-only probe ran with approved access to its existing local
runtime state. No global settings, skill installation or credentials were edited.

## External no-code dry run: WAIVED / NON-BLOCKING

Prompt submitted to a separate ephemeral, read-only Codex CLI session:

```text
How should a new Dental inventory feature be approached?

This is a NO-CODE dry run to verify project-local skill discovery in a fresh
Codex session launched from the Dental repository. Identify the relevant
discovered project skills, read their applicable instructions, and inspect
enough local source evidence to explain the approach. Do not edit or create
files, run business processes, modify databases, send notifications, commit,
or implement any feature. Do not start model design. Keep the answer concise
and identify evidence read.
```

The invocation used `codex exec --ephemeral --sandbox read-only --json --cd
D:/Code/odoo/dental`, with output directed outside the Dental/composition source
repositories. It exited **1** without a model answer. The model endpoint returned
**HTTP 401, `invalid_api_key`**: external provider authentication unavailable.
This failed attempt is **NON-BLOCKING** under the project owner's closure
decision. No successful independent reasoning result exists; the external dry
run is waived, not reported as passed.

A read-only diagnostic showed that the CLI's saved login is ChatGPT, while the
parent environment also supplies a `CODEX_API_KEY` variable. A proposed retry
would have cleared that variable only in the child process, leaving global
configuration and saved credentials untouched. **Automatic approval review
rejected that retry before execution**, stating that sending potentially
sensitive repository contents to the external OpenAI API lacked explicit
authorization for that payload and destination. No workaround was attempted.
Credential values are intentionally excluded from this evidence.

The owner subsequently waived this external validation and accepted the local
evidence as sufficient. No retry, external transmission, authentication change
or further approval request is required or authorized for this validation.

## Local policy rehearsal (not the independent dry-run result)

The installed policy supports the following no-code reasoning, checked in the
current working session against the matrix's inspected source:

- Start with `sd-odoo-dental` and a complete `REUSE AUDIT`; consult applicable
  `odoo-guidelines` sections. Use `odoo-review` and `odoo-security` later when
  reviewing the approved implementation, and web guidance if a UI is in scope.
- Odoo candidates: `product.product`, `product.template`, `stock.move`,
  `stock.move.line`, `stock.location`, `stock.quant`, `stock.picking`.
- Dental already links treatment services and prescription lines to products;
  it has no stock dependency or consumption implementation. SD's `addons/`
  contains no implementation. Inspect module availability before proposing work.
- Product master: `USE`; inventory engine: `USE`; stock ledger: `USE`. No new
  foundational capability is justified by the broad inventory idea alone.
- Reject duplicate product masters, custom stock quantity tables and custom
  inventory ledgers. Actual clinical consumption triggers, reversals and any
  treatment/material relation require a separate design audit and human decision.
- Decision for this broad idea: **DESIGN REVIEW REQUIRED**. No code or future
  clinical schema is created. This local rehearsal is supplementary evidence;
  it does not claim a successful independent model answer. The external dry run
  is waived by the closure decision.

## Final change scope

All **31 new Dental files** are within `.agents/` (24 skill files plus the
project-owned line-ending attributes file) or `docs/development/` (6 files).
The attributes preserve vendored bytes on future Windows checkouts without
modifying upstream content or global configuration. The complete upstream file list is in the hash
manifest; the project-specific additions are the SD skill, provenance, matrix,
verification report, filtered discovery response, checksum manifest and local
validation helper. No project `AGENTS.md` was necessary for discovery.

- Before closure staging, Dental tracked source and index were unchanged;
  no business source was modified.
- Odoo Core is unchanged; the reference checkout remains clean.
- Composition branch, HEAD and existing dirty-path status are preserved.
- `git diff --check`, individual untracked-file whitespace checks and the
  authorized path-scope check pass.
- Validation performed no staging, commit, business process, database
  modification or notification. The separately authorized closure commit is
  limited to these 31 files under `.agents/` and `docs/development/` on
  `port/odoo20-demo`; it includes no `dental_clinic` business source.

Authorized closure commit subject:
`chore(agent): add Odoo development skills and reuse policy`.
