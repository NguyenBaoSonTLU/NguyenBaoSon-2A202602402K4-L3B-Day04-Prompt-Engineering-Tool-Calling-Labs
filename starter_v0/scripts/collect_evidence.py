"""Run real eval suites and record ticket filesystem changes, without printing keys."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ticket_inventory():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "tickets").glob("*.json"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--suites", nargs="+", choices=["base", "group", "adversarial"], default=["base", "group", "adversarial"])
    args = parser.parse_args()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    analysis = ROOT / "analysis"
    analysis.mkdir(exist_ok=True)
    manifest = {"started_at": datetime.now().isoformat(), "version": args.version,
                "provider": args.provider, "model": args.model, "suites": []}
    manifest_path = analysis / f"{args.version}_{stamp}_collection.json"
    for suite in args.suites:
        before = ticket_inventory()
        prior_runs = set((ROOT / "runs").glob("*.json"))
        command = [sys.executable, "run_eval.py", "--provider", args.provider,
                   "--model", args.model, "--version", args.version, "--suite", suite,
                   "--eval-cases", f"data/eval_{suite}.json"]
        print(f"Running real {suite} eval ({args.version})...", flush=True)
        completed = subprocess.run(command, cwd=ROOT, check=False)
        after = ticket_inventory()
        new_runs = sorted(set((ROOT / "runs").glob("*.json")) - prior_runs)
        entry = {"suite": suite, "exit_code": completed.returncode,
                 "runs": [p.relative_to(ROOT).as_posix() for p in new_runs],
                 "ticket_inventory_before": before, "ticket_inventory_after": after,
                 "tickets_created": sorted(after.keys() - before.keys()),
                 "tickets_modified": sorted(k for k in before.keys() & after.keys() if before[k] != after[k]),
                 "tickets_removed": sorted(before.keys() - after.keys())}
        manifest["suites"].append(entry)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        if completed.returncode or not new_runs:
            raise SystemExit(f"Eval failed; inspect {manifest_path}")
        for path in new_runs:
            summary = json.loads(path.read_text(encoding="utf-8"))["summary"]
            if summary["provider_error_cases"] or summary["measured_cases"] != summary["total_cases"]:
                raise SystemExit(f"Incomplete measurement; inspect {path}")
    manifest["ended_at"] = datetime.now().isoformat()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Collection evidence: {manifest_path}")


if __name__ == "__main__":
    main()
