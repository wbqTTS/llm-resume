import json
import os
import re
from typing import Any, Dict, List, Tuple


DEMO_JOB_TEXT = """岗位名称：Java 后端开发工程师
公司：星河智联科技有限公司

岗位职责：
1. 参与核心业务系统后端服务设计、开发与维护，保障系统稳定性与可扩展性。
2. 基于 Spring Boot、MyBatis、Redis、MySQL 构建高并发业务接口。
3. 参与接口性能优化、数据库查询优化、日志监控与线上问题排查。
4. 与产品、前端、测试协作完成需求拆解、接口联调和上线交付。

任职要求：
1. 计算机相关专业，本科及以上学历。
2. 熟悉 Java、Spring Boot、MySQL、Redis，理解常见数据结构和操作系统基础。
3. 有完整项目经验，能够说明个人职责、技术难点和量化结果。
4. 具备良好的沟通能力、学习能力和文档习惯。

加分项：
1. 了解消息队列、Docker、Linux、Nginx 或微服务架构。
2. 有 AI、推荐系统、简历生成、信息抽取等项目经验。
"""


DEMO_RESUME_DATA: Dict[str, Any] = {
    "personal": {
        "name": "张明",
        "birthdate": "2003.11",
        "phone": "13800001234",
        "politics": "共青团员",
        "email": "zhangming@example.com",
        "hometown": "福建福州",
        "photo": "",
        "title": "Java 后端开发 / AI 应用开发",
        "summary": "计算机专业本科生，熟悉 Java 后端开发、数据库设计和 AI 应用集成，具备完整项目交付经验。",
        "media": {"github": "https://github.com/demo-user", "linkedin": "", "medium": "", "devpost": ""},
    },
    "education": [
        {
            "university": "福州大学",
            "degree": "计算机科学与技术 本科",
            "from_date": "2022.09",
            "to_date": "2026.06",
            "gpa": "3.66/4.00",
            "honors": "校一等奖学金、数学建模竞赛省级一等奖",
            "courses": ["数据结构", "操作系统", "数据库系统原理", "计算机网络", "软件工程"],
        }
    ],
    "work_experience": [
        {
            "role": "后端开发实习生",
            "company": "星云软件工作室",
            "location": "福州",
            "from_date": "2025.03",
            "to_date": "2025.08",
            "description": [
                "参与 Spring Boot 业务接口开发，完成用户、权限、文件上传等模块。",
                "使用 Redis 缓存热点配置数据，减少重复数据库查询。",
                "协助排查接口超时问题，优化慢 SQL 并补充接口日志。",
            ],
        }
    ],
    "projects": [
        {
            "name": "智能简历生成与岗位匹配系统",
            "type": "毕业设计 / AI 应用开发",
            "from_date": "2025.10",
            "to_date": "2026.05",
            "description": [
                "基于 Streamlit 构建简历生成平台，支持 JD 输入、简历上传、模型配置、PDF 导出。",
                "设计 RAG + CoT 的章节优化流程，根据岗位关键词重写项目和工作经历。",
                "集成 SQLite 保存历史记录，并提供匹配度分析、词云和简历比对功能。",
            ],
        },
        {
            "name": "校园二手交易平台",
            "type": "Java 全栈项目",
            "from_date": "2024.09",
            "to_date": "2024.12",
            "description": [
                "使用 Spring Boot、MyBatis、MySQL 实现商品发布、搜索、收藏和订单管理。",
                "设计基础 RBAC 权限模型，区分普通用户和管理员操作。",
                "使用分页查询和索引优化商品列表接口响应速度。",
            ],
        },
    ],
    "skill_section": [
        {"name": "编程语言", "skills": ["Java", "Python", "SQL", "JavaScript"]},
        {"name": "后端框架", "skills": ["Spring Boot", "MyBatis", "Flask"]},
        {"name": "数据库与中间件", "skills": ["MySQL", "Redis", "SQLite"]},
        {"name": "工具与部署", "skills": ["Git", "Docker", "Linux", "LaTeX"]},
    ],
    "social_practice": [
        {
            "role": "学院科技协会成员",
            "description": ["组织技术分享活动，协助同学完成 Java 与数据库课程项目答疑。"],
        }
    ],
    "certifications": ["CET-6", "计算机二级 Java"],
    "achievements": ["校级优秀学生干部", "互联网+创新创业大赛校级银奖"],
}


GENERATION_STEPS: List[Tuple[str, int]] = [
    ("解析简历", 15),
    ("解析 JD", 35),
    ("生成原始版", 50),
    ("AI 优化", 72),
    ("编译 PDF", 90),
    ("结果分析", 100),
]


