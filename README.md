# I-SCEET

**Intelligent Safety-Critical Environment Engineering Toolchain**

I-SCEET is a framework-oriented project for supporting the development of safety-critical software engineering artifacts through an intelligent and structured workflow inspired by aerospace practices.

## Project Vision

The main objective of I-SCEET is to help generate and organize key engineering artifacts such as:

- High-Level Requirements (HLR)
- Low-Level Requirements (LLR)
- Source Code
- Low-Level Tests (LLT)
- High-Level Tests (HLT)
- Traceability Matrices
- DO-178C-like project documents

I-SCEET is the core project.  
Application examples such as STM32 bootloader and drivers are only initial case studies used to validate the approach.

## Global Workflow

The project follows this high-level pipeline:

1. Input engineering context  
   - Product Design Specification (PDS)  
   - Hardware context  
   - System architecture  

2. Generate HLR  
3. Generate LLR  
4. Generate source code  
5. Generate LLT  
6. Generate HLT  
7. Generate traceability artifacts  

## Repository Structure

```text
I-SCEET/
├── data/                    # Input and support data
├── deterministic_core/      # Deterministic validation and generation layer
├── docs/                    # Engineering, DO-178-like, templates, report
├── examples/                # Case studies and demonstrations
├── models/                  # AI-oriented generation models
├── notebooks/               # Google Colab / experiments
├── orchestrator/            # Workflow coordination and routing
├── outputs/                 # Generated artifacts
├── ui/                      # Future interface layer
├── README.md
├── requirements.txt
└── LICENSE
