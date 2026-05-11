from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Callable

import yaml

GUIDANCE_INLINE_PATTERN = re.compile(r"\[guidance:\s*(.*?)\]", re.IGNORECASE)
MARKDOWN_BLOCK_PATTERN = re.compile(
    r"```(?:yaml|yml|json)\n(.*?)```", re.DOTALL | re.IGNORECASE
)
RUST_PUBLIC_TYPE_PATTERN = re.compile(
    r"^\s*pub\s+(?:struct|enum)\s+(?P<name>[A-Z][A-Za-z0-9_]*)",
    re.MULTILINE,
)
DERIVE_DEBUG_PATTERN = re.compile(
    r"#\s*\[derive\((?P<body>[^\]]*Debug[^\]]*)\)\]"
)

LANGUAGE_BY_SUFFIX = {
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cuh": "cuda",
    ".cu": "cuda",
    ".c": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".py": "python",
    ".rs": "rust",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}

AUDITABLE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cu",
    ".cuh",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".py",
    ".rs",
}

LANGUAGE_ALIASES = {
    "c++": "cpp",
    "cplusplus": "cpp",
    "cpp": "cpp",
    "cuda": "cuda",
    "cu": "cuda",
    "py": "python",
    "python": "python",
    "rs": "rust",
    "rust": "rust",
}

PROJECT_GUIDANCE_TEMPLATE = {
    "version": 1,
    "metadata": {
        "name": "universal-guidance",
        "description": "Project-level defaults for coding agents.",
    },
    "rules": [
        {
            "id": "report-guidance-conflicts",
            "slot": "compliance.conflict_reporting",
            "description": "Report rule conflicts instead of silently discarding them.",
            "checker": "advisory",
            "severity": "warning",
        },
        {
            "id": "audit-mode-no-write",
            "slot": "compliance.audit_mode",
            "description": "Audit mode reports violations without modifying files.",
            "checker": "advisory",
            "severity": "warning",
        },
    ],
}

TEMPLATE_RULESETS = {
    "python": {
        "version": 1,
        "scope": {"paths": ["python/**"], "languages": ["python"]},
        "rules": [
            {
                "id": "python-snake-case",
                "slot": "naming.identifier_style",
                "description": "Prefer snake_case identifiers in Python code.",
                "checker": "advisory",
                "style": "snake_case",
                "severity": "error",
            },
            {
                "id": "python-type-annotations",
                "slot": "python.public_api_typing",
                "description": "Require type annotations for public Python APIs.",
                "checker": "advisory",
                "severity": "warning",
            },
        ],
    },
    "cpp": {
        "version": 1,
        "scope": {
            "paths": ["cpp/**", "include/**", "src/**"],
            "languages": ["cpp"],
        },
        "rules": [
            {
                "id": "cpp-camel-case",
                "slot": "naming.identifier_style",
                "description": "Prefer CamelCase identifiers in C++ code.",
                "checker": "advisory",
                "style": "CamelCase",
                "severity": "error",
            },
            {
                "id": "cpp-exceptions-allowed",
                "slot": "language.exceptions",
                "description": "Exceptions are allowed unless inline guidance disables them.",
                "checker": "feature_toggle",
                "feature": "exceptions",
                "allowed": True,
                "severity": "warning",
            },
            {
                "id": "no-raw-new",
                "slot": "security.no_raw_new",
                "description": "Forbid raw new/delete; prefer RAII wrappers or containers.",
                "checker": "pattern",
                "pattern": r"\bnew\b",
                "message": "use of raw new",
                "severity": "error",
            },
        ],
    },
    "cuda": {
        "version": 1,
        "scope": {"paths": ["cuda/**", "kernels/**"], "languages": ["cuda"]},
        "rules": [
            {
                "id": "cuda-kernel-error-checking",
                "slot": "cuda.kernel_error_checking",
                "description": "Wrap kernel launches with error checking.",
                "checker": "advisory",
                "severity": "warning",
            },
            {
                "id": "cuda-thread-indexing",
                "slot": "cuda.thread_indexing",
                "description": "Use descriptive thread indexing helpers in kernels.",
                "checker": "advisory",
                "severity": "warning",
            },
        ],
    },
    "rust": {
        "version": 1,
        "scope": {"paths": ["rust/**", "crates/**"], "languages": ["rust"]},
        "rules": [
            {
                "id": "rust-public-debug",
                "slot": "rust.public_debug",
                "description": "Public Rust types must implement Debug.",
                "checker": "rust_public_debug",
                "severity": "warning",
            },
            {
                "id": "rust-strict-clippy",
                "slot": "rust.clippy",
                "description": "Run strict clippy guidance for Rust code.",
                "checker": "advisory",
                "severity": "warning",
            },
        ],
    },
}


