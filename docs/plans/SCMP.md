# SOFTWARE CONFIGURATION MANAGEMENT PLAN

**SCMP**

**Intelligent Safety-Critical Engineering Environment Toolchain**

DO-178C Lifecycle Automation (M1 → M6)

| Field | Value |
|---|---|
| Document ID | SCMP |
| Version | 3.0 |
| Status | BASELINE |
| Date | 2026-07-03 |
| Author | Hatem ADOUANI |
| Project | I-SCEET |
| Institution | Personal project |
| DAL Level | A (Assumed for demonstration purposes in an Engine Control-like safety-critical context) |
| Standard | RTCA DO-178C / EUROCAE ED-12C + DO-330 |

## 1. Document Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0 | 2026-04-23 | Hatem ADOUANI | Initial draft — project kickoff |
| 2.0 | 2026-06-29 | Hatem ADOUANI | Updated SCI register with verified local model stack and versions (PSAC v3.0, SDP v3.0, SVP v2.0, SQAP/SRS/SDS/SCS now APPROVED); fixed AI module CI example (removed external API model reference) |
| 3.0 | 2026-07-03 | Hatem ADOUANI | Baseline: removed TOOLCHAIN suffix; added DD and CT as tracked configuration items; SCI register now reflects the draft/baseline versioning scheme with a per-document baseline counter. |

## 2. Introduction

### 2.1 Purpose

This Software Configuration Management Plan (SCMP) defines the configuration management (CM) processes, methods, and responsibilities for the Intelligent Safety-Critical Engineering Environment Toolchain (I-SCEET) project. The SCMP ensures that all software lifecycle artifacts are uniquely identified, version-controlled, baselined, and change-controlled throughout the project lifecycle in accordance with DO-178C §7.

This document shall be reviewed and approved prior to the creation of any lifecycle artifact and is a required deliverable for SOI #1.

### 2.2 Project Overview

The I-SCEET project produces lifecycle artifacts through six AI modules (M1–M6). All inputs, outputs, and intermediate artifacts produced by these modules are subject to configuration management from the moment of creation:

