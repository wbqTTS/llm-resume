import os
import json
from typing import List
from pydantic import BaseModel, Field
from dashscope import Generation

# ==========================================
# 🔑 配置区域
# ==========================================
# 请在此处填入你的 DashScope API Key
DASHSCOPE_API_KEY = "sk-993b13d43fe141d7bbe9f226c0bc9b71"

INPUT_FILE = "extracted_job.txt"
OUTPUT_FILE = "structured_job_data.json"


# ==========================================

# 定义与你的 schema 完全一致的数据模型
class JobDetails(BaseModel):
    job_title: str = Field(description="The specific role, its level, and scope within the organization.")
    job_purpose: str = Field(description="A high-level overview of the role and why it exists in the organization.")
    keywords: List[str] = Field(description="Key expertise, skills, and requirements the job demands.")
    job_duties_and_responsibilities: List[str] = Field(
        description="Focus on essential functions, their frequency and importance, level of decision-making, areas of accountability, and any supervisory responsibilities.")
    required_qualifications: List[str] = Field(
        description="Including education, minimum experience, specific knowledge, skills, abilities, and any required licenses or certifications.")
    preferred_qualifications: List[str] = Field(
        description="Additional \"nice-to-have\" qualifications that could set a candidate apart.")
    company_name: str = Field(description="The name of the hiring organization.")
    company_details: str = Field(
        description="Overview, mission, values, or way of working that could be relevant for tailoring a resume or cover letter.")


def clean_text_with_qwen(raw_text):
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == "sk-你的API_KEY_在这里":
        print("❌ 错误：请先在脚本中配置有效的 DASHSCOPE_API_KEY")
        return None

    # 构建针对特定 Schema 的 Prompt
    prompt = f"""
    你是一名专业的招聘数据分析师。请阅读以下从招聘网站抓取的原始文本，并严格按照指定的 JSON Schema 提取信息。

    ### 提取目标 (Schema 定义)
    你需要提取以下 8 个字段，请严格遵守字段的定义：
    1. **job_title**: 具体的职位名称、级别及范围。
    2. **job_purpose**: 职位的高层概述，该职位存在的意义。
    3. **keywords**: 关键专业技能、核心能力列表 (List[str])。
    4. **job_duties_and_responsibilities**: 核心职责列表 (List[str])，关注基本职能、决策层级、问责领域及管理职责。
    5. **required_qualifications**: 硬性要求列表 (List[str])，包括学历、最低经验、必备技能/证书。
    6. **preferred_qualifications**: 加分项列表 (List[str])，即“优先考虑”的条件。
    7. **company_name**: 招聘公司的全称。
    8. **company_details**: 公司简介、使命、价值观或工作方式（用于定制简历的信息）。

    ### 约束条件
    - 如果某个字段在原文中找不到明确信息，请填写 null (不要编造)。
    - 输出必须是**纯粹的 JSON 格式**。
    - **不要**输出 markdown 代码块标记（如 ```json ... ```）。
    - **不要**输出任何解释性文字，只输出 JSON 字符串。

    ### 原始文本
    ---
    {raw_text[:18000]} 
    ---
    """

    print("🤖 正在调用 Qwen 大模型进行结构化提取...")

    try:
        # 使用 qwen-plus 以获得更好的指令遵循能力
        response = Generation.call(
            model="qwen-plus",
            api_key=DASHSCOPE_API_KEY,
            messages=[
                {'role': 'system',
                 'content': 'You are a strict JSON extractor. Output ONLY valid JSON matching the requested schema.'},
                {'role': 'user', 'content': prompt}
            ],
            result_format='message'
        )

        if response.status_code == 200:
            content = response.output.choices[0].message.content
            return content
        else:
            print(f"❌ 调用失败: Code={response.status_code}, Message={response.message}")
            return None

    except Exception as e:
        print(f"💥 发生异常: {e}")
        return None


def parse_and_validate(json_str):
    """解析 JSON 并尝试用 Pydantic 验证"""
    if not json_str:
        return None

    # 清理可能的 markdown 包裹
    clean_str = json_str.strip()
    if clean_str.startswith("```"):
        lines = clean_str.split("\n")
        if lines[0].startswith("```json"):
            lines = lines[1:]
        elif lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```": lines = lines[:-1]
        clean_str = "\n".join(lines).strip()

    try:
        # 先解析为字典
        data_dict = json.loads(clean_str)

        # 使用 Pydantic 模型进行验证和类型转换
        # 这会自动处理 List[str] 的验证，如果模型返回的是字符串，这里可能会报错，
        # 但 Qwen 通常能很好遵循 List 指令。
        job_obj = JobDetails(**data_dict)
        return job_obj

    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 解析失败: {e}")
        # 尝试修复：查找第一个 { 和最后一个 }
        start = clean_str.find("{")
        end = clean_str.rfind("}")
        if start != -1 and end != -1:
            try:
                data_dict = json.loads(clean_str[start:end + 1])
                return JobDetails(**data_dict)
            except Exception as inner_e:
                print(f"修复后依然失败: {inner_e}")
        return None
    except Exception as e:
        print(f"⚠️ Pydantic 验证失败 (可能是字段缺失或类型不匹配): {e}")
        # 即使验证失败，也尝试返回原始字典以便调试
        try:
            return json.loads(clean_str)
        except:
            return None


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到文件: {INPUT_FILE}")
        print("💡 请先运行爬虫脚本生成该文件。")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    if len(raw_text) < 50:
        print("⚠️ 原始文件内容过少，跳过清洗。")
        return

    print(f"📄 已读取原始文件，长度：{len(raw_text)} 字符")

    # 调用大模型
    json_result_str = clean_text_with_qwen(raw_text)

    if not json_result_str:
        print("❌ 大模型未返回有效结果。")
        return

    # 解析并验证
    result = parse_and_validate(json_result_str)

    if not result:
        print("❌ 无法解析或验证数据。原始返回如下:")
        print("-" * 30)
        print(json_result_str)
        print("-" * 30)
        return

    # 转换为字典以便打印和保存
    if isinstance(result, JobDetails):
        data = result.model_dump()
    else:
        data = result  # fallback if validation failed but parsing succeeded

    # ==========================================
    # 🖨️ 控制台打印 (格式化输出)
    # ==========================================
    print("\n" + "=" * 70)
    print("✨ Qwen 结构化提取结果")
    print("=" * 70)

    # 定义打印映射
    display_map = {
        "job_title": "🏷️ 职位名称 (Job Title)",
        "company_name": "🏢 公司名称 (Company)",
        "job_purpose": "🎯 职位目的 (Purpose)",
        "company_details": "🏛️ 公司详情 (Details)",
        "keywords": "🔑 关键词 (Keywords)",
        "job_duties_and_responsibilities": "⚙️ 职责 (Duties & Responsibilities)",
        "required_qualifications": "✅ 硬性要求 (Required Quals)",
        "preferred_qualifications": "🌟 加分项 (Preferred Quals)"
    }

    for key, label in display_map.items():
        value = data.get(key)
        if value:
            print(f"\n[{label}]")
            if isinstance(value, list):
                for item in value:
                    print(f"  • {item}")
            else:
                # 长文本换行缩进
                lines = str(value).split("\n")
                for line in lines:
                    print(f"  {line}")

    print("\n" + "=" * 70)

    # 保存结果
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 结构化数据已保存至: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()