"""Check technical evidence and secrets without exposing environment values."""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
from env_loader import load_lab_env
from tools import TOOL_FUNCTIONS, load_tool_declarations


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO).decode("utf-8").strip()


def main():
    load_lab_env(ROOT)
    declarations = load_tool_declarations(ROOT / "artifacts/tools.yaml")
    registry_matches = {d["name"] for d in declarations} == set(TOOL_FUNCTIONS)
    arguments_match = all(set(d["parameters"]["properties"]) == set(inspect.signature(TOOL_FUNCTIONS[d["name"]]).parameters) for d in declarations)
    group = json.loads((ROOT / "data/eval_group.json").read_text(encoding="utf-8"))["cases"]
    group_valid = len(group) == len({c["id"] for c in group}) == 10 and sum("query" in c for c in group) == sum("turns" in c for c in group) == 5
    fixed = ["starter_v0/data/eval_base.json", "starter_v0/data/eval_adversarial.json", "starter_v0/data/eval_helpdesk_extension.json"]
    fixed_unchanged = not git("diff", "311580e", "--", *fixed)
    hashes = {name: hashlib.sha256((ROOT / "artifacts" / name).read_bytes()).hexdigest() for name in ["system_prompt.md", "tools.yaml"]}
    final_runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "runs").glob("v4_*.json"))]
    final_match = len(final_runs) >= 3 and all(r["prompt_hash"] == hashes["system_prompt.md"] and r["tools_hash"] == hashes["tools.yaml"] for r in final_runs)
    measured = all(r["summary"]["provider_error_cases"] == 0 and r["summary"]["measured_cases"] == r["summary"]["total_cases"] for r in final_runs)
    eligible = git("ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    forbidden = [p for p in eligible if Path(p).name == ".env" or "/.venv/" in p or "/__pycache__/" in p or p.startswith("starter_v0/tickets/")]
    secrets = [value for name, value in os.environ.items() if (name.endswith("_API_KEY") or name.endswith("_TOKEN")) and len(value) >= 16 and not any(marker in value.lower() for marker in ["your_", "your-", "example", "replace", "changeme"])]
    secret_files = []
    syntax_errors = []
    for relative in eligible:
        path = REPO / relative
        if not path.is_file() or path.suffix not in {".py", ".md", ".txt", ".csv", ".json", ".yaml", ".yml"}:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if any(secret in content for secret in secrets) or re.search(r"\bsk-[A-Za-z0-9_-]{24,}", content):
            secret_files.append(relative)
        if path.suffix == ".py":
            try:
                compile(content, relative, "exec")
            except SyntaxError:
                syntax_errors.append(relative)
    result = {
        "checked_at": datetime.now().isoformat(),
        "git_head_at_check": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "remote": git("remote", "get-url", "origin"),
        "technical_checks": {"registry_matches": registry_matches, "arguments_match": arguments_match,
                             "group_exactly_5_plus_5": group_valid, "fixed_eval_files_unchanged": fixed_unchanged,
                             "final_artifacts_match_v4_runs": final_match, "final_runs_fully_measured": measured,
                             "no_forbidden_git_files": not forbidden, "no_detected_real_keys": not secret_files,
                             "python_syntax_ok": not syntax_errors},
        "forbidden_files": forbidden, "secret_file_paths_only": secret_files, "syntax_errors": syntax_errors,
        "secret_scan_scope": "Git tracked + eligible untracked text; compare configured API key/token values and OpenAI-like key pattern. Synthetic adversarial fixtures are not real credentials. Not a guarantee against every possible secret format.",
        "human_items_pending": ["Confirm the inherited TEAM.md identity/reflection still describes the submitter",
                               "Repository naming and applicable deadline; VLearn submission is reported in inherited SUBMISSION.md but not independently verified in this session"],
    }
    out = ROOT / "analysis/submission_check.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["technical_checks"], indent=2))
    if not all(result["technical_checks"].values()):
        raise SystemExit("Technical verification failed; inspect analysis/submission_check.json (no secret values printed).")


if __name__ == "__main__":
    main()
