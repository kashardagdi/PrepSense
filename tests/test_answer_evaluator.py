import unittest
from answer_evaluator import (
    robust_parse_evaluation,
    _build_default_breakdown,
    _normalize_evaluation_dict,
)


class TestAnswerEvaluator(unittest.TestCase):
    def test_default_breakdown_technical(self):
        bd = _build_default_breakdown(8, "technical")
        self.assertIn("technical_accuracy", bd)
        self.assertIn("problem_solving_depth", bd)
        self.assertIn("communication_clarity", bd)
        self.assertAlmostEqual(bd["technical_accuracy"]["score"], 3.2, places=1)

    def test_default_breakdown_behavioral(self):
        bd = _build_default_breakdown(9, "behavioral")
        self.assertIn("situation_and_task", bd)
        self.assertIn("action_taken", bd)
        self.assertIn("result_and_reflection", bd)

    def test_robust_parse_evaluation_json(self):
        sample = """
        ```json
        {
            "score": 9,
            "breakdown": {
                "technical_accuracy": {"score": 4, "maximum": 4, "evidence": "Used EXPLAIN ANALYZE"},
                "problem_solving_depth": {"score": 3, "maximum": 3, "evidence": "Checked indexing"},
                "communication_clarity": {"score": 2, "maximum": 3, "evidence": "Clear flow"}
            },
            "strengths": ["Strong DB profiling knowledge"],
            "missing_points": ["Could mention vacuum analyze"],
            "suggestions": ["Test with real data volumes"]
        }
        ```
        """
        result = robust_parse_evaluation(sample, "technical")
        self.assertEqual(result["score"], 9)
        self.assertIn("breakdown", result)
        self.assertEqual(result["breakdown"]["technical_accuracy"]["score"], 4.0)
        self.assertIn("Strong DB profiling knowledge", result["strengths"])

    def test_robust_parse_fallback(self):
        result = robust_parse_evaluation("Invalid output with score: 6", "technical")
        self.assertEqual(result["score"], 6)
        self.assertIn("breakdown", result)
        self.assertIn("technical_accuracy", result["breakdown"])

    def test_heuristic_short_answer_calibrated(self):
        from answer_evaluator import evaluate_answer_heuristic
        short_ans = "Python is nice."
        result = evaluate_answer_heuristic("Explain Python", short_ans, "technical")
        self.assertLessEqual(result["score"], 4)
        self.assertTrue(any("too brief" in m.lower() for m in result["missing_points"]))

    def test_heuristic_thorough_answer_calibrated(self):
        from answer_evaluator import evaluate_answer_heuristic
        thorough_ans = (
            "In my previous project, we faced an API latency spike under heavy load. "
            "I investigated the issue using APM telemetry and discovered sequential database scans. "
            "To solve this, I designed composite indexes on filtered columns, introduced Redis caching "
            "for read-heavy routes with a 5-minute TTL, and conducted load tests using k6. "
            "This reduced p95 latency from 850ms to 95ms and handled 5x concurrent traffic without errors."
        )
        result = evaluate_answer_heuristic("Describe optimizing a system", thorough_ans, "technical")
        self.assertGreaterEqual(result["score"], 7)
        self.assertIn("breakdown", result)


if __name__ == "__main__":
    unittest.main()
