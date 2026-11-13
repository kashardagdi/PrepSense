import unittest
from roadmap_generator import (
    generate_learning_roadmap,
    roadmap_to_markdown,
    _repair_truncated_json,
    _extract_json,
)


class TestRoadmapGenerator(unittest.TestCase):
    def setUp(self):
        self.sample_skill_gap_report = {
            "skill_assessments": [
                {
                    "skill": "Python",
                    "status": "matched",
                    "importance": "critical",
                    "reason": "Found on resume.",
                    "resume_evidence": "Extensive experience in Python.",
                    "recommendation": "Maintain proficiency.",
                },
                {
                    "skill": "SQL",
                    "status": "partial",
                    "importance": "critical",
                    "reason": "Mentioned basic SQL only.",
                    "resume_evidence": "Basic queries.",
                    "recommendation": "Practice complex joins, indexing and query optimization.",
                },
                {
                    "skill": "Docker",
                    "status": "missing",
                    "importance": "critical",
                    "reason": "No containerization experience found.",
                    "resume_evidence": "Not found in resume text.",
                    "recommendation": "Build and run multi-container applications with Docker Compose.",
                },
            ],
            "recommendations": [
                {"skill": "SQL", "action": "Practice complex joins and query optimization."},
                {"skill": "Docker", "action": "Containerize a full-stack application."},
            ],
        }

        self.sample_job_info = {
            "role": "Software Development Engineer (SDE) Intern",
            "required_skills": ["Python", "SQL", "Docker"],
            "tools": ["Git"],
        }

    def test_rule_based_fallback_generation(self):
        roadmap = generate_learning_roadmap(
            skill_gap_report=self.sample_skill_gap_report,
            job_info=self.sample_job_info,
            company_name="Amazon",
            timeline_weeks=4,
            use_llm=False,
        )

        self.assertIsInstance(roadmap, dict)
        self.assertEqual(roadmap["target_role"], "Software Development Engineer (SDE) Intern")
        self.assertEqual(roadmap["company_name"], "Amazon")
        self.assertEqual(roadmap["timeline_weeks"], 4)
        self.assertIn("readiness_score", roadmap)
        self.assertGreaterEqual(roadmap["readiness_score"], 0)
        self.assertLessEqual(roadmap["readiness_score"], 100)

        phases = roadmap.get("phases", [])
        self.assertEqual(len(phases), 3)

        # Check phase 1 includes missing skill Docker
        p1 = phases[0]
        p1_skills = [m["skill"].lower() for m in p1["milestones"]]
        self.assertIn("docker", p1_skills)

        # Check phase 2 includes partial skill SQL
        p2 = phases[1]
        p2_skills = [m["skill"].lower() for m in p2["milestones"]]
        self.assertIn("sql", p2_skills)

        # Check milestones contain resources and checkpoints
        for p in phases:
            for m in p["milestones"]:
                self.assertIn("resource", m)
                self.assertIn("interview_check", m)
                self.assertIn("project_or_exercise", m)

    def test_json_repair_and_extract(self):
        truncated = '{"summary": "Test summary", "phases": [{"phase_number": 1, "milestones": [{"skill": "Docker"'
        repaired = _repair_truncated_json(truncated)
        parsed = _extract_json(repaired)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.get("summary"), "Test summary")

    def test_roadmap_to_markdown_formatting(self):
        roadmap = generate_learning_roadmap(
            skill_gap_report=self.sample_skill_gap_report,
            job_info=self.sample_job_info,
            company_name="Amazon",
            timeline_weeks=4,
            use_llm=False,
        )
        md = roadmap_to_markdown(roadmap)
        self.assertIn("# Personalized Learning Roadmap", md)
        self.assertIn("Software Development Engineer (SDE) Intern", md)
        self.assertIn("Amazon", md)
        self.assertIn("Docker", md)
        self.assertIn("SQL", md)


if __name__ == "__main__":
    unittest.main()
