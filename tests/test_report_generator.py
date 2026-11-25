import unittest
from report_generator import build_report_html, build_report_filename


class TestReportGenerator(unittest.TestCase):
    def test_build_report_filename(self):
        account = {"name": "Mehul Sharma", "id": "mehul"}
        result = {"company_name": "Google"}
        filename = build_report_filename(account, result)
        self.assertTrue(filename.startswith("prepsense_report_mehul_sharma_google_"))
        self.assertTrue(filename.endswith(".html"))

    def test_build_report_html_minimal(self):
        account = {
            "id": "cand_test",
            "name": "Alex",
            "target_role": "Backend Engineer",
            "stats": {"total_inputs": 0, "total_interviews": 0, "average_score": 0.0, "scores_history": []},
            "recent_activity": [],
        }
        html = build_report_html(account=account)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Alex", html)
        self.assertIn("Backend Engineer", html)
        self.assertIn("PREPSENSE", html)

    def test_build_report_html_full(self):
        account = {
            "id": "kashan",
            "name": "Kashan",
            "target_role": "ML Engineer",
            "stats": {"total_inputs": 3, "total_interviews": 1, "average_score": 8.0, "scores_history": [7.0, 8.0, 9.0]},
            "recent_activity": [
                {"type": "answer_evaluated", "company": "Zerodha", "question": "Explain indexes", "score": 8, "timestamp": "2026-11-24T20:00:00"}
            ],
        }
        result = {
            "company_name": "Zerodha",
            "job_info": {"job_title": "Software Engineer"},
            "questions": [{"question": "Explain indexes in SQL", "type": "technical"}],
        }
        skill_gap_report = {
            "skill_assessments": [
                {"skill": "Python", "status": "matched", "explanation": "Demonstrated", "resume_evidence": "3 years Python", "recommendation": "None"},
                {"skill": "Docker", "status": "missing", "explanation": "Not found", "resume_evidence": "", "recommendation": "Learn Docker basics"},
            ]
        }
        evaluation_history = {
            "0_0": {
                "question": "Explain indexes in SQL",
                "question_type": "technical",
                "score": 8,
                "breakdown": {
                    "technical_accuracy": {"score": 3.5, "maximum": 4, "evidence": "Used B-Tree"},
                    "problem_solving_depth": {"score": 2.5, "maximum": 3, "evidence": "Discussed trade-offs"},
                    "communication_clarity": {"score": 2.0, "maximum": 3, "evidence": "Clear response"},
                },
            }
        }
        answer_feedback = {
            "0_0": {
                "score": 8,
                "strengths": ["Clear technical explanation"],
                "missing_points": ["Could mention p99 latency"],
            }
        }
        roadmap = {
            "phases": [
                {
                    "phase_name": "Phase 1: Foundations",
                    "goal": "Bridge missing Docker skills",
                    "milestones": [{"title": "Docker containerization tutorial", "estimated_hours": 6}],
                }
            ]
        }

        html = build_report_html(
            account=account,
            result=result,
            skill_gap_report=skill_gap_report,
            evaluation_history=evaluation_history,
            answer_feedback=answer_feedback,
            roadmap=roadmap,
        )

        self.assertIn("Kashan", html)
        self.assertIn("Zerodha", html)
        self.assertIn("Python", html)
        self.assertIn("Docker", html)
        self.assertIn("Explain indexes in SQL", html)
        self.assertIn("Phase 1: Foundations", html)
        self.assertIn("@media print", html)


if __name__ == "__main__":
    unittest.main()
