import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import account_manager
from account_manager import (
    load_accounts_db,
    save_accounts_db,
    get_active_account,
    get_all_accounts,
    update_account_profile,
    switch_or_create_account,
    record_user_answer_input,
    record_interview_created,
)


class TestAccountManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = Path(tempfile.gettempdir()) / f"test_prepsense_accounts_{id(self)}.json"
        if self.temp_file.exists():
            self.temp_file.unlink()
        self.patcher = patch("account_manager._get_accounts_file", return_value=self.temp_file)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if self.temp_file.exists():
            self.temp_file.unlink()

    def test_default_account_creation(self):
        account = get_active_account()
        self.assertIsNotNone(account)
        self.assertEqual(account["stats"]["total_inputs"], 0)

    def test_switch_or_create_account(self):
        account = switch_or_create_account("john_doe", "John Doe", "Backend Engineer")
        self.assertEqual(account["id"], "john_doe")
        self.assertEqual(account["name"], "John Doe")
        self.assertEqual(account["target_role"], "Backend Engineer")

        active = get_active_account()
        self.assertEqual(active["id"], "john_doe")

    def test_get_all_accounts_and_update_profile(self):
        switch_or_create_account("cand1", "Candidate One", "Frontend Dev")
        switch_or_create_account("cand2", "Candidate Two", "Cloud Architect")

        all_acc = get_all_accounts()
        self.assertIn("cand1", all_acc)
        self.assertIn("cand2", all_acc)

        updated = update_account_profile("cand1", name="Candidate Prime", target_role="Staff Frontend")
        self.assertEqual(updated["name"], "Candidate Prime")
        self.assertEqual(updated["target_role"], "Staff Frontend")

    def test_record_user_answer_input(self):
        switch_or_create_account("alice", "Alice")
        record_user_answer_input("What is OOP?", score=8.0, company="Microsoft", user_id="alice")
        record_user_answer_input("How do you handle conflict?", score=10.0, company="Microsoft", user_id="alice")

        active = get_active_account()
        self.assertEqual(active["stats"]["total_inputs"], 2)
        self.assertEqual(active["stats"]["average_score"], 9.0)
        self.assertEqual(len(active["recent_activity"]), 2)

    def test_record_interview_created(self):
        switch_or_create_account("bob", "Bob")
        record_interview_created("Google", "SDE Intern", user_id="bob")

        active = get_active_account()
        self.assertEqual(active["stats"]["total_interviews"], 1)


if __name__ == "__main__":
    unittest.main()
