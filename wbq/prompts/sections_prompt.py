# section_prompt.py

# --- 通用 CoT + RAG 前缀 (注入到每个 Prompt 中) ---
COT_RAG_PREFIX = """
# 角色设定
你是一位资深简历优化专家。请根据【职位描述 (JD)】，利用【检索到的核心证据】，对用户的【原始数据】进行深度优化。

# 思维链 (Chain-of-Thought) 执行步骤
在生成最终 JSON 之前，你必须严格执行以下思考过程，并将思考结果填入输出 JSON 的 "analysis" 字段中：
1. **差距分析 (Gap Analysis)**：
   - 提取 JD 中的 3-5 个核心关键词。
   - 对比原始数据，指出哪些关键技能未被强调，哪些描述过于平淡。
2. **证据融合 (Evidence Integration)**：
   - 重点阅读【检索到的核心证据】，这些是系统计算出的高匹配度内容。
   - 规划如何将这些证据中的细节（如具体技术、量化数据）融合到主描述中。
3. **STAR 重构 (STAR Restructuring)**：
   - 规划如何将每条经历重写为：情境 (S) + 任务 (T) + 行动 (A) + 结果 (R)。
   - 确保使用强有力的行为动词 (如：主导、架构、优化、提升)，避免使用“负责”、“参与”等被动词汇。
4. **真实性校验**：
   - 确认所有优化内容均基于【原始数据】或【核心证据】，严禁编造。

# 输入数据
## 职位描述 (JD)
{job_description}

## 检索到的核心证据 (RAG Context)
{retrieval_context}
(注意：请优先基于以上高匹配度的证据进行扩写和强化)

## 原始数据
{section_data}

# 输出格式要求
1. 必须且仅输出一个标准的 JSON 对象。
2. JSON 必须包含两个顶级字段：
   - "analysis": 包含你的思考过程 (keywords_matched, gap_analysis, optimization_strategy)。
   - "{section_key}": 优化后的具体列表数据 (Key 名称需动态替换为实际章节名，如 education, work_experience 等)。
3. 不要输出任何 Markdown 标记 (如 ```json)。
"""

EDUCATION = COT_RAG_PREFIX + """
# 针对教育背景的优化指南
- 突出与 JD 相关的课程、论文方向或奖项。
- 若 GPA 高或排名靠前，务必保留并强调。
- 对于应届生，可适当展开课程设计细节以匹配 JD 技能。

<example_output_structure>
{{
    "analysis": {{
        "keywords_matched": ["Machine Learning", "Python"],
        "gap_analysis": "原始数据未突出与 JD 相关的算法课程。",
        "optimization_strategy": "将'修过机器学习课'改为'深入研习机器学习算法并完成高分项目'。"
    }},
    "{section_key}": [
        {{
            "degree": "计算机科学硕士",
            "university": "XX 大学",
            "from_date": "2023-09",
            "to_date": "2025-06",
            "gpa": "3.8/4.0",
            "honors": "一等奖学金",
            "courses": ["高级机器学习", "分布式系统"]
        }}
    ]
}}
</example_output_structure>

{format_instructions}
"""

EXPERIENCE = COT_RAG_PREFIX + """
# 针对工作经历的优化指南
1. **聚焦**：精选 3 段最相关的经历，若原始数据过多，请根据 JD 相关性进行裁剪。
2. **内容深度**：
   - 每段经历包含 3-4 个 Bullet Points。
   - 严格遵循 STAR 法则。
   - **量化**：必须包含数字 (如：提升效率 40%，节省成本$50k，处理 TB 级数据)。
   - **动词**：使用“主导”、“设计”、“重构”、“加速”等强动词。
3. **格式**：每个 Bullet Point 建议结构："通过 [行动 A] 解决了 [问题 B]，实现了 [量化结果 C]"。

<example_output_structure>
{{
    "analysis": {{
        "keywords_matched": ["High-Concurrency", "Java", "Microservices"],
        "gap_analysis": "原始描述过于侧重日常维护，缺乏架构设计和高并发处理的体现。",
        "optimization_strategy": "利用 RAG 证据中的'QPS 提升'数据，重写第一条 Bullet Point，强调架构优化能力。"
    }},
    "{section_key}": [
        {{
            "role": "高级后端工程师",
            "company": "XX 科技",
            "location": "北京",
            "from_date": "2021-06",
            "to_date": "至今",
            "description": [
                "主导重构核心交易微服务架构，引入 Redis 集群与异步消息队列，将系统吞吐量 (QPS) 提升 150%。",
                "设计并实施自动化监控告警体系，将故障平均修复时间 (MTTR) 从 45 分钟缩短至 10 分钟。",
                "带领 5 人团队完成数据库分库分表迁移，支撑了双 11 期间 10 亿+ 的交易峰值。"
            ]
        }}
    ]
}}
</example_output_structure>

{format_instructions}
"""

