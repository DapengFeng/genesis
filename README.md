# Multi-Language Template Repository

This repository is a starter template for projects that want a consistent
development workflow across multiple languages and toolchains.

## What this template provides

- Repository-level quality checks managed with `pre-commit`
- Formatting and linting defaults for common project assets
- Structured GitHub issue and pull request templates
- Coding-agent guidance for AI-assisted contribution workflows
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

## Coding agent support

This repository includes structured guidance for AI-assisted workflows:

- `AGENTS.md` defines repository-wide expectations for coding agents
- `.github/copilot-instructions.md` adds GitHub Copilot-specific guidance
- `.github/ISSUE_TEMPLATE/` contains machine-readable issue forms
- `.github/PULL_REQUEST_TEMPLATE.md` defines the expected PR structure

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
