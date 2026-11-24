"""
PrepSense - Coding Interview Challenge Engine & Sandboxed Code Runner.

Provides curated interview coding challenges, an in-process sandboxed Python
test runner, and an automated code reviewer for time/space complexity analysis.
"""

from __future__ import annotations

import json
import re
import sys
import time
from typing import Dict, Any, List

from llm import ask_ai, extract_json_string


CODING_CHALLENGES = {
    "two_sum": {
        "id": "two_sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Arrays & Hashing",
        "description": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`. Each input has exactly one solution, and you may not use the same element twice.",
        "examples": [
            {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]"},
            {"input": "nums = [3, 2, 4], target = 6", "output": "[1, 2]"},
            {"input": "nums = [3, 3], target = 6", "output": "[0, 1]"},
        ],
        "starter_code": """def two_sum(nums: list[int], target: int) -> list[int]:
    # Write your solution below
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
""",
        "entry_point": "two_sum",
        "test_cases": [
            {"args": ([2, 7, 11, 15], 9), "expected": [0, 1]},
            {"args": ([3, 2, 4], 6), "expected": [1, 2]},
            {"args": ([3, 3], 6), "expected": [0, 1]},
            {"args": ([-1, -2, -3, -4, -5], -8), "expected": [2, 4]},
            {"args": ([10, 20, 30, 40], 70), "expected": [2, 3]},
        ],
    },
    "valid_parentheses": {
        "id": "valid_parentheses",
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "category": "Stacks & Strings",
        "description": "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. Open brackets must be closed by the same type of brackets in the correct order.",
        "examples": [
            {"input": 's = "()"', "output": "True"},
            {"input": 's = "()[]{}"', "output": "True"},
            {"input": 's = "(]"', "output": "False"},
        ],
        "starter_code": """def is_valid(s: str) -> bool:
    # Write your solution below
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
""",
        "entry_point": "is_valid",
        "test_cases": [
            {"args": ("()",), "expected": True},
            {"args": ("()[]{}",), "expected": True},
            {"args": ("(]",), "expected": False},
            {"args": ("([)]",), "expected": False},
            {"args": ("{[]}",), "expected": True},
            {"args": ("",), "expected": True},
        ],
    },
    "merge_intervals": {
        "id": "merge_intervals",
        "title": "Merge Intervals",
        "difficulty": "Medium",
        "category": "Intervals & Sorting",
        "description": "Given an array of `intervals` where `intervals[i] = [start_i, end_i]`, merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.",
        "examples": [
            {"input": "intervals = [[1,3],[2,6],[8,10],[15,18]]", "output": "[[1,6],[8,10],[15,18]]"},
            {"input": "intervals = [[1,4],[4,5]]", "output": "[[1,5]]"},
        ],
        "starter_code": """def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    # Write your solution below
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        prev = merged[-1]
        if current[0] <= prev[1]:
            prev[1] = max(prev[1], current[1])
        else:
            merged.append(current)
    return merged
""",
        "entry_point": "merge_intervals",
        "test_cases": [
            {"args": ([[1, 3], [2, 6], [8, 10], [15, 18]],), "expected": [[1, 6], [8, 10], [15, 18]]},
            {"args": ([[1, 4], [4, 5]],), "expected": [[1, 5]]},
            {"args": ([[1, 4], [0, 4]],), "expected": [[0, 4]]},
            {"args": ([[1, 4], [2, 3]],), "expected": [[1, 4]]},
            {"args": ([],), "expected": []},
        ],
    },
    "max_profit": {
        "id": "max_profit",
        "title": "Best Time to Buy and Sell Stock",
        "difficulty": "Easy",
        "category": "Arrays & Greedy",
        "description": "You are given an array `prices` where `prices[i]` is the price of a given stock on the $i^{\\text{th}}$ day. You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock. Return the maximum profit you can achieve.",
        "examples": [
            {"input": "prices = [7, 1, 5, 3, 6, 4]", "output": "5 (buy at 1, sell at 6)"},
            {"input": "prices = [7, 6, 4, 3, 1]", "output": "0 (no profit)"},
        ],
        "starter_code": """def max_profit(prices: list[int]) -> int:
    # Write your solution below
    min_price = float('inf')
    max_p = 0
    for price in prices:
        if price < min_price:
            min_price = price
        elif price - min_price > max_p:
            max_p = price - min_price
    return max_p
""",
        "entry_point": "max_profit",
        "test_cases": [
            {"args": ([7, 1, 5, 3, 6, 4],), "expected": 5},
            {"args": ([7, 6, 4, 3, 1],), "expected": 0},
            {"args": ([2, 4, 1],), "expected": 2},
            {"args": ([1, 2],), "expected": 1},
        ],
    },
    "binary_search": {
        "id": "binary_search",
        "title": "Binary Search",
        "difficulty": "Easy",
        "category": "Binary Search",
        "description": "Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, then return its index. Otherwise, return -1 in $O(\\log n)$ runtime complexity.",
        "examples": [
            {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"},
            {"input": "nums = [-1,0,3,5,9,12], target = 2", "output": "-1"},
        ],
        "starter_code": """def search(nums: list[int], target: int) -> int:
    # Write your solution below
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
""",
        "entry_point": "search",
        "test_cases": [
            {"args": ([-1, 0, 3, 5, 9, 12], 9), "expected": 4},
            {"args": ([-1, 0, 3, 5, 9, 12], 2), "expected": -1},
            {"args": ([5], 5), "expected": 0},
            {"args": ([5], -5), "expected": -1},
        ],
    },
}


def run_coding_test_cases(code_str: str, challenge_id: str) -> Dict[str, Any]:
    """
    Execute user's code against challenge test cases in an in-process sandboxed namespace.
    """
    challenge = CODING_CHALLENGES.get(challenge_id)
    if not challenge:
        return {"error": f"Unknown challenge: {challenge_id}", "all_passed": False, "results": []}

    entry_point = challenge["entry_point"]
    test_cases = challenge["test_cases"]

    # Restricted environment
    safe_globals: Dict[str, Any] = {
        "__builtins__": {
            "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
            "chr": chr, "dict": dict, "divmod": divmod, "enumerate": enumerate,
            "filter": filter, "float": float, "format": format, "frozenset": frozenset,
            "hash": hash, "hex": hex, "int": int, "isinstance": isinstance,
            "iter": iter, "len": len, "list": list, "map": map, "max": max,
            "min": min, "next": next, "oct": oct, "ord": ord, "pow": pow,
            "print": print, "range": range, "reversed": reversed, "round": round,
            "set": set, "slice": slice, "sorted": sorted, "str": str, "sum": sum,
            "tuple": tuple, "zip": zip,
        }
    }

    # Pre-populate safe modules
    import math, collections, heapq, itertools, bisect, re
    safe_globals.update({
        "math": math, "collections": collections, "heapq": heapq,
        "itertools": itertools, "bisect": bisect, "re": re,
    })

    # Compile user's submission
    try:
        compiled = compile(code_str, "<candidate_solution>", "exec")
        exec(compiled, safe_globals)
    except Exception as e:
        return {
            "error": f"Compilation Error: {type(e).__name__}: {e}",
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "results": [],
        }

    func = safe_globals.get(entry_point)
    if not callable(func):
        return {
            "error": f"Function '{entry_point}' not found or not callable in your code.",
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "results": [],
        }

    results: List[Dict[str, Any]] = []
    passed_count = 0

    for idx, tc in enumerate(test_cases, 1):
        args = tc["args"]
        expected = tc["expected"]

        t0 = time.perf_counter()
        try:
            got = func(*args)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)

            # Check correctness (for Two Sum, order of pair or sorted order can match)
            if challenge_id == "two_sum" and isinstance(got, list) and isinstance(expected, list):
                is_correct = sorted(got) == sorted(expected)
            else:
                is_correct = (got == expected)

            if is_correct:
                passed_count += 1

            results.append({
                "test_case": idx,
                "passed": is_correct,
                "input": str(args if len(args) > 1 else args[0]),
                "expected": str(expected),
                "got": str(got),
                "runtime_ms": elapsed_ms,
                "error": None,
            })
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
            results.append({
                "test_case": idx,
                "passed": False,
                "input": str(args if len(args) > 1 else args[0]),
                "expected": str(expected),
                "got": "Exception",
                "runtime_ms": elapsed_ms,
                "error": f"{type(e).__name__}: {e}",
            })

    return {
        "error": None,
        "all_passed": (passed_count == len(test_cases)),
        "passed_count": passed_count,
        "total_count": len(test_cases),
        "results": results,
    }


def review_code_solution(
    code_str: str,
    challenge_id: str,
    execution_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate senior-level code review for algorithm complexity, readability, and edge cases.
    """
    challenge = CODING_CHALLENGES.get(challenge_id, {})
    title = challenge.get("title", challenge_id)

    prompt = f"""You are a staff software engineer reviewing an interview code submission for '{title}'.
Analyze the solution's algorithmic complexity, edge cases, and code cleanliness.

CANDIDATE CODE:
{code_str[:600]}

TEST STATUS:
Passed: {execution_result.get('passed_count')}/{execution_result.get('total_count')}

Return valid JSON with:
{{
  "time_complexity": "O(N), O(N log N), O(N^2), etc.",
  "space_complexity": "O(1), O(N), etc.",
  "quality_score": 8, // integer 1-10
  "strengths": ["Clean idiomatic python", "Handles empty input"],
  "improvements": ["Could optimize space", "Add type annotations"],
  "overall_verdict": "2-sentence summary of interview readiness for this problem."
}}"""

    try:
        response = ask_ai(prompt, format="json")
        cleaned = extract_json_string(response)
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and parsed.get("time_complexity"):
            return {
                "time_complexity": str(parsed.get("time_complexity", "O(N)")),
                "space_complexity": str(parsed.get("space_complexity", "O(1)")),
                "quality_score": int(parsed.get("quality_score", 8)),
                "strengths": list(parsed.get("strengths", ["Correct implementation", "Handles base cases"])),
                "improvements": list(parsed.get("improvements", ["Consider further space optimization"])),
                "overall_verdict": str(parsed.get("overall_verdict", "Solid implementation with good algorithmic clarity.")),
            }
    except Exception as e:
        print(f"[CodeReview] LLM unavailable ({e}). Using heuristic code reviewer.")

    # Rule-based fallback code analysis
    return _heuristic_code_review(code_str, challenge_id, execution_result)


def _heuristic_code_review(code_str: str, challenge_id: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
    all_passed = execution_result.get("all_passed", False)
    passed_cnt = execution_result.get("passed_count", 0)
    total_cnt = execution_result.get("total_count", 1)

    # Complexity estimation heuristics
    has_nested_loops = bool(re.search(r"for\s+.*:\s*\n.*for\s+.*:", code_str))
    has_hashmap = bool(re.search(r"(\{\}|dict\(\)|seen|mapping|counter)", code_str, re.IGNORECASE))
    has_sort = bool(re.search(r"(\.sort\(|sorted\()", code_str))

    if challenge_id == "two_sum":
        time_c = "O(N)" if has_hashmap else ("O(N^2)" if has_nested_loops else "O(N)")
        space_c = "O(N)" if has_hashmap else "O(1)"
    elif challenge_id == "merge_intervals":
        time_c = "O(N log N)" if has_sort else "O(N)"
        space_c = "O(N)"
    elif challenge_id == "binary_search":
        time_c = "O(log N)"
        space_c = "O(1)"
    else:
        time_c = "O(N log N)" if has_sort else ("O(N^2)" if has_nested_loops else "O(N)")
        space_c = "O(N)" if has_hashmap else "O(1)"

    base_score = 9 if all_passed else (6 if passed_cnt > 0 else 4)
    if has_nested_loops and challenge_id in ["two_sum"]:
        base_score -= 2

    strengths = []
    if all_passed:
        strengths.append(f"Successfully passed all {total_cnt} test cases.")
    if has_hashmap and challenge_id in ["two_sum", "valid_parentheses"]:
        strengths.append("Optimal use of hash table/dictionary for O(1) lookups.")
    if not has_nested_loops:
        strengths.append("Avoided brute-force quadratic loops.")

    improvements = []
    if not all_passed:
        improvements.append(f"Failed {total_cnt - passed_cnt} edge case test cases. Review zero-length or boundary inputs.")
    if has_nested_loops:
        improvements.append("Replace nested iterations with a dictionary to reduce time complexity.")
    if "try:" not in code_str and "assert" not in code_str:
        improvements.append("Consider defensive input validation against invalid types or None.")

    verdict = (
        f"Solid interview solution achieving {time_c} runtime. Demonstrates good command of data structures."
        if all_passed
        else f"Solution passed {passed_cnt}/{total_cnt} tests. Focus on boundary condition handling before submitting in a live interview."
    )

    return {
        "time_complexity": time_c,
        "space_complexity": space_c,
        "quality_score": base_score,
        "strengths": strengths or ["Idiomatic Python syntax"],
        "improvements": improvements or ["Add docstring and type hints"],
        "overall_verdict": verdict,
    }
