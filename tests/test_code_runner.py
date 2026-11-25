import unittest
from code_runner import run_coding_test_cases, review_code_solution, CODING_CHALLENGES


class TestCodeRunner(unittest.TestCase):
    def test_two_sum_correct_solution(self):
        code = """def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []
"""
        res = run_coding_test_cases(code, "two_sum")
        self.assertTrue(res["all_passed"])
        self.assertEqual(res["passed_count"], res["total_count"])
        self.assertIsNone(res["error"])

    def test_two_sum_buggy_solution(self):
        code = """def two_sum(nums: list[int], target: int) -> list[int]:
    return [0, 0]
"""
        res = run_coding_test_cases(code, "two_sum")
        self.assertFalse(res["all_passed"])
        self.assertGreater(len(res["results"]), 0)

    def test_syntax_error_handled_safely(self):
        code = "def two_sum(nums:): syntax error"
        res = run_coding_test_cases(code, "two_sum")
        self.assertFalse(res["all_passed"])
        self.assertIn("Compilation Error", res["error"])

    def test_missing_function_handled_safely(self):
        code = "x = 42"
        res = run_coding_test_cases(code, "two_sum")
        self.assertFalse(res["all_passed"])
        self.assertIn("not found", res["error"])

    def test_valid_parentheses_challenge(self):
        code = """def is_valid(s: str) -> bool:
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    return not stack
"""
        res = run_coding_test_cases(code, "valid_parentheses")
        self.assertTrue(res["all_passed"])

    def test_review_code_solution(self):
        code = """def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""
        exec_res = run_coding_test_cases(code, "two_sum")
        review = review_code_solution(code, "two_sum", exec_res)
        self.assertIn("O(N)", review["time_complexity"])
        self.assertGreaterEqual(review["quality_score"], 7)


if __name__ == "__main__":
    unittest.main()
