import json
import os
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from wbq import AutoApplyModel
from wbq.ui.pages.model_config import QWEN_DEFAULT_API_KEY
import wbq.core as core_module


JOB_TEXT = """职位名称：高级 Python 后端工程师
所属部门：技术研发部
工作地点：北京/上海/深圳

岗位职责：
1. 负责公司核心业务系统的后端架构设计、开发与优化，确保系统的高可用性、高并发性和扩展性。
2. 主导数据库建模与性能调优，解决复杂场景下的数据存储与查询瓶颈。
3. 设计和实现高效的 RESTful API 接口，支持前端及第三方合作伙伴的集成。
4. 推进微服务化改造，利用 Docker 和 Kubernetes 进行容器化编排与管理。
5. 指导初级工程师，进行代码审查，提升团队整体代码质量和技术氛围。

任职要求：
1. 计算机相关专业本科及以上学历，5 年以上 Python 后端开发经验。
2. 精通 Python 语言，深入理解多进程、多线程及异步 IO 编程模型。
3. 熟练掌握 Django 或 FastAPI 等主流 Web 框架，有大型分布式系统开发经验者优先。
4. 精通 MySQL、PostgreSQL 等关系型数据库，具备优秀的 SQL 编写及调优能力；熟练使用 Redis 等缓存技术。
5. 熟悉 Linux 操作系统，掌握 Docker、Kubernetes 等容器化技术，有 AWS 或阿里云使用经验。
6. 熟悉 RabbitMQ、Kafka 等消息中间件，了解微服务架构治理。
7. 具备良好的沟通能力和团队合作精神，对技术有热情，学习能力强。

加分项：
- 有电商、金融等高并发业务场景经验者优先。
- 有开源项目贡献或技术博客者优先。"""


RESUME_DATA = {
    "personal": {
        "name": "王碧强",
        "birthdate": "2003.11",
        "phone": "19559098287",
        "politics": "共青团员",
        "email": "Biqiang_Wang2022@outlook.com",
        "hometown": "福建福州",
        "photo": "C:/Users/21080/Desktop/profile_picture.jpg",
    },
    "education": [
        {
            "university": "福州大学(211)",
            "degree": "计算机科学与技术（实验班）",
            "from_date": "2022.09",
            "to_date": "2026.06",
            "gpa": "3.66/4.00",
            "honors": "第十四届全国大学生数学竞赛省一等奖（同专业前三）、第三十三届全国大学生数学建模竞赛省二等奖、第十六届电工杯数学建模省三等奖、校三等奖学金（三次）",
            "courses": [
                "操作系统(92)",
                "计算机组成原理(91)",
                "数据库系统原理(90)",
                "概率论与数理统计(98)",
                "离散数学(96)",
                "线性代数(93)",
            ],
        }
    ],
    "work_experience": [
        {
            "role": "人工智能/机器学习工程师 II",
            "company": "菲尼克斯大学 (University of Phoenix)",
            "from_date": "2025年2月",
            "to_date": "至今",
            "description": [
                "构建了生成式人工智能 + 可解释性工具（LangGraph + OpenAI），用于处理非结构化数据并自动解释复杂的学术/财务计算，将顾问支持能力提高了6倍",
                "将组织知识库与大语言模型集成，构建管道以提取代码逻辑并转化为逐步解释，加速了入职流程并提高了开发人员生产力",
                "通过使用 LangGraph 和 OpenAI 构建生成式人工智能 + 可解释性工具来处理非结构化数据并自动解释复杂的学术/财务计算，将顾问支持能力提高了6倍。",
            ],
        }
    ],
    "projects": [
        {
            "name": "医院综合管理平台",
            "type": "全栈开发",
            "from_date": "2024.10",
            "to_date": "2024.12",
            "description": [
                "技术栈：Spring Boot 2.7 + MyBatis-Plus + MySQL + Redis + Vue 3 + Element Plus + ECharts + WebSocket",
                "Situation: 医院原有管理系统采用传统C/S架构，数据分散在各科室独立Excel表中，导致药品库存不透明、病历调阅效率低、人工统计错误频发，管理层无法实时掌握运营数据。",
                "Task: 开发医院内部管理平台，覆盖医师管理、药品库存、电子病历、科室调度、数据统计分析五大核心模块。实现精细化权限控制和实时数据看板，帮助管理层监控药品存量、医师接诊效率等关键指标。",
                "Action: 采用Spring Boot+MyBatis-Plus构建动态查询引擎，支持多条件组合检索，通过Redis缓存提升查询性能70%；开发药品效期预警系统，采用乐观锁解决并发冲突；实现HL7标准结构化病历管理，支持PDF导出与AES-256加密。基于Vue3+Element Plus开发动态表单，集成ECharts实现药品库存热力图与医师效率雷达图，通过WebSocket实时推送预警；优化Excel批量导入功能，实现万级数据30秒内快速处理。",
                "Result: 效期预警使药品报废率降低28%，病历调阅效率提升60%，通过自动化数据校验，人工录入错误率下降45%，支持50+科室并发操作，核心接口平均响应时间<300ms。",
            ],
        },
        {
            "name": "DHR架构流量检测系统",
            "type": "网络安全",
            "from_date": "2025.5",
            "to_date": "2025.6",
            "description": [
                "异常流量检测模型开发：通过模拟SYN泛洪、UDP泛洪等攻击，采集3000+异常流量样本，构建训练数据集。开发基于随机森林（准确率98.2%）和支持向量机（检测延迟15ms）等的异构检测模型组，实现多维度攻击识别。",
                "智能防御系统实现：对接OpenFlow控制器，实现攻击自动阻断（平均阻断时间350ms），累计拦截DDoS等攻击5000+，保护15+业务IP。",
            ],
        },
    ],
    "skill_section": [
        {"name": "编程语言", "skills": ["C", "C++", "Python", "Java", "PostgreSQL", "Shell script"]},
        {"name": "开发框架", "skills": ["SpringBoot", "SpringMVC", "Mybatis/Mybatis-plus", "SpringBoot自动装配", "IOC", "AOP", "Vue"]},
        {"name": "数据库", "skills": ["MySQL", "SQL语句", "MySQL高性能优化", "事务", "索引", "锁", "日志"]},
        {"name": "Linux操作", "skills": ["Linux常用命令", "Linux环境下系统和网络配置"]},
        {"name": "办公软件", "skills": ["码字速度每分钟80+", "Excel高效处理数据", "Word专业排版", "PPT可视化设计"]},
    ],
    "social_practice": [
        {"role": "思政课程实践小组主要成员", "description": ["负责调研闽侯县居民消费行为与消费方式，发现63%居民消费方式已从线下转向'社区团购+直播电商'新模式。"]},
        {"role": "院红十字会成员", "description": ["期间进行了若干次志愿活动。"]},
    ],
}


