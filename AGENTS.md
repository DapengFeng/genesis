# AGENTS.md

## Purpose

This repository uses structured GitHub issue forms and a structured pull
request template so coding agents can gather the same context that human
reviewers need.

## Required Workflow

1. Start from the matching issue form and keep every section heading intact.
2. Replace every `{{PLACEHOLDER}}` with repository-specific content before
   submitting an issue or pull request. Automation fails validation for
   issues and pull requests that still contain unresolved template tokens.
3. Prefer short bullet lists, numbered steps, and fenced code blocks over
   open-ended prose.
4. Run `pre-commit run --all-files` before requesting review.
5. Paste test commands and their results into the pull request template.

## Repository Checks

- Install hooks with `pre-commit install -t commit-msg`
- Validate changes with `pre-commit run --all-files`
- Use conventional commit messages because commit-msg checks are enabled

## Template Guidance

### Bug Reports

Always provide:

- `Context / Background`
- `Reproduction Steps`
- `Expected Behavior`
- `Actual Behavior`
- `Environment`
- `Agent-Specific Notes`

### Feature Requests

Always provide:

- `Context / Background`
- `Problem Statement`
- `Proposed Change`
- `Acceptance Criteria`
- `Alternatives Considered`
- `Agent-Specific Notes`

### Pull Requests

Always provide:

- `Summary of Changes`
- `Related Issue`
- `Testing Evidence`
- `Screenshots or Logs` when relevant
- `Breaking Changes`
- `Human Review Checklist`

## Style Notes for Agents

- Keep examples copy-paste ready.
- Avoid ambiguous phrases such as "it is broken" without reproduction details.
- Record constraints, acceptance criteria, and review notes in the dedicated
  `Agent-Specific Notes` sections.
- Mirror the filled-in bug report and pull request examples in `README.md`
  when drafting new submissions.