STYLE_DETAILS: Dict[str, Dict[str, str]] = {
    "classic": {"scene": "通用求职、金融、咨询、管理岗位", "tone": "稳重、正式、兼容性强"},
    "creative": {"scene": "产品、运营、设计、创意类岗位", "tone": "视觉层次更强，适合展示个人风格"},
    "academic": {"scene": "升学、科研、教师、研究助理岗位", "tone": "强调论文、科研、教学和学术服务"},
    "minimal": {"scene": "软件开发、数据分析、工程技术岗位", "tone": "紧凑清爽，突出技能和项目"},
}


OPTIMIZATION_PRESETS: Dict[str, Dict[str, Any]] = {
    "保守优化": {
        "caption": "仅优化工作和项目表达，尽量不改变原始内容。",
        "fields": {"education": False, "work_experience": True, "projects": True, "skill_section": False},
    },
    "标准优化": {
        "caption": "推荐。重点强化项目、工作经历和技能关键词。",
        "fields": {"education": True, "work_experience": True, "projects": True, "skill_section": True},
    },
    "强匹配优化": {
        "caption": "更积极地围绕 JD 重排表达，适合投递高度匹配岗位。",
        "fields": {
            "education": True,
            "work_experience": True,
            "projects": True,
            "skill_section": True,
            "research_experience": True,
            "teaching_experience": True,
            "academic_service": True,
        },
    },
}


def ensure_demo_resume_file(upload_dir: str = "uploads") -> str:
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, "demo_resume_zh.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEMO_RESUME_DATA, f, ensure_ascii=False, indent=2)
    return path


def normalize_manual_form(data: Dict[str, Any]) -> Dict[str, Any]:
    if "personal" in data:
        return data
    personal_keys = ["name", "birthdate", "phone", "politics", "email", "hometown", "photo", "title", "summary", "media"]
    personal = {key: data.get(key, "" if key != "media" else {}) for key in personal_keys}
    normalized = {"personal": personal}
    for key, value in data.items():
        if key not in personal_keys:
            normalized[key] = value
    return normalized


def resume_data_to_form(data: Dict[str, Any]) -> Dict[str, Any]:
    """把规范简历 JSON 转成 Streamlit 手动表单使用的扁平结构。"""
    if "personal" not in data:
        return data
    form_data = dict(data)
    personal = form_data.pop("personal", {}) or {}
    form_data.update(personal)
    return form_data


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(flatten_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(v) for v in value)
    return str(value)


def extract_keywords(job_details: Dict[str, Any]) -> List[str]:
    keywords = job_details.get("keywords", []) if isinstance(job_details, dict) else []
    if isinstance(keywords, str):
        keywords = re.split(r"[,，、\s]+", keywords)
    return [kw.strip() for kw in keywords if isinstance(kw, str) and kw.strip()]


def keyword_coverage(resume_details: Dict[str, Any], job_details: Dict[str, Any]) -> List[Dict[str, Any]]:
    resume_text = flatten_text(resume_details).lower()
    rows = []
    for keyword in extract_keywords(job_details):
        rows.append({"关键词": keyword, "是否覆盖": "已覆盖" if keyword.lower() in resume_text else "待补充"})
    return rows


def resume_quality_checks(resume_details: Dict[str, Any], job_details: Dict[str, Any] | None = None) -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []
    text = flatten_text(resume_details)
    sections = {
        "教育背景": resume_details.get("education"),
        "工作经历": resume_details.get("work_experience"),
        "项目经历": resume_details.get("projects"),
        "技能": resume_details.get("skill_section"),
    }
    for name, value in sections.items():
        if not value:
            checks.append({"检查项": name, "状态": "需补充", "建议": f"{name}为空，会降低简历完整度。"})
        else:
            checks.append({"检查项": name, "状态": "通过", "建议": "内容已填写。"})

    number_count = len(re.findall(r"\d+|%|％", text))
    checks.append({
        "检查项": "量化表达",
        "状态": "通过" if number_count >= 3 else "可增强",
        "建议": "建议在项目/经历中补充性能、规模、人数、耗时、准确率等数字。" if number_count < 3 else "已有一定量化结果。",
    })

    repeated = _find_repeated_fragments(text)
    checks.append({
        "检查项": "重复内容",
        "状态": "可增强" if repeated else "通过",
        "建议": f"存在重复表达：{'; '.join(repeated[:3])}" if repeated else "未发现明显重复表达。",
    })

    action_words = ["负责", "设计", "实现", "优化", "构建", "排查", "交付", "提升", "降低", "集成"]
    action_count = sum(text.count(word) for word in action_words)
    checks.append({
        "检查项": "动词强度",
        "状态": "通过" if action_count >= 4 else "可增强",
        "建议": "建议使用设计、实现、优化、提升、降低等行动动词突出贡献。" if action_count < 4 else "行动动词使用较充分。",
    })

    coverage = keyword_coverage(resume_details, job_details or {})
    missing = [row["关键词"] for row in coverage if row["是否覆盖"] == "待补充"]
    checks.append({
        "检查项": "岗位关键词覆盖",
        "状态": "通过" if len(missing) <= 2 else "可增强",
        "建议": "待补充：" + "、".join(missing[:8]) if missing else "岗位关键词覆盖良好。",
    })
    return checks


