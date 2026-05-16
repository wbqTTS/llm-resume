from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph


THESIS_PATH = Path(r"C:\Users\21080\Desktop\毕设\102201204_王碧强_基于LLM的简历智能生成与优化系统.docx")
BACKUP_PATH = THESIS_PATH.with_name(THESIS_PATH.stem + "_4.3修改前备份.docx")
OUTPUT_DIR = Path(r"C:\Users\21080\Desktop\毕设\ref_sys\job-llm\output\thesis_section_43_assets")
FONT_PATH = Path(r"C:\Windows\Fonts\msyh.ttc")


SECTIONS = [
    {
        "title": "4.3.1 用户管理功能设计",
        "body": [
            "用户管理模块位于系统入口层，负责完成用户会话建立、用户上下文恢复以及工作台状态展示。当前版本前端采用“用户名+密码”的登录展示方式，但后端仍保持轻量化实现：系统读取用户名后调用数据库用户管理器查询用户记录；若该用户名尚不存在，则自动创建用户并返回新的用户ID；若已存在，则直接复用原有用户ID。随后系统将用户ID、用户名以及导航状态写入Streamlit会话状态，完成登录流程。",
            "进入用户中心后，系统会基于当前用户ID读取历史生成记录，展示工作台状态卡、历史概览图表以及历史版本列表。若用户点击“加载此版本”，系统会从数据库中恢复原始简历数据、结构化JD、模型配置、已生成结果和分析缓存，并将页面自动跳转到结果分析页面。若用户退出登录，系统会统一清空与当前任务相关的临时状态，避免不同用户之间的数据串扰。",
        ],
        "caption": "图 4-7 用户管理功能时序图",
        "diagram_name": "fig_4_7_user_management.png",
        "actors": ["用户", "Streamlit页面", "会话状态", "ResumeDB"],
        "messages": [
            (0, 1, "输入用户名和密码并提交"),
            (1, 3, "根据用户名查询/创建用户"),
            (3, 1, "返回 user_id 与用户名"),
            (1, 2, "写入 user_id / username / nav_radio"),
            (1, 3, "读取该用户历史记录"),
            (3, 1, "返回历史记录摘要"),
            (0, 1, "点击加载历史版本"),
            (1, 3, "按 record_id 读取完整记录"),
            (3, 1, "返回源数据、JD、模型配置、结果缓存"),
            (1, 2, "恢复会话并跳转结果分析"),
        ],
    },
    {
        "title": "4.3.2 数据输入功能设计",
        "body": [
            "数据输入模块负责组织职位描述与个人简历两类核心输入，并将其统一整理为后续生成流程可直接消费的结构化上下文。职位描述支持“招聘链接抓取”和“文本粘贴”两种方式；为保证答辩演示稳定性，系统同时提供岗位标签推荐、技术关键词补充以及一键载入Demo数据能力。用户点击相关标签后，系统会将标签内容追加至JD文本框，从而减少手工输入成本。",
            "个人简历输入支持PDF/JSON上传和手动表单填写两种主路径。若选择文件上传，系统记录源文件路径并用于后续简历解析；若选择手动填写，则页面按教育背景、工作经历、项目经历、技能、学术补充等模块组织表单，并将其标准化为统一的简历JSON结构。对于部分文本输入场景，系统复用了已有的语音输入接口，以提升交互便利性。此外，用户也可一键载入稳定的演示数据，用于快速跑通整套流程。",
        ],
        "caption": "图 4-8 数据输入功能时序图",
        "diagram_name": "fig_4_8_data_input.png",
        "actors": ["用户", "数据输入页", "辅助组件", "会话状态"],
        "messages": [
            (0, 1, "选择 JD 输入方式"),
            (1, 2, "触发标签推荐 / 语音输入 / Demo载入"),
            (2, 1, "返回文本补充结果"),
            (0, 1, "填写或上传简历"),
            (1, 2, "标准化表单 / 校验上传文件"),
            (2, 1, "返回结构化简历数据"),
            (1, 3, "保存 jd_text / jd_url / form_data / resume_source"),
            (3, 1, "返回当前输入状态"),
        ],
    },
    {
        "title": "4.3.3 模型配置功能设计",
        "body": [
            "模型配置模块负责在生成前建立统一的大模型调用参数。系统当前支持Qwen、GPT、Gemini和Ollama四类提供商，页面会联动展示可选模型、适用场景提示以及热门推荐。对于Qwen，系统支持优先读取环境变量中的DashScope密钥，并在当前版本中为演示配置提供默认API Key填充能力；对于本地部署模型如Ollama，则更强调模型名称与本地服务可用性检查。",
            "当用户完成配置后，页面会将 provider、model、api_key 封装为 llm_config 写入会话状态。后续生成简历、生成求职信、面试助手和结果分析中的LLM调用均统一从该配置对象读取参数。这样的设计可以将模型配置与业务流程解耦，既方便切换不同模型，也降低了核心逻辑模块与页面组件之间的耦合度。",
        ],
        "caption": "图 4-9 模型配置功能时序图",
        "diagram_name": "fig_4_9_model_config.png",
        "actors": ["用户", "模型配置页", "模型映射/提示", "会话状态"],
        "messages": [
            (0, 1, "选择 provider 与 model"),
            (1, 2, "查询模型说明与推荐信息"),
            (2, 1, "返回模型备注 / 热门推荐"),
            (0, 1, "输入或确认 API Key"),
            (1, 3, "保存 llm_config"),
            (3, 1, "返回配置成功状态"),
        ],
    },
    {
        "title": "4.3.4 简历生成与优化功能设计",
        "body": [
            "简历生成与优化模块是系统的核心执行单元。用户在页面上选择优化强度、需要优化的章节以及简历模板风格后，生成页首先从会话状态读取原始简历来源、JD文本或链接、模型配置和优化字段集合，并创建 AutoApplyModel 实例。随后系统依次执行简历解析、JD结构化提取、原始版内容组织、章节级优化、LaTeX渲染与PDF编译等步骤。页面侧则通过阶段进度面板向用户展示“解析简历—解析JD—生成原始版—AI优化—编译PDF—结果分析”的总体进度。",
            "在优化阶段，核心模块会根据用户选中的字段构造章节配置，并利用线程池并发处理工作经历、项目经历、技能、教育背景等模块。每个章节在进入优化前，都会先通过检索器获取与岗位要求最相关的上下文片段，再交由大模型结合链式提示完成重写或增强；若某章节未被勾选，则直接保留原始内容；若模型输出解析失败，则回退到原始数据，保证整份简历不会因为单个章节异常而中断。最终系统汇总优化后的结构化简历，生成优化版PDF，并按需生成求职信PDF。",
            "需要说明的是，当前版本的前端生成页展示的是“阶段级进度”而非“逐字段实时优化面板”。这是因为章节优化由核心模块内部的并发线程池完成，页面层目前只能稳定感知到阶段状态，而无法低风险地实时接收每个章节的分析结果。该设计虽然在交互细粒度上有所保守，但显著提高了生成流程的稳定性，更适合毕业设计演示环境。",
        ],
        "caption": "图 4-10 简历生成与优化功能时序图",
        "diagram_name": "fig_4_10_generation.png",
        "actors": ["用户", "生成页面", "AutoApplyModel", "Retriever", "LLM", "LaTeX渲染器"],
        "messages": [
            (0, 1, "提交生成请求"),
            (1, 2, "创建模型实例并读取会话配置"),
            (2, 4, "解析简历 / 提取 JD"),
            (4, 2, "返回结构化简历与岗位信息"),
            (2, 3, "按章节检索相关上下文"),
            (3, 2, "返回 RAG 片段"),
            (2, 4, "并发优化选中章节"),
            (4, 2, "返回优化后章节与分析"),
            (2, 5, "渲染原始版与优化版 PDF"),
            (5, 2, "返回 PDF 路径"),
            (2, 1, "回写 generated_result 与状态"),
        ],
    },
    {
        "title": "4.3.5 结果分析功能设计",
        "body": [
            "结果分析模块负责对已生成的简历进行展示、评估和解释。系统会从会话状态中读取优化版PDF路径、原始版路径、结构化简历、结构化JD以及分析器缓存，首先组织结果页的下载与预览区，包括PDF下载、Word导出、Overleaf编辑入口和简历预览。随后模块计算并展示质量分析、匹配度分析、关键词覆盖、词云、改进建议、模拟面试问答和简历对比等内容。",
            "其中，质量分析部分会同时计算“原始匹配度”“当前人岗匹配度”“关键词匹配度”“语义相似度”和“个人特色保留度”等指标，并通过图表和术语说明帮助用户理解分数含义；匹配度分析模块使用雷达图和评分详情展示多维契合情况；词云模块通过高频词可视化帮助用户观察岗位需求与简历关键词重合程度；面试模块则在典型问题之外增加了AI面试助手，用于针对用户回答继续追问并给出点评。若模型调用不可用，改进建议和问答模块会回退到规则化结果，保证页面可正常展示。",
        ],
        "caption": "图 4-11 结果分析功能时序图",
        "diagram_name": "fig_4_11_results.png",
        "actors": ["用户", "结果分析页", "分析器", "LLM", "文件服务"],
        "messages": [
            (0, 1, "打开结果分析页面"),
            (1, 4, "读取 PDF / Word / 对比源文件"),
            (4, 1, "返回文件内容或路径"),
            (1, 2, "计算质量指标 / 雷达图 / 词云"),
            (2, 1, "返回图表数据与评分"),
            (1, 3, "生成建议 / 面试问答 / 助手点评"),
            (3, 1, "返回文本结果"),
            (1, 0, "展示下载、图表与交互面板"),
        ],
    },
    {
        "title": "4.3.6 历史记录管理功能设计",
        "body": [
            "历史记录管理模块承担系统的持久化与回溯能力。每次生成成功后，系统会将用户ID、生成时间、模板风格、模型配置、原始简历路径、优化版PDF路径、求职信路径、结构化简历JSON、结构化JD以及分析结果等信息统一写入数据库。当前版本在原有记录基础上进一步补充了 source_data_json 和 job_details_json 字段，以保证后续从历史版本恢复时，质量分析与结果分析模块能够重新获得完整的上下文。",
            "用户回到用户中心后，系统会根据当前用户ID查询历史记录摘要，并生成模板风格分布、模型配置分布和生成时间分布三张概览图。用户可在列表中查看任意一次生成的状态、模型信息和文件路径，并选择“加载此版本”恢复到当前会话中继续分析，也可以直接删除无效记录。该模块使系统形成了从输入、生成、分析到追溯复用的闭环，提高了整体可维护性和演示完整度。",
        ],
        "caption": "图 4-12 历史记录管理功能时序图",
        "diagram_name": "fig_4_12_history.png",
        "actors": ["用户", "用户中心页面", "会话状态", "ResumeDB"],
        "messages": [
            (1, 3, "保存生成记录与分析结果"),
            (3, 1, "返回保存状态"),
            (0, 1, "进入用户中心"),
            (1, 3, "按 user_id 查询历史摘要"),
            (3, 1, "返回历史概览与记录列表"),
            (0, 1, "点击加载此版本"),
            (1, 3, "按 record_id 查询完整记录"),
            (3, 1, "返回 source_data / job_details / result"),
            (1, 2, "恢复会话状态并跳转页面"),
        ],
    },
    {
        "title": "4.3.7 管理员面板功能设计",
        "body": [
            "管理员面板模块用于展示系统级运营统计和后台维护能力，是当前版本在原有用户端流程之外新增的产品化扩展。该模块采用单独的管理员入口，用户进入管理员页面后，系统首先要求输入预置的管理员用户名与密码；只有校验通过后，才允许访问统计看板、用户管理、记录管理、数据导出以及授权申请处理等功能。由于该模块主要面向毕业设计演示场景，管理员身份校验和普通用户申请管理员权限的流程目前采用前端可见、后端轻量实现的方式完成，在不增加复杂权限系统的前提下，完整展示了后台管理能力。",
            "在已通过身份校验的前提下，管理员面板会调用数据库管理器读取用户总数、今日活跃用户、累计生成记录、今日新增记录等指标，并渲染生成趋势、模板风格分布、模型配置分布以及用户记录数Top10等图表。同时，页面提供用户列表查看、用户名修改、用户删除、记录按条件筛选、单条记录删除，以及CSV数据导出等操作；对于“申请管理员权限”的演示流程，管理员还可以在授权申请页中对待处理申请执行批准或驳回操作。该模块使系统不仅具备面向个人求职者的业务能力，也具备了基本的后台治理与数据运营展示能力。",
        ],
        "caption": "图 4-13 管理员面板功能时序图",
        "diagram_name": "fig_4_13_admin.png",
        "actors": ["管理员", "管理员页面", "会话状态", "ResumeDB"],
        "messages": [
            (0, 1, "输入管理员账号与密码"),
            (1, 2, "写入 admin_authenticated 状态"),
            (1, 3, "读取全局用户与记录统计"),
            (3, 1, "返回指标、图表与列表数据"),
            (0, 1, "执行用户/记录管理操作"),
            (1, 3, "修改用户名 / 删除用户 / 删除记录"),
            (3, 1, "返回更新结果"),
            (0, 1, "处理管理员授权申请"),
            (1, 2, "更新演示态申请结果"),
        ],
    },
]


