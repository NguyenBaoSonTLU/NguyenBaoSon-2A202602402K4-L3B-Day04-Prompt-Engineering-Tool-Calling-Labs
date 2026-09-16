"""Build reproducible indexes from saved runs; never fabricate model results."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run_eval import summarize


def main():
    analysis = ROOT / "analysis"
    analysis.mkdir(exist_ok=True)
    remote_commit = "d0deff4972e1b4cfec221ce66fc16d8105cb051c"
    remote_files = set(subprocess.check_output(["git", "ls-tree", "-r", "--name-only", remote_commit, "starter_v0/runs"], cwd=ROOT.parent).decode().splitlines())
    index = {"generated_at": datetime.now().isoformat(),
             "file_hash_method": "SHA-256 after CRLF-to-LF normalization (stable across Git checkouts)",
             "runs": [], "transcripts": []}
    review = []
    versions = []
    preceding = {}
    for path in sorted((ROOT / "runs").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        summary = run["summary"]
        if summarize(run["results"]) != summary:
            raise ValueError(f"Saved metrics differ from recalculated metrics: {path.name}")
        valid = summary["provider_error_cases"] == 0 and summary["measured_cases"] == summary["total_cases"]
        relative = path.relative_to(ROOT).as_posix()
        series = "remote_d0deff4" if "starter_v0/" + relative in remote_files else "local_completion"
        case_set = [{"id": c["id"], "input": c["input"], "expect": c["expect"]} for c in run["results"]]
        case_hash = hashlib.sha256(json.dumps(case_set, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        index["runs"].append({"file": relative, "sha256": hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                              "series": series, "valid_measurement": valid, "case_set_sha256": case_hash,
                              "version": run["version"], "suite": run["suite"],
                              "artifact_version": run["artifact_version"], "summary": summary})
        for case in run["results"]:
            results = case.get("tool_results", [])
            errors = [event for event in results if event.get("error") or event.get("result", {}).get("error")]
            writes = [event for event in results if event.get("result", {}).get("status") in {"created", "needs_confirmation"}]
            if not case["result"]["passed"] or errors or writes:
                review.append({"run": relative, "case_id": case["id"],
                               "automatic_pass": case["result"]["passed"],
                               "failures": case["result"].get("failures", []),
                               "actual_calls": case["result"].get("actual_tool_calls", []),
                               "tool_errors": errors, "write_results": writes})
        version = run["version"]
        if series == "local_completion" and (run["suite"] == "base" or version == "v4"):
            historical = version in {"v1", "v2"}
            hypothesis = {
                "v0": "Baseline; original prompt recovered from Git with matching SHA-256.",
                "v1": "Historical hypothesis not recorded; cannot reconstruct from metrics alone.",
                "v2": "Historical hypothesis not recorded; cannot reconstruct from metrics alone.",
                "v3": "Retrospective interpretation of saved prompt: explicit routing, scope and confirmation rules should reduce errors; original pre-run hypothesis is unavailable.",
                "v4": "Pre-recorded in analysis/experiment_v4.md: concise authority rules plus stronger tool descriptions should improve boundaries and scope.",
            }[version]
            before = preceding.get((series, run["suite"]), "")
            if version == "v4" and run["suite"] != "base":
                prior = [entry for entry in index["runs"] if entry["series"] == series and entry["version"] == "v3" and entry["suite"] == run["suite"]]
                before = prior[-1]["summary"]["case_accuracy"] if prior else ""
            versions.append({"version": version, "author": "not_recorded" if version != "v4" else "Codex-assisted; see TEAM.md",
                             "changed_artifact": "baseline" if version == "v0" else "system_prompt.md; tools.yaml" if version == "v4" else "system_prompt.md (hash changed)",
                             "artifact_version": run["artifact_version"], "prompt_hash": run["prompt_hash"], "tools_hash": run["tools_hash"],
                             "reason": "Historical snapshot/notes missing" if historical else f"Review {run['suite']} tool routing and result boundaries",
                             "hypothesis": hypothesis, "metric_name": f"{run['suite']}.case_accuracy", "metric_before": before,
                             "metric_after": summary["case_accuracy"], "run_file": relative})
        if valid:
            preceding[(series, run["suite"])] = summary["case_accuracy"]
    for path in sorted((ROOT / "transcripts").glob("*.json")):
        transcript = json.loads(path.read_text(encoding="utf-8"))
        index["transcripts"].append({"file": path.relative_to(ROOT).as_posix(),
                                     "sha256": hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                                     "artifact_version": transcript["artifact_version"],
                                     "turn_count": len(transcript["turns"]),
                                     "statuses": [turn["status"] for turn in transcript["turns"]]})
    (analysis / "evidence_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (analysis / "tool_result_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    with (analysis / "local_version_log.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(versions[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(versions)
    original_log = ROOT / "artifacts/snapshots/remote_d0deff4/version_log.csv"
    remote_rows = list(csv.DictReader(original_log.open(encoding="utf-8")))
    for row in remote_rows:
        row.update(series="remote_d0deff4", run_file=row["run_file"].removeprefix("../"), metric_name="base.case_accuracy")
    for row in versions:
        row["series"] = "local_completion"
    with (ROOT / "artifacts/version_log.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(versions[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows([*remote_rows, *versions])
    with (analysis / "run_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["series", "version", "suite", "valid_measurement", "total_cases", "passed_cases", "case_accuracy", "provider_error_cases", "measured_cases", "file"], lineterminator="\n")
        writer.writeheader()
        for run in index["runs"]:
            writer.writerow({key: run.get(key, run["summary"].get(key)) for key in writer.fieldnames})
    print(f"Indexed {len(index['runs'])} real runs and {len(index['transcripts'])} real transcripts; metrics recalculated OK.")


if __name__ == "__main__":
    main()
