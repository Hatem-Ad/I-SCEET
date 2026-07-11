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
    from orchestrator.sutc_builder import build_sutc
    from orchestrator.svtc_builder import build_svtc
    from orchestrator.tm_builder import build_tm
    XLSX_BUILDERS_AVAILABLE = True
except ImportError:
    XLSX_BUILDERS_AVAILABLE = False

# srd_builder/sddd_builder are imported unconditionally above (M1/M2 are
# core to the pipeline); sutc/svtc/tm_builder (M4/M5/M6) match the new
# 5-sheet A0/A1/A2/B0/B1 format — BUILDERS_AVAILABLE reflects docx
# builders only, since those are always ready.
BUILDERS_AVAILABLE = True

# ── OUTPUT DIRECTORIES ────────────────────────────────────────────────────────
OUTPUT_BASE = Path(__file__).parent.parent / "outputs"

# ── DOC FILTERING (Option B) ──────────────────────────────────────────────────
MODULE_DOC_FILTER = {
    "M1": ["PSAC", "SDP", "SRS", "PDS", "ARCH", "HW"],
    "M2": ["SDP", "SRS", "SDS"],
    "M3": ["SDP", "SCS", "SDS"],
    "M4": ["SVP", "SRS", "SVS"],
    "M5": ["SVP", "SRS", "SVS"],
    "M6": ["SCMP", "SQAP"],
}

MODULE_OUTPUT_TYPE = {
    "M1": "SRD",
    "M2": "SDDD",
    "M3": "/src",
    "M4": "SUTC",
    "M5": "SVTC",
    "M6": "TM",
}

