"""
================================================================================
 I-SCEET — PC Pipeline Orchestrator v3.0
 File: orchestrator/pc_pipeline.py
================================================================================
 Reads documents from SQLite → sends to Colab API → saves outputs to SQLite
 M1/M2 → .docx  |  M4/M5/M6 → .xlsx  |  versioning per module
 v3.0: live progress polling (/progress) while Colab generates, so the
       Streamlit UI can show "Loading M1... / Generating... / Unloading..."
       instead of a static spinner.
================================================================================
"""

import requests, os, sys, sqlite3, threading, time
from datetime import datetime
from pathlib import Path

from orchestrator.srd_builder import build_srd
from orchestrator.sddd_builder import build_sddd

try:
    from orchestrator.dd_builder import build_dd
    from orchestrator.ct_builder import build_ct
    DD_CT_BUILDERS_AVAILABLE = True
except ImportError:
    DD_CT_BUILDERS_AVAILABLE = False

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Backend.db import (
    get_artifacts, save_artifact, get_tc_remarks,
    update_project_status, get_artifact_by_module,
    get_next_version
)

try:
    from orchestrator.xlsx_builder import build_sutc, build_svtc, build_tm
    XLSX_BUILDERS_AVAILABLE = True
except ImportError:
    XLSX_BUILDERS_AVAILABLE = False

# srd_builder/sddd_builder are imported unconditionally above (M1/M2 are
# core to the pipeline); xlsx_builder (M4/M5/M6) is optional until it is
# updated for the new formats — BUILDERS_AVAILABLE reflects docx builders
# only, since those are always ready.
BUILDERS_AVAILABLE = True

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

# Icons per stage — used to build the live status message
STAGE_ICONS = {
    "loading":    "📥",
    "loaded":     "✅",
    "generating": "🧠",
    "unloading":  "🗑️",
    "idle":       "💤",
    "done":       "🎉",
    "error":      "❌",
    "ready":      "♻️",
}


