import unittest
from unittest.mock import patch

from agents.nodes import analyze_skill_gap_node


class TestSkillGapNode(unittest.TestCase):

    @patch("agents.nodes.analyze_skill_gap")
    def test_analyze_skill_gap_node(self, mock_analyzer):

        resume_text = "Built data pipelines using Python."
        job_info = {
            "job_title": "Backend Developer Intern",
            "technical_skills": ["Python", "FastAPI"]
        }

        expected_report = {
            "skill_assessments": [
                {
                    "skill": "Python",
                    "category": "technical",
                    "status": "matched",
                    "resume_evidence": "using Python",
                    "reason": "Practical Python experience."
                }
            ],
            "recommendations": []
        }

        mock_analyzer.return_value = expected_report

        state = {
            "resume_text": resume_text,
            "job_info": job_info
        }

        result = analyze_skill_gap_node(state)

        mock_analyzer.assert_called_once_with(
            resume_text=resume_text,
            job_info=job_info
        )

        self.assertEqual(
            result["skill_gap_report"],
            expected_report
        )

        self.assertEqual(
            result["current_step"],
            "skill_gap_analyzed"
        )

    def test_empty_resume_raises_error(self):

        state = {
            "resume_text": "",
            "job_info": {"technical_skills": ["Python"]}
        }

        with self.assertRaises(ValueError):
            analyze_skill_gap_node(state)


if __name__ == "__main__":
    unittest.main()