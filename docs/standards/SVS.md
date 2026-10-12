# SOFTWARE VERIFICATION STANDARD

**SVS**

*Rules for Writing LLT and HLT - Governs M4 and M5*

| Document ID | SVS-1 |
|---|---|
| Version | 1.0 |
| Status | BASELINE |
| Date | 2026-07-03 |
| Author | Hatem ADOUANI |
| Project | I-SCEET |
| Institution | Personal project |
| Governs | M4 (LLT generation -> SUTC) and M5 (HLT generation -> SVTC) |
| Standard | RTCA DO-178C Section 6.4 / Table A-7 (MC/DC, DAL A) |

## 1. Document Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0 (BASELINE) | 2026-07-03 | Hatem ADOUANI | Initial release - defines LLT (SUTC, M4) and HLT (SVTC, M5) writing rules, the A0/A1/B1/B2 document structure, MC/DC coverage requirements, and traceability rules, aligned with PSAC, SVP, SRS and SDS. |

## I. Introduction

### I.1 Purpose

This Software Verification Standard (SVS) defines the rules, structure, and quality criteria for the low-level and high-level test cases produced by the I-SCEET toolchain. It governs:

- M4 - which generates Low-Level Tests (LLT), stored in SUTC (Software Unit Test Case), structurally verifying each LLR
- M5 - which generates High-Level Tests (HLT), stored in SVTC (Software Verification Test Case), functionally verifying each HLR

These rules shall be injected as constraints into the M4 and M5 AI module prompts and shall be applied by the independent reviewer during verification of SUTC and SVTC.

### I.2 Scope

This document covers: SUTC and SVTC document structure (A0/A1/B1/B2), test case identification, MC/DC coverage requirements for LLT, functional test derivation rules for HLT, and traceability from test cases back to LLR/HLR.

### I.3 Independence Requirement

Per SVP Sec.3.3, M4 (LLT) is independent of M3 (code generation), and M5 (HLT) is independent of M1 (HLR generation). This independence is the reason LLT/HLT are derived from the LLR/HLR text itself, never from the generated source code or from each other.

## II. Referenced Documents

