import unittest
from adaptive_followup import generate_adaptive_followup, _generate_heuristic_followup


class TestAdaptiveFollowup(unittest.TestCase):
    def test_empty_question_raises_value_error(self):
        with self.assertRaises(ValueError):
            generate_adaptive_followup("", "Answer")

    def test_empty_answer_prompts_for_input(self):
        res = generate_adaptive_followup("What is Python?", "")
        self.assertEqual(res["probe_focus"], "Initial Answer Required")

    def test_technical_caching_probe(self):
        answer = "We used Redis cache to speed up read queries and lower database load."
        res = _generate_heuristic_followup("How did you scale the app?", answer, "technical")
        self.assertIn("invalidation", res["followup_question"].lower())
        self.assertIn("Cache Invalidation", res["probe_focus"])

    def test_technical_database_probe(self):
        answer = "I optimized PostgreSQL indexes and normalized the relational database schema."
        res = _generate_heuristic_followup("Describe your DB design.", answer, "technical")
        self.assertIn("sharding", res["followup_question"].lower())
        self.assertIn("Database Scalability", res["probe_focus"])

    def test_behavioral_conflict_probe(self):
        answer = "I had a disagreement with the product manager regarding API deadlines, but we aligned."
        res = _generate_heuristic_followup("Tell me about a conflict.", answer, "behavioral")
        self.assertIn("interpersonal", res["followup_question"].lower())
        self.assertIn("Conflict Resolution", res["probe_focus"])


if __name__ == "__main__":
    unittest.main()
