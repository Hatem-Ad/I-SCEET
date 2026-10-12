# SOFTWARE DEVELOPMENT PLAN

**SDP**

### Intelligent Safety-Critical Engineering Environment Toolchain

DO-178C Lifecycle Automation (M1 → M6)

| Document ID | SDP |
|---|---|
| Version | 4.0 |
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
| 1.0 | 2026-03-15 | Hatem ADOUANI | Initial draft — project kickoff |
| 2.0 | 2026-04-20 | Hatem ADOUANI | Alignment with the PSACv2.0 version |
| 3.0 | 2026-06-29 | Hatem ADOUANI | Replaced placeholder LangChain/OpenAI environment with verified local stack: FastAPI + llama-cpp-python on Colab, Streamlit + SQLite on PC, ngrok tunnel |
| 4.0 | 2026-07-03 | Hatem ADOUANI | Baseline: removed TOOLCHAIN suffix; documented M2 prompt v4.1 structure (I-V sections, Parameters table, Causes/Effects matrix, DD/CT tag extraction) as the current M1/M2/M3 development environment. |

## 2. Introduction

### 2.1 Purpose

This Software Development Plan (SDP) defines the software development process, methods, standards, and environment for the Intelligent Safety-Critical Engineering Environment Toolchain (I-SCEET) project. The SDP establishes how each development activity will be planned, executed, and controlled in accordance with DO-178C objectives.

This document shall be reviewed and approved prior to the commencement of any development activity and is a required deliverable for SOI #1.

### 2.2 Project Overview

The I-SCEET project is an AI-powered toolchain composed of six intelligent modules (M1 to M6), each automating a specific phase of the DO-178C software development lifecycle:

| Module | Name | Input | Output | DO-178C § |
|---|---|---|---|---|
| M1 | HLR Generator | PDS + Hardware Doc + System Architecture | High Level Requirements (HLR) | §5 |
| M2 | LLR Generator | HLR | Low Level Requirements (LLR) | §6 |
| M3 | Code Generator | LLR | Source Code | §7 |
| M4 | LLT Generator | LLR | Low Level Tests (LLT) | §9 |
| M5 | HLT Generator | HLR | High Level Tests (HLT) | §9 |
| M6 | Traceability Generator | All artifacts | Traceability Matrix | §11 |

### 2.3 Scope

This SDP applies to all software development activities performed within the I-SCEET project, including AI-assisted generation of HLR, LLR, source code, test cases, and traceability data. It covers the full development lifecycle from requirements through integration, and establishes the development standards that all generated and reviewed artifacts must satisfy.

### 2.4 Referenced Documents

- RTCA DO-178C — Software Considerations in Airborne Systems and Equipment Certification (2012)
- RTCA DO-330 — Software Tool Qualification Considerations
- RTCA DO-331 — Model-Based Development and Verification Supplement
- SAE ARP4754A — Guidelines for Development of Civil Aircraft and Systems
- SAE ARP4761 — Guidelines for Conducting Safety Assessments
- PSAC — Plan for Software Aspects of Certification
- SVP — Software Verification Plan
- SCMP — Software Configuration Management Plan
- SQAP — Software Quality Assurance Plan
- SCS — Software Coding Standards

## 3. Software Development Process

### 3.1 Lifecycle Model

The I-SCEET project follows the sequential DO-178C software lifecycle model, aligned with the V-model as defined in PSAC. The development lifecycle is divided into the following ordered phases:

