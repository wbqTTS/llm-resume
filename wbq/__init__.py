# zlm/__init__.py
"""
 wbq(Job-LLM) Package.
AI-driven resume customization and job application automation.
"""

# 1. 版本信息 (可选)
__version__ = "1.0.0"
__author__ = "Wang Biqiang"

# 2. 核心公共 API 导出
# 用户现在可以使用: from wbq import AutoApplyModel
from .core import AutoApplyModel
from .services import CoverLetterService, JobExtractionService, ResumeBuildService, ResumeInputService


# 3. 定义 __all__ 明确控制 "from zlm import *" 的行为
__all__ = [
    "AutoApplyModel",
    "CoverLetterService",
    "JobExtractionService",
    "ResumeBuildService",
    "ResumeInputService",
]