def set_cn_font():
    if FONT_PATH.exists():
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
        plt.rcParams["axes.unicode_minus"] = False


def add_paragraph_before(anchor: Paragraph, text: str = "", style: str | None = None) -> Paragraph:
    paragraph = anchor.insert_paragraph_before(text)
    if style:
        paragraph.style = style
    return paragraph


def remove_paragraph(paragraph: Paragraph):
    element = paragraph._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def create_sequence_diagram(output_path: Path, actors: list[str], messages: list[tuple[int, int, str]], title: str):
    set_cn_font()
    font_prop = fm.FontProperties(fname=str(FONT_PATH)) if FONT_PATH.exists() else None

    fig, ax = plt.subplots(figsize=(11.2, 5.8), dpi=220)
    ax.set_xlim(-0.5, len(actors) - 0.5)
    ax.set_ylim(0, len(messages) + 2)
    ax.axis("off")

    head_y = len(messages) + 1.2
    line_top = len(messages) + 0.75
    line_bottom = 0.8
    colors = ["#4F8EF7", "#23B5AF", "#F59E0B", "#8B5CF6", "#EF4444", "#14B8A6"]

    for idx, actor in enumerate(actors):
        ax.text(
            idx,
            head_y,
            actor,
            ha="center",
            va="center",
            fontsize=12,
            fontproperties=font_prop,
            bbox=dict(boxstyle="round,pad=0.35", fc="#F7F7FB", ec="#D9DDEA", lw=1.2),
        )
        ax.plot([idx, idx], [line_bottom, line_top], linestyle="--", color="#B8C1D9", linewidth=1.2)

    for msg_index, (src, dst, label) in enumerate(messages, start=1):
        y = len(messages) + 0.2 - msg_index
        color = colors[(msg_index - 1) % len(colors)]
        dx = dst - src
        start_x = src + 0.05 if dx >= 0 else src - 0.05
        end_x = dst - 0.05 if dx >= 0 else dst + 0.05
        ax.annotate(
            "",
            xy=(end_x, y),
            xytext=(start_x, y),
            arrowprops=dict(arrowstyle="->", lw=1.8, color=color),
        )
        ax.text(
            (src + dst) / 2,
            y + 0.18,
            label,
            ha="center",
            va="bottom",
            fontsize=10,
            color="#2D3748",
            fontproperties=font_prop,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.92),
        )

    ax.text(
        (len(actors) - 1) / 2,
        len(messages) + 1.8,
        title,
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        fontproperties=font_prop,
        color="#1F2937",
    )
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def build_assets():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for section in SECTIONS:
        create_sequence_diagram(
            OUTPUT_DIR / section["diagram_name"],
            section["actors"],
            section["messages"],
            section["title"].replace("4.3.", "").replace("功能设计", "时序图"),
        )


