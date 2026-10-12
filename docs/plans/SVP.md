# SOFTWARE VERIFICATION PLAN

**SVP**

**Intelligent Safety-Critical Engineering Environment Toolchain**

DO-178C Lifecycle Automation (M1 → M6)

| Field | Value |
|---|---|
| Document ID | SVP |
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
| 1.0 | 2026-06-29 | Hatem ADOUANI | Initial draft — project kickoff |
| 2.0 | 2026-06-29 | Hatem ADOUANI | Added AI model independence verification (Sec. 3.3): M4 (Gemma3 27B) independent of M3 (Qwen2.5-Coder 32B); M5 (DeepSeek-R1 32B) independent of M1 (Qwen3 32B) |
| 3.0 | 2026-07-03 | Hatem ADOUANI | Baseline: removed TOOLCHAIN suffix; referenced new SVS-1 standard governing LLT/HLT test-case writing rules for M4/M5. |

## 2. Introduction

### 2.1 Purpose

This Software Verification Plan (SVP) defines the verification processes, methods, activities, and responsibilities for the Intelligent Safety-Critical Engineering Environment Toolchain (I-SCEET) project. The SVP establishes how each AI-generated lifecycle artifact will be verified against DO-178C objectives prior to use in downstream activities.

This document shall be reviewed and approved prior to the commencement of any verification activity and is a required deliverable for SOI #1.

### 2.2 Project Overview

The I-SCEET project is an AI-powered toolchain composed of six intelligent modules (M1 to M6). Verification activities apply to the outputs of each module as follows:

| Module | Name | Input | Output Document | Verification Document | DO-178C § |
|---|---|---|---|---|---|
| M1 | HLR Generator | PDS + HW Doc + System Architecture | SRD | Review record + SRD sign-off | §5 |
| M2 | LLR Generator | SRD (HLRs) | SDDD | Review record + SDDD sign-off | §6 |
| M3 | Code Generator | SDDD (LLRs) | /src folder | Code review + static analysis report | §7 |
| M4 | LLT Generator | SDDD (LLRs) | SUTC | LLT review record + coverage report | §9 |
| M5 | HLT Generator | SRD (HLRs) | SVTC | HLT review record + coverage report | §9 |
| M6 | Traceability Generator | All artifacts | TM | Traceability audit record | §11 |

### 2.3 Scope

This SVP covers all verification activities performed on AI-generated artifacts within the I-SCEET project. It applies to reviews, analyses, testing, coverage measurement, and traceability verification. It does not cover the development activities themselves, which are governed by SDP.

### 2.4 Referenced Documents

- RTCA DO-178C — Software Considerations in Airborne Systems and Equipment Certification (2012)
- RTCA DO-330 — Software Tool Qualification Considerations
- SAE ARP4754A — Guidelines for Development of Civil Aircraft and Systems
- SAE ARP4761 — Guidelines for Conducting Safety Assessments
- PSAC — Plan for Software Aspects of Certification
- SDP — Software Development Plan
- SCMP — Software Configuration Management Plan
- SQAP — Software Quality Assurance Plan
- SRS — Software Requirements Standards
- SDS — Software Design Standards
- SCS — Software Code Standards

## 3. Verification Overview

### 3.1 Verification Objectives

The verification process shall demonstrate that the software lifecycle data produced by each AI module satisfies the applicable DO-178C objectives. In accordance with DO-178C §6.3, verification shall establish that:

- Requirements are accurate, consistent, verifiable, and traceable
- The software design correctly and completely implements the requirements
- The source code correctly implements the design
- Test cases adequately cover all requirements and achieve required structural coverage
- Traceability is complete and bidirectional across all lifecycle artifacts

### 3.2 Verification Approach

Each AI-generated artifact follows a generate-then-verify model. No artifact may be used as input to a subsequent module until it has been independently reviewed and all action items closed. The following verification methods are applied:

