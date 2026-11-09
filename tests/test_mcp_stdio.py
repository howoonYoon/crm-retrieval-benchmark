import json
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_TEST_PATH = PROJECT_ROOT / "scripts" / "mcp_smoke_test.py"


class MCPStdioSmokeTests(unittest.TestCase):
    def test_client_connects_to_local_stdio_server(self):
        completed = subprocess.run(
            [sys.executable, str(SMOKE_TEST_PATH)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["initialize"]["server_name"],
            "salesforce-crm-troubleshooting",
        )
        self.assertTrue(result["initialize"]["server_version"])
        self.assertTrue(result["initialize"]["protocol_version"])
        self.assertEqual(len(result["tools_list"]), 4)
        self.assertTrue(all(result["schema_checks"].values()))
        self.assertTrue(all(result["invalid_args"].values()))
        self.assertTrue(all(result["mock_checks"].values()))
        self.assertEqual(result["call_timeout_seconds"], 20)
        self.assertIn("Starting MCP server over stdio", completed.stderr)


if __name__ == "__main__":
    unittest.main()
