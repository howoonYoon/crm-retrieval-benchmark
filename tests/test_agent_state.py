import unittest
from langchain_core.messages import HumanMessage

from agent.state import AgentState
class AgentStateTests(unittest.TestCase):
    def test_initial_state_has_no_tool_calls(self):
        state: AgentState = {
            "messages":[
                HumanMessage(content='Case 12345 오류를 분석해줘')
            ],
            "case_id": None,
            "evidence": [],
            "tool_calls": [],
            "attempted_calls": set(),
            "answer": None,
        }

        self.assertEqual(state["tool_calls"], [])
        self.assertIsNone(state["case_id"])


if __name__ == "__main__":
    unittest.main()