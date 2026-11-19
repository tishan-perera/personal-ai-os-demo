import unittest

from atrium.prompts import DEMO_PROMPTS
from atrium.router import route_request


class RouterTests(unittest.TestCase):
    def test_scripted_prompts_hit_the_expected_desk(self) -> None:
        for label, text, seat_id, _proposal in DEMO_PROMPTS:
            with self.subTest(label=label):
                route = route_request(text)
                self.assertEqual(route.seat_id, seat_id)
                self.assertGreater(route.score, 0)

    def test_greeting_stays_with_the_chief(self) -> None:
        route = route_request("Hello there")
        self.assertEqual(route.seat_id, "chief")
        self.assertEqual(route.score, 0)
        self.assertIn("Mara Quinn", route.reason)

    def test_tie_stays_with_the_chief(self) -> None:
        route = route_request("pay the post")
        self.assertEqual(route.seat_id, "chief")
        self.assertIn("tied", route.reason)
        self.assertIn("Content", route.reason)
        self.assertIn("Finance", route.reason)

    def test_matching_is_case_insensitive(self) -> None:
        route = route_request("SUMMARIZE THE FICTIONAL INBOX")
        self.assertEqual(route.seat_id, "mail")


if __name__ == "__main__":
    unittest.main()
