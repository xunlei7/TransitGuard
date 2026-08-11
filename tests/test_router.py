import unittest

from transitguard.domain import Intent
from transitguard.router import parse_question


class RouterTests(unittest.TestCase):
    def test_lettered_route_status(self):
        parsed = parse_question("Is the A train delayed?")
        self.assertEqual(parsed.intent, Intent.SERVICE_STATUS)
        self.assertEqual(parsed.route_id, "A")

    def test_numbered_route_arrival(self):
        parsed = parse_question("When is the next 7 train?", stop_id="725N")
        self.assertEqual(parsed.intent, Intent.NEXT_ARRIVAL)
        self.assertEqual(parsed.route_id, "7")
        self.assertEqual(parsed.stop_id, "725N")

    def test_does_not_treat_article_as_a_train(self):
        parsed = parse_question("Is a train delayed?")
        self.assertIsNone(parsed.route_id)

    def test_rejects_out_of_scope_question(self):
        parsed = parse_question("Who designed Grand Central Terminal?")
        self.assertEqual(parsed.intent, Intent.UNSUPPORTED)


if __name__ == "__main__":
    unittest.main()

