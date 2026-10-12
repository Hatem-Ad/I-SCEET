# Documentation

- [`diagrams/I-SCEET_architecture.png`](diagrams/I-SCEET_architecture.png) —
  the M1→M6 data flow (the same flow is shown as a Mermaid diagram in the
  [main README](../README.md#pipeline)).

## DO-178C plans and standards

The project's own planning and standards documents, written for the
STM32F303 bootloader case study. They were authored as `.docx` and are kept
here as Markdown so they can be read and diffed on GitHub.

| Folder | Documents |
|---|---|
| [`plans/`](plans/) | [PSAC](plans/PSAC.md), [SDP](plans/SDP.md), [SVP](plans/SVP.md), [SQAP](plans/SQAP.md), [SCMP](plans/SCMP.md) |
| [`standards/`](standards/) | [SRS](standards/SRS.md), [SDS](standards/SDS.md), [SCS](standards/SCS.md), [SVS](standards/SVS.md) |

Notes on the conversion:

- Page headers, footers and page breaks were not carried over.
- The supervisor placeholder rows (`[Supervisor Name]`) were removed and the
  institution field reads "Personal project".
- Text and tables are otherwise unchanged; code samples in SCS are fenced
  blocks.

### Summaries for the models

`plans/summaries/` and `standards/summaries/` hold the short text versions
that the pipeline actually consumes (upload them in *Step 2* of the
*Upload* page). `plans/summaries/00_PROJECT_OVERRIDES_FOR_MODELS.txt` lists
project decisions that take precedence over older wording in the summaries.

You can upload your own plans and standards instead; uploads are stored in
the local SQLite database, not in this repository.
