# Copilot instructions

## Project requirements

- Read `SPEC.md` before implementing behavior; use `PLAN.md` as the implementation order.
- Use only the Python standard library.
- In `src/`, do not use Python's built-in `dict`, `set`, or `hash()` for the hash-table
  implementation or URL storage. Use the project's hash-table classes instead.
- Add or update focused tests before implementing a behavior change. Preserve the existing
  tests unless the user explicitly asks to change them.
- Keep the public behavior and diagnostics consistent across the chaining and linear
  probing implementations.
- Report validation failures explicitly. Do not silently return success-shaped fallbacks.

## Git Flow

- `main` contains release-ready work. Integrate completed steps into `develop`.
- Start each numbered issue from the latest `develop` in
  `feature/<issue-number>-<short-name>`.
- Keep one issue/step per feature branch and post progress and completion details on its
  matching GitHub issue.
- Commit with `Step N: 한 일 (#이슈번호)`, push the feature branch, then merge it into
  `develop` and push `develop`. Close the issue only after the step is complete.
- Do not commit unrelated changes or amend existing commits.

## Validation

- Run `make test` for Python behavior changes.
- Run `make experiment` when changing probe-count measurements.
- Start the server with `make serve`; verify HTTP behavior locally before relying on
  Codespaces port visibility.
