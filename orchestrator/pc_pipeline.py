"""
================================================================================
 I-SCEET — PC Pipeline Orchestrator v2.0
 File: orchestrator/pc_pipeline.py
================================================================================
 Reads documents from SQLite → sends to Colab API → saves outputs to SQLite
 M1/M2 → .docx  |  M4/M5/M6 → .xlsx  |  versioning per module
================================================================================
"""

import requests, os, sys, sqlite3
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import (
    get_artifacts, save_artifact, get_tc_remarks,
    update_project_status, get_artifact_by_module,
    get_next_version
)

try:
    from orchestrator.docx_builder import build_srd, build_sddd
    from orchestrator.xlsx_builder import build_sutc, build_svtc, build_tm
    BUILDERS_AVAILABLE = True
except ImportError:
    BUILDERS_AVAILABLE = False

# ── OUTPUT DIRECTORIES ────────────────────────────────────────────────────────
OUTPUT_BASE = Path(__file__).parent.parent / "outputs"

# ── DOC FILTERING (Option B) ──────────────────────────────────────────────────
MODULE_DOC_FILTER = {
    "M1": ["PSAC", "SDP", "SRS-0xx", "PDS", "ARCH", "HW"],
    "M2": ["SDP", "SRS-0xx", "SDS-0xx"],
    "M3": ["SDP", "SCS-0xx", "SDS-0xx"],
    "M4": ["SVP", "SRS-0xx"],
    "M5": ["SVP", "SRS-0xx"],
    "M6": ["SCMP", "SQAP"],
}

MODULE_OUTPUT_TYPE = {
    "M1": "SRD-0xx",
    "M2": "SDDD-0xx",
    "M3": "/src",
    "M4": "SUTC-0xx",
    "M5": "SVTC-0xx",
    "M6": "TM-0xx",
}

MODULE_PREV_OUTPUTS = {
    "M2": ["SRD-0xx"],
    "M3": ["SDDD-0xx"],
    "M4": ["SDDD-0xx"],
    "M5": ["SRD-0xx"],
    "M6": ["SRD-0xx", "SDDD-0xx", "/src", "SUTC-0xx", "SVTC-0xx"],
}

MODULE_FORMAT = {
    "M1": "docx", "M2": "docx",
    "M3": "txt",
    "M4": "xlsx", "M5": "xlsx", "M6": "xlsx",
}


class PCPipeline:
    def __init__(self, colab_url: str, project_id: int, project_name: str = "project"):
        self.colab_url    = colab_url.rstrip("/")
        self.project_id   = project_id
        self.project_name = project_name
        self.timeout      = 600

    def test_connection(self) -> dict:
        try:
            r = requests.get(f"{self.colab_url}/status", timeout=10)
            return r.json()
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    # ── ARTIFACT LOADING ──────────────────────────────────────────────────────
    def _load_artifacts(self) -> dict:
        artifacts = get_artifacts(self.project_id)
        result = {}
        for a in artifacts:
            result[a["type"]] = a["content"] or ""
        return result

    def _build_module_input(self, module: str, all_artifacts: dict) -> dict:
        input_artifacts = {}
        for doc_type in MODULE_DOC_FILTER.get(module, []):
            if doc_type in all_artifacts and all_artifacts[doc_type]:
                input_artifacts[doc_type] = all_artifacts[doc_type][:6000]
        for output_type in MODULE_PREV_OUTPUTS.get(module, []):
            if output_type in all_artifacts and all_artifacts[output_type]:
                input_artifacts[output_type] = all_artifacts[output_type][:8000]
        return input_artifacts

    def _get_tc_remarks(self, module: str) -> str:
        remarks = get_tc_remarks(self.project_id)
        module_remarks = [r for r in remarks
                          if r["module"] == module and r["status"] == "open"]
        if not module_remarks:
            return ""
        return "\n".join(
            f"[{r['document']}] {r['req_id']}: {r['remark']}"
            for r in module_remarks
        )

    # ── VERSION MANAGEMENT ────────────────────────────────────────────────────
    def _get_next_version(self, module: str) -> str:
        """Get next version number for a module's artifact."""
        try:
            version = get_next_version(self.project_id, module)
            return f"{version}.0"
        except Exception:
            return "1.0"

    # ── FILE BUILDER ──────────────────────────────────────────────────────────
    def _build_output_file(self, module: str, text_output: str,
                           version: str) -> str | None:
        """Convert text output to .docx or .xlsx file. Returns file path."""
        if not BUILDERS_AVAILABLE:
            return None

        out_dir = OUTPUT_BASE / self.project_name / f"v{version}"
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            if module == "M1":
                path = str(out_dir / f"SRD-0xx_v{version}.docx")
                build_srd(text_output, path, version, self.project_name)
                return path
            elif module == "M2":
                path = str(out_dir / f"SDDD-0xx_v{version}.docx")
                build_sddd(text_output, path, version, self.project_name)
                return path
            elif module == "M4":
                path = str(out_dir / f"SUTC-0xx_v{version}.xlsx")
                build_sutc(text_output, path, version)
                return path
            elif module == "M5":
                path = str(out_dir / f"SVTC-0xx_v{version}.xlsx")
                build_svtc(text_output, path, version)
                return path
            elif module == "M6":
                path = str(out_dir / f"TM-0xx_v{version}.xlsx")
                build_tm(text_output, path, version)
                return path
            elif module == "M3":
                path = str(out_dir / "src.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text_output)
                return path
        except Exception as e:
            print(f"  ⚠️ Builder error for {module}: {e}")
            return None

    # ── RUN ONE MODULE ────────────────────────────────────────────────────────
    def run_module(self, module: str, progress_callback=None) -> dict:
        if progress_callback:
            progress_callback(module, "loading_docs")

        all_artifacts   = self._load_artifacts()
        input_artifacts = self._build_module_input(module, all_artifacts)
        tc_remarks      = self._get_tc_remarks(module)

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

        if result.get("status") == "success":
            text_output = result["output"]
            version     = self._get_next_version(module)

            # Build .docx or .xlsx file
            if progress_callback:
                progress_callback(module, "building_file")

            file_path = self._build_output_file(module, text_output, version)

            # Save to SQLite (text + file path + version)
            save_artifact(
                self.project_id,
                module,
                MODULE_OUTPUT_TYPE[module],
                text_output,
                file_path or "",
                version=version
            )

            result["version"]   = version
            result["file_path"] = file_path
            result["file_format"] = MODULE_FORMAT.get(module, "txt")

            if progress_callback:
                progress_callback(module, "saved")

        return result

    def run_auto(self, progress_callback=None) -> dict:
        results = {}
        update_project_status(self.project_id, "in_progress")
        for module in ["M1","M2","M3","M4","M5","M6"]:
            result = self.run_module(module, progress_callback)
            results[module] = result
            if result.get("status") == "error":
                update_project_status(self.project_id, "error")
                return results
        update_project_status(self.project_id, "complete")
        return results

    def run_single(self, module: str, progress_callback=None) -> dict:
        return self.run_module(module, progress_callback)