@dataclass(frozen=True)
class GuidanceDocument:
    path: Path
    data: dict[str, Any]
    source_priority: int


Checker = Callable[[Path, str, dict[str, Any]], list[dict[str, Any]]]
CHECKERS: dict[str, Checker] = {}


def register_checker(name: str, handler: Checker) -> None:
    CHECKERS[name] = handler


def normalize_language(value: str | None) -> str | None:
    if value is None:
        return None
    return LANGUAGE_ALIASES.get(value.lower(), value.lower())


def infer_language(path: Path) -> str | None:
    return normalize_language(LANGUAGE_BY_SUFFIX.get(path.suffix.lower()))


def discover_guidance_files(root: Path) -> list[Path]:
    agent_dir = root / ".agent"
    candidates: list[Path] = []
    for name in (
        "guidance.yaml",
        "guidance.yml",
        "guidance.json",
        "guidance.md",
    ):
        path = agent_dir / name
        if path.exists():
            candidates.append(path)
    guidance_dir = agent_dir / "guidance"
    if guidance_dir.exists():
        for suffix in ("*.yaml", "*.yml", "*.json", "*.md"):
            candidates.extend(sorted(guidance_dir.rglob(suffix)))
    return sorted(dict.fromkeys(candidates))


def parse_guidance_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    if suffix == ".md":
        if text.startswith("---\n"):
            parts = text.split("\n---\n", maxsplit=1)
            front_matter = parts[0][4:].strip()
            return yaml.safe_load(front_matter) or {}
        match = MARKDOWN_BLOCK_PATTERN.search(text)
        if match:
            return yaml.safe_load(match.group(1)) or {}
        raise ValueError(
            "No fenced YAML or JSON guidance block found in markdown file"
        )
    raise ValueError(f"Unsupported guidance file type: {path.suffix}")


def load_guidance(root: Path) -> tuple[list[GuidanceDocument], list[str]]:
    warnings: list[str] = []
    documents: list[GuidanceDocument] = []
    for path in discover_guidance_files(root):
        try:
            data = parse_guidance_file(path)
        except Exception as exc:  # pragma: no cover - exercised via tests
            warnings.append(
                f"Warning: skipped invalid guidance file {path}: {exc}"
            )
            continue
        if not isinstance(data, dict):
            warnings.append(
                f"Warning: skipped invalid guidance file {path}: expected a mapping"
            )
            continue
        if "version" not in data:
            warnings.append(
                f"Warning: guidance file {path} is missing a version field"
            )
        documents.append(
            GuidanceDocument(
                path=path,
                data=data,
                source_priority=compute_source_priority(root, path),
            )
        )
    return documents, warnings


def compute_source_priority(root: Path, path: Path) -> int:
    agent_dir = root / ".agent"
    if path == agent_dir / "guidance.yaml":
        return 10
    if path == agent_dir / "guidance.yml":
        return 10
    if path == agent_dir / "guidance.json":
        return 10
    if path == agent_dir / "guidance.md":
        return 10
    return 20 + len(path.relative_to(agent_dir / "guidance").parts)


