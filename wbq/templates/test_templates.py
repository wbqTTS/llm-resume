import os
import sys
import time
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("❌ 错误: 未找到 jinja2 库。请运行: pip install jinja2")
    sys.exit(1)

# ==========================================
# 1. 配置部分
# ==========================================

TEST_DATA = {
  "personal": {
    "name": "王碧强",
    "birthdate": "2003.11",
    "phone": "19559098287",
    "politics": "共青团员",
    "email": "2108095381@qq.com",
    "hometown": "福建福州",
    "photo": "C:/Users/21080/Desktop/profile_picture.jpg",

    "title": "我构建解决现实世界问题的人工智能系统。",
    "summary": "多才多艺的工程师，拥有6年开发可投入生产的机器学习解决方案和全栈应用程序的经验。管理从设计到部署及云环境优化的端到端管道。热衷于推进人工智能基础设施、微调基础模型，并在全球范围内提供可扩展且具成本效益的解决方案。",
    "media": {
      "linkedin": "https://linkedin.com/in/saurabhzinjad",
      "github": "https://github.com/Ztrimus",
      "medium": "https://ztrimus.medium.com",
      "devpost": "https://devpost.com/Ztrimus"
    }
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
        "线性代数(93)"
      ]
    }
  ],
  "work_experience": [
    {
      "role": "人工智能/机器学习工程师 II",
      "company": "菲尼克斯大学 (University of Phoenix)",
      "location": "美国",
      "from_date": "2025年2月",
      "to_date": "至今",
      "description": [
        "构建了生成式人工智能 + 可解释性工具（LangGraph + OpenAI），用于处理非结构化数据并自动解释复杂的学术/财务计算，将顾问支持能力提高了6倍",
        "将组织知识库与大语言模型集成，构建管道以提取代码逻辑并转化为逐步解释，加速了入职流程并提高了开发人员生产力"
      ]
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
        "采用Spring Boot+MyBatis-Plus构建动态查询引擎，通过Redis缓存提升查询性能70%",
        "效期预警使药品报废率降低28%，病历调阅效率提升60%"
      ]
    },
    {
      "name": "DHR架构流量检测系统",
      "type": "网络安全",
      "from_date": "2025.5",
      "to_date": "2025.6",
      "description": [
        "开发基于随机森林（准确率98.2%）和支持向量机（检测延迟15ms）的异构检测模型组",
        "对接OpenFlow控制器实现攻击自动阻断，累计拦截DDoS攻击5000+"
      ]
    }
  ],
  "skill_section": [
    {"name": "编程语言", "skills": ["C", "C++", "Python", "Java", "PostgreSQL", "Shell script"]},
    {"name": "开发框架", "skills": ["SpringBoot", "SpringMVC", "Mybatis/Mybatis-plus", "Vue"]},
    {"name": "数据库", "skills": ["MySQL", "PostgreSQL", "Redis"]},
    {"name": "Linux操作", "skills": ["Linux常用命令", "网络配置"]},
    {"name": "办公软件", "skills": ["Excel", "Word", "PPT"]}
  ],
  "social_practice": [
    {
      "role": "思政课程实践小组主要成员",
      "description": ["负责调研居民消费行为，发现63%居民消费方式已从线下转向'社区团购+直播电商'新模式。"]
    },
    {
      "role": "院红十字会成员",
      "description": ["期间进行了若干次志愿活动。"]
    }
  ],
  "certifications": [
    {
      "name": "深度学习专项课程",
      "date": "2024.03",
      "by": "DeepLearning.AI"
    },
    {
      "name": "服务器端后端开发",
      "date": "2023.12",
      "by": "香港科技大学"
    }
  ],
  "achievements": [
    {
      "name": "第十四届全国大学生数学竞赛省一等奖",
      "date": "2023.12"
    },
    {
      "name": "第三十三届全国大学生数学建模竞赛省二等奖",
      "date": "2024.09"
    },
    {
      "name": "第十六届电工杯数学建模省三等奖",
      "date": "2024.05"
    }
  ]
}
TEMPLATES_TO_TEST = [
    # {"id": "minimal", "file": "resume_minimal.tex.jinja", "name": "极简现代风"},
    {"id": "creative", "file": "resume_creative.tex.jinja", "name": "创意活力风"},
    # {"id": "academic", "file": "resume_academic.tex.jinja", "name": "学术严谨风"},
    # {"id": "classic", "file": "resume_classic.tex.jinja", "name": "商务经典风"},
]


# ==========================================
# ✅ LaTeX 安全转义函数
# ==========================================

def escape_latex(text):
    if text is None:
        return ""
    text = str(text)

    # 必须先转义反斜杠，再转义其他字符
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),  # 转义 #
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    return text


