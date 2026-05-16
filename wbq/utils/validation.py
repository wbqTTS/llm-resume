from __future__ import annotations

from typing import Any, Dict, List, Tuple

from wbq.schemas.job_details_schema import JobDetails
from wbq.utils.app_support import normalize_manual_form


class ModelOutputValidationError(ValueError):
    """Raised when an LLM response cannot be used as structured application data."""


def _model_to_dict(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def validate_job_details_payload(payload: Any) -> Dict[str, Any]:
    """Validate and normalize a job-details response from the LLM."""
    if not isinstance(payload, dict):
        raise ModelOutputValidationError("JD 解析失败：模型没有返回 JSON 对象。")

    try:
        return _model_to_dict(JobDetails(**payload))
    except Exception as exc:
        raise ModelOutputValidationError(f"JD 解析失败：模型返回字段缺失或格式不正确。{exc}") from exc


def validate_resume_payload(payload: Any) -> Dict[str, Any]:
    """Normalize resume data while keeping partial manual input usable."""
    if not isinstance(payload, dict):
        raise ModelOutputValidationError("简历解析失败：简历内容不是 JSON 对象。")

    normalized = normalize_manual_form(payload)
    normalized.setdefault("personal", {})
    for section in [
        "education",
        "work_experience",
        "projects",
        "skill_section",
        "social_practice",
        "certifications",
        "achievements",
        "research_experience",
        "teaching_experience",
        "academic_service",
    ]:
        normalized.setdefault(section, [])

    if not isinstance(normalized["personal"], dict):
        raise ModelOutputValidationError("简历解析失败：personal 字段格式不正确。")

    return normalized


def extract_section_payload(response: Any, section_name: str, fallback: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extract one optimized section from an LLM response, falling back safely."""
    analysis: Dict[str, Any] = {}
    processed_data = None

    if isinstance(response, dict):
        processed_data = response.get(section_name)
        if isinstance(response.get("analysis"), dict):
            analysis = response["analysis"]
    elif isinstance(response, list):
        processed_data = response

    if section_name == "skill_section" and isinstance(processed_data, list):
        processed_data = [item for item in processed_data if isinstance(item, dict) and item.get("skills")]

    if isinstance(processed_data, list):
        return processed_data, analysis

    return fallback, {
        "error": "LLM output parsing failed",
        "fallback": True,
        "raw_type": type(response).__name__,
    }