MODULE_PREV_OUTPUTS = {
    "M2": ["SRD"],
    "M3": ["SDDD"],
    "M4": ["SDDD"],
    "M5": ["SRD"],
    "M6": ["SRD", "SDDD", "/src", "SUTC", "SVTC"],
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
        self.timeout      = 1800  # was 600s — too short once HW docs pushed
                                  # context to ~14k tokens on a 32B model;
                                  # 30 min covers worst case (M1/M3/M5 + large input)
        self.poll_interval = 1.5  # seconds between /progress polls

    def test_connection(self) -> dict:
        try:
            r = requests.get(f"{self.colab_url}/status", timeout=10)
            return r.json()
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def chat(self, module: str, question: str, artifacts: dict) -> dict:
        """Call the consultative /chat endpoint (Colab notebook Cell 11 —
        uses M6/Phi-4, independent from the generator modules, per its own
        docstring). This endpoint is SYNCHRONOUS on the Colab side (not
        the async job pattern /generate_async uses) — a long timeout is
        used here to absorb Phi-4's load time, but this is still a real
        ngrok-timeout risk on the free tier if the model isn't already
        cached. Flagged, not fixed here — ask if you want it converted to
        the async job pattern too."""
        try:
            r = requests.post(
                f"{self.colab_url}/chat",
                json={"module": module, "question": question, "artifacts": artifacts},
                timeout=600,  # was 180s - too short for a Phi-4 cold start on ngrok free tier
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            return {"status": "error", "answer":
                    "Request timed out — Phi-4 may still be loading. "
                    "This can happen on ngrok's free tier for slow cold starts."}
        except Exception as e:
            return {"status": "error", "answer": f"Chat request failed: {e}"}

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

        if module == "M6":
            # M6 reads ALL prior artifacts at once - raw concatenation with
            # per-artifact truncation risks cutting a tag ([COV.HLR-xxx],
            # @req, ...) in half, silently breaking a traceability link.
            # Deterministic tag extraction replaces the full text with a
            # compact, complete correlation summary instead (see
            # tag_extractor.py) - typically ~97% smaller, and nothing is
            # ever truncated mid-tag since only whole tags are captured.
            try:
                from orchestrator.tag_extractor import build_m6_input
                m6_summary = build_m6_input(
                    srd_text=all_artifacts.get("SRD", ""),
                    sddd_text=all_artifacts.get("SDDD", ""),
                    src_text=all_artifacts.get("/src", ""),
                    sutc_text=all_artifacts.get("SUTC", ""),
                    svtc_text=all_artifacts.get("SVTC", ""),
                )
                input_artifacts["TAG_SUMMARY"] = m6_summary
            except Exception as e:
                print(f"  ⚠️ Tag extraction failed, falling back to truncated raw text: {e}")
                for output_type in MODULE_PREV_OUTPUTS.get(module, []):
                    if output_type in all_artifacts and all_artifacts[output_type]:
                        input_artifacts[output_type] = all_artifacts[output_type][:8000]
        elif module == "M2" and all_artifacts.get("SRD"):
            # M2 needs full HLR substance (Statement, Category, Safety
            # Effect) plus the Architecture section to derive meaningful
            # LLRs - unlike M6, a pure ID-tag summary would lose exactly
            # the content M2 needs. context_summarizer keeps that
            # substance while dropping cover-page/reference-list bulk that
            # M2 doesn't use, and - unlike a blind [:8000] cut - never
            # truncates mid-HLR.
            try:
                from orchestrator.context_summarizer import summarize_srd_for_m2
                input_artifacts["SRD"] = summarize_srd_for_m2(all_artifacts["SRD"])
            except Exception as e:
                print(f"  ⚠️ SRD summarization failed, falling back to truncated raw text: {e}")
                input_artifacts["SRD"] = all_artifacts["SRD"][:8000]
        elif module == "M3" and all_artifacts.get("SDDD"):
            # M3 needs Prototype/Parameters/Called Functions/Causes-Effects
            # /Implementation/DD tags to generate correct code, but not
            # Design-Traceability/Mean-of-Verification/Rationale (M4/M5/M6's
            # concern) or the document-level Intro/References/Summary.
            # Reuses sddd_builder's own tested parser rather than new regex,
            # ~40% smaller than raw text and never truncates mid-LLR.
            try:
                from orchestrator.context_summarizer import summarize_sddd_for_m3
                input_artifacts["SDDD"] = summarize_sddd_for_m3(all_artifacts["SDDD"])
            except Exception as e:
                print(f"  ⚠️ SDDD summarization failed, falling back to truncated raw text: {e}")
                input_artifacts["SDDD"] = all_artifacts["SDDD"][:8000]
        else:
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
    def _get_next_version(self, module: str) -> dict:
        """Returns the {baseline_number, minor_number, status} dict for
        this run, computed against the module's PRIMARY output type
        (MODULE_OUTPUT_TYPE[module]) so that when a module produces
        several artifacts in one run (M2 -> SDDD+DD+CT), they all share
        the same version number - computed once here, reused for all of
        them in run_module(), rather than each type incrementing
        independently and drifting apart."""
        try:
            return get_next_version(self.project_id, module, MODULE_OUTPUT_TYPE[module])
        except Exception:
            return {"baseline_number": 1, "minor_number": 0, "status": "DRAFT"}

    # ── FILE BUILDER ──────────────────────────────────────────────────────────
    def _build_output_file(self, module: str, text_output: str, version: dict):
        """Convert text output to .docx/.xlsx file(s).
        `version` is the {baseline_number, minor_number, status} dict from
        _get_next_version() — never a bare string, so filenames and DB
        rows can never drift apart.
        Returns (primary_path, extra_artifacts) where extra_artifacts is a
        dict {doc_type: path} for modules that produce more than one file
        (currently only M2: SDDD.docx + DD.xlsx + CT.xlsx). Empty dict for
        every other module — no behavior change for them."""
        if not BUILDERS_AVAILABLE:
            return None, {}

        version_str = f"{version['baseline_number']}.{version['minor_number']}"
        out_dir = OUTPUT_BASE / self.project_name / f"v{version_str}"
        out_dir.mkdir(parents=True, exist_ok=True)
        extra_artifacts = {}

        try:
            if module == "M1":
                path = str(out_dir / f"SRD_v{version_str}.docx")
                build_srd(text_output, path, version_str, self.project_name)
                return path, extra_artifacts
            elif module == "M2":
                path = str(out_dir / f"SDDD_v{version_str}.docx")
                build_sddd(text_output, path, version_str, self.project_name)
                if DD_CT_BUILDERS_AVAILABLE:
                    try:
                        dd_path = str(out_dir / f"DD_v{version_str}.xlsx")
                        build_dd(text_output, dd_path, version_str)
                        extra_artifacts["DD"] = dd_path
                    except Exception as e:
                        print(f"  ⚠️ DD builder error: {e}")
                    try:
                        ct_path = str(out_dir / f"CT_v{version_str}.xlsx")
                        build_ct(text_output, ct_path, version_str)
                        extra_artifacts["CT"] = ct_path
                    except Exception as e:
                        print(f"  ⚠️ CT builder error: {e}")
                return path, extra_artifacts
            elif module == "M4":
                path = str(out_dir / f"SUTC_v{version_str}.xlsx")
                build_sutc(text_output, path, version_str)
                return path, extra_artifacts
            elif module == "M5":
                path = str(out_dir / f"SVTC_v{version_str}.xlsx")
                build_svtc(text_output, path, version_str)
                return path, extra_artifacts
            elif module == "M6":
                path = str(out_dir / f"TM_v{version_str}.xlsx")
                build_tm(text_output, path, version_str)
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
    def run_module(self, module: str, progress_callback=None, phase_scope: str = None) -> dict:
        """
        progress_callback(module: str, message: str) is called repeatedly
        with a human-readable live status string, e.g.:
          "📥 Loading Qwen3-32B-Q4_K_M.gguf..."
          "🧠 M1 is generating output... (this can take a few minutes)"
          "🗑️ Unloading M1..."

        phase_scope (M1 only): a comma-separated list of PDS-ID prefixes
        to cover in this run, e.g. "PDS-BOOT-*, PDS-CLK-*, PDS-FLASH-*" -
        splits a large PDS across multiple generation passes when the
        full set wouldn't fit comfortably in context. Leave None to cover
        every PDS item in one pass (default).

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

        if phase_scope and module == "M1":
            input_artifacts["PHASE_SCOPE"] = f"PHASE SCOPE: {phase_scope}"

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
            version_str = f"{version['baseline_number']}.{version['minor_number']}"

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
                # Same version dict reused on purpose - SDDD/DD/CT from the
                # same M2 run stay numbered together (see _get_next_version
                # docstring), rather than each type drifting independently.
                save_artifact(
                    self.project_id, module, doc_type, "", extra_path, version=version
                )

            result["version"]     = version_str
            result["file_path"]   = file_path
            result["extra_files"] = extra_artifacts
            result["file_format"] = MODULE_FORMAT.get(module, "txt")

            report(f"✅ {module} complete — saved as v{version_str}")

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

    def run_single(self, module: str, progress_callback=None, phase_scope: str = None) -> dict:
        return self.run_module(module, progress_callback, phase_scope=phase_scope)