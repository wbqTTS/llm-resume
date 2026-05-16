# =============================================================================
# 1. 修改导入：使用新的单数名称提示词，并导入新增的 PERSONAL 和 SOCIAL_PRACTICE
# =============================================================================
from wbq.prompts.sections_prompt import (
    EXPERIENCE,
    SKILLS,
    PROJECTS,
    EDUCATION,          # 原为 EDUCATIONS，改为单数 EDUCATION
    SOCIAL_PRACTICE     # 新增：社会实践提示词
)

# =============================================================================
# 2. 修改导入 Schema：同样使用新的单数名称，并移除不需要的
# =============================================================================
from wbq.schemas.sections_schemas import (
    SocialPractice,
    Personal,
    Experience,
    SkillSection,
    Project,
    Education,        # 注意：这里可能需要检查，如果 schema 也改为了单数 Education，则需同步修改
    # Certifications,  # 已移除
    # Achievements     # 已移除
)

# =============================================================================
# 3. Embedding 模型配置（保持不变）
# =============================================================================
GPT_EMBEDDING_MODEL = "text-embedding-ada-002"
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"
OLLAMA_EMBEDDING_MODEL = "bge-m3"
QWEN_EMBEDDING_MODEL = "text-embedding-v3"

# =============================================================================
# 4. 默认 LLM 配置（保持不变）
# =============================================================================
DEFAULT_LLM_PROVIDER = "Qwen"
DEFAULT_LLM_MODEL = "qwen-max"

# =============================================================================
# 5. LLM 映射（保持不变）
# =============================================================================
LLM_MAPPING = {
    'Qwen': {
        "api_env": "DASHSCOPE_API_KEY",
        "model": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long", "qwen-vl-max", "qwen-vl-plus"],
    },
    'GPT': {
        "api_env": "OPENAI_API_KEY",
        "model": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-1106-preview", "gpt-3.5-turbo"],
    },
    'Gemini': {
        "api_env": "GEMINI_API_KEY",
        "model": ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-1.5-pro-exp-0801"],
    },
    'Ollama': {
        "api_env": None,  # Ollama 是本地部署，不需要 API Key
        "model": [
            "qwen2.5:1.5b",   # 目前已在本地部署的模型
            "llama3", "llama3.1", "llama3.2",  # Meta Llama 系列
            "qwen2.5", "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b",  # 阿里通义千问系列
            "phi3", "phi3.5",  # 微软 Phi 系列
            "gemma2", "gemma2:9b", "gemma2:27b",  # Google Gemma 系列
            "mistral", "mixtral",  # Mistral AI 系列
            "deepseek-v2", "deepseek-v3", "deepseek-r1",  # 深度求索系列
            "nomic-embed-text",  # Embedding 模型
            "all-minilm",  # 轻量级 Embedding 模型
            "codellama",  # 代码模型
        ],
    },
}

# =============================================================================
# 6. 核心修改：section_mapping - 适配新简历模式
# =============================================================================
from wbq.prompts.sections_prompt import (
    EDUCATION, EXPERIENCE, PROJECTS, SKILLS, SOCIAL_PRACTICE,
    RESEARCH_EXPERIENCE, TEACHING_EXPERIENCE, ACADEMIC_SERVICE
)

# 导入对应的 Schema
from wbq.schemas.sections_schemas import (
    Education, Experience, Project, SkillSection, SocialPractice,
    ResearchExperience, TeachingExperience, AcademicService
)

section_mapping = {
    # 非学术风格模块
    "work_experience": {"prompt": EXPERIENCE, "schema": Experience},
    "skill_section": {"prompt": SKILLS, "schema": SkillSection},
    "projects": {"prompt": PROJECTS, "schema": Project},
    "education": {"prompt": EDUCATION, "schema": Education},
    "social_practice": {"prompt": SOCIAL_PRACTICE, "schema": SocialPractice},

    # 学术风格核心模块
    "research_experience": {"prompt": RESEARCH_EXPERIENCE, "schema": ResearchExperience},
    "teaching_experience": {"prompt": TEACHING_EXPERIENCE, "schema": TeachingExperience},
    "academic_service": {"prompt": ACADEMIC_SERVICE, "schema": AcademicService},
}