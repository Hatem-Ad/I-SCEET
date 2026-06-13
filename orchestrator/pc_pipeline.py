"""
================================================================================
 I-SCEET — PC Pipeline Orchestrator
 File: orchestrator/pc_pipeline.py
================================================================================
 Reads documents from SQLite → sends to Colab API → saves outputs to SQLite
================================================================================
"""

import requests
import sqlite3
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import (
    get_artifacts, save_artifact, get_tc_remarks,
    update_project_status, get_artifact_by_module
)

# ── DOC FILTERING (Option B) ──────────────────────────────────────────────────
MODULE_DOC_FILTER = {
    "M1": ["PSAC", "SDP", "SRS-001", "PDS", "ARCH", "HW"],
    "M2": ["SDP", "SRS-001", "SDS-001"],
    "M3": ["SDP", "SCS-001", "SDS-001"],
    "M4": ["SVP", "SRS-001"],
    "M5": ["SVP", "SRS-001"],
    "M6": ["SCMP", "SQAP"],
}

# Module output types
MODULE_OUTPUT = {
    "M1": "SRD-001",
    "M2": "SDDD-001",
    "M3": "/src",
    "M4": "SVCP-LLT-001",
    "M5": "SVCP-HLT-001",
    "M6": "STD-001",
}

# M2-M6 also need previous module outputs
MODULE_PREV_OUTPUTS = {
    "M2": ["SRD-001"],
    "M3": ["SDDD-001"],
    "M4": ["SDDD-001"],
    "M5": ["SRD-001"],
    "M6": ["SRD-001", "SDDD-001", "/src", "SVCP-LLT-001", "SVCP-HLT-001"],
}


class PCPipeline:
    """
    PC-side pipeline orchestrator.
    Reads docs from SQLite, calls Colab FastAPI, saves results to SQLite.
    """

    def __init__(self, colab_url: str, project_id: int):
        self.colab_url  = colab_url.rstrip("/")
        self.project_id = project_id
        self.timeout    = 600  # 10 min per module

    # ── CONNECTION TEST ───────────────────────────────────────────────────────
    def test_connection(self) -> dict:
        try:
            r = requests.get(f"{self.colab_url}/status", timeout=10)
            return r.json()
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    # ── LOAD ARTIFACTS FROM SQLITE ────────────────────────────────────────────
    def _load_artifacts(self) -> dict:
        """Load all artifacts for this project from SQLite."""
        artifacts = get_artifacts(self.project_id)
        result = {}
        for a in artifacts:
            result[a["type"]] = a["content"]
        return result

    # ── BUILD MODULE INPUT ────────────────────────────────────────────────────
    def _build_module_input(self, module: str, all_artifacts: dict) -> dict:
        """
        Build the artifacts dict to send to Colab for a given module.
        Combines filtered planning/standards docs + required previous outputs.
        """
        input_artifacts = {}

        # 1. Add filtered planning + standards docs
        for doc_type in MODULE_DOC_FILTER.get(module, []):
            if doc_type in all_artifacts:
                input_artifacts[doc_type] = all_artifacts[doc_type]

        # 2. Add required previous module outputs
        for output_type in MODULE_PREV_OUTPUTS.get(module, []):
            if output_type in all_artifacts:
                input_artifacts[output_type] = all_artifacts[output_type]

        return input_artifacts

    # ── GET TC REMARKS FOR MODULE ─────────────────────────────────────────────
    def _get_tc_remarks(self, module: str) -> str:
        remarks = get_tc_remarks(self.project_id)
        module_remarks = [r for r in remarks if r["module"] == module
                          and r["status"] == "open"]
        if not module_remarks:
            return ""
        lines = []
        for r in module_remarks:
            lines.append(f"[{r['document']}] {r['req_id']}: {r['remark']}")
        return "\n".join(lines)

    # ── RUN ONE MODULE ────────────────────────────────────────────────────────
    def run_module(self, module: str, progress_callback=None) -> dict:
        """
        Run a single module:
        1. Load artifacts from SQLite
        2. Call Colab /generate
        3. Save output to SQLite
        """
        if progress_callback:
            progress_callback(module, "loading_docs")

        all_artifacts = self._load_artifacts()
        input_artifacts = self._build_module_input(module, all_artifacts)
        tc_remarks = self._get_tc_remarks(module)

        if not input_artifacts:
            return {
                "status":  "error",
                "module":  module,
                "message": f"No input artifacts found for {module}. "
                           f"Required: {MODULE_DOC_FILTER.get(module, [])}"
            }

        if progress_callback:
            progress_callback(module, "generating")

        try:
            r = requests.post(
                f"{self.colab_url}/generate",
                json={
                    "module":     module,
                    "artifacts":  input_artifacts,
                    "tc_remarks": tc_remarks,
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            result = r.json()

        except requests.exceptions.Timeout:
            return {"status": "error", "module": module,
                    "message": "Colab timeout — model took too long"}
        except Exception as e:
            return {"status": "error", "module": module, "message": str(e)}

        # Save output to SQLite
        if result.get("status") == "success":
            save_artifact(
                self.project_id,
                module,
                MODULE_OUTPUT[module],
                result["output"],
            )
            if progress_callback:
                progress_callback(module, "saved")

        return result

    # ── RUN FULL PIPELINE ─────────────────────────────────────────────────────
    def run_auto(self, progress_callback=None) -> dict:
        """Run full pipeline M1→M6 automatically."""
        results = {}
        modules = ["M1", "M2", "M3", "M4", "M5", "M6"]

        update_project_status(self.project_id, "in_progress")

        for module in modules:
            result = self.run_module(module, progress_callback)
            results[module] = result

            if result.get("status") == "error":
                update_project_status(self.project_id, "error")
                return results

        update_project_status(self.project_id, "complete")
        return results

    # ── RUN SINGLE MODULE ─────────────────────────────────────────────────────
    def run_single(self, module: str, progress_callback=None) -> dict:
        """Run a single module (for manual mode or re-generation)."""
        return self.run_module(module, progress_callback)
