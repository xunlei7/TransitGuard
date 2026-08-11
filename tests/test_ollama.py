import json
import unittest
from unittest.mock import patch

from transitguard.domain import Intent
from transitguard.ollama import OllamaQuestionParser


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        parsed = {"intent": "next_arrival", "route_id": "7", "stop_id": "725N"}
        return json.dumps({"response": json.dumps(parsed)}).encode("utf-8")


class OllamaParserTests(unittest.TestCase):
    @patch("urllib.request.urlopen", return_value=_Response())
    def test_validates_structured_parser_output(self, _mock_urlopen):
        parsed = OllamaQuestionParser()("How long until the next 7 train?")
        self.assertEqual(parsed.intent, Intent.NEXT_ARRIVAL)
        self.assertEqual(parsed.route_id, "7")
        self.assertEqual(parsed.stop_id, "725N")


if __name__ == "__main__":
    unittest.main()

