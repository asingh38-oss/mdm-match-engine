# Contributing

This project is organized as a staged MDM matching pipeline. The goal of this guide is to keep changes predictable, easy to review, and safe to integrate during the capstone timeline.

## Working Agreement

- Keep preprocessing, matching, and utility changes separated when possible.
- Prefer small pull requests with one clear purpose.
- Do not commit secrets, raw MDM exports, or populated `.env` files.
- Document any threshold or scoring changes in `docs/threshold_calibration.md`.
- Document any architecture-level changes in `docs/architecture.md`.

## Suggested Branch Naming

- `feature/<short-description>` for new capabilities
- `fix/<short-description>` for bug fixes
- `chore/<short-description>` for low-risk cleanup or documentation

## Repo Areas

- `src/preprocessing/`: normalization, translation, abbreviation expansion, candidate generation
- `src/matching/`: levels 1 through 5 plus orchestration
- `src/utils/`: configuration, logging, and record loading helpers
- `tests/unit/`: focused unit coverage for stable components
- `docs/`: architecture notes, findings, and calibration decisions

## Change Checklist

Before opening a PR or merging a branch, confirm the following:

- The change is scoped to one concern.
- New assumptions are captured in docs or code comments.
- Any user-facing behavior changes are reflected in the README.
- Any scoring or threshold updates are explained in plain language.
- New files follow the existing naming style used in the repo.

## Low-Risk Contribution Ideas

These are good options when the team needs incremental progress without destabilizing the demo:

- Improve docstrings and inline code comments.
- Expand architecture or findings notes.
- Add project process docs for onboarding and handoff.
- Clarify expected input and output formats in documentation.
- Add non-executable examples to existing docs.

## Data Handling Reminder

Use synthetic or approved sample data in the repo. Real customer records should stay outside version control and should be treated according to Honeywell and course guidance.
