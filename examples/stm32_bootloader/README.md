# Example — STM32F303 UART bootloader (`stm32f303_boot_drv`)

A small, self-made case study used to exercise the whole I-SCEET pipeline:
a UART bootloader, its driver layer and a placeholder application for the
STM32F303VC on an STM32F3DISCOVERY board.

All input files here were written from scratch for this repository. They are
intentionally short (12 PDS items) so a full M1→M6 run stays fast.

## Inputs

| File | Upload slot | Content |
|---|---|---|
| [`inputs/PDS_stm32f303_boot_drv.txt`](inputs/PDS_stm32f303_boot_drv.txt) | PDS | 12 product items (`PDS-BOOT-001` … `PDS-APP-001`) |
| [`inputs/ARCH_stm32f303_boot_drv.txt`](inputs/ARCH_stm32f303_boot_drv.txt) | ARCH | software items, layers, start-up sequence, update state machine |
| [`inputs/HW_stm32f303_context.txt`](inputs/HW_stm32f303_context.txt) | HW | MCU, clocks, memory map, application header, pin-out |

## How to run

1. Start the UI (`bash start.sh`) with `COLAB_URL` set in `.env`.
2. **Upload** page: create a project named `stm32f303_boot_drv`, then upload
   the three files above in *Step 3 — Inputs M1*. Planning/standards documents
   (step 2) are optional.
3. **Pipeline** page: test the connection, then run M1 (or AUTO for M1→M6).
4. Review the generated SRD, SDDD, source and test workbooks on the
   **Revue** page. Expect each PDS item to be covered by 2–6 HLRs.

Generated files land in `outputs/stm32f303_boot_drv/` (git-ignored).

## Example output

[`run-2026-07-11/`](run-2026-07-11/) contains raw pipeline output for this
case study (SRD, SDDD, data dictionary, constants, test and traceability
workbooks). It is unreviewed model output, kept to show what the pipeline
produces; see its README for its limits.

## Hardware references

The vendor documents are not redistributed here; get them from st.com:

- STM32F303xB/xC datasheet
- RM0316 — STM32F303 reference manual
- PM0214 — Cortex-M4 programming manual
- AN2606 — STM32 system memory boot mode