def rebuild_section_43():
    if not THESIS_PATH.exists():
        raise FileNotFoundError(f"未找到论文文件：{THESIS_PATH}")

    if not BACKUP_PATH.exists():
        shutil.copy2(THESIS_PATH, BACKUP_PATH)

    doc = Document(str(THESIS_PATH))
    paragraphs = doc.paragraphs

    start_idx = next(i for i, p in enumerate(paragraphs) if p.text.strip() == "4.3 系统详细设计")
    end_idx = next(i for i, p in enumerate(paragraphs) if p.text.strip() == "4.4 核心算法设计")
    anchor = paragraphs[end_idx]

    for paragraph in doc.paragraphs[start_idx + 1 : end_idx]:
        remove_paragraph(paragraph)

    content_blocks: list[tuple[str, str | Path]] = []
    content_blocks.append(
        (
            "paragraph",
            "本节结合当前版本系统的实际实现，对用户管理、数据输入、模型配置、简历生成与优化、结果分析以及历史记录管理六个核心模块进行详细设计说明。与前文总体设计不同，本节重点描述页面层、会话状态、数据库与核心服务之间的协作方式，并通过时序图展示关键交互过程，以说明系统在真实运行时的处理链路。",
        )
    )

    for section in SECTIONS:
        content_blocks.append(("subtitle", section["title"]))
        for body_paragraph in section["body"]:
            content_blocks.append(("paragraph", body_paragraph))
        content_blocks.append(("image", OUTPUT_DIR / section["diagram_name"]))
        content_blocks.append(("caption", section["caption"]))
        content_blocks.append(("blank", ""))

    for block_type, payload in content_blocks:
        if block_type == "subtitle":
            paragraph = add_paragraph_before(anchor, str(payload), style="Normal")
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(12)
        elif block_type == "paragraph":
            paragraph = add_paragraph_before(anchor, str(payload), style="Normal")
            paragraph.paragraph_format.first_line_indent = Cm(0.74)
            paragraph.paragraph_format.line_spacing = 1.5
        elif block_type == "caption":
            paragraph = add_paragraph_before(anchor, str(payload), style="Normal")
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif block_type == "image":
            paragraph = add_paragraph_before(anchor, "", style="Normal")
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.add_run()
            run.add_picture(str(payload), width=Cm(15.8))
        elif block_type == "blank":
            add_paragraph_before(anchor, "", style="Normal")

    doc.save(str(THESIS_PATH))


def main():
    build_assets()
    rebuild_section_43()
    print(f"Updated: {THESIS_PATH}")
    print(f"Backup: {BACKUP_PATH}")
    print(f"Assets: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