def match_scope(
    scope: dict[str, Any] | None, relative_path: str, language: str | None
) -> bool:
    if not scope:
        return True
    normalized_language = normalize_language(language)
    for key in ("languages",):
        values = scope.get(key)
        if values:
            normalized_values = {
                normalize_language(str(value)) for value in values
            }
            if normalized_language not in normalized_values:
                return False
    extensions = scope.get("extensions")
    if extensions:
        suffix = Path(relative_path).suffix.lower()
        if suffix not in {value.lower() for value in extensions}:
            return False
    globs = list(scope.get("paths", [])) + list(scope.get("files", []))
    if globs and not any(fnmatch(relative_path, pattern) for pattern in globs):
        return False
    return True


def rule_specificity(rule: dict[str, Any], relative_path: str) -> int:
    scope = rule.get("applies_to") or {}
    globs = list(scope.get("paths", [])) + list(scope.get("files", []))
    if not globs:
        return 0
    matched = [pattern for pattern in globs if fnmatch(relative_path, pattern)]
    if not matched:
        return -1
    return max(
        pattern.count("/") + len(pattern.replace("*", ""))
        for pattern in matched
    )


def rule_slot(rule: dict[str, Any]) -> str:
    return str(rule.get("slot") or rule.get("feature") or rule["id"])


def inline_guidance_rules(inline_guidance: str | None) -> list[dict[str, Any]]:
    if not inline_guidance:
        return []
    phrases = GUIDANCE_INLINE_PATTERN.findall(inline_guidance)
    if not phrases:
        phrases = [inline_guidance]
    synthetic_rules: list[dict[str, Any]] = []
    for phrase in phrases:
        lowered = phrase.lower()
        if "no exceptions" in lowered:
            synthetic_rules.append(
                {
                    "id": "inline-no-exceptions",
                    "slot": "language.exceptions",
                    "description": phrase.strip(),
                    "checker": "feature_toggle",
                    "feature": "exceptions",
                    "allowed": False,
                    "severity": "error",
                    "source": "inline",
                }
            )
    return synthetic_rules


