import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crm_mock_data import MOCK_CASE_ID  # noqa: E402
from mcp_server import mcp  # noqa: E402


class MCPToolRegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_four_tools_are_registered(self):
        tools = await mcp.list_tools()
        tools_by_name = {tool.name: tool for tool in tools}

        self.assertEqual(
            set(tools_by_name),
            {
                "search_documents",
                "get_case_record",
                "get_case_metadata",
                "get_error_logs",
            },
        )
        self.assertEqual(
            tools_by_name["search_documents"].input_schema["required"], ["query"]
        )
        self.assertEqual(
            tools_by_name["search_documents"].input_schema["properties"]["strategy"][
                "enum"
            ],
            ["bm25", "dense", "hybrid_rrf"],
        )
        top_k_schema = tools_by_name["search_documents"].input_schema["properties"][
            "top_k"
        ]
        self.assertEqual(top_k_schema["minimum"], 1)
        self.assertEqual(top_k_schema["maximum"], 10)
        self.assertEqual(
            tools_by_name["get_case_record"].input_schema["required"], ["case_id"]
        )
        self.assertEqual(
            tools_by_name["get_case_record"].input_schema["properties"]["case_id"][
                "const"
            ],
            MOCK_CASE_ID,
        )
        self.assertNotIn("required", tools_by_name["get_case_metadata"].input_schema)
        self.assertEqual(
            tools_by_name["get_error_logs"].input_schema["required"], ["case_id"]
        )

    async def test_registered_tools_return_structured_content(self):
        case_result = await mcp.call_tool(
            "get_case_record",
            {"case_id": MOCK_CASE_ID},
        )
        metadata_result = await mcp.call_tool("get_case_metadata", {})
        logs_result = await mcp.call_tool(
            "get_error_logs",
            {"case_id": MOCK_CASE_ID},
        )
        search_result = await mcp.call_tool(
            "search_documents",
            {"query": "Email-to-Case routing address", "top_k": 1, "strategy": "bm25"},
        )

        for result in (case_result, metadata_result, logs_result, search_result):
            self.assertFalse(result.is_error)
            self.assertIsNotNone(result.structured_content)

        self.assertEqual(case_result.structured_content["data_source"], "mock")
        self.assertEqual(case_result.structured_content["record"]["Id"], MOCK_CASE_ID)
        self.assertEqual(metadata_result.structured_content["object"]["api_name"], "Case")
        self.assertEqual(logs_result.structured_content["case_id"], MOCK_CASE_ID)
        self.assertEqual(search_result.structured_content["strategy"], "bm25")
        self.assertEqual(len(search_result.structured_content["evidence"]), 1)


if __name__ == "__main__":
    unittest.main()