| Method | Description | Applied to |
|---|---|---|
| Review / Inspection | Independent engineer reads the artifact against a DO-178C checklist and raises action items for any deficiency | SRD, SDDD, /src, SUTC, SVTC, TM |
| Analysis | Formal assessment of properties such as traceability completeness, complexity, MISRA-C compliance, orphan detection | LLRs, Source Code, Traceability Matrix |
| Testing | Execution of generated test cases (SUTC, SVTC) against source code and measurement of structural coverage | /src folder |
| Coverage Analysis | Measurement of statement, decision, and MC/DC coverage against DAL A objectives using a qualified coverage tool | /src folder — all modules |

### 3.3 Verification Independence

Per DO-178C §6.3.2, verification activities shall be performed by personnel independent from those who produced the artifact under review. Independence is defined as:

- The reviewer has not configured, prompted, or tuned the AI module that produced the artifact
- The reviewer has not authored the input document(s) fed to the AI module
- At the AI module level, independent verification modules (M4, M5) shall use a distinct model and prompt from the generation modules they verify: M4 (Gemma3 27B) is independent of M3 (Qwen2.5-Coder 32B); M5 (DeepSeek-R1-Distill 32B) is independent of M1 (Qwen3 32B), per SCMP §3.3
- For DAL A, tool-generated verification outputs (coverage reports, static analysis) shall additionally be reviewed by an independent engineer

## 4. Verification Activities by Module

### 4.1 M1 Output Verification — SRD (HLRs)

The HLRs generated by M1 and the System Architecture section provided by the engineer shall be verified as follows:

| Activity | Criterion | DO-178C Objective | Performed By |
|---|---|---|---|
| HLR Review | Each HLR conforms to SRS format rules (ID, 'shall' language, no ambiguity) | §6.3.1a — Accuracy | Independent Engineer |
| Completeness Check | Every PDS item has at least one HLR child; no unaddressed system requirement | §6.3.1b — Completeness | Independent Engineer |
| Consistency Check | No contradictions exist between HLRs | §6.3.1c — Consistency | Independent Engineer |
| Verifiability Check | Each HLR can be verified by inspection, analysis, or test | §6.3.1d — Verifiability | Independent Engineer |
| Derived Req. Review | All [DERIVED] HLRs identified, justified, and submitted to safety process | §6.3.1e — Traceability | Systems Engineer + QA |
| Traceability Check | Each HLR is linked to at least one PDS item; TM updated | §6.3.1f — Traceability | Independent Engineer |
| System Architecture Review | Architecture section is consistent with HW doc and PDS inputs | §6.3.2 — Accuracy | Engineer |

### 4.2 M2 Output Verification — SDDD (Software Architecture + LLRs)

The Software Architecture and LLRs generated by M2 shall be verified as follows:

| Activity | Criterion | DO-178C Objective | Performed By |
|---|---|---|---|
| LLR Review | Each LLR conforms to SRS format; correct 'shall' language; no ambiguity | §6.3.2a — Accuracy | Independent Engineer |
| HLR-to-LLR Completeness | Each HLR is fully addressed by at least one LLR; no HLR left unimplemented | §6.3.2b — Completeness | Independent Engineer |
| No Undocumented Functions | No LLR introduces functionality not traceable to an HLR (unless [DERIVED]) | §6.3.2c — Consistency | Independent Engineer |
| Architecture Review | Module decomposition, interfaces, and data flows correctly implement HLRs | §6.3.2d — Design accuracy | Independent Engineer |
| Complexity Analysis | No module exceeds complexity limits defined in SDS | §6.3.2e — Standards | Independent Engineer |
| Traceability Update | LLR-to-HLR links established and recorded in TM | §6.3.2f — Traceability | Independent Engineer |

### 4.3 M3 Output Verification — /src Folder (Source Code)

The source code generated by M3 shall be verified as follows:

