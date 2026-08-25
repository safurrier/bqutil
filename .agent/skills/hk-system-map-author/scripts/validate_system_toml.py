#!/usr/bin/env python3
"""Validate Harness Kit .harness/system.toml files.

This script performs structural validation only. It does not prove that component
or invariant claims are semantically true.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
COMMANDISH_PREFIXES = (
    "cargo ",
    "go test ",
    "make ",
    "mise ",
    "npm ",
    "pnpm ",
    "pytest ",
    "python ",
    "uv ",
    "yarn ",
)
MAX_SUMMARY = 180
MAX_STATEMENT = 220
MAX_RULE = 220
KNOWN_TOP_LEVEL = {"version", "system", "components", "relations"}
KNOWN_SYSTEM = {"name", "summary"}
KNOWN_COMPONENT = {
    "id",
    "title",
    "kind",
    "paths",
    "read_before_editing",
    "validation_checks",
    "invariants",
}
KNOWN_INVARIANT = {"id", "statement", "evidence", "validation_checks"}
KNOWN_RELATION = {"from", "to", "kind", "rule"}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    field_path: str | None = None
    related_path: str | None = None
    check_label: str | None = None


@dataclass(frozen=True)
class Result:
    ok: bool
    path: str
    findings: list[Finding]
    info: dict[str, Any]


class ProfileLoadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def git_root(path: Path) -> Path:
    try:
        out = subprocess.check_output(  # noqa: S603
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],  # noqa: S607
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return Path(out).resolve()
    except Exception:
        return path.resolve()


def is_glob(ref: str) -> bool:
    return any(ch in ref for ch in "*?[")


def looks_like_command(value: str) -> bool:
    return value.strip().startswith(COMMANDISH_PREFIXES)


def path_exists_or_glob(repo: Path, ref: str) -> bool:
    if ref.startswith(("http://", "https://")):
        return True
    if looks_like_command(ref):
        return False
    p = Path(ref)
    if p.is_absolute():
        return p.exists()
    if is_glob(ref):
        return any(
            fnmatch.fnmatch(str(path.relative_to(repo)), ref)
            for path in repo.rglob("*")
        )
    return (repo / p).exists()


def string_list(value: Any, *, non_empty: bool = False) -> bool:
    if not isinstance(value, list):
        return False
    if non_empty and not value:
        return False
    return all(isinstance(item, str) and item.strip() for item in value)


def add_unknown_findings(
    findings: list[Finding], table: dict[str, Any], allowed: set[str], field_path: str
) -> None:
    for key in sorted(set(table) - allowed):
        findings.append(
            Finding(
                "unknown-field",
                "warning",
                f"unknown field '{key}' at {field_path}",
                f"{field_path}.{key}" if field_path else key,
            )
        )


def load_profile_checks(profile: Path | None) -> set[str]:
    if profile is None:
        return set()
    try:
        text = profile.read_text()
    except OSError as e:
        raise ProfileLoadError(
            "missing-profile", f"profile could not be read: {e}"
        ) from e
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ProfileLoadError(
            "invalid-profile-toml", f"profile TOML could not be parsed: {e}"
        ) from e
    checks = data.get("checks", [])
    if checks is None:
        return set()
    labels: set[str] = set()
    if isinstance(checks, list):
        for check in checks:
            if isinstance(check, dict) and isinstance(check.get("name"), str):
                labels.add(check["name"])
    return labels


def validate_map(
    repo: Path, path: Path, profile: Path | None = None, strict_profile: bool = False
) -> Result:
    findings: list[Finding] = []
    info: dict[str, Any] = {"components": 0, "invariants": 0, "relations": 0}

    if not path.exists():
        findings.append(
            Finding("missing-system-map", "error", f"system map not found: {path}")
        )
        return Result(False, str(path), findings, info)

    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        findings.append(Finding("invalid-toml", "error", f"invalid TOML: {e}", None))
        return Result(False, str(path), findings, info)

    if not isinstance(data, dict):
        findings.append(
            Finding("invalid-root", "error", "root TOML value must be a table")
        )
        return Result(False, str(path), findings, info)

    add_unknown_findings(findings, data, KNOWN_TOP_LEVEL, "")

    version = data.get("version")
    info["version"] = version if isinstance(version, int) else None
    if version != 1:
        findings.append(
            Finding("invalid-version", "error", "version = 1 is required", "version")
        )

    system = data.get("system")
    if not isinstance(system, dict):
        findings.append(
            Finding("missing-system", "error", "[system] table is required", "system")
        )
    else:
        add_unknown_findings(findings, system, KNOWN_SYSTEM, "system")
        for key in ("name", "summary"):
            if not isinstance(system.get(key), str) or not system.get(key, "").strip():
                findings.append(
                    Finding(
                        "missing-system-field",
                        "error",
                        f"[system].{key} is required",
                        f"system.{key}",
                    )
                )
        if (
            isinstance(system.get("summary"), str)
            and len(system["summary"]) > MAX_SUMMARY
        ):
            findings.append(
                Finding(
                    "long-summary",
                    "warning",
                    f"system.summary should be <= {MAX_SUMMARY} chars",
                    "system.summary",
                )
            )

    components = data.get("components")
    if not isinstance(components, list) or not components:
        findings.append(
            Finding(
                "missing-components",
                "error",
                "at least one [[components]] table is required",
                "components",
            )
        )
        components = []

    try:
        known_checks = load_profile_checks(profile)
    except ProfileLoadError as e:
        findings.append(
            Finding(
                e.code,
                "error",
                e.message,
                "profile",
                str(profile) if profile else None,
            )
        )
        known_checks = set()
    unresolved_checks: set[str] = set()
    component_ids: set[str] = set()
    all_component_ids: list[str] = []
    invariant_count = 0

    for index, component in enumerate(components):
        cpath = f"components[{index}]"
        if not isinstance(component, dict):
            findings.append(
                Finding(
                    "invalid-component", "error", "component must be a table", cpath
                )
            )
            continue
        add_unknown_findings(findings, component, KNOWN_COMPONENT, cpath)
        cid = component.get("id")
        if not isinstance(cid, str) or not ID_RE.match(cid):
            findings.append(
                Finding(
                    "invalid-component-id",
                    "error",
                    "component id must be kebab-case",
                    f"{cpath}.id",
                )
            )
            cid = f"<component-{index}>"
        elif cid in component_ids:
            findings.append(
                Finding(
                    "duplicate-component-id",
                    "error",
                    f"duplicate component id '{cid}'",
                    f"{cpath}.id",
                )
            )
        else:
            component_ids.add(cid)
            all_component_ids.append(cid)

        for key in ("title", "kind"):
            if (
                not isinstance(component.get(key), str)
                or not component.get(key, "").strip()
            ):
                findings.append(
                    Finding(
                        "missing-component-field",
                        "error",
                        f"component {cid} missing {key}",
                        f"{cpath}.{key}",
                    )
                )

        paths = component.get("paths")
        if not string_list(paths, non_empty=True):
            findings.append(
                Finding(
                    "invalid-paths",
                    "error",
                    f"component {cid} paths must be a non-empty string array",
                    f"{cpath}.paths",
                )
            )
        else:
            for pos, ref in enumerate(paths):
                if not path_exists_or_glob(repo, ref):
                    findings.append(
                        Finding(
                            "missing-path",
                            "error",
                            f"component {cid} referenced path/glob does not exist: {ref}",
                            f"{cpath}.paths[{pos}]",
                            ref,
                        )
                    )

        for field in ("read_before_editing", "validation_checks"):
            if field in component and not string_list(component[field]):
                findings.append(
                    Finding(
                        "invalid-string-list",
                        "error",
                        f"component {cid} {field} must be a string array",
                        f"{cpath}.{field}",
                    )
                )
        if "read_before_editing" in component and string_list(
            component["read_before_editing"]
        ):
            for pos, ref in enumerate(component["read_before_editing"]):
                if not path_exists_or_glob(repo, ref):
                    findings.append(
                        Finding(
                            "missing-read-before",
                            "error",
                            f"read_before_editing path does not exist: {ref}",
                            f"{cpath}.read_before_editing[{pos}]",
                            ref,
                        )
                    )
        if "validation_checks" in component and string_list(
            component["validation_checks"]
        ):
            for label in component["validation_checks"]:
                if looks_like_command(label):
                    findings.append(
                        Finding(
                            "command-in-check-label",
                            "error",
                            "validation_checks must contain labels, not commands",
                            f"{cpath}.validation_checks",
                            check_label=label,
                        )
                    )
                if profile is not None and label not in known_checks:
                    unresolved_checks.add(label)

        seen_invariants: set[str] = set()
        invariants = component.get("invariants", [])
        if invariants is None:
            invariants = []
        if not isinstance(invariants, list):
            findings.append(
                Finding(
                    "invalid-invariants",
                    "error",
                    f"component {cid} invariants must be an array",
                    f"{cpath}.invariants",
                )
            )
            invariants = []
        for inv_index, invariant in enumerate(invariants):
            ipath = f"{cpath}.invariants[{inv_index}]"
            invariant_count += 1
            if not isinstance(invariant, dict):
                findings.append(
                    Finding(
                        "invalid-invariant", "error", "invariant must be a table", ipath
                    )
                )
                continue
            add_unknown_findings(findings, invariant, KNOWN_INVARIANT, ipath)
            iid = invariant.get("id")
            if not isinstance(iid, str) or not ID_RE.match(iid):
                findings.append(
                    Finding(
                        "invalid-invariant-id",
                        "error",
                        "invariant id must be kebab-case",
                        f"{ipath}.id",
                    )
                )
                iid = f"<invariant-{inv_index}>"
            elif iid in seen_invariants:
                findings.append(
                    Finding(
                        "duplicate-invariant-id",
                        "error",
                        f"duplicate invariant id '{iid}' within component '{cid}'",
                        f"{ipath}.id",
                    )
                )
            else:
                seen_invariants.add(iid)
            statement = invariant.get("statement")
            if not isinstance(statement, str) or not statement.strip():
                findings.append(
                    Finding(
                        "missing-invariant-statement",
                        "error",
                        "invariant statement is required",
                        f"{ipath}.statement",
                    )
                )
            elif len(statement) > MAX_STATEMENT:
                findings.append(
                    Finding(
                        "long-invariant-statement",
                        "warning",
                        f"invariant statement should be <= {MAX_STATEMENT} chars",
                        f"{ipath}.statement",
                    )
                )
            for field in ("evidence", "validation_checks"):
                if field in invariant and not string_list(invariant[field]):
                    findings.append(
                        Finding(
                            "invalid-string-list",
                            "error",
                            f"invariant {field} must be a string array",
                            f"{ipath}.{field}",
                        )
                    )
            if "evidence" in invariant and string_list(invariant["evidence"]):
                for pos, ref in enumerate(invariant["evidence"]):
                    if not path_exists_or_glob(repo, ref):
                        findings.append(
                            Finding(
                                "missing-evidence",
                                "error",
                                f"invariant evidence path/glob does not exist: {ref}",
                                f"{ipath}.evidence[{pos}]",
                                ref,
                            )
                        )
            if "validation_checks" in invariant and string_list(
                invariant["validation_checks"]
            ):
                for label in invariant["validation_checks"]:
                    if looks_like_command(label):
                        findings.append(
                            Finding(
                                "command-in-check-label",
                                "error",
                                "validation_checks must contain labels, not commands",
                                f"{ipath}.validation_checks",
                                check_label=label,
                            )
                        )
                    if profile is not None and label not in known_checks:
                        unresolved_checks.add(label)

    relations = data.get("relations", [])
    if relations is None:
        relations = []
    if not isinstance(relations, list):
        findings.append(
            Finding(
                "invalid-relations", "error", "relations must be an array", "relations"
            )
        )
        relations = []
    for index, relation in enumerate(relations):
        rpath = f"relations[{index}]"
        if not isinstance(relation, dict):
            findings.append(
                Finding("invalid-relation", "error", "relation must be a table", rpath)
            )
            continue
        add_unknown_findings(findings, relation, KNOWN_RELATION, rpath)
        for key in ("from", "to", "kind", "rule"):
            if (
                not isinstance(relation.get(key), str)
                or not relation.get(key, "").strip()
            ):
                findings.append(
                    Finding(
                        "missing-relation-field",
                        "error",
                        f"relation {key} is required",
                        f"{rpath}.{key}",
                    )
                )
        for key in ("from", "to"):
            endpoint = relation.get(key)
            if isinstance(endpoint, str) and endpoint not in component_ids:
                findings.append(
                    Finding(
                        "unknown-relation-endpoint",
                        "error",
                        f"relation {key} references unknown component '{endpoint}'",
                        f"{rpath}.{key}",
                    )
                )
        if isinstance(relation.get("rule"), str) and len(relation["rule"]) > MAX_RULE:
            findings.append(
                Finding(
                    "long-relation-rule",
                    "warning",
                    f"relation rule should be <= {MAX_RULE} chars",
                    f"{rpath}.rule",
                )
            )

    for label in sorted(unresolved_checks):
        findings.append(
            Finding(
                "unresolved-check-label",
                "error" if strict_profile else "warning",
                f"validation check label does not exist in profile: {label}",
                check_label=label,
            )
        )

    info.update(
        {
            "components": len(component_ids),
            "component_ids": all_component_ids,
            "invariants": invariant_count,
            "relations": len(relations),
            "profile": str(profile) if profile else None,
            "known_profile_checks": sorted(known_checks),
        }
    )
    ok = not any(f.severity == "error" for f in findings)
    return Result(ok, str(path), findings, info)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root or path inside it",
    )
    parser.add_argument(
        "--system-map",
        type=Path,
        help="Path to system.toml; defaults to <repo>/.harness/system.toml",
    )
    parser.add_argument(
        "--profile",
        type=Path,
        help="Optional HK profile TOML for check-label validation",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as failures"
    )
    parser.add_argument(
        "--strict-profile",
        action="store_true",
        help="Treat unresolved profile check labels as errors",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    args = parser.parse_args(argv)

    repo = git_root(args.repo).resolve()
    system_map = (
        args.system_map.resolve()
        if args.system_map
        else repo / ".harness" / "system.toml"
    )
    profile = args.profile.resolve() if args.profile else None
    result = validate_map(
        repo, system_map, profile=profile, strict_profile=args.strict_profile
    )

    has_error = any(f.severity == "error" for f in result.findings)
    has_warning = any(f.severity == "warning" for f in result.findings)
    exit_failed = has_error or (args.strict and has_warning)
    if exit_failed and result.ok:
        result = Result(False, result.path, result.findings, result.info)

    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        status = "failed" if exit_failed else "ok"
        print(f"system.toml validation {status}: {result.path}")
        for finding in result.findings:
            loc = f" [{finding.field_path}]" if finding.field_path else ""
            print(f"{finding.severity.upper()} {finding.code}{loc}: {finding.message}")
        if not result.findings:
            print("No findings.")
        components = result.info.get("components", 0)
        invariants = result.info.get("invariants", 0)
        relations = result.info.get("relations", 0)
        print(f"components={components} invariants={invariants} relations={relations}")

    return 1 if exit_failed else 0


if __name__ == "__main__":
    sys.exit(main())
