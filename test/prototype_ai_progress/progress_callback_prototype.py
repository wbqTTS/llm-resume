from __future__ import annotations

import concurrent.futures
import time


def _fake_section_worker(config: dict):
    time.sleep(config.get("delay", 0.01))
    return config["section_name"], config.get("data"), config.get("analysis")


def run_parallel_sections(configs: list[dict], section_callback=None):
    results = {}
    analyses = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_section = {executor.submit(_fake_section_worker, cfg): cfg for cfg in configs}

        for future in concurrent.futures.as_completed(future_to_section):
            section_name, data, analysis = future.result()

            if data is not None:
                results[section_name] = data
                if analysis:
                    analyses[section_name] = analysis
                if section_callback:
                    section_callback(section_name, data, analysis)

    return results, analyses


def build_progress_event(section_name: str, data, analysis: dict | None) -> dict:
    analysis = analysis or {}
    if analysis.get("skipped"):
        status = "skipped"
    elif analysis.get("fallback"):
        status = "fallback"
    else:
        status = "optimized"

    return {
        "section_name": section_name,
        "has_data": data is not None,
        "status": status,
        "keywords_matched": analysis.get("keywords_matched", []),
        "optimization_strategy": analysis.get("optimization_strategy", ""),
        "gap_analysis": analysis.get("gap_analysis", ""),
        "error": analysis.get("error", ""),
    }