def score_interpretations(scores: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    labels = {
        "个人特色保留度": "衡量优化后简历是否仍保留用户原始经历和个人特点。",
        "人岗匹配度": "衡量优化后简历与目标 JD 的关键词和语义匹配程度。",
        "原始匹配度": "衡量未优化简历与目标 JD 的基础匹配程度，可作为优化前对照。",
    }
    for name, value in scores.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0
        if numeric >= 0.75:
            advice = "表现较好，适合用于演示或正式投递。"
        elif numeric >= 0.45:
            advice = "仍有提升空间，建议继续补充岗位关键词和量化成果。"
        else:
            advice = "匹配度偏低，建议重新选择经历重点或调整优化强度。"
        rows.append({"指标": name, "含义": labels.get(name, "用于衡量简历质量的辅助指标。"), "建议": advice})
    return rows


def compare_resume_keywords(original_resume: Dict[str, Any], optimized_resume: Dict[str, Any], job_details: Dict[str, Any]) -> Dict[str, List[str]]:
    original_text = flatten_text(original_resume).lower()
    optimized_text = flatten_text(optimized_resume).lower()
    keywords = extract_keywords(job_details)
    added = [kw for kw in keywords if kw.lower() not in original_text and kw.lower() in optimized_text]
    retained = [kw for kw in keywords if kw.lower() in original_text and kw.lower() in optimized_text]
    missing = [kw for kw in keywords if kw.lower() not in optimized_text]
    return {
        "新增关键词": added,
        "保留关键词": retained,
        "仍待补充": missing,
    }


def _find_repeated_fragments(text: str) -> List[str]:
    fragments = re.split(r"[。；;\n]+", text)
    seen = set()
    repeated = []
    for item in fragments:
        cleaned = re.sub(r"\s+", "", item)
        if len(cleaned) < 12:
            continue
        if cleaned in seen:
            repeated.append(cleaned[:30])
        seen.add(cleaned)
    return repeated


def friendly_error_message(exc: Exception | str, stage: str = "") -> str:
    text = str(exc)
    lower = text.lower()
    prefix = f"{stage}失败：" if stage else "操作失败："
    if "ollama" in lower or "status code: 502" in lower or "502" in lower or "bad gateway" in lower:
        return prefix + "Ollama 本地模型服务不可用或返回 502，请确认 Ollama 已启动、所选模型已拉取完成，然后重试。"
    if "failed to connect" in lower or "connection refused" in lower or "connectex" in lower or "actively refused" in lower:
        return prefix + "模型服务连接失败，请确认本地模型服务或远程接口当前可访问。"
    if "api" in lower or "key" in lower or "dashscope" in lower or "openai" in lower:
        return prefix + "模型调用异常，请检查 API Key、模型名称和网络连接。"
    if "json" in lower or "parse" in lower:
        return prefix + "模型返回格式不符合 JSON 要求，请降低优化强度或重试。"
    if "xelatex" in lower or "latex" in lower or "pdf" in lower:
        return prefix + "PDF 编译异常，请确认已安装 xelatex，并检查简历内容是否包含特殊字符。"
    if "file" in lower or "path" in lower or "no such" in lower or "不存在" in text:
        return prefix + "文件路径异常，请重新上传简历或确认输出目录存在。"
    if "job" in lower or "jd" in lower or "职位" in text:
        return prefix + "职位描述解析异常，请优先粘贴完整 JD 文本。"
    return prefix + text[:180]


def set_step(step_name: str) -> None:
    try:
        import streamlit as st
        st.session_state.current_step = step_name
        st.session_state.nav_radio = step_name
    except Exception:
        pass
