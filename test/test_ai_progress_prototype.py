import unittest
from pathlib import Path
import sys

PROTOTYPE_DIR = Path(__file__).resolve().parent / "prototype_ai_progress"
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_DIR))

from progress_callback_prototype import (
    build_progress_event,
    run_parallel_sections,
)


class TestAIProgressPrototype(unittest.TestCase):
    def test_callback_receives_completed_sections(self):
        configs = [
            {
                "section_name": "work_experience",
                "delay": 0.03,
                "data": [{"role": "Backend Engineer"}],
                "analysis": {
                    "keywords_matched": ["Python", "Redis"],
                    "optimization_strategy": "强化并发与缓存经验",
                    "gap_analysis": "量化结果表达不足",
                },
            },
            {
                "section_name": "projects",
                "delay": 0.01,
                "data": [{"name": "Hospital Platform"}],
                "analysis": {"skipped": True, "reason": "User configuration"},
            },
            {
                "section_name": "education",
                "delay": 0.02,
                "data": [{"school": "FZU"}],
                "analysis": {"fallback": True, "error": "LLM output parsing failed"},
            },
        ]

        callback_events = []

        def section_callback(section_name, data, analysis):
            callback_events.append(build_progress_event(section_name, data, analysis))

        results, analyses = run_parallel_sections(configs, section_callback=section_callback)

        self.assertEqual(set(results.keys()), {"work_experience", "projects", "education"})
        self.assertEqual(set(analyses.keys()), {"work_experience", "projects", "education"})
        self.assertEqual(len(callback_events), 3)

        status_map = {item["section_name"]: item["status"] for item in callback_events}
        self.assertEqual(status_map["work_experience"], "optimized")
        self.assertEqual(status_map["projects"], "skipped")
        self.assertEqual(status_map["education"], "fallback")

        optimized_event = next(item for item in callback_events if item["section_name"] == "work_experience")
        self.assertEqual(optimized_event["keywords_matched"], ["Python", "Redis"])
        self.assertEqual(optimized_event["optimization_strategy"], "强化并发与缓存经验")
        self.assertEqual(optimized_event["gap_analysis"], "量化结果表达不足")


if __name__ == "__main__":
    unittest.main()
