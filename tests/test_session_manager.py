import unittest
from session_manager import (
    save_session_cache,
    load_session_cache,
    clear_session_cache,
    _get_cache_file,
)


class TestSessionManager(unittest.TestCase):
    def tearDown(self):
        clear_session_cache()

    def test_save_and_load_session(self):
        clear_session_cache()
        dummy_state = {
            "interview_id": 42,
            "interview_result": {
                "company_name": "Google",
                "questions": [{"question": "What is Python?", "type": "technical"}],
            },
            "skill_gap_report": {"skill_assessments": []},
            "roadmap_completed": {"p1_m1", "p2_m2"},
            "nav_history": ["Overview", "Interview Practice"],
            "candidate_answer_42_1": "My detailed drafted answer.",
            "attempt_count_42_1": 2,
        }

        saved = save_session_cache(dummy_state)
        self.assertTrue(saved)
        self.assertTrue(_get_cache_file().exists())

        loaded = load_session_cache()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["interview_id"], 42)
        self.assertEqual(loaded["interview_result"]["company_name"], "Google")
        self.assertIsInstance(loaded["roadmap_completed"], set)
        self.assertIn("p1_m1", loaded["roadmap_completed"])
        self.assertEqual(loaded["candidate_answers"].get("candidate_answer_42_1"), "My detailed drafted answer.")
        self.assertEqual(loaded["attempt_counts"].get("attempt_count_42_1"), 2)

    def test_clear_session(self):
        dummy_state = {
            "interview_result": {"company_name": "Amazon"},
        }
        save_session_cache(dummy_state)
        self.assertTrue(_get_cache_file().exists())

        cleared = clear_session_cache()
        self.assertTrue(cleared)
        self.assertFalse(_get_cache_file().exists())
        self.assertIsNone(load_session_cache())


if __name__ == "__main__":
    unittest.main()
