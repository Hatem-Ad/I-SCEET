# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-13

First public release.

### Added

- Streamlit UI (`ui/`): upload, pipeline, review, remarks (TC) and history pages.
- Orchestrator and document builders (`orchestrator/`): client for the model
  server, and builders turning model output into `.docx`, `.xlsx` and `.zip`
  artifacts (SRD, SDDD, DD, CT, source, SUTC, SVTC, TM).
- SQLite storage (`Backend/db.py`): projects, artifact versions, reviews and
  remarks; `DB_PATH` read from `.env`.
- System prompts for the six generation modules M1–M6 (`models/system_prompts/`).
- STM32F303 UART bootloader example inputs (`examples/stm32_bootloader/`) and
  the raw pipeline output of the 2026-07-11 run.
- Sanitized plans and standards (`docs/`).
- gitleaks leak guard: `leak-guard` GitHub Actions workflow scanning the full
  history, and an optional pre-commit hook, both using `.gitleaks.toml`.
- MIT license.

### Known limits

- The model server is not part of this repository; without a compatible
  server, the pipeline cannot generate anything.
- AI output must be reviewed by a qualified engineer; requirements, code,
  tests and M6 traceability can be incomplete or wrong.
- Not certified tooling: no DO-330 qualification and no claim of DO-178C
  compliance.
- Local model runners and deterministic (non-AI) checks are planned, not
  implemented.
- No automated tests for this repository yet.
- The UI is partly in French.

[0.1.0]: https://github.com/Hatem-Ad/I-SCEET/releases/tag/v0.1.0
