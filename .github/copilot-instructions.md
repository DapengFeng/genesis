# GitHub Copilot Instructions

Use the repository templates as structured inputs and outputs.

## When creating or updating an issue

- Select the matching issue form instead of opening a blank issue.
- Replace every `{{PLACEHOLDER}}` with specific project details.
- Keep reproduction steps deterministic and numbered.
- Put expected output, actual output, and logs in separate sections.

## When creating a pull request

- Fill every heading in `.github/PULL_REQUEST_TEMPLATE.md`.
- Include the exact validation commands that were run.
- Paste test results or manual verification notes in fenced code blocks.
- Call out breaking changes explicitly, even when the answer is "none".

## Before requesting review

- Run `pre-commit run --all-files`.
- Confirm that issue and PR sections are complete and machine-readable.
- Keep the change summary and review checklist concise for human reviewers.

## Guidance prompt

- Read `AGENTS.md` before generating, refactoring, or reviewing code.
- Make the smallest correct change and preserve the existing structure.
- Surface conflicts, missing requirements, or ambiguity instead of guessing.
- Keep outputs machine-readable with short bullets, numbered steps, and fenced code blocks.
- Include the exact validation commands and results before requesting review.