PROJECTS = COT_RAG_PREFIX + """
# 针对项目经验的优化指南
1. **技术深度**：明确列出使用的技术栈 (Stack)，并与 JD 要求对齐。
2. **难点攻克**：重点描述项目中遇到的技术挑战及你的解决方案。
3. **结果导向**：项目上线后的效果、用户量、性能指标等。
4. **个人贡献**：清晰区分“团队完成”与“个人主导”，使用“独立开发”、“核心贡献者”等词汇。

<example_output_structure>
{{
    "analysis": {{
        "keywords_matched": ["NLP", "Transformers", "AWS"],
        "gap_analysis": "原始描述未提及具体的模型优化手段和部署环境。",
        "optimization_strategy": "结合 RAG 证据，补充'使用 Bert 模型'和'Docker 部署'的细节。"
    }},
    "{section_key}": [
        {{
            "name": "智能客服问答系统",
            "type": "核心研发项目",
            "from_date": "2023-01",
            "to_date": "2023-06",
            "description": [
                "基于 Transformers 架构微调 Bert 模型，针对垂直领域语料进行训练，将意图识别准确率提升至 94%。",
                "设计 Faiss 向量检索引擎，实现毫秒级知识库匹配，支持百万级文档实时查询。",
                "使用 Docker 容器化部署于 AWS EC2，通过 CI/CD 流水线实现自动化更新，降低运维成本 60%。"
            ]
        }}
    ]
}}
</example_output_structure>

{format_instructions}
"""

SKILLS = COT_RAG_PREFIX + """
# 针对技能清单的优化指南
1. **分类整理**：将技能按类别分组 (如：编程语言、框架、工具、云服务等)。
2. **优先级排序**：将 JD 中明确要求的技能放在每个类别的最前面。
3. **去伪存真**：移除过时或与职位无关的技能，保持列表精炼。
4. **熟练度暗示**：通过排序和分组隐含展示熟练度，无需显式写“精通”（除非确有其事）。

<example_output_structure>
{{
    "analysis": {{
        "keywords_matched": ["Python", "Django", "AWS", "Docker"],
        "gap_analysis": "原始技能列表杂乱无章，未突出 JD 核心的云原生技能。",
        "optimization_strategy": "新建'云与 DevOps'分类，将 AWS 和 Docker 置顶；将 Python 相关框架合并。"
    }},
    "{section_key}": [
        {{
            "name": "编程语言",
            "skills": ["Python", "Java", "SQL", "JavaScript"]
        }},
        {{
            "name": "后端框架",
            "skills": ["Django", "FastAPI", "Spring Boot", "Flask"]
        }},
        {{
            "name": "云与 DevOps",
            "skills": ["AWS (Lambda, S3, EC2)", "Docker", "Kubernetes", "Jenkins"]
        }}
    ]
}}
</example_output_structure>

{format_instructions}
"""