| Activity | Criterion | DO-178C Objective | Performed By |
|---|---|---|---|
| Code Review | Each source file reviewed against SCS checklist: naming, commenting, structure | §6.3.3a — Accuracy | Independent Engineer |
| LLR-to-Code Traceability | Each LLR is implemented by at least one function; header comments reference LLR IDs | §6.3.3b — Completeness | Independent Engineer |
| MISRA-C Analysis | Static analysis tool run on all /src files; all mandatory rules satisfied; deviations logged | §6.3.3c — Standards | Independent Engineer |
| No Dead Code | No unreachable code paths exist in any /src file | §6.3.3d — Consistency | Independent Engineer |
| Stack / Memory Usage | No dynamic memory allocation; stack depth estimated and within hardware limits | §6.3.3e — Safety | Independent Engineer |
| Code-to-LLR Traceability | All code traced to at least one LLR; orphan code reported to M6 | §6.3.3f — Traceability | Independent Engineer |

### 4.4 M4 Output Verification — SUTC (Low Level Tests)

M4 reads EXCLUSIVELY from SDDD (LLRs). The generated LLT cases shall be verified as follows:

| Activity | Criterion | DO-178C Objective | Performed By |
|---|---|---|---|
| LLR Coverage Review | Each LLR has at least one normal-range test case and one robustness test case | §6.4.2.1a — Coverage | Independent Engineer |
| Test Case Accuracy | Expected results defined for each test case; no ambiguous pass/fail criteria | §6.4.2.1b — Accuracy | Independent Engineer |
| Structural Coverage (DAL A) | Statement + Decision + MC/DC coverage achieved on all /src files | §6.4.4.2 — MC/DC | Coverage Tool + Engineer |
| Input Boundary Analysis | Boundary values, equivalence classes, and invalid inputs covered per LLR | §6.4.2.1c — Robustness | Independent Engineer |
| LLT-to-LLR Traceability | Each test case traces to at least one LLR; no orphan test cases | §6.4.2.2 — Traceability | Independent Engineer |
| Test Independence | LLT author has not configured M4 or authored SDDD LLRs | §6.3.2 — Independence | QA |

### 4.5 M5 Output Verification — SVTC (High Level Tests)

M5 reads EXCLUSIVELY from SRD (HLRs). The generated HLT cases shall be verified as follows:

| Activity | Criterion | DO-178C Objective | Performed By |
|---|---|---|---|
| HLR Coverage Review | Each HLR has at least one normal-range test case validating functional behavior | §6.4.1.1a — Coverage | Independent Engineer |
| Test Case Accuracy | Expected results defined for each test case; no ambiguous pass/fail criteria | §6.4.1.1b — Accuracy | Independent Engineer |
| Boundary & Robustness | Performance and timing requirements verified; out-of-range inputs tested per HLR | §6.4.1.1c — Robustness | Independent Engineer |
| HLT-to-HLR Traceability | Each test case traces to at least one HLR in SRD; no orphan test cases | §6.4.1.2 — Traceability | Independent Engineer |
| No LLR Leakage | HLT cases reference only HLRs from SRD — never LLRs from SDDD | §6.4.1 — Independence | QA |
| Functional Independence | HLT author has not configured M5 or authored SRD HLRs | §6.3.2 — Independence | QA |

### 4.6 M6 Output Verification — TM (Traceability Matrix)

The traceability matrix generated by M6 shall be audited as follows:

| Activity | Criterion | DO-178C Objective | Performed By |
|---|---|---|---|
| Upward Traceability | Each HLR traces to at least one PDS item; each LLR traces to at least one HLR | §6.5a — Completeness | Independent Engineer |
| Downward Traceability | Each PDS item covered by HLR; each HLR covered by LLR; each LLR covered by code | §6.5b — Completeness | Independent Engineer |
| Test Traceability | Each HLR covered by at least one HLT; each LLR covered by at least one LLT | §6.5c — Coverage | Independent Engineer |
| Orphan Detection | No HLR, LLR, source file, or test case exists without a parent link in TM | §6.5d — Completeness | QA + Engineer |
| Coverage Traceability | Coverage results (MC/DC) linked to corresponding LLR and test case IDs in TM | §6.5e — Coverage | Independent Engineer |

## 5. Coverage Objectives

### 5.1 Structural Coverage by DAL

As this project assumes DAL A (Engine Control context), ALL three coverage levels are required on all /src files:

