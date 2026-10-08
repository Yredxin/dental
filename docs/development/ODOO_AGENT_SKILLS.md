# Odoo 20 agent skills and SD Dental policy

Installed on 2026-10-08 (Asia/Shanghai) for SKILL-FOUNDATION-01. This foundation
makes official framework guidance available alongside the project's reuse-first
policy before future Dental feature work. It authorizes no business changes.

## Provenance

| Field | Recorded value |
| --- | --- |
| Source repository | `https://github.com/Yredxin/odoo.git` (project's Odoo source fork) |
| Source checkout | `D:/odoo-sd/odoo20-clean` |
| Source branch | `20.0` |
| Source commit | `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` |
| Source directory | `skills/` (Git tree `74fed0325871394bbd9ce7aca69afedad1d7e0c0`) |
| Copy date | `2026-10-08`, Asia/Shanghai |
| Destination repository | `https://github.com/Yredxin/dental.git` |
| Destination | `D:/Code/odoo/dental/.agents/skills/` (repository-relative `.agents/skills/`) |
| Dental baseline | `port/odoo20-demo` at `d2c766a498d523f704ac95303b1227c1fd40a551` |
| Composition reference | `D:/Code/odoo/odoo-sd`, `main` at `bf6d30035701159f968f8c5901b38d186fa48521` |

The exact local source revision is the Odoo 20 reference recorded by the existing
development environment. Its `odoo/release.py` declares version 20.0. The runtime
is separately pinned to `odoo:20.0-20260926` at
`sha256:cdd83e8359b3e8c357895d476396c05021fed9975bf420f353bab25fcaed1533` with
PostgreSQL 18. **The exact source commit corresponding to the runtime image is
not established.** See the composition checkout's
`deployment/dev/PREFLIGHT.md` and `deployment/dev/DEVELOPMENT.md`. Do not imply
the source checkout and image are byte-identical.

## Installed content

The complete `skills/` tree was copied byte-for-byte: **23 files**, including its
upstream `README.md`, both `AUTHORING.md` files and all guideline files. Installed
official skills:

- `odoo-guidelines`
- `odoo-web-guidelines`
- `odoo-security`
- `odoo-review`

All four must remain together because they reference siblings. The project-owned
`.agents/.gitattributes` disables line-ending conversion for skill files so future
Windows checkouts preserve their recorded bytes without changing global Git settings.
The official skills are vendored copies: **do not manually edit, translate,
prune or improve them**.
Put project architecture rules in
[sd-odoo-dental](../../.agents/skills/sd-odoo-dental/SKILL.md), which complements
the official skills and defers to them on framework details.

[ODOO_AGENT_SKILLS_SHA256.json](ODOO_AGENT_SKILLS_SHA256.json) records the SHA-256
and pinned Git blob ID of every official file. During installation, each local
source file and copied destination was compared with `git cat-file blob` at the
recorded source commit. No moving remote ref or network download was used.

## Project-local discovery

[Codex's official skill documentation](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
supports `.agents/skills/` between the session's current directory and repository
root. Launch a **fresh session from `D:/Code/odoo/dental`**, or a subdirectory of
that Git repository. A session rooted at the sibling composition repository or
the parent `D:/Code/odoo` is not evidence of discovery inside Dental. No global
installation, machine configuration or project `AGENTS.md` is required for
loading these skills.

The SD skill's description routes Dental feature assessment and implementation
to the required audit. Skill discovery is not a substitute for human acceptance
of a design. Follow its workflow before implementation.

See [verification evidence](ODOO_AGENT_SKILLS_VERIFICATION.md) for the fresh
harness scan, no-code dry run and validation results. The installed skills are
available to subsequent turns/sessions; restart if an existing session retains
an old catalog.

## Deliberate update procedure

1. Start a separately authorized tooling task. Confirm clean affected paths and
   pin the intended Odoo **20** source commit; never silently use `master`, another
   major version or an unpinned branch. Record any change in source origin.
2. Inspect upstream differences from the recorded commit, including sibling
   references, new/deleted skills, guideline semantics and licensing. Review
   those differences before replacement; do not automatically update later.
3. Copy the complete official skill tree from the approved commit, preserving
   bytes and sibling layout. Keep `sd-odoo-dental` separate. If upstream introduces
   a collision with a project skill, stop for a decision rather than overwrite it.
4. Regenerate the official manifest from the approved Git blobs; update this
   provenance and copy date. Do not use the working tree as an unverified source.
5. Validate all manifests, local links/anchors and sibling references. Compare
   the installed file set and hashes against the pinned source tree. Start a
   fresh Codex session in Dental and repeat discovery and the no-code dry run.
6. Review the diff, run `git diff --check`, confirm the authorized path scope,
   and submit the completed change for human acceptance before committing unless
   prior explicit authorization applies.

No future updates or business features are scheduled by this installation.
