# Models

This folder contains the system prompts of the I-SCEET generation modules.

## Modules

Each module is defined by its system prompt in
[`system_prompts/`](system_prompts/) and runs on a separate GPU host
(see the main README, *Model server*).

| Module | Prompt | Role |
|---|---|---|
| M1 | `M1_system_prompt.txt` | High-Level Requirements (HLR) from PDS, hardware context and system architecture |
| M2 | `M2_system_prompt.txt` | Low-Level Requirements (LLR) and software design from HLR |
| M3 | `M3_system_prompt.txt` | Source code proposals from LLR and design |
| M4 | `M4_system_prompt.txt` | Low-Level Tests from code and LLR |
| M5 | `M5_system_prompt.txt` | High-Level Tests from HLR and system behaviour |
| M6 | `M6_system_prompt.txt` | Traceability links across requirements, code and tests |

Running these modules locally (without the model server) is planned work.

## Goal

These models represent the intelligent layer of I-SCEET.  
Their role is to support a structured engineering workflow for safety-critical development.

## Note

The examples used to validate the models are only case studies.  
The main objective is to make the framework reusable across different embedded and safety-critical scenarios.
