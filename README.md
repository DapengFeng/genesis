# Multi-Language Template Repository

This repository is a starter template for projects that want a consistent
development workflow across multiple languages and toolchains.

## What this template provides

- Repository-level quality checks managed with `pre-commit`
- Formatting and linting defaults for common project assets
- Structured GitHub issue and pull request templates
- Coding-agent guidance for AI-assisted contribution workflows
- A universal guidance scaffold for project, directory, and language-specific
  agent rules
- Baseline ignore rules and repository metadata for new projects

## Included tooling

The template is designed to support a mix of languages and project types.
Current hooks and configuration cover:

- C/C++ formatting and linting
- Python formatting and linting
- Rust formatting and static checks
- Dockerfile linting
- CMake formatting
- Makefile linting
- YAML validation and general repository hygiene checks
- Conventional commit message validation

## Quick start

1. Use this repository as a template for your new project.
2. Clone the generated repository.
3. Install `pre-commit`.
4. Install repository hooks:

   ```bash
   pre-commit install -t commit-msg
   ```

5. Run the full validation suite:

   ```bash
   pre-commit run --all-files
   ```

6. Add your project code, language-specific tooling, and project documentation.

## Repository workflow

Use the existing repository automation before opening a pull request:

- Run `pre-commit run --all-files`
- Use conventional commit messages
- Keep issue reports and pull requests aligned with the provided templates
- Replace every `{{PLACEHOLDER}}` before submitting an issue or pull request.
  GitHub Actions validates this automatically on new and edited submissions.

## Coding agent support

This repository includes structured guidance for AI-assisted workflows:

- `AGENTS.md` defines repository-wide expectations for coding agents
- `.github/copilot-instructions.md` adds GitHub Copilot-specific guidance
- `.agent/guidance.yaml` provides project-level defaults for the universal
  guidance system
- `.agent/guidance/*.yaml` provides layered language or directory overrides for
  Python, C++, CUDA, Rust, or custom stacks
- `.github/ISSUE_TEMPLATE/` contains machine-readable issue forms
- `.github/PULL_REQUEST_TEMPLATE.md` defines the expected PR structure

### Universal guidance quick start

Use the lightweight `ai` helper to scaffold and inspect reusable guidance
rules:

```bash
./ai init --template python,cpp
./ai resolve python/example.py
./ai audit cpp/
```

The scaffolded files use a layered model:

- project defaults live in `.agent/guidance.yaml`
- language or directory overrides live in `.agent/guidance/*.yaml`
- inline instructions such as `[guidance: No exceptions this time]` override
  file-based rules for a single run

Example scaffold:

```text
.agent/
├── guidance.yaml
└── guidance/
    ├── cpp.yaml
    └── python.yaml
```

Each guidance file declares a versioned ruleset. Rules can be scoped by
language, extension, or path glob, and the resolver reports conflicts instead
of silently dropping lower-priority rules.

### Audit mode and syntax warnings

- `./ai audit <path>` prints guidance violations with file locations and never
  rewrites files.
- The built-in templates include examples for:
  - Python snake_case naming and public API typing guidance
  - C++ CamelCase naming, raw `new` detection, and exception toggles
  - CUDA kernel and indexing reminders
  - Rust `Debug` compliance for public types
- Invalid YAML, JSON, or Markdown guidance files are skipped with a warning so
  the remaining valid rules still apply.

## Example structured submissions

Use these short examples as a reference when filling in the repository
templates.

### Bug report example

````md
## Context / Background

- Goal: confirm pull requests contain fully completed template sections
- Trigger: submit a PR with `{{TEST_RESULTS}}` still present in the body
- Impact: reviewers cannot rely on the template fields being complete

## Reproduction Steps

1. Open a pull request from this template repository
2. Leave `{{TEST_RESULTS}}` unchanged in the PR body
3. Submit the pull request

## Expected Behavior

The placeholder validation workflow fails and reports the unresolved token.

## Actual Behavior

The pull request is accepted without any warning, so the incomplete template is
easy to miss during review.

## Environment

- OS: GitHub-hosted workflow runner
- Compiler / interpreter: Python 3.12
- Commit / branch: `main`
- Additional dependencies: none

## Screenshots / Logs

~~~md
PR body excerpt:
- Related: #12

### Results

{{TEST_RESULTS}}
~~~

## Agent-Specific Notes

- Keep the workflow lightweight and repository-scoped
- Reuse the existing template headings
````

### Pull request example

````md
## Summary of Changes

- Add placeholder validation for issue and pull request bodies
- Document filled-in examples for bug reports and pull requests

## Related Issue

- Related: #12

## Testing Evidence

### Commands

```bash
pre-commit run --all-files
```

### Results

```text
All hooks passed.
```

## Screenshots or Logs

```text
No screenshots were needed for this metadata-only change.
```

## Breaking Changes

- [x] No breaking changes
- [ ] Breaking changes described below

None.

## Human Review Checklist

- [x] The changes are limited to the stated problem
- [x] The issue, motivation, and acceptance criteria are reflected in this PR
- [x] Tests or manual verification steps are included
- [x] Documentation and templates were updated where needed
- [x] Risks, trade-offs, and follow-up work are documented when applicable
````

## When to customize this template

After creating a new repository from this template, update it to match your
project:

- Replace generic descriptions with project-specific documentation
- Add or remove toolchains in `.pre-commit-config.yaml`
- Extend `.gitignore` for your build outputs and editor settings
- Update or remove `AGENTS.md` and `.github/copilot-instructions.md` if your
  project does not use coding-agent workflows
- Add build, test, and release workflows that match your stack

This template gives new repositories a clean starting point for contributor
experience, review consistency, and automated validation across a mixed-language
codebase.
