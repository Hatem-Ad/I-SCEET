# Models

This folder contains the main generation models used by I-SCEET.

## Available Models

### Model1_HLR.py
Generates High-Level Requirements (HLR) from engineering inputs such as PDS, hardware context, and system architecture.

### Model2_LLR.py
Transforms HLR into Low-Level Requirements (LLR) and prepares a more detailed software-oriented decomposition.

### Model3_CodeGen_AI.py
Generates source code proposals from LLR and design logic.

### Model4_LLT.py
Generates Low-Level Test artifacts based on code and low-level requirements.

### Model5_HLT.py
Generates High-Level Test artifacts based on high-level requirements and system behavior.

### Model6_Traceability.py
Builds traceability links across requirements, code, and tests.

## Goal

These models represent the intelligent layer of I-SCEET.  
Their role is to support a structured engineering workflow for safety-critical development.

## Note

The examples used to validate the models are only case studies.  
The main objective is to make the framework reusable across different embedded and safety-critical scenarios.
