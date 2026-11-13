import unittest
from account_manager import (
    load_accounts_db,
    save_accounts_db,
    get_active_account,
    switch_or_create_account,
    record_user_answer_input,
    record_interview_created,
    _get_accounts_file,
)


class TestAccountManager(unittest.TestCase):
    def setUp(self):
        self.accounts_file = _get_accounts_file()
        if self.accounts_file.exists():
            self.accounts_file.unlink()

    def tearDown(self):
        if self.accounts_file.exists():
            self.accounts_file.unlink()

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
