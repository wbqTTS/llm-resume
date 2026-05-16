from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass


def clean_path_part(text: str, fallback: str = "untitled") -> str:
    if not text or not isinstance(text, str):
        return fallback
    cleaned = re.sub(r"[^\u4e00-\u9fff\u3400-\u4dbfa-zA-Z0-9]+", "", text)
    return cleaned or fallback


@dataclass(frozen=True)
class AppPathManager:
    """Centralized path builder for uploads, generated outputs and template assets."""

    project_root: str
    uploads_dir: str = "uploads"
    output_dir: str = "output"
    template_dir: str = os.path.join("wbq", "templates")

    @classmethod
    def from_cwd(cls, cwd: str | None = None) -> "AppPathManager":
        return cls(project_root=os.path.abspath(cwd or os.getcwd()))

    def uploads_path(self, *parts: str) -> str:
        return self._join_and_create(self.uploads_dir, *parts)

    def output_path(self, *parts: str) -> str:
        return self._join_and_create(self.output_dir, *parts)

    def template_path(self, *parts: str) -> str:
        return os.path.join(self.project_root, self.template_dir, *parts)

    def run_dir(self, job_details: dict, user_id: str | None = None, timestamp: str | None = None) -> str:
        company = clean_path_part(job_details.get("company_name", ""), "Jobs")
        run_user = str(user_id or "unknown")
        run_timestamp = str(timestamp or int(time.time()))
        return self.output_path(company, run_user, run_timestamp)

    def job_document_path(
        self,
        job_details: dict,
        document_type: str,
        user_id: str | None = None,
        timestamp: str | None = None,
    ) -> str:
        run_dir = self.run_dir(job_details, user_id=user_id, timestamp=timestamp)
        company = clean_path_part(job_details.get("company_name", ""), "Jobs")
        title = clean_path_part(job_details.get("job_title", ""), "Position")[:30]
        stem = f"{company}_{title}"
        suffix_map = {
            "jd": "_JD.json",
            "resume": "_resume.json",
            "cv": "_cv.txt",
        }
        return os.path.join(run_dir, stem + suffix_map.get(document_type, "_"))

    def _join_and_create(self, base: str, *parts: str) -> str:
        path = os.path.join(self.project_root, base, *parts)
        target_dir = path if not os.path.splitext(path)[1] else os.path.dirname(path)
        os.makedirs(target_dir, exist_ok=True)
        return path