class PCPipeline:
    def __init__(self, colab_url: str, project_id: int, project_name: str = "project"):
        self.colab_url    = colab_url.rstrip("/")
        self.project_id   = project_id
        self.project_name = project_name
        self.timeout      = 600
        self.poll_interval = 1.5  # seconds between /progress polls

    def test_connection(self) -> dict:
        try:
            r = requests.get(f"{self.colab_url}/status", timeout=10)
            return r.json()
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def _poll_progress(self) -> dict:
        """Single lightweight poll of Colab's live status. Never raises."""
        try:
            r = requests.get(f"{self.colab_url}/progress", timeout=5)
            return r.json()
        except Exception:
            return {"module": None, "stage": "unknown", "detail": ""}

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
        try:
            version = get_next_version(self.project_id, module)
            return f"{version}.0"
        except Exception:
            return "1.0"

    # ── FILE BUILDER ──────────────────────────────────────────────────────────
    def _build_output_file(self, module: str, text_output: str, version: str):
        """Convert text output to .docx/.xlsx file(s).
        Returns (primary_path, extra_artifacts) where extra_artifacts is a
        dict {doc_type: path} for modules that produce more than one file
        (currently only M2: SDDD.docx + DD.xlsx + CT.xlsx). Empty dict for
        every other module — no behavior change for them."""
        if not BUILDERS_AVAILABLE:
            return None, {}

        out_dir = OUTPUT_BASE / self.project_name / f"v{version}"
        out_dir.mkdir(parents=True, exist_ok=True)
        extra_artifacts = {}

        try:
            if module == "M1":
                path = str(out_dir / f"SRD-0xx_v{version}.docx")
                build_srd(text_output, path, version, self.project_name)
                return path, extra_artifacts
            elif module == "M2":
                path = str(out_dir / f"SDDD-0xx_v{version}.docx")
                build_sddd(text_output, path, version, self.project_name)
                if DD_CT_BUILDERS_AVAILABLE:
                    try:
                        dd_path = str(out_dir / f"DD-0xx_v{version}.xlsx")
                        build_dd(text_output, dd_path, version)
                        extra_artifacts["DD-0xx"] = dd_path
                    except Exception as e:
                        print(f"  ⚠️ DD builder error: {e}")
                    try:
                        ct_path = str(out_dir / f"CT-0xx_v{version}.xlsx")
                        build_ct(text_output, ct_path, version)
                        extra_artifacts["CT-0xx"] = ct_path
                    except Exception as e:
                        print(f"  ⚠️ CT builder error: {e}")
                return path, extra_artifacts
            elif module == "M4":
                path = str(out_dir / f"SUTC-0xx_v{version}.xlsx")
                build_sutc(text_output, path, version)
                return path, extra_artifacts
            elif module == "M5":
                path = str(out_dir / f"SVTC-0xx_v{version}.xlsx")
                build_svtc(text_output, path, version)
                return path, extra_artifacts
            elif module == "M6":
                path = str(out_dir / f"TM-0xx_v{version}.xlsx")
                build_tm(text_output, path, version)
                return path, extra_artifacts
            elif module == "M3":
                path = str(out_dir / "src.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text_output)
                return path, extra_artifacts
        except Exception as e:
            print(f"  ⚠️ Builder error for {module}: {e}")
            return None, {}

    # ── RUN ONE MODULE (with live progress polling) ────────────────────────────
    def run_module(self, module: str, progress_callback=None) -> dict:
        """
        progress_callback(module: str, message: str) is called repeatedly
        with a human-readable live status string, e.g.:
          "📥 Loading Qwen3-32B-Q4_K_M.gguf..."
          "🧠 M1 is generating output... (this can take a few minutes)"
          "🗑️ Unloading M1..."

        Uses the async job pattern (POST /generate_async + GET /result/<id>)
        instead of one long blocking POST — this avoids ngrok's free-tier
        timeout killing long-running generation requests.
        """
        def report(msg):
            if progress_callback:
                progress_callback(module, msg)

        report("📄 Loading input documents from database...")

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

        # ── 1. Start the job — this call returns almost instantly ─────────────
        try:
            r = requests.post(
                f"{self.colab_url}/generate_async",
                json={
                    "module":     module,
                    "artifacts":  input_artifacts,
                    "tc_remarks": tc_remarks,
                },
                timeout=15,
            )
            r.raise_for_status()
            job_id = r.json()["job_id"]
        except Exception as e:
            return {"status": "error", "module": module,
                    "message": f"Failed to start job: {e}"}

        report("🚀 Job started — waiting for Colab...")

        # ── 2. Poll /result/<job_id> AND /progress every few seconds ──────────
        last_detail = None
        start_time  = time.time()

        while True:
            # Check job status (fast, short-lived request)
            try:
                jr = requests.get(f"{self.colab_url}/result/{job_id}", timeout=10)
                jr.raise_for_status()
                job = jr.json()
            except Exception as e:
                job = {"status": "running"}  # transient network hiccup, keep polling

            if job.get("status") == "done":
                result = job["result"]
                break
            elif job.get("status") == "error":
                return {"status": "error", "module": module,
                        "message": job.get("error", "Unknown error on Colab")}

            # Still running — update live status from /progress
            status = self._poll_progress()
            detail = status.get("detail", "")
            stage  = status.get("stage", "")
            if detail and detail != last_detail:
                icon = STAGE_ICONS.get(stage, "⏳")
                report(f"{icon} {detail}")
                last_detail = detail

            if time.time() - start_time > self.timeout:
                return {"status": "error", "module": module,
                        "message": f"Timed out after {self.timeout}s waiting for {module}"}

            time.sleep(self.poll_interval)

        if result.get("status") == "success":
            text_output = result["output"]
            version     = self._get_next_version(module)

            report(f"📝 Formatting {MODULE_OUTPUT_TYPE[module]} document...")
            file_path, extra_artifacts = self._build_output_file(module, text_output, version)

            save_artifact(
                self.project_id,
                module,
                MODULE_OUTPUT_TYPE[module],
                text_output,
                file_path or "",
                version=version
            )
            for doc_type, extra_path in extra_artifacts.items():
                save_artifact(
                    self.project_id, module, doc_type, "", extra_path, version=version
                )

            result["version"]     = version
            result["file_path"]   = file_path
            result["extra_files"] = extra_artifacts
            result["file_format"] = MODULE_FORMAT.get(module, "txt")

            report(f"✅ {module} complete — saved as v{version}")

        return result

    def run_auto(self, progress_callback=None) -> dict:
        results = {}
        update_project_status(self.project_id, "in_progress")
        for module in ["M1", "M2", "M3", "M4", "M5", "M6"]:
            result = self.run_module(module, progress_callback)
            results[module] = result
            if result.get("status") == "error":
                update_project_status(self.project_id, "error")
                return results
        update_project_status(self.project_id, "complete")
        return results

    def run_single(self, module: str, progress_callback=None) -> dict:
        return self.run_module(module, progress_callback)