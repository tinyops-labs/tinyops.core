# Contributing

- Use PEP 8 and keep changes small and focused.
- Add or update tests when you change behavior.
- Unit tests: from the repo root run `pytest tests/`.
- One logical change per pull request, CI must be green before merge.
- In the MR, explain what was wrong or missing, what you did, and any non-obvious choices.

Integration tests (Docker Daemon needed): `pytest integration_tests/` from the repo root.