def deep_escape(data):
    if isinstance(data, dict):
        return {k: deep_escape(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [deep_escape(i) for i in data]
    elif isinstance(data, str):
        return escape_latex(data)
    return data


# ==========================================
# 编译 LaTeX
# ==========================================

def compile_latex(tex_path, output_pdf_path, cls_path):
    dir_path = os.path.dirname(os.path.abspath(tex_path))
    file_name = os.path.basename(tex_path)
    prev_dir = os.getcwd()

    try:
        os.chdir(dir_path)

        # 复制 resume.cls 到编译目录
        target_cls = os.path.join(dir_path, "resume.cls")
        if not os.path.exists(target_cls):
            shutil.copy(cls_path, target_cls)
            print(f"   📄 已复制 resume.cls")

        # 🔍 检查并复制 styles 目录
        styles_src = os.path.join(os.path.dirname(cls_path), "styles")
        styles_dst = os.path.join(dir_path, "styles")

        if not os.path.exists(styles_dst):
            if os.path.exists(styles_src):
                shutil.copytree(styles_src, styles_dst)
                print(f"   📁 已复制 styles 目录到编译目录")
                # 验证复制是否成功
                if os.path.exists(styles_dst):
                    style_files = os.listdir(styles_dst)
                    print(f"   📋 styles 目录内容: {style_files}")
                else:
                    print("   ❌ styles 目录复制失败！")
            else:
                print(f"   ⚠️ 源 styles 目录不存在: {styles_src}")
                return False
        else:
            print(f"   📁 styles 目录已存在")
            style_files = os.listdir(styles_dst)
            print(f"   📋 styles 目录内容: {style_files}")

        print(f"   ⏳ 正在编译: {file_name} ...", end=" ", flush=True)

        # 编译两次以确保交叉引用正确
        for i in range(2):
            result = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-halt-on-error", file_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode != 0:
                print("\n   ❌ 编译错误日志:")
                # 打印更多错误行
                error_lines = result.stdout.split('\n')[-50:]
                for line in error_lines:
                    if 'error' in line.lower() or '!' in line or 'undefined' in line.lower():
                        print(f"      {line}")
                # 保存完整日志到文件
                log_file = os.path.join(dir_path, "error_log.txt")
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(result.stdout)
                print(f"      📄 完整日志已保存到: {log_file}")
                raise Exception("编译失败")

        pdf_name = os.path.splitext(file_name)[0] + ".pdf"
        full_pdf_path = os.path.join(dir_path, pdf_name)

        if os.path.exists(full_pdf_path):
            shutil.move(full_pdf_path, output_pdf_path)
            print("✅ 成功")

            # 自动打开PDF文件
            try:
                if sys.platform.startswith('win'):  # Windows
                    os.startfile(output_pdf_path)
                elif sys.platform.startswith('darwin'):  # macOS
                    subprocess.run(['open', output_pdf_path])
                else:  # Linux
                    subprocess.run(['xdg-open', output_pdf_path])
                print("   📂 已自动打开PDF文件")
            except Exception as e:
                print(f"   ⚠️ 无法自动打开PDF: {e}")

            return True

        print("❌ 未生成 PDF")
        return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

    finally:
        os.chdir(prev_dir)


# ==========================================
# 主逻辑
# ==========================================

def main():
    print("🚀 开始测试模板")
    print("=" * 50)

    templates_dir = os.path.dirname(os.path.abspath(__file__))
    cls_source = os.path.join(templates_dir, "resume.cls")
    styles_source = os.path.join(templates_dir, "styles")

    # 检查必要文件和目录是否存在
    print(f"📂 模板目录: {templates_dir}")

    if not os.path.exists(cls_source):
        print(f"❌ 错误: 找不到 resume.cls 文件: {cls_source}")
        sys.exit(1)
    else:
        print(f"✅ 找到 resume.cls")

    if not os.path.exists(styles_source):
        print(f"❌ 错误: 找不到 styles 目录: {styles_source}")
        sys.exit(1)
    else:
        style_files = os.listdir(styles_source)
        print(f"✅ 找到 styles 目录，包含文件: {style_files}")

    # 创建临时工作目录
    work_dir = tempfile.mkdtemp(prefix="resume_test_")
    print(f"🔧 临时工作目录: {work_dir}")

    # 复制 styles 目录到临时工作目录
    styles_dst = os.path.join(work_dir, "styles")
    try:
        shutil.copytree(styles_source, styles_dst)
        print(f"📁 已复制 styles 目录到临时目录")

        # 验证复制结果
        if os.path.exists(styles_dst):
            copied_files = os.listdir(styles_dst)
            print(f"📋 临时目录 styles 内容: {copied_files}")
        else:
            print("❌ styles 目录复制失败！")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 复制 styles 目录时出错: {e}")
        sys.exit(1)

    # 复制 resume.cls 到临时工作目录
    cls_dst = os.path.join(work_dir, "resume.cls")
    try:
        shutil.copy(cls_source, cls_dst)
        print(f"📄 已复制 resume.cls 到临时目录")
    except Exception as e:
        print(f"❌ 复制 resume.cls 时出错: {e}")
        sys.exit(1)

    print("=" * 50)

    # 创建 Jinja2 环境
    latex_jinja_env = Environment(
        loader=FileSystemLoader(templates_dir),
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="\\VAR{",
        variable_end_string="}",
        comment_start_string="(((",
        comment_end_string=")))",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False
    )

    latex_jinja_env.filters['escape_latex'] = escape_latex

    # 使用测试数据
    data = deep_escape(TEST_DATA)

    results = []
    success_count = 0

    for tpl in TEMPLATES_TO_TEST:
        print(f"\n--- {tpl['name']} ({tpl['id']}) ---")

        try:
            template = latex_jinja_env.get_template(tpl["file"])
            latex_code = template.render(**data)

            tex_file = os.path.join(work_dir, tpl["file"].replace(".jinja", ""))

            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(latex_code)

            print(f"   📝 已生成: {os.path.basename(tex_file)}")

            pdf_file = tex_file.replace(".tex", ".pdf")
            success = compile_latex(tex_file, pdf_file, cls_source)

            results.append(success)
            if success:
                success_count += 1
                print(f"   📄 PDF 已保存到: {pdf_file}")

        except Exception as e:
            print(f"   ❌ 处理模板时出错: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {success_count}/{len(results)} 成功")

    if success_count == len(results):
        print("✅ 所有模板编译成功！")
    else:
        print(f"❌ {len(results) - success_count} 个模板编译失败")

    print(f"📁 临时文件保存在: {work_dir}")
    print("=" * 50)


if __name__ == "__main__":
    main()