def resolve_guidance(
    root: Path,
    target_path: Path,
    *,
    language: str | None = None,
    inline_guidance: str | None = None,
) -> dict[str, Any]:
    documents, warnings = load_guidance(root)
    absolute_target = (
        target_path if target_path.is_absolute() else root / target_path
    )
    relative_path = absolute_target.relative_to(root).as_posix()
    resolved_language = normalize_language(language) or infer_language(
        absolute_target
    )
    candidates: list[tuple[tuple[int, int], str, dict[str, Any], str]] = []
    for document in documents:
        if not match_scope(
            document.data.get("scope"), relative_path, resolved_language
        ):
            continue
        for rule in document.data.get("rules", []):
            if not match_scope(
                rule.get("applies_to"), relative_path, resolved_language
            ):
                continue
            specificity = rule_specificity(rule, relative_path)
            if specificity < 0:
                continue
            candidates.append(
                (
                    (document.source_priority, specificity),
                    rule_slot(rule),
                    dict(rule),
                    str(document.path),
                )
            )
    for rule in inline_guidance_rules(inline_guidance):
        candidates.append(((100, 100), rule_slot(rule), dict(rule), "inline"))

    resolved: dict[str, dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    for priority, slot, rule, source in sorted(
        candidates, key=lambda item: item[0], reverse=True
    ):
        current = resolved.get(slot)
        payload = {
            key: value for key, value in rule.items() if key != "source"
        }
        if current is None:
            resolved[slot] = {
                "priority": list(priority),
                "rule": payload,
                "source": source,
            }
            continue
        if current["rule"] != payload:
            conflicts.append(
                {
                    "slot": slot,
                    "selected_source": current["source"],
                    "ignored_source": source,
                    "selected_rule_id": current["rule"].get("id"),
                    "ignored_rule_id": payload.get("id"),
                }
            )

    return {
        "path": relative_path,
        "language": resolved_language,
        "rules": [
            {"slot": slot, **entry} for slot, entry in sorted(resolved.items())
        ],
        "conflicts": conflicts,
        "warnings": warnings,
    }


def build_derived_rules(resolution: dict[str, Any]) -> list[dict[str, Any]]:
    derived_rules: list[dict[str, Any]] = []
    for entry in resolution["rules"]:
        rule = entry["rule"]
        if (
            rule.get("checker") == "feature_toggle"
            and rule.get("feature") == "exceptions"
        ):
            if not rule.get("allowed", True):
                derived_rules.append(
                    {
                        "id": "exceptions-disabled",
                        "checker": "pattern",
                        "pattern": r"\b(?:throw|try|catch)\b",
                        "message": "exception handling disabled by active guidance",
                        "severity": rule.get("severity", "error"),
                    }
                )
    return derived_rules


def collect_line_column(text: str, position: int) -> tuple[int, int]:
    line = text.count("\n", 0, position) + 1
    column = position - text.rfind("\n", 0, position)
    return line, column


def pattern_checker(
    path: Path, content: str, rule: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    pattern = re.compile(rule["pattern"])
    for match in pattern.finditer(content):
        line, column = collect_line_column(content, match.start())
        findings.append(
            {
                "path": str(path),
                "line": line,
                "column": column,
                "severity": rule.get("severity", "warning"),
                "rule_id": rule.get("id", "pattern-match"),
                "message": rule.get(
                    "message", rule.get("description", "pattern violation")
                ),
            }
        )
    return findings


def advisory_checker(
    path: Path, content: str, rule: dict[str, Any]
) -> list[dict[str, Any]]:
    del path, content, rule
    return []


def feature_toggle_checker(
    path: Path, content: str, rule: dict[str, Any]
) -> list[dict[str, Any]]:
    del path, content, rule
    return []


def rust_public_debug_checker(
    path: Path, content: str, rule: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for match in RUST_PUBLIC_TYPE_PATTERN.finditer(content):
        anchor = match.start()
        prefix = content[max(0, anchor - 120) : anchor]
        if DERIVE_DEBUG_PATTERN.search(prefix):
            continue
        line, column = collect_line_column(content, match.start())
        findings.append(
            {
                "path": str(path),
                "line": line,
                "column": column,
                "severity": rule.get("severity", "warning"),
                "rule_id": rule.get("id", "rust-public-debug"),
                "message": "Deviation: public type missing Debug impl",
            }
        )
    return findings


register_checker("advisory", advisory_checker)
register_checker("feature_toggle", feature_toggle_checker)
register_checker("pattern", pattern_checker)
register_checker("rust_public_debug", rust_public_debug_checker)


def audit_file(
    root: Path,
    target_path: Path,
    *,
    language: str | None = None,
    inline_guidance: str | None = None,
) -> dict[str, Any]:
    resolution = resolve_guidance(
        root,
        target_path,
        language=language,
        inline_guidance=inline_guidance,
    )
    absolute_target = (
        target_path if target_path.is_absolute() else root / target_path
    )
    content = absolute_target.read_text(encoding="utf-8")
    findings: list[dict[str, Any]] = []
    active_rules = [entry["rule"] for entry in resolution["rules"]]
    active_rules.extend(build_derived_rules(resolution))
    for rule in active_rules:
        checker = CHECKERS.get(rule.get("checker", "advisory"))
        if checker is None:
            resolution["warnings"].append(
                f"Warning: unknown checker '{rule.get('checker')}' in {absolute_target}"
            )
            continue
        findings.extend(checker(absolute_target, content, rule))
    resolution["findings"] = findings
    return resolution


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def scaffold_templates(
    root: Path, templates: list[str], force: bool = False
) -> list[Path]:
    written: list[Path] = []
    project_guidance_path = root / ".agent" / "guidance.yaml"
    if force or not project_guidance_path.exists():
        write_yaml(project_guidance_path, PROJECT_GUIDANCE_TEMPLATE)
        written.append(project_guidance_path)
    for template in templates:
        ruleset = TEMPLATE_RULESETS[template]
        template_path = root / ".agent" / "guidance" / f"{template}.yaml"
        if template_path.exists() and not force:
            continue
        write_yaml(template_path, ruleset)
        written.append(template_path)
    return written


def expand_targets(root: Path, raw_targets: list[str]) -> list[Path]:
    if not raw_targets:
        return []
    expanded: list[Path] = []
    for raw_target in raw_targets:
        candidate = Path(raw_target)
        absolute = candidate if candidate.is_absolute() else root / candidate
        if absolute.is_dir():
            for path in sorted(absolute.rglob("*")):
                if (
                    path.is_file()
                    and path.suffix.lower() in AUDITABLE_SUFFIXES
                ):
                    expanded.append(path)
            continue
        expanded.append(absolute)
    return expanded


def parse_template_list(raw_templates: str) -> list[str]:
    templates = [
        normalize_language(part.strip())
        for part in raw_templates.split(",")
        if part.strip()
    ]
    invalid = [
        template for template in templates if template not in TEMPLATE_RULESETS
    ]
    if invalid:
        raise ValueError(
            "Unsupported template(s): "
            + ", ".join(sorted(set(str(item) for item in invalid)))
        )
    return [str(template) for template in templates]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universal coding guidance helper"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Scaffold guidance files")
    init_parser.add_argument(
        "--template", required=True, help="Comma-separated template list"
    )
    init_parser.add_argument(
        "--root", default=".", help="Project root to scaffold"
    )
    init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing files"
    )

    resolve_parser = subparsers.add_parser(
        "resolve", help="Resolve effective guidance"
    )
    resolve_parser.add_argument("target", help="File to resolve guidance for")
    resolve_parser.add_argument("--root", default=".", help="Project root")
    resolve_parser.add_argument(
        "--language", help="Explicit language override"
    )
    resolve_parser.add_argument(
        "--inline-guidance",
        help="Inline guidance such as [guidance: No exceptions this time]",
    )

    audit_parser = subparsers.add_parser(
        "audit", help="Audit files against guidance"
    )
    audit_parser.add_argument(
        "targets", nargs="*", help="Files or directories to audit"
    )
    audit_parser.add_argument("--root", default=".", help="Project root")
    audit_parser.add_argument("--language", help="Explicit language override")
    audit_parser.add_argument(
        "--inline-guidance",
        help="Inline guidance such as [guidance: No exceptions this time]",
    )

    return parser


def command_init(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    templates = parse_template_list(args.template)
    written = scaffold_templates(root, templates, force=args.force)
    for path in written:
        print(path.relative_to(root).as_posix())
    return 0


def command_resolve(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    target = Path(args.target)
    resolution = resolve_guidance(
        root,
        target,
        language=args.language,
        inline_guidance=args.inline_guidance,
    )
    print(json.dumps(resolution, indent=2, sort_keys=True))
    return 0


def command_audit(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    targets = expand_targets(root, args.targets)
    if not targets:
        print("No files selected for audit.")
        return 0
    warnings: list[str] = []
    findings: list[dict[str, Any]] = []
    for target in targets:
        resolution = audit_file(
            root,
            target,
            language=args.language,
            inline_guidance=args.inline_guidance,
        )
        warnings.extend(resolution["warnings"])
        findings.extend(resolution["findings"])
    for warning in dict.fromkeys(warnings):
        print(warning, file=sys.stderr)
    if not findings:
        print("No guidance violations found.")
        return 0
    for finding in findings:
        print(
            f"{Path(finding['path']).relative_to(root).as_posix()}:"
            f"{finding['line']}:{finding['column']}: "
            f"{finding['severity']} [{finding['rule_id']}] {finding['message']}"
        )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        return command_init(args)
    if args.command == "resolve":
        return command_resolve(args)
    if args.command == "audit":
        return command_audit(args)
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
