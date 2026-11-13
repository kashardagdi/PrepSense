import json
import unittest
from unittest.mock import patch

from skill_gap_analyzer import (
    extract_required_skills,
    validate_skill_gap_report,
    analyze_skill_gap,
)


class TestSkillGapAnalyzer(unittest.TestCase):

    def setUp(self):
        self.resume_text = (
            "Developed a student project using Python "
            "to process and analyse data. "
            "Docker is listed under technical skills."
        )

        self.job_info = {
            "job_title": "Backend Developer Intern",
            "technical_skills": ["Python", "FastAPI"],
            "tools_and_technologies": ["Docker"]
        }

    def test_extract_required_skills(self):
        skills = extract_required_skills(self.job_info)

        self.assertEqual(len(skills), 3)
        self.assertEqual(skills[0]["skill"], "Python")
        self.assertEqual(skills[0]["category"], "technical")

    def test_valid_skill_gap_report(self):
        report = {
            "skill_assessments": [
                {
                    "skill": "Python",
                    "category": "technical",
                    "status": "matched",
                    "resume_evidence": "using Python",
                    "reason": "Practical project experience found."
                },
                {
                    "skill": "FastAPI",
                    "category": "technical",
                    "status": "missing",
                    "resume_evidence": None,
                    "reason": "No evidence found."
                },
                {
                    "skill": "Docker",
                    "category": "tool",
                    "status": "partial",
                    "resume_evidence": "Docker is listed under technical skills",
                    "reason": "Listed familiarity without project evidence."
                }
            ],
            "recommendations": [
                {
                    "skill": "FastAPI",
                    "action": "Build a REST API project."
                },
                {
                    "skill": "Docker",
                    "action": "Practise containerising an application."
                }
            ]
        }

        result = validate_skill_gap_report(
            report,
            extract_required_skills(self.job_info),
            self.resume_text
        )

        self.assertEqual(len(result["skill_assessments"]), 3)
        self.assertEqual(len(result["recommendations"]), 2)

    def test_rejects_fabricated_resume_evidence(self):
        report = {
            "skill_assessments": [
                {
                    "skill": "Python",
                    "category": "technical",
                    "status": "matched",
                    "resume_evidence": "Developed five enterprise applications",
                    "reason": "Practical experience found."
                }
            ],
            "recommendations": []
        }

        with self.assertRaises(ValueError):
            validate_skill_gap_report(
                report,
                [{"skill": "Python", "category": "technical"}],
                self.resume_text
            )

    @patch("skill_gap_analyzer.ask_ai")
    def test_analyze_skill_gap(self, mock_ask_ai):
        response = {
            "skill_assessments": [
                {
                    "skill": "Python",
                    "category": "technical",
                    "status": "matched",
                    "resume_evidence": "using Python",
                    "reason": "Project experience found."
                },
                {
                    "skill": "FastAPI",
                    "category": "technical",
                    "status": "missing",
                    "resume_evidence": None,
                    "reason": "No evidence found."
                },
                {
                    "skill": "Docker",
                    "category": "tool",
                    "status": "partial",
                    "resume_evidence": "Docker is listed under technical skills",
                    "reason": "Listed but no practical use demonstrated."
                }
            ],
            "recommendations": [
                {
                    "skill": "FastAPI",
                    "action": "Build a REST API project."
                }
            ]
        }

        mock_ask_ai.return_value = json.dumps(response)

        result = analyze_skill_gap(
            self.resume_text,
            self.job_info
        )

        self.assertEqual(len(result["skill_assessments"]), 3)
        mock_ask_ai.assert_called_once()


if __name__ == "__main__":
    unittest.main()