- RTCA DO-178C Section 6.4 - Software Testing Process
- RTCA DO-178C Table A-7 - Structural coverage objectives (Modified Condition/Decision Coverage required for DAL A)
- PSAC - Plan for Software Aspects of Certification
- SVP - Software Verification Plan (independence rules, Sec.3.3)
- SRS - Software Requirements Standards (HLR/LLR format this document's tests trace back to)
- SDS - Software Design Standards (Causes/Effects table format that B1 sheets are built from)

## III. LLT Rules (SUTC - M4 Output)

### III.1 Purpose and Scope

LLT (Low-Level Tests) verify that the implementation of each LLR is structurally correct - every branch of the LLR's Causes/Effects table shall be exercised, both to TRUE and to FALSE independently of every other condition (MC/DC). LLT are derived from the LLR text (Causes/Effects, Implementation), never from the M3-generated source code, to preserve M4's independence from M3.

### III.2 SUTC Document Structure

Each SUTC is a spreadsheet with exactly four sheets, one set per function whose LLR(s) are under test:

| Sheet | Content |
|---|---|
| A0 | Function name, Author, Date, one-line description of the function |
| A1 | List of source documents needed to generate the test: the relevant LLR ID(s), SDS, and any [Rxx] reference used in the LLR's [JUS.[Rxx]...] tag |
| B1 | Matrix: rows = Causes/Effects branches from the LLR's table, columns = UTC IDs; each intersection cell holds T or F, marking which UTC exercises that branch to which outcome. Every row shall have at least one T and, where the branch has a false case, at least one F |
| B2 | Detailed unit test cases: one row per UTC ID, with preconditions, inputs, expected outputs, pass/fail criteria |

### III.3 Test Case ID Format

| Format | Example | Notes |
|---|---|---|
| SUTC_[SUBSYSTEM]_UFT[N] | SUTC_BOOT_UFT1 | N increments sequentially per subsystem across all UTCs in that subsystem's SUTC, not per function |

### III.4 MC/DC Coverage Requirement

Per DO-178C Table A-7, DAL A software requires Modified Condition/Decision Coverage (MC/DC). Concretely for SUTC generation:

- Every distinct Cause/Effect row in the source LLR's table shall map to at least one UTC in B1
- For a condition with independent sub-conditions (e.g. compound causes joined by AND/OR in the LLR), each sub-condition shall be shown to independently affect the outcome - this typically requires more than one UTC per row
- B1's T/F matrix is the evidence of this coverage - a row with only T's and no F (or vice versa) for a condition that has both outcomes in the LLR is a coverage gap
- 100% MC/DC across all LLRs in the subsystem is mandatory before M4's output is accepted

### III.5 Traceability

Every UTC in B2 shall reference the exact LLR ID it verifies (e.g. LLR-CLK-002-01). Every LLR with a Causes/Effects table shall have at least one UTC; an LLR with no branching (unconditional Effects only, per SDS) still requires exactly one UTC verifying the unconditional behavior.

## IV. HLT Rules (SVTC - M5 Output)

### IV.1 Purpose and Scope

HLT (High-Level Tests) verify that the software's observable behavior satisfies each HLR - functionally, as a black box. HLT are derived from the HLR statement (WHAT the software shall do), never from the LLR design or the source code, to preserve M5's independence from M1.

Example (as given by the project owner): HLR states 'The software shall read data from flash memory.' The corresponding HLT gives a flash memory address from the HW docs, initializes that memory with a known value, runs the read function, and expects to read back the same value - confirming the functional behavior, not any particular implementation detail.

### IV.2 SVTC Document Structure

Each SVTC is a spreadsheet with exactly four sheets, mirroring SUTC:

| Sheet | Content |
|---|---|
| A0 | Function/capability name, Author, Date, one-line description |
| A1 | List of source documents needed to generate the test: the relevant HLR ID(s), PDS item, and hardware reference manual sections |
| B1 | Matrix: rows = functional scenarios derived from the HLR statement, columns = FT IDs; each intersection cell holds T or F |
| B2 | Detailed functional test cases: one row per FT ID, with preconditions, inputs, expected outputs, pass/fail criteria |

### IV.3 Test Case ID Format

| Format | Example | Notes |
|---|---|---|
| SVTC_[SUBSYSTEM]_FT[N] | SVTC_BOOT_FT1 | N increments sequentially per subsystem across all FTs in that subsystem's SVTC |

### IV.4 Functional Test Derivation Rules

- Every HLR shall have at least one FT covering its normal (nominal) behavior
- Every HLR with a Safety Effect (per SRS Sec.4.1) shall have at least one FT covering the corresponding failure/error path (e.g. CRC failure, watchdog expiry)
- FT inputs and expected outputs shall reference concrete values from the HW reference manual or PDS - no symbolic placeholders
- FTs shall not reference LLR IDs, function names, or register-level detail - that would break M5's independence from M1/M2 design decisions

### IV.5 Traceability

Every FT in B2 shall reference the exact HLR ID it verifies (e.g. HLR-CLK-002). Every HLR shall have at least one FT.

## V. Traceability

M6 shall incorporate LLT and HLT into the project Traceability Matrix (TM) using the following chain, extending the chain already defined in SRS Sec.7.4:

| Level | Links to | Stored in |
|---|---|---|
| LLR-ID | -> UTC-ID(s) | SUTC, B2 sheet |
| HLR-ID | -> FT-ID(s) | SVTC, B2 sheet |
| UTC-ID | -> LLR Causes/Effects row(s) | SUTC, B1 matrix |
| FT-ID | -> HLR functional scenario | SVTC, B1 matrix |

A LLR or HLR with no corresponding test case at its respective level is a coverage gap and shall block SOI progression until resolved.

## VI. Review Checklist

### VI.1 SUTC Review Checklist

| # | Check Item |
|---|---|
| U01 | ID follows format SUTC_[SUBSYSTEM]_UFT[N] |
| U02 | A0 sheet populated: function name, author, date, description |
| U03 | A1 lists the exact LLR ID(s) and referenced documents |
| U04 | B1 matrix covers every Causes/Effects row from the source LLR |
| U05 | B1 shows both T and F for every branch that has both outcomes in the LLR (MC/DC evidence) |
| U06 | B2 test cases are concrete - specific input values, specific expected outputs |
| U07 | No UTC references M3-generated code or implementation details not present in the LLR |
| U08 | Every LLR in scope has at least one UTC |

### VI.2 SVTC Review Checklist

| # | Check Item |
|---|---|
| F01 | ID follows format SVTC_[SUBSYSTEM]_FT[N] |
| F02 | A0 sheet populated: capability name, author, date, description |
| F03 | A1 lists the exact HLR ID(s) and referenced documents |
| F04 | B1 matrix covers the nominal case and, where applicable, the safety/failure case |
| F05 | B2 test cases use concrete values from the HW reference manual or PDS |
| F06 | No FT references LLR IDs, function names, or register-level detail |
| F07 | Every HLR in scope has at least one FT |

## VII. Examples

### VII.1 Correct SUTC Example (LLT, real LLR)

Source LLR: LLR-CLK-002-01 (Configure Clock Source), Causes: HSI / HSE, Effects: configure internal / external clock.

A0: Function=configure_clock_source | Author=Hatem ADOUANI | Date=2026-07-03 | Description: configures the RCC clock source register based on the requested source.

| Causes/Effects row | UTC_HSI | UTC_HSE |
|---|---|---|
| Cause: source == HSI | T | F |
| Cause: source == HSE | F | T |

| UTC ID | Precondition | Input | Expected | Pass Criteria |
|---|---|---|---|---|
| SUTC_CLK_UFT1 | Clock source register at reset value | source = E_BOOT_CLK_HSI | clock.fres_config.HSI = TRUE | Register bit for HSI set, HSE bit unchanged |
| SUTC_CLK_UFT2 | Clock source register at reset value | source = E_BOOT_CLK_HSE | clock.fres_config.HSE = TRUE | Register bit for HSE set, HSI bit unchanged |

### VII.2 Correct SVTC Example (HLT, real HLR)

Source HLR: HLR-CLK-002 (the software shall configure the clock source as commanded).

A0: Capability=Clock Source Configuration | Author=Hatem ADOUANI | Date=2026-07-03 | Description: verifies the system clock reflects the commanded source at the hardware level.

| FT ID | Precondition | Input | Expected | Pass Criteria |
|---|---|---|---|---|
| SVTC_CLK_FT1 | System powered on, default clock state | Command HSE as clock source via the public API | SYSCLK derived from HSE, measurable on MCO pin | Measured frequency matches HSE-derived expected value +/-1% |

## VIII. Approvals

This document requires the following approvals before SOI #1 and before M4 or M5 are executed:

| Role | Name | Date |
|---|---|---|
| Author | Hatem ADOUANI |  |
| Quality Assurance | [QA Name] |  |
| Certification Authority | [Authority Rep] |  |
