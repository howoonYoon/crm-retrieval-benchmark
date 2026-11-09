import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crm_mock_data import (  # noqa: E402
    MOCK_CASE_ID,
    get_case_metadata,
    get_case_record,
    get_error_logs,
)


class CRMMockDataTests(unittest.TestCase):
    def test_case_record_is_explicitly_marked_as_mock(self):
        response = get_case_record(MOCK_CASE_ID)

        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["data_source"], "mock")
        self.assertTrue(response["is_mock"])
        self.assertEqual(response["record"]["Id"], MOCK_CASE_ID)

    def test_case_metadata_describes_case_fields(self):
        response = get_case_metadata()
        field_names = {field["name"] for field in response["object"]["fields"]}

        self.assertEqual(response["object"]["api_name"], "Case")
        self.assertIn("Status", field_names)
        self.assertIn("AccountId", field_names)

    def test_error_logs_are_filtered_by_case_id(self):
        response = get_error_logs(MOCK_CASE_ID)

        self.assertEqual(response["case_id"], MOCK_CASE_ID)
        self.assertEqual(response["count"], len(response["logs"]))
        self.assertGreater(response["count"], 0)

    def test_unknown_case_id_is_rejected(self):
        for function in (get_case_record, get_error_logs):
            with self.subTest(function=function.__name__):
                with self.assertRaises(ValueError):
                    function("500000000000999AAA")


if __name__ == "__main__":
    unittest.main()