- Planning (SOI #1 gate): All planning documents completed and approved
- Software Requirements (M1, M2): HLR and LLR generation and review
- Software Design & Coding (M2, M3): Architecture, LLR refinement, source code generation
- Software Verification (M4, M5, M6): Test generation, execution, and traceability
- Certification (SOI #4): Software Accomplishment Summary (SAS) and final review

The lifecycle ensures full traceability from requirements to verification in accordance with DO-178C objectives.

### 3.2 Development Approach

Each module (M1 to M6) follows a generate-then-review model: the AI agent produces an initial artifact, which is then subject to independent human review against applicable DO-178C objectives. No AI-generated artifact is considered complete until the review is passed and all action items are closed.

Where an AI-generated artifact introduces a derived requirement (a requirement with no direct parent in the PDS), this shall be explicitly identified, tagged, and submitted to the safety process per ARP4761.

AI-generated artifacts are not considered developed software data unless independently reviewed and validated by qualified personnel.

### 3.3 Development Activities by Module

| Module | Phase | Activities | Output Artifacts |
|---|---|---|---|
| M1 | HLR Generation | Ingest PDS + HW docs; AI extraction; engineer review | Software Requirements Data (HLR set) |
| M2 | LLR Derivation | HLR decomposition; interface definition; constraint allocation | Low Level Requirements document |
| M3 | Source Code Generation | LLR-to-code mapping; MISRA-C compliance; coding standard checks | Source Code + Coding Standards compliance report |
| M4 | LLT Generation | Derive test cases from LLR; structural coverage targeting | Low Level Test cases + expected results |
| M5 | HLT Generation | Derive test cases from HLR; functional/boundary coverage | High Level Test cases + expected results |
| M6 | Traceability | Bidirectional linking; orphan detection; gap analysis | Traceability Matrix |

## 4. Software Development Environment

### 4.1 Development Host Environment

All development activities shall be conducted on a controlled host environment with the following characteristics:

- Operating System: Linux (Debian 12) or Windows 11 — version controlled
- Primary Language: Python 3.11 (AI orchestration); C + assembly(generated target code) 
- Target Hardware: STM32F303-based embedded system (for generated code integration)
- AI Framework: Custom FastAPI server on Google Colab (GPU) using llama-cpp-python; local GGUF models only — no external API calls. 
- All model versions, prompts, and generation parameters (temperature, tokens, etc.) are configuration-controlled and baselined. 
- Any change to these elements requires re-verification of impacted artifacts.

### 4.2 Development Tools

| Tool | Purpose | Version | Qualification Required |
|---|---|---|---|
| M1 — AI HLR Agent (Qwen3 32B) | Generate HLR from PDS/HW/Architecture | 1.0 | Yes — DO-330 TQL-5 |
| M2 — AI LLR Agent (Mistral Small 24B) | Generate LLR from HLR | 1.0 | Yes — DO-330 TQL-5 |
| M3 — AI Code Agent (Qwen2.5-Coder 32B) | Generate Source Code from LLR | 1.0 | Yes — DO-330 TQL-4 |
| M4 — AI LLT Agent (Gemma3 27B — independent of M3) | Generate Low Level Tests | 1.0 | Yes — DO-330 TQL-4 |
| M5 — AI HLT Agent (DeepSeek-R1-Distill 32B — independent of M1) | Generate High Level Tests | 1.0 | Yes — DO-330 TQL-4 |
| M6 — Traceability Agent (Phi-4 14B) | Generate Traceability Matrix | 1.0 | Yes — DO-330 TQL-5 |
| Python 3.11 / FastAPI + llama-cpp-python | AI agent orchestration framework | TBD | No — output verified by subsequent activity |
| [Requirements Tool] | Requirements management (e.g., DOORS) | TBD | TBD |
| [Version Control] | Configuration management (e.g., Git) | TBD | No |

### 4.3 Tool Qualification Strategy

Per RTCA DO-330, AI modules whose output feeds directly into safety-critical lifecycle data must be qualified. The following qualification levels apply:

- TQL-5: Tools whose output is independently verified by a subsequent activity (M1, M2, M6)
- TQL-4: Tools that automate verification activities (M3, M4, M5)

Each AI module shall have a dedicated Tool Qualification Plan (TQP) documenting tool operational requirements, qualification data, and known limitations.

### 4.4 Version Control and Baselining

All source artifacts, AI agent configurations, and generated outputs shall be placed under version control per SCMP. A formal baseline shall be established at each SOI gate. Changes to any baselined artifact require formal change control authorization.

All configuration items shall be uniquely identified, versioned, and traceable to the baseline established at each SOI gate.

## 5. Software Standards

### 5.1 Applicable Standards

| Standard | Applies To | Notes |
|---|---|---|
| MISRA-C:2012 | M3 — Generated Source Code | Mandatory for all C code generated by M3; violations tracked in problem report system |
| DO-178C §5 | M1 — HLR | All HLR shall be verifiable, unambiguous, and consistent |
| DO-178C §6 | M2 — LLR / Design | LLR shall be traceable to HLR; no undocumented functions |
| DO-178C §7 | M3 — Source Code | Code shall comply with project coding standards (SCS) |
| SCS | All generated code | Project Software Coding Standards document; includes naming, commenting, complexity limits |

### 5.2 Requirements Standards

All HLR and LLR produced by M1 and M2 shall conform to the following properties as required by DO-178C §5 and §6:

- Verifiable: Each requirement can be confirmed by inspection, analysis, or test
- Unambiguous: Only one interpretation is possible for each requirement statement
- Consistent: No contradictions exist between requirements at the same or different levels
- Traceable: Each LLR maps to at least one HLR; each HLR maps to at least one PDS element
- Complete: No unintended functions; all operating modes are addressed

### 5.3 Coding Standards

All source code generated by M3 shall conform to the Software Coding Standards document (SCS). Key rules include:

- MISRA-C:2012 compliance — all mandatory rules enforced; advisory rules reviewed
- No dynamic memory allocation in safety-critical paths
- All variables initialized before use; no implicit type conversions
- Functions limited to a single well-defined responsibility; cyclomatic complexity ≤ 10
- All code paths covered by test cases; no unreachable code

All deviations from MISRA-C shall be formally documented, justified, and approved.

## 6. Reviews and Inspections

### 6.1 Review Strategy

All AI-generated artifacts shall undergo independent review before being accepted as verified lifecycle data. The following review types are defined:

| Review Type | Target Artifact | Performed By | Criteria |
|---|---|---|---|
| Peer Review | HLR, LLR, Source Code | Independent Engineer | DO-178C §5/§6/§7 objectives satisfied; checklist completed |
| Code Review | M3 Generated Source Code | Independent Engineer | MISRA-C compliance; no dead code; proper error handling |
| Test Review | LLT (M4), HLT (M5) | Independent Engineer | Test cases cover all requirements; expected results defined |
| Traceability Review | Traceability Matrix (M6) | QA + Engineer | No orphan requirements; bidirectional links complete |
| SOI Review | All lifecycle data | Certification Authority | All applicable DO-178C objectives satisfied per SOI checklist |

### 6.2 Review Independence

Per DO-178C, reviews of safety-critical software outputs shall be performed by personnel who are independent from the original generation activity. Independence is defined as no direct involvement in the AI module configuration or prompt engineering for the artifact under review.

This independence ensures objective assessment of AI-generated outputs.

## 7. Transition Criteria

Transition from one lifecycle phase to the next requires satisfaction of the following criteria:

| Phase | Entry Criteria | Exit Criteria | Responsible |
|---|---|---|---|
| Planning → Requirements | All 5 planning documents approved (SOI #1) | PSAC, SDP, SVP, SCMP, SQAP reviewed and baselined | Author + Supervisor + QA |
| Requirements → Design | HLR baselined and reviewed | LLR complete, traceable to HLR, no open critical issues | Module M1/M2 Engineer |
| Design → Code | LLR reviewed and approved | Source Code generated, MISRA-C analysis complete, no critical deviations | Module M3 Engineer |
| Code → Verification | Source Code baselined | All HLT and LLT generated, reviewed, and approved | Module M4/M5 Engineer |
| Verification → Certification | All tests executed, traceability matrix complete (SOI #3) | SAS compiled, all lifecycle data reviewed by certification authority (SOI #4) | QA + Author |

## 8. Software Configuration Management

Configuration management of all development artifacts is governed by SCMP. The following principles apply in the context of this SDP:

- All module inputs and outputs shall be uniquely identified and version-controlled
- AI agent prompts, model versions, and temperature settings are considered development environment configuration items and shall be baselined
- Any change to a baselined AI configuration item that could affect output shall trigger a re-review of affected artifacts
- Problem reports raised during development shall be tracked in the project problem report system and resolved prior to the relevant SOI gate

## 9. Software Quality Assurance

Software Quality Assurance activities during development are governed by SQAP. Development-phase SQA activities include:

- Verification that development activities follow this SDP
- Audit of review records to ensure independence and completeness
- Confirmation that coding standards compliance analysis has been performed on all M3 outputs
- Tracking of all non-conformances raised against development artifacts through to closure
- SQA sign-off required at each lifecycle phase transition per the transition criteria in Section 7

## 10. Additional Considerations

### 10.1 Derived Requirements Handling

AI-generated requirements (HLR from M1, LLR from M2) may introduce derived requirements — requirements with no direct parent in the Product Description Specification. All derived requirements shall be:

- Explicitly identified and tagged as 'derived' in the requirements data
- Reviewed and approved by the systems engineer prior to use in downstream modules
- Submitted to the safety process for impact assessment per ARP4761

### 10.2 Limitations of AI-Generated Development Artifacts

The following limitations are acknowledged and shall be mitigated through mandatory human review activities during development:

- AI models may generate plausible but semantically incorrect requirements or code — mitigated by independent engineer review against DO-178C objectives
- AI models may not account for all hardware constraints visible in the STM32F303 platform documentation — mitigated by providing full hardware documentation as M1 input
- Generated code may contain MISRA-C deviations not detectable without static analysis — mitigated by mandatory static analysis tool execution prior to review
- AI model non-determinism may produce different outputs for identical inputs across runs — mitigated by locking model version and generation parameters and recording them in the CM baseline

### 10.3 Previously Developed Software

Not applicable to this project. All software artifacts are generated fresh by the AI toolchain for this project instance.

### 10.4 COTS and Third-Party Components

COTS components used within the AI modules (e.g., LLM frameworks, Python libraries) shall be identified, documented in the Software Configuration Index, and assessed for their impact on certification objectives and potential for introducing unsafe behavior.

## 11. Approvals

This document requires the following approvals before SOI #1:

| Role | Name | Signature | Date |
|---|---|---|---|
| Author | Hatem Adouani |  |  |
| Quality Assurance | [QA Name] |  |  |
| Certification Authority | [Authority Rep] |  |  |
