# Example run — 2026-07-11 (raw pipeline output)

Output of the I-SCEET pipeline on the STM32F303 bootloader case study
(project `stm32f303_boot_drv`), kept as an example of what the pipeline
produces. **It is raw model output, not reviewed evidence:** nothing here has
been verified, approved or baselined.

## Files

| File | Module | Notes |
|---|---|---|
| [`SRD_v1.4.docx`](SRD_v1.4.docx) | M1 (Qwen3 32B) | Software Requirements Data, 17 HLRs |
| [`SDDD_v1.4.docx`](SDDD_v1.4.docx) | M2 (Mistral Small 24B) | Software Design Description, 21 LLRs |
| [`DD_v1.4.xlsx`](DD_v1.4.xlsx) | M2 | Data dictionary |
| [`CT_v1.4.xlsx`](CT_v1.4.xlsx) | M2 | Constants table |
| [`SUTC_v1.0.xlsx`](SUTC_v1.0.xlsx) | M4 | Software unit test cases (low-level tests) |
| [`SVTC_v1.0.xlsx`](SVTC_v1.0.xlsx) | M5 | Software verification test cases (high-level tests) |
| [`TM_v1.0.xlsx`](TM_v1.0.xlsx) | M6 | Traceability matrix |
| [`inputs/`](inputs/) | — | The exact M1 inputs used for this run |

## About SUTC, SVTC and TM

`SUTC_v1.0.xlsx`, `SVTC_v1.0.xlsx` and `TM_v1.0.xlsx` are v1.0 outputs of
M4, M5 and M6, kept as raw, unreviewed pipeline output to show the format
of the M4–M6 workbooks. They are not consistent with SRD 1.4 and SDDD 1.4:
the TM references `LLR-BOOT-003-01` and `LLR-BOOT-004-01`, which do not
exist in SDDD 1.4.

The M3 source code of this run is not included.

## Inputs

[`inputs/`](inputs/) holds the longer PDS, architecture and hardware
summaries that were actually fed to M1 for this run. For a new run, use the
shorter curated inputs in [`../inputs/`](../inputs/) instead; they are
written for new users and keep a full M1→M6 run fast.

| File | Upload slot |
|---|---|
| [`inputs/PDS_summary_for_M1.txt`](inputs/PDS_summary_for_M1.txt) | PDS |
| [`inputs/ARCH_summary_for_M1.txt`](inputs/ARCH_summary_for_M1.txt) | ARCH |
| [`inputs/HW_summary.txt`](inputs/HW_summary.txt) | HW |

## Changes from the original output

The project name in the document headers was renamed to
`stm32f303_boot_drv`, and the institution field and the footer notice now
read "Personal project". The content is otherwise unchanged.