| Module | Output Artifact | CM Item Type | Baseline |
|---|---|---|---|
| M1 | SRD | Software Requirements Document | Baseline 2 (SOI #2) |
| M2 | SDDD | Software Design Description Document | Baseline 2 (SOI #2) |
| M3 | /src folder | Source Code | Baseline 2 (SOI #2) |
| M4 | SUTC | Low Level Test Cases & Procedures | Baseline 3 (SOI #3) |
| M5 | SVTC | High Level Test Cases & Procedures | Baseline 3 (SOI #3) |
| M6 | TM | Traceability Data | Baseline 3 (SOI #3) |
| All | SVTR | Software Verification Test Result | Baseline 3 (SOI #3) |
| — | SAS | Software Accomplishment Summary | Baseline 4 (SOI #4) |

### 2.3 Scope

This SCMP applies to all software configuration items (SCIs) produced, used, or modified during the I-SCEET project lifecycle, including planning documents, standards documents, AI-generated artifacts, tool configurations, and verification records.

### 2.4 Referenced Documents

- RTCA DO-178C — Software Considerations in Airborne Systems and Equipment Certification (2012)
- RTCA DO-330 — Software Tool Qualification Considerations
- PSAC — Plan for Software Aspects of Certification
- SDP — Software Development Plan
- SVP — Software Verification Plan
- SQAP — Software Quality Assurance Plan

## 3. Software Configuration Items (SCIs)

### 3.1 Definition

A Software Configuration Item (SCI) is any artifact that must be uniquely identified, versioned, and controlled throughout the project lifecycle. SCIs are divided into three categories:

| Category | Description | Examples |
|---|---|---|
| Category 1 — Planning & Standards | Documents defining project rules and strategy | PSAC, SDP, SVP, SCMP, SQAP, SRS, SDS, SCS |
| Category 2 — Development Artifacts | AI-generated lifecycle data | SRD, SDDD, /src folder |
| Category 3 — Verification Artifacts | Test data, results, and traceability | SUTC, SVTC, SVTR, TM, SAS |

### 3.2 Complete SCI Register

| SCI ID | Name | Category | Produced by | Baseline |
|---|---|---|---|---|
| PSAC | Plan for Software Aspects of Certification | 1 — Planning | Engineer | BSL-01 |
| SDP | Software Development Plan | 1 — Planning | Engineer | BSL-01 |
| SVP | Software Verification Plan | 1 — Planning | Engineer | BSL-01 |
| SCMP | Software Configuration Management Plan | 1 — Planning | Engineer | BSL-01 |
| SQAP | Software Quality Assurance Plan | 1 — Planning | Engineer | BSL-01 |
| SRS | Software Requirements Standards | 1 — Standards | Engineer | BSL-01 |
| SDS | Software Design Standards | 1 — Standards | Engineer | BSL-01 |
| SCS | Software Code Standards | 1 — Standards | Engineer | BSL-01 |
| SRD | Software Requirements Document (HLRs) | 2 — Development | M1 | BSL-02 |
| SDDD | Software Design Description Document (LLRs) | 2 — Development | M2 | BSL-02 |
| /src | Source Code Folder | 2 — Development | M3 | BSL-02 |
| SUTC | Low Level Test Cases & Procedures | 3 — Verification | M4 | BSL-03 |
| SVTC | High Level Test Cases & Procedures | 3 — Verification | M5 | BSL-03 |
| TM | Traceability Data | 3 — Verification | M6 | BSL-03 |
| SVTR | Software Verification Test Result | 3 — Verification | Engineer | BSL-03 |
| SAS | Software Accomplishment Summary | 3 — Verification | Engineer | BSL-04 |

### 3.3 AI Module Configuration Items

The AI modules themselves (M1–M6) are configuration items. The following parameters shall be version-controlled for each module:

- Model name and version (e.g., Qwen3 32B Q4_K_M.gguf for M1; Mistral Small 24B for M2; Qwen2.5-Coder 32B for M3; Gemma3 27B for M4; DeepSeek-R1-Distill-Qwen 32B for M5; Phi-4 14B for M6 — all local GGUF files, no external API)
- System prompt / instruction set — versioned as a text file in the CM repository
- Temperature, seed, max_tokens, and other generation parameters
- Input document versions used during a generation run
- Output document produced (linked to SCI ID and version)

Any change to an AI module configuration that could affect its output shall trigger re-review of all affected downstream artifacts.

## 4. Version Control

### 4.1 Version Control Tool

All SCIs shall be managed in a Git repository hosted on a controlled server. The repository structure shall mirror the SCI categories:

| Repository Folder | Contents | Access |
|---|---|---|
| /planning | PSAC, SDP, SVP, SCMP, SQAP | Engineer + QA + Supervisor |
| /standards | SRS, SDS, SCS | Engineer + QA |
| /requirements | SRD (HLRs + System Architecture) | Engineer + Independent Reviewer |
| /design | SDDD (LLRs + Software Architecture) | Engineer + Independent Reviewer |
| /src | Source code subfolders — one per functional module | Engineer + Independent Reviewer |
| /tests | SUTC, SVTC | Engineer + Independent Reviewer |
| /verification | SVTR, coverage reports, review records | Engineer + QA |
| /traceability | TM | Engineer + QA |
| /ai-configs | AI module prompts, model versions, generation params | Engineer |
| /certification | SAS, SOI review records | Engineer + QA + Supervisor |

### 4.2 Versioning Scheme

All SCIs shall follow this versioning scheme:

| Version Type | Format | When Used |
|---|---|---|
| Major version | X.0 | Significant content change affecting downstream artifacts |
| Minor version | X.Y | Corrections, clarifications, or additions that do not change scope |
| Draft | X.Y-DRAFT | Document in progress, not yet reviewed or approved |
| Baseline | Tag: BL-N | Frozen snapshot at SOI gate — immutable after tagging |

### 4.3 Commit Rules

- Every commit shall reference the SCI ID, version, and a brief description of the change
- Commits to baselined branches are forbidden — changes require a formal change request (see §6)
- AI generation runs shall produce a commit recording: module ID, input SCI versions, output SCI version, model config hash
- Review sign-offs shall be recorded as annotated Git tags on the reviewed commit

## 5. Baselines

### 5.1 Baseline Definition

A baseline is a formally approved and frozen snapshot of a set of SCIs at a specific point in the project lifecycle. Once baselined, an SCI can only be modified through the formal change control process defined in §6.

### 5.2 Project Baselines

| Baseline ID | Name | SOI Gate | SCIs Included | Approval Required |
|---|---|---|---|---|
| BSL-01 | Planning Baseline | SOI #1 | PSAC, SDP, SVP, SCMP, SQAP, SRS, SDS, SCS | Author + Supervisor + QA + Certification Authority |
| BSL-02 | Development Baseline | SOI #2 | BSL-01 + SRD, SDDD, /src folder | Independent Reviewer + QA |
| BSL-03 | Verification Baseline | SOI #3 | BSL-02 + SUTC, SVTC, SVTR, TM | Independent Reviewer + QA |
| BSL-04 | Certification Baseline | SOI #4 | BSL-03 + SAS, all SOI review records, full lifecycle package | Author + QA + Certification Authority |

### 5.3 Baseline Procedure

- Step 1: All SCIs for the baseline are reviewed and all problem reports closed
- Step 2: QA signs off that the baseline is complete and compliant
- Step 3: The baseline is tagged in Git as BL-N (e.g., git tag -a BSL-01 -m 'Planning Baseline')
- Step 4: The tagged branch is protected — no direct commits allowed after tagging
- Step 5: The baseline is recorded in the Software Configuration Index (SCI register) with date, approver, and tag hash

## 6. Change Control

### 6.1 Change Request Process

Any modification to a baselined SCI requires a formal Change Request (CR). The change control process is:

| Step | Activity | Responsible | Output |
|---|---|---|---|
| 1 | Raise Change Request | Any team member | CR form with: SCI ID, version, description of change, reason, impact estimate |
| 2 | Impact Analysis | Engineer + QA | Impact analysis report: which downstream SCIs are affected; re-verification scope |
| 3 | CR Approval | Supervisor + QA | Approved or rejected CR — recorded in the change log |
| 4 | Implementation | Engineer | Updated SCI with new version number; change referenced in commit message |
| 5 | Re-Verification | Independent Reviewer | Verification of affected downstream artifacts per SVP |
| 6 | Baseline Update | QA | Updated baseline tag if SOI gate artifacts are affected |

### 6.2 Change Request Classification

| Class | Description | Approval Level | Re-Verification Required |
|---|---|---|---|
| Class 1 — Critical | Change affects safety-critical HLR, LLR, or source code; impacts DAL objectives | Supervisor + QA + Certification Authority | Full re-verification of affected artifacts |
| Class 2 — Major | Change affects non-safety content or adds new requirements; impacts traceability | Supervisor + QA | Partial re-verification per impact analysis |
| Class 3 — Minor | Correction of typos, formatting, or non-technical content; no functional impact | QA | Review record update only |

### 6.3 AI Re-Generation Rules

If a change to a planning or standards document requires re-generation of an AI module output:

- A Class 1 or Class 2 CR shall be raised before re-running any AI module
- The AI module configuration (prompt, model version, parameters) shall be unchanged unless a separate CR covers it
- The re-generated artifact shall receive a new version number and undergo full re-verification
- Both the original and updated versions shall remain in the CM repository for audit purposes

## 7. Problem Reports

### 7.1 Problem Report Process

Any deficiency identified in a software lifecycle artifact — whether during review, testing, or audit — shall be recorded as a Problem Report (PR). The PR process is:

| Step | Activity | Responsible | Output |
|---|---|---|---|
| 1 | Raise PR | Any team member | PR form: PR-NNN, SCI ID, version, description, severity, date |
| 2 | Severity Classification | QA | Critical / Major / Minor classification assigned |
| 3 | Root Cause Analysis | Engineer | Root cause identified; fix proposed |
| 4 | Fix Implementation | Engineer | Updated SCI version; CR raised if baselined artifact |
| 5 | Re-Verification | Independent Reviewer | Verify fix resolves the deficiency; close PR |
| 6 | PR Closure | QA | PR marked closed in tracking system; referenced in SVTR |

### 7.2 PR Severity Classification

| Severity | Definition | Must Close Before |
|---|---|---|
| Critical | Deficiency that could cause unsafe behavior, incorrect safety-critical output, or certification failure | Next SOI gate — no exceptions |
| Major | Deficiency that affects functional correctness, traceability completeness, or standards compliance | Next SOI gate |
| Minor | Formatting error, typo, or non-functional issue with no impact on verification objectives | SAS compilation |

### 7.3 PR Tracking

- All PRs shall be tracked in the project issue tracker (e.g., Git Issues or equivalent)
- PR status shall be reviewed at each lifecycle phase transition
- No SOI gate shall be passed with open Critical or Major PRs
- PR statistics (total raised, closed, open) shall be reported in SAS

## 8. Software Configuration Index (SCI Register)

The Software Configuration Index is the master register of all SCIs, their current versions, baseline status, and location. It shall be maintained as a living document updated at each lifecycle phase transition.

| SCI ID | Current Version | Status | Baseline | Location | Last Modified |
|---|---|---|---|---|---|
| PSAC | 3.0 | APPROVED | BSL-01 | /planning/PSAC_I-SCEET.docx | 2026-06-29 |
| SDP | 3.0 | APPROVED | BSL-01 | /planning/SDP_I-SCEET.docx | 2026-06-29 |
| SVP | 2.0 | APPROVED | BSL-01 | /planning/SVP_I-SCEET.docx | 2026-06-29 |
| SCMP | 2.0 | DRAFT | BSL-01 | /planning/SCMP_I-SCEET.docx | 2026-06-29 |
| SQAP | 1.0 | APPROVED | BSL-01 | /planning/SQAP_I-SCEET.docx | 2026-06-29 |
| SRS | 1.0 | APPROVED | BSL-01 | /standards/SRS.docx | 2026-06-29 |
| SDS | 1.0 | APPROVED | BSL-01 | /standards/SDS.docx | 2026-06-29 |
| SCS | 1.0 | APPROVED | BSL-01 | /standards/SCS.docx | 2026-06-29 |
| SRD | — | NOT YET | BSL-02 | /requirements/SRD.docx | TBD |
| SDDD | — | NOT YET | BSL-02 | /design/SDDD.docx | TBD |
| /src | — | NOT YET | BSL-02 | /src/ | TBD |
| SUTC | — | NOT YET | BSL-03 | /tests/SUTC.docx | TBD |
| SVTC | — | NOT YET | BSL-03 | /tests/SVTC.docx | TBD |
| TM | — | NOT YET | BSL-03 | /traceability/TM.xlsx | TBD |
| SVTR | — | NOT YET | BSL-03 | /verification/SVTR.docx | TBD |
| SAS | — | NOT YET | BSL-04 | /certification/SAS.docx | TBD |

## 9. CM Roles and Responsibilities

| Role | CM Responsibilities |
|---|---|
| Author / Developer | Creates SCIs; commits to Git with correct version and references; raises CRs and PRs when deficiencies found |
| Independent Reviewer | Reviews SCIs and signs off review records; cannot commit to the SCI they reviewed; raises PRs for deficiencies found |
| CM Manager (Engineer/QA) | Maintains SCI register; approves baselines; manages branch protection; audits commit discipline |
| QA Officer | Audits CM process compliance; verifies all PRs closed before SOI gates; signs off baseline approvals |
| Supervisor | Approves Class 1 and Class 2 CRs; witnesses SOI gate baseline tagging |

## 10. SOI Gate CM Checklist

| SOI Gate | CM Checklist Items |
|---|---|
| SOI #1 — BSL-01 | All 8 planning/standards SCIs at approved version All SCIs committed to /planning and /standards folders No open Critical or Major PRs BSL-01 tag applied and branch protected SCI register updated |
| SOI #2 — BSL-02 | SRD, SDDD, /src at approved version All review records committed to /verification All PRs from BSL-02 scope closed BSL-02 tag applied and branch protected SCI register updated AI module configs recorded in /ai-configs |
| SOI #3 — BSL-03 | SUTC, SVTC, SVTR, TM at approved version Coverage results committed to /verification All PRs from BSL-03 scope closed BSL-03 tag applied and branch protected SCI register updated |
| SOI #4 — BSL-04 | SAS at approved version All SOI review records committed All PRs in the project closed BSL-04 tag applied — project lifecycle complete Full SCI register submitted to certification authority |

## 11. Additional Considerations

### 11.1 AI Module Output Reproducibility

AI modules may produce non-deterministic outputs across runs. To ensure CM integrity:

- The exact model version, prompt hash, and generation parameters used to produce each SCI shall be recorded in /ai-configs at generation time
- If an SCI must be re-generated, the original generation record shall be preserved and the new run shall create a new SCI version under change control
- Outputs of different runs of the same module with the same inputs shall be treated as different versions — not overwrites

### 11.2 Archive and Retention

All project SCIs, baselines, CM records, PRs, and CRs shall be retained for a minimum of 10 years after project completion, consistent with DO-178C archiving requirements for certified software.

### 11.3 Tool Configuration Management

Development and verification tools (static analysis, coverage tool, test execution) are themselves configuration items. Tool versions shall be:

- Recorded in the SCI register under a dedicated /tools section
- Kept constant for the duration of each baseline period
- Changed only via formal CR with impact analysis

## 12. Approvals

This document requires the following approvals before SOI #1:

| Role | Name | Signature | Date |
|---|---|---|---|
| Author | Hatem ADOUANI |  |  |
| Quality Assurance | [QA Name] |  |  |
| Certification Authority | [Authority Rep] |  |  |
