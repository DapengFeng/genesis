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