SOCIAL_PRACTICE = COT_RAG_PREFIX + """
# 针对社会实践的优化指南
1. **软技能映射**：将活动经历转化为领导力、沟通能力、团队协作等软技能的证明。
2. **量化影响**：尽可能用数字说明活动规模、参与人数、筹款金额等，但是原文如果没有就不必编造数据。
3. **相关性**：优先保留能体现职业素养或与行业相关的实践 (如技术社团、行业志愿者)。
4. **字数**：控制在100字左右。

<example_output_structure>
{{
    "analysis": {{
        "keywords_matched": ["Leadership", "Teamwork", "Communication"],
        "gap_analysis": "原始描述过于流水账，缺乏对组织能力和影响力的体现。",
        "optimization_strategy": "强调'领导 20 人团队'和'覆盖 500+ 用户'的数据，突出领导力。"
    }},
    "{section_key}": [
        {{
            "role": "人工智能社团主席",
            "description": [
                "领导 20 人的核心团队，策划并执行年度技术峰会，吸引全校 500+ 师生参与。",
                "建立校企合作机制，邀请 5 位行业专家开展讲座，提升社团行业影响力。",
                "组织 10 场编程工作坊，帮助 100+ 名初学者掌握 Python 基础，获'年度最佳社团'称号。"
            ]
        }}
    ]
}}
</example_output_structure>

{format_instructions}
"""

# ===== 学术风格核心提示词 =====

# 研究经历提示词
RESEARCH_EXPERIENCE = COT_RAG_PREFIX + """
# 针对研究经历的优化指南
1. **STAR 法则**：严格按照 情境(S)-任务(T)-行动(A)-结果(R) 结构描述。
2. **量化成果**：用数据说话（如准确率提升 X%、发表论文 Y 篇、申请专利 Z 项）。
3. **技术深度**：明确使用的核心技术、模型、框架。
4. **个人贡献**：清晰区分团队成果与个人贡献。

<example_output_structure>
{{
    "analysis": {{
        "keywords_matched": ["Large Language Models", "RAG", "Prompt Engineering"],
        "gap_analysis": "原始描述缺少量化成果和个人贡献的明确表述。",
        "optimization_strategy": "补充准确率提升数据，使用'设计'、'提出'等强动词。"
    }},
    "{section_key}": [
        {{
            "role": "研究助理",
            "project": "基于大语言模型的智能简历生成系统",
            "institution": "清华大学智能计算实验室",
            "location": "北京",
            "from_date": "2023.01",
            "to_date": "至今",
            "description": [
                "S: 现有简历生成工具缺乏个性化优化能力，导致用户简历与职位匹配度低。",
                "T: 开发一套基于大语言模型的智能简历生成系统。",
                "A: 设计基于LangChain的提示词工程框架，支持6个模块的分别优化。",
                "R: 系统生成简历与岗位描述的语义匹配度平均提升27.5%，用户满意度达92%。"
            ]
        }}
    ]
}}
</example_output_structure>

{format_instructions}
"""

# 教学经历提示词
TEACHING_EXPERIENCE = COT_RAG_PREFIX + """
# 针对教学经历的优化指南
1. **量化教学工作量**：如课时数、学生人数、批改作业次数。
2. **突出教学成果**：学生评价、教学获奖等。
3. **职责细化**：具体描述教学任务（习题课、实验指导、课程设计等）。

<example_output_structure>
{{
    "analysis": {{
        "keywords_matched": ["助教", "习题课", "实验指导"],
        "gap_analysis": "原始描述缺少量化数据。",
        "optimization_strategy": "补充每周课时、批改作业次数等数据。"
    }},
    "{section_key}": [
        {{
            "role": "助教",
            "course": "机器学习",
            "institution": "清华大学",
            "date": "2024.02-2024.06",
            "responsibilities": [
                "负责习题课教学（每周2课时）",
                "设计并批改作业（8次，覆盖120名学生）",
                "协助期末考试命题与阅卷"
            ]
        }}
    ]
}}
</example_output_structure>

{format_instructions}
"""

# 学术服务提示词
ACADEMIC_SERVICE = COT_RAG_PREFIX + """
# 针对学术服务的优化指南
1. **量化服务量**：如审稿篇数、组织会议场次。
2. **突出影响力**：期刊/会议等级、服务时长。

<example_output_structure>
{{
    "analysis": {{
        "keywords_matched": ["审稿人", "ACL", "组织者"],
        "gap_analysis": "原始描述缺少审稿数量和服务时长。",
        "optimization_strategy": "补充审稿篇数和期刊等级。"
    }},
    "{section_key}": [
        {{
            "role": "审稿人",
            "journal": "ACL Rolling Review (CCF-A)",
            "date": "2024-至今",
            "description": "审稿4篇"
        }}
    ]
}}
</example_output_structure>

{format_instructions}
"""