| DAL | Statement | Decision | MC/DC | Status for I-SCEET |
|---|---|---|---|---|
| A | Required | Required | Required | ✓ APPLIES — all /src files |
| B | Required | Required | Not Required | N/A |
| C | Required | Not Required | Not Required | N/A |
| D | Not Required | Not Required | Not Required | N/A |

### 5.2 MC/DC Coverage Requirements (DAL A)

Modified Condition/Decision Coverage (MC/DC) requires that for every Boolean decision:

- Each condition in the decision has been shown to independently affect the outcome
- Each condition has been shown to take both a TRUE and FALSE value
- Each decision has been shown to take both a TRUE and FALSE outcome

M4-generated test cases (SUTC) must achieve full MC/DC on all /src files. Coverage gaps identified during execution must be reported as problem reports and resolved before SOI #3.

### 5.3 Coverage Tool

A qualified coverage analysis tool shall be used to measure structural coverage. The tool shall be qualified per DO-330 at the appropriate TQL level. Coverage results shall be recorded in the Software Verification Test Result (SVTR) and linked to TM.

## 6. Verification Environment

### 6.1 Verification Tools

| Tool | Purpose | Qualification Required |
|---|---|---|
| M4 — AI LLT Agent | Generate low level test cases from SDDD LLRs | Yes — DO-330 TQL-4 |
| M5 — AI HLT Agent | Generate high level test cases from SRD HLRs | Yes — DO-330 TQL-4 |
| M6 — Traceability Agent | Generate and audit TM traceability matrix | Yes — DO-330 TQL-5 |
| Static Analysis Tool | MISRA-C compliance check on /src folder | Yes — DO-330 TQL-5 |
| Coverage Analysis Tool | Statement / Decision / MC/DC coverage on /src | Yes — DO-330 TQL-4 |
| [Test Execution Tool] | Execute SUTC and SVTC on target or host | TBD |
| [Version Control — Git] | Baseline verification artifacts | No |

### 6.2 Target Environment

Verification activities shall be performed on the following environment:

- Host OS: Linux (Debian 12) or Windows 11 — version controlled
- Target Hardware: STM32F303-based embedded system (for integration testing)
- Compiler: [TBD — version locked and configuration-managed]
- All tool versions and configurations shall be recorded in the Software Configuration Index (SCI)

## 7. Verification Results and Problem Reports

### 7.1 Software Verification Test Result (SVTR)

All verification activities shall produce recorded results stored in SVTR. For each verification activity, SVTR shall capture:

- Artifact verified (document ID, version, date)
- Verification method applied (review / analysis / test / coverage)
- Pass / Fail status for each criterion
- Reviewer name and independence confirmation
- Reference to any problem reports raised
- Final sign-off and date

### 7.2 Problem Reports

Any deficiency identified during a verification activity shall be recorded as a Problem Report (PR) in the project tracking system. Problem reports shall:

- Be assigned a unique ID (PR-NNN)
- Classify severity: Critical / Major / Minor
- Reference the artifact and criterion that failed
- Be resolved and closed before the artifact is accepted as verified
- Be tracked through to SOI gate closure per SCMP

### 7.3 Re-Verification Rules

If a verified artifact is modified after acceptance (e.g., due to a change request), the following re-verification rules apply:

- Any change to SRD HLRs triggers re-verification of SDDD, /src, SVTC, and TM
- Any change to SDDD LLRs triggers re-verification of /src, SUTC, and TM
- Any change to /src triggers re-execution of SUTC and re-measurement of coverage
- Impact analysis must be performed and documented before re-verification scope is agreed

## 8. Transition Criteria

