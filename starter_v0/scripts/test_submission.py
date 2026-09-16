"""Offline regression checks; these are not live model eval evidence."""
from __future__ import annotations

import importlib
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from chat import run_model_tool_loop
from providers.base import ModelResponse, ToolCall
from run_eval import load_cases, validate_expected_tools
from tools import TOOL_FUNCTIONS, load_tool_declarations
from tools.search_device_info.tool import search_device_info
from tools.search_kb.tool import search_kb
from tools.policy.tool import search_company_policy


class SubmissionChecks(unittest.TestCase):
    def test_registry_and_group_contract(self):
        declarations = load_tool_declarations(ROOT / "artifacts/tools.yaml")
        self.assertEqual({d["name"] for d in declarations}, set(TOOL_FUNCTIONS))
        for declaration in declarations:
            schema = declaration["parameters"]
            self.assertEqual(set(schema["properties"]), set(inspect.signature(TOOL_FUNCTIONS[declaration["name"]]).parameters))
            self.assertLessEqual(set(schema.get("required", [])), set(schema["properties"]))
        cases = load_cases(ROOT / "data/eval_group.json", "B")
        self.assertEqual(len(cases), 10)
        self.assertEqual(len({c["id"] for c in cases}), 10)
        self.assertEqual(sum("query" in c and "turns" not in c for c in cases), 5)
        self.assertEqual(sum("turns" in c and "query" not in c for c in cases), 5)
        validate_expected_tools(cases, declarations, ROOT / "data/eval_group.json")

    def test_ticket_guard_blocks_unconfirmed_and_sensitive_writes(self):
        module = importlib.import_module("tools.create_ticket.tool")
        with tempfile.TemporaryDirectory() as directory, patch.object(module, "TICKET_DIR", Path(directory)):
            self.assertEqual(module.create_ticket("Test issue", confirmed=False)["status"], "needs_confirmation")
            self.assertEqual(module.create_ticket("password=FAKE_TEST_SECRET", confirmed=True)["error"], "restricted_sensitive_data")
            self.assertEqual(list(Path(directory).iterdir()), [])
            created = module.create_ticket("Test issue", "low", "LT-411", True)
            self.assertEqual(created["status"], "created")
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_external_identifier_rejected_before_http(self):
        with patch("tools.search_device_info.tool.requests.post") as post:
            result = search_device_info("Lenovo", "ThinkPad T14 Gen 4 LT-204 EMP-1001", "support")
            self.assertEqual(result["error"], "restricted_internal_identifier")
            post.assert_not_called()

    def test_retrieval_separates_instruction_text(self):
        kb = search_kb("print queue troubleshooting safety sample", "printing")
        policy = search_company_policy("critical", "incident_response")
        for result, field in [(kb, "content"), (policy, "facts")]:
            flagged = [hit for hit in result["results"] if hit["untrusted_text"]]
            self.assertTrue(flagged)
            for hit in flagged:
                for line in hit["untrusted_text"]:
                    self.assertNotIn(line, hit[field])

    def test_provider_error_preserves_completed_tool_evidence(self):
        class FailingProvider:
            calls = 0

            def complete(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return ModelResponse(tool_calls=[ToolCall("inspect_device", {"asset_id": "LT-411", "check": "software"})])
                raise RuntimeError("synthetic provider outage for offline test")

        result = run_model_tool_loop(provider=FailingProvider(), messages=[], tools=[], model=None, max_tool_rounds=4)
        self.assertEqual(result["status"], "provider_error")
        self.assertEqual(result["tool_events"][0]["tool"], "inspect_device")
        self.assertEqual(len(result["rounds"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
