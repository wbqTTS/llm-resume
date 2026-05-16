from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ResumeInputService:
    model: Any

    def parse(self, source_path: str) -> Dict[str, Any]:
        return self.model.user_data_extraction(source_path)


@dataclass
class JobExtractionService:
    model: Any

    def extract(self, url: str | None = None, text: str | None = None, user_id: str | None = None) -> Tuple[Dict[str, Any] | None, str | None]:
        return self.model.job_details_extraction(url=url, job_site_content=text, user_id=user_id)


@dataclass
class ResumeBuildService:
    model: Any

    def build(
        self,
        job_details: Dict[str, Any],
        user_data: Dict[str, Any],
        template_style: str = "classic",
        optimize_fields: List[str] | None = None,
        user_id: str | None = None,
    ) -> Tuple[str | None, Dict[str, Any]]:
        return self.model.resume_builder(
            job_details=job_details,
            user_data=user_data,
            template_style=template_style,
            optimize_fields=optimize_fields,
            user_id=user_id,
        )


@dataclass
class CoverLetterService:
    model: Any

    def generate(
        self,
        job_details: Dict[str, Any],
        user_data: Dict[str, Any],
        need_pdf: bool = True,
        user_id: str | None = None,
    ) -> Tuple[str | None, str | None]:
        return self.model.cover_letter_generator(
            job_details=job_details,
            user_data=user_data,
            need_pdf=need_pdf,
            user_id=user_id,
        )
