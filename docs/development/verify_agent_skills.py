"""Read-only validation of vendored bytes, file sets and Markdown references.

Run from any directory with Python 3. Use --source for comparison with the
recorded local Odoo Git object database. Harness discovery is a separate check.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def anchors(document):
    """GitHub-style anchors for the simple ATX headings used by these skills."""
    seen = {}
    result = set()
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", document, re.MULTILINE):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        occurrence = seen.get(slug, 0)
        seen[slug] = occurrence + 1
        result.add(slug if occurrence == 0 else f"{slug}-{occurrence}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Local Odoo source checkout")
    args = parser.parse_args()
    docs = Path(__file__).resolve().parent
    root = docs.parent.parent
    skills = root / ".agents" / "skills"
    manifest = json.loads((docs / "ODOO_AGENT_SKILLS_SHA256.json").read_text(encoding="utf-8"))
    official = {entry["path"]: entry for entry in manifest["files"]}
    errors = []
    skill_names = ["odoo-guidelines", "odoo-web-guidelines", "odoo-security", "odoo-review"]
    actual = set()
    for name in skill_names:
        directory = skills / name
        if not (directory / "SKILL.md").is_file():
            errors.append(f"Missing official SKILL.md: {name}")
        actual.update(path.relative_to(skills).as_posix() for path in directory.rglob("*") if path.is_file())
    if (skills / "README.md").is_file():
        actual.add("README.md")
    if actual != set(official):
        errors.append(f"Official file-set mismatch: missing={set(official) - actual}, extra={actual - set(official)}")
    for relative, entry in official.items():
        path = skills / relative
        if not path.is_file():
            errors.append(f"Missing file: {relative}")
            continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            errors.append(f"SHA-256 mismatch: {relative}")
        blob_id = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if blob_id != entry["git_blob"]:
            errors.append(f"Git blob mismatch: {relative}")

    if args.source:
        git = ["git", "--git-dir=" + str(args.source.resolve() / ".git")]
        entries = subprocess.check_output(
            git + ["ls-tree", "-r", manifest["source_commit"], "skills"], text=True
        ).splitlines()
        upstream = {}
        for entry in entries:
            metadata, path = entry.split("\t", 1)
            upstream[path.removeprefix("skills/")] = metadata.split()[2]
        if upstream != {path: entry["git_blob"] for path, entry in official.items()}:
            errors.append("Manifest differs from the pinned source Git tree")
        for relative, object_id in upstream.items():
            committed = subprocess.check_output(git + ["cat-file", "blob", object_id])
            installed = skills / relative
            if not installed.is_file() or installed.read_bytes() != committed:
                errors.append(f"Pinned source/installed bytes differ: {relative}")
            if (args.source / "skills" / relative).read_bytes() != committed:
                errors.append(f"Source worktree/commit bytes differ: {relative}")

    reference_count = 0
    documents = sorted(skills.rglob("*.md")) + sorted(docs.glob("*.md"))
    for path in documents:
        document = path.read_text(encoding="utf-8")
        references = re.findall(r"\[[^\]\n]+\]\(([^)\s]+)\)", document)
        references += re.findall(r"`(\.\.?/[^`\s]+\.md(?:#[^`\s]+)?)`", document)
        for reference in references:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc:
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            reference_count += 1
            if not target.is_file():
                errors.append(f"Missing reference: {path.relative_to(root)} -> {reference}")
            elif parsed.fragment and target.suffix == ".md":
                if unquote(parsed.fragment) not in anchors(target.read_text(encoding="utf-8")):
                    errors.append(f"Missing anchor: {path.relative_to(root)} -> {reference}")

    for name in skill_names + ["sd-odoo-dental"]:
        path = skills / name / "SKILL.md"
        if not path.is_file():
            errors.append(f"Missing skill: {name}")
            continue
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---\n") or "\n---\n" not in content[4:]:
            errors.append(f"Missing YAML frontmatter: {name}")
    print(json.dumps({
        "result": "FAIL" if errors else "PASS",
        "official_files": len(official),
        "skills": len(skill_names) + 1,
        "local_references_checked": reference_count,
        "pinned_source_comparison": bool(args.source),
        "errors": errors,
    }, indent=2))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