def main():
    project_root = PROJECT_ROOT
    output_dir = project_root / "output" / "perf_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        resume_json_path = Path(tmp_dir) / "resume_input.json"
        resume_json_path.write_text(json.dumps(RESUME_DATA, ensure_ascii=False, indent=2), encoding="utf-8")

        timing = {
            "resume_parse": None,
            "jd_parse": None,
            "builder_total": None,
            "raw_stage": None,
            "ai_optimize": None,
            "final_pdf_compile": None,
            "post_optimize_overhead": None,
            "total_flow": None,
        }
        section_events = []
        latex_calls = []
        builder_started = None
        final_builder_end = None

        original_latex = core_module.json_to_latex_to_pdf

        def timed_latex(*args, **kwargs):
            call_index = len(latex_calls) + 1
            start = time.perf_counter()
            result = original_latex(*args, **kwargs)
            end = time.perf_counter()
            latex_calls.append(
                {
                    "index": call_index,
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "dst_path": kwargs.get("dst_path"),
                }
            )
            return result

        core_module.json_to_latex_to_pdf = timed_latex

        try:
            model = AutoApplyModel(
                api_key=QWEN_DEFAULT_API_KEY,
                provider="Qwen",
                model="qwen-max",
                downloads_dir=str(output_dir),
            )

            flow_start = time.perf_counter()
            t0 = time.perf_counter()
            user_data = model.user_data_extraction(str(resume_json_path), is_st=False)
            t1 = time.perf_counter()
            timing["resume_parse"] = t1 - t0

            t2 = time.perf_counter()
            job_details, jd_path = model.job_details_extraction(
                job_site_content=JOB_TEXT,
                is_st=False,
                user_id="perf-test",
            )
            t3 = time.perf_counter()
            timing["jd_parse"] = t3 - t2

            def section_callback(section_name, data, analysis):
                section_events.append(
                    {
                        "section": section_name,
                        "at": time.perf_counter(),
                        "status": (
                            "skipped"
                            if analysis and isinstance(analysis, dict) and analysis.get("skipped")
                            else "fallback"
                            if analysis and isinstance(analysis, dict) and analysis.get("fallback")
                            else "optimized"
                        ),
                        "keywords": (analysis or {}).get("keywords_matched", []) if isinstance(analysis, dict) else [],
                    }
                )

            builder_started = time.perf_counter()
            resume_path, resume_details = model.resume_builder(
                job_details,
                user_data,
                template_style="classic",
                is_st=False,
                optimize_fields=["work_experience", "projects"],
                user_id="perf-test",
                section_callback=section_callback,
            )
            final_builder_end = time.perf_counter()
            timing["builder_total"] = final_builder_end - builder_started
            timing["total_flow"] = final_builder_end - flow_start

            if latex_calls:
                timing["raw_stage"] = latex_calls[0]["end"] - builder_started
            if section_events and latex_calls:
                timing["ai_optimize"] = max(event["at"] for event in section_events) - latex_calls[0]["end"]
            if len(latex_calls) >= 2:
                timing["final_pdf_compile"] = latex_calls[1]["duration"]
                if section_events:
                    timing["post_optimize_overhead"] = final_builder_end - max(event["at"] for event in section_events) - latex_calls[1]["duration"]

            result = {
                "config": {
                    "provider": "Qwen",
                    "model": "qwen-max",
                    "template_style": "classic",
                    "optimized_fields": ["work_experience", "projects"],
                },
                "artifacts": {
                    "resume_json_path": str(resume_json_path),
                    "jd_json_path": jd_path,
                    "resume_pdf_path": resume_path,
                },
                "timing_seconds": timing,
                "latex_calls": latex_calls,
                "section_events": [
                    {
                        "section": event["section"],
                        "status": event["status"],
                        "elapsed_since_builder_start": round(event["at"] - builder_started, 4),
                        "keywords": event["keywords"],
                    }
                    for event in section_events
                ],
                "status": {
                    "job_details_ok": bool(job_details),
                    "resume_ok": bool(resume_details),
                    "resume_pdf_exists": bool(resume_path and os.path.exists(resume_path)),
                },
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        finally:
            core_module.json_to_latex_to_pdf = original_latex


if __name__ == "__main__":
    main()
