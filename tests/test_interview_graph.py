import unittest
from unittest.mock import patch

from agents.graph import create_interview_graph


class TestInterviewGraph(unittest.TestCase):

    def test_skill_gap_report_flows_through_graph(self):

        expected_report = {
            "skill_assessments": [
                {
                    "skill": "Python",
                    "category": "technical",
                    "status": "matched",
                    "resume_evidence": "Built pipelines using Python",
                    "reason": "Practical Python experience."
                }
            ],
            "recommendations": []
        }

        executed_nodes = []

        # Mock resume extraction
        def fake_extract_resume(state):
            executed_nodes.append("extract_resume")
            return {
                "resume_text": "Built pipelines using Python."
            }

        # Mock company research
        def fake_research_company(state):
            executed_nodes.append("research_company")
            return {
                "company_research": "Company profile"
            }

        # Mock job parsing
        def fake_parse_job(state):
            executed_nodes.append("parse_job")
            return {
                "job_info": {
                    "job_title": "Backend Developer Intern",
                    "technical_skills": ["Python"]
                }
            }

        # Mock skill gap analysis
        def fake_analyze_skill_gap(state):
            executed_nodes.append("analyze_skill_gap")

            self.assertIn("resume_text", state)
            self.assertIn("job_info", state)

            return {
                "skill_gap_report": expected_report
            }

        # Mock question generation
        def fake_generate_questions(state):
            executed_nodes.append("generate_questions")

            self.assertEqual(
                state["skill_gap_report"],
                expected_report
            )

            return {
                "questions": ["Sample interview question"]
            }

        # Mock question validation
        def fake_validate_questions(state):
            executed_nodes.append("validate_questions")

            self.assertEqual(
                state["skill_gap_report"],
                expected_report
            )

            return {
                "questions_validated": True,
                "current_step": "interview_ready"
            }

        # Replace real nodes with lightweight test functions
        with patch.multiple(
            "agents.graph",
            extract_resume_node=fake_extract_resume,
            research_company_node=fake_research_company,
            parse_job_node=fake_parse_job,
            analyze_skill_gap_node=fake_analyze_skill_gap,
            generate_questions_node=fake_generate_questions,
            validate_questions_node=fake_validate_questions,
        ):

            graph = create_interview_graph()

            result = graph.invoke({
                "company_name": "Example Company",
                "job_description": "Backend Developer Intern",
                "resume_pdf": None
            })

        expected_order = [
            "extract_resume",
            "research_company",
            "parse_job",
            "analyze_skill_gap",
            "generate_questions",
            "validate_questions"
        ]

        self.assertEqual(executed_nodes, expected_order)

        self.assertEqual(
            result["skill_gap_report"],
            expected_report
        )

        self.assertTrue(result["questions_validated"])


if __name__ == "__main__":
    unittest.main()