| Phase Transition | Entry Criteria | Exit Criteria | Responsible |
|---|---|---|---|
| SOI #1 → M1 | PSAC, SDP, SVP, SCMP, SQAP, SRS, SDS, SCS all approved | Certification authority SOI #1 review passed; all planning docs baselined | Author + Supervisor + QA |
| M1 → M2 | SRD produced by M1 | SRD §2 (HLRs) reviewed; all PRs closed; SRD baselined | Independent Engineer |
| M2 → M3 | SDDD produced by M2; SRD verified | SDDD reviewed (architecture + LLRs); no undocumented functions; SDDD baselined | Independent Engineer |
| M3 → M4/M5 | SDDD verified; /src produced by M3 | /src reviewed; MISRA-C clean; LLR-to-code traceability complete; /src baselined | Independent Engineer |
| M4/M5 → M6 | SUTC and SVTC produced | Both test sets reviewed; coverage executed; MC/DC achieved; SVTR updated | Independent Engineer |
| M6 → SOI #3 | TM produced by M6; all prior verifications complete | TM audited; no orphan requirements or code; TM baselined | QA + Engineer |
| SOI #3 → SOI #4 | All lifecycle data complete and baselined | SAS compiled; certification authority SOI #4 review passed | Author + QA |

## 9. SOI Review Plan

| SOI | Timing | Verification Items Reviewed | Acceptance Criteria |
|---|---|---|---|
| SOI #1 | Before M1 starts | SVP (this document), PSAC, SDP, SCMP, SQAP, SRS, SDS, SCS | All planning and standards documents approved; verification approach accepted by certification authority |
| SOI #2 | After M1 + M2 + M3 | SRD review record, SDDD review record, /src review record, MISRA-C report | All artifacts reviewed, PRs closed, baselines established; no open critical or major issues |
| SOI #3 | After M4 + M5 + M6 | SUTC review, SVTC review, SVTR (coverage results), TM audit record | MC/DC coverage achieved on all /src; traceability complete; no orphans; all PRs resolved |
| SOI #4 | Project end | SAS, full lifecycle data package | All DO-178C objectives for DAL A satisfied; SAS signed off |

## 10. Configuration Management and Quality Assurance

### 10.1 Configuration Management

All verification artifacts (review records, SVTR, PRs, coverage reports) shall be placed under configuration management per SCMP. Key rules:

- Verification records shall be baselined at each SOI gate alongside the artifacts they verify
- Any re-verification triggered by a change shall reference the original PR and be linked to the updated artifact baseline
- SVTR shall be version-controlled and updated with each new verification cycle

### 10.2 Quality Assurance

SQA verification activities are governed by SQAP. Verification-phase SQA activities include:

- Confirmation that no artifact was accepted as verified without a completed review record
- Audit that M4 only reads SDDD and M5 only reads SRD — mixing is a non-conformance
- Confirmation that coverage results meet DAL A MC/DC objectives before SOI #3
- Review of all open PRs before each SOI gate

## 11. Additional Considerations

### 11.1 Verification of Derived Requirements

HLRs tagged [DERIVED] in SRD shall undergo an additional verification step: safety impact assessment per ARP4761. Derived LLRs in SDDD shall similarly be flagged and reviewed. No derived requirement shall propagate to M3 or M4/M5 without explicit engineer approval.

### 11.2 AI Non-Determinism

AI modules (M4, M5) may produce different test cases across runs for identical inputs. To mitigate this:

- Model version and generation parameters (temperature, seed) shall be locked and configuration-managed
- If re-generation is required, all previously accepted test cases shall be re-reviewed
- Differences between generations shall be documented as a change request

### 11.3 Coverage Gaps

If structural coverage analysis reveals uncovered code paths after M4 test execution, the following process applies:

- A problem report (PR) shall be raised identifying the uncovered path and its source LLR
- M4 may be re-run with additional constraints to generate supplementary test cases
- If coverage cannot be achieved, a formal justification (dead code analysis) shall be produced and accepted by QA

### 11.4 Limitations of AI-Generated Test Cases

- AI-generated test cases may not cover all corner cases — mitigated by mandatory independent review against DO-178C §9 objectives
- AI-generated expected results may contain errors — mitigated by engineer validation of each expected result prior to test execution
- Coverage tool results are only valid if the tool is qualified per DO-330 — tool qualification must be confirmed before SOI #3

## 12. Approvals

This document requires the following approvals before SOI #1:

| Role | Name | Signature | Date |
|---|---|---|---|
| Author | Hatem ADOUANI |  |  |
| Quality Assurance | [QA Name] |  |  |
| Certification Authority | [Authority Rep] |  |  |
