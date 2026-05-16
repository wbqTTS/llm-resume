import base64
import json
import os
import time
from datetime import datetime
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.font_manager import FontProperties
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from wbq.ui.app_context import *
from wbq.ui.constants import STEP_GENERATION


TERM_EXPLANATIONS = [
    {"术语": "关键词匹配度", "说明": "衡量简历与岗位描述中核心关键词的直接重合程度，越高说明命中了更多岗位明确要求。"},
    {"术语": "语义相似度", "说明": "衡量简历表述与岗位要求在整体语义上的接近程度，即使词不完全一致也能反映匹配情况。"},
    {"术语": "个人特色保留度", "说明": "衡量优化后简历保留原始经历亮点和个人风格的程度，越高越不容易失真。"},
    {"术语": "人岗匹配度", "说明": "衡量优化后简历与目标岗位要求的贴合程度，是当前最值得关注的核心指标。"},
    {"术语": "原始匹配度", "说明": "衡量原始简历与岗位描述的贴合程度，可作为优化前基线。"},
]


class CachedAnalyzer:
    def __init__(self, scores, suggestions, questions, radar, wordcloud):
        self.scores = scores or {}
        self._suggestions = suggestions or []
        self._questions = questions or []
        self._radar = radar
        self._wordcloud = wordcloud

    def get_radar_chart(self):
        return self._radar

    def get_wordcloud(self):
        return self._wordcloud

    def get_improvement_suggestions(self):
        return self._suggestions

    def get_interview_questions(self, top_k=5):
        return self._questions[:top_k] if self._questions else []

    def export_report(self, output_path: str, quality_analysis_data: dict | None = None) -> str:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        font_registered = False
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            FONT_PATH,
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                    font_registered = True
                    break
                except Exception:
                    continue

        if font_registered:
            chinese_style = ParagraphStyle("ChineseStyle", parent=styles["Normal"], fontName="ChineseFont", fontSize=10, leading=14)
            title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontName="ChineseFont", fontSize=16, leading=20)
            heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading1"], fontName="ChineseFont", fontSize=12, leading=16)
            font_name = "ChineseFont"
        else:
            chinese_style = styles["Normal"]
            title_style = styles["Title"]
            heading_style = styles["Heading1"]
            font_name = "Helvetica"

        story = [Paragraph("简历诊断报告", title_style), Spacer(1, 12 * mm)]
        story.append(Paragraph("一、匹配度评分", heading_style))
        story.append(Spacer(1, 6 * mm))
        score_data = [["维度", "得分"]] + [[k, f"{v}%"] for k, v in self.scores.items()]
        score_table = Table(score_data, colWidths=[100 * mm, 40 * mm])
        score_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(score_table)
        story.append(Spacer(1, 10 * mm))

        story.append(Paragraph("二、质量分析", heading_style))
        story.append(Spacer(1, 6 * mm))
        if quality_analysis_data:
            quality_rows = [
                ["指标", "个人特色保留度", "人岗匹配度", "原始匹配度"],
                [
                    "关键词匹配度",
                    f"{quality_analysis_data.get('overlap_user', 0):.3f}",
                    f"{quality_analysis_data.get('overlap_job', 0):.3f}",
                    f"{quality_analysis_data.get('overlap_match', 0):.3f}",
                ],
                [
                    "语义相似度",
                    f"{quality_analysis_data.get('cosine_user', 0):.3f}",
                    f"{quality_analysis_data.get('cosine_job', 0):.3f}",
                    f"{quality_analysis_data.get('cosine_match', 0):.3f}",
                ],
            ]
            quality_table = Table(quality_rows, colWidths=[50 * mm, 45 * mm, 45 * mm, 45 * mm])
            quality_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            story.append(quality_table)
        else:
            story.append(Paragraph("当前没有可导出的质量分析数据。", chinese_style))
        story.append(Spacer(1, 10 * mm))

        story.append(Paragraph("三、改进建议", heading_style))
        story.append(Spacer(1, 6 * mm))
        for suggestion in self.get_improvement_suggestions():
            story.append(Paragraph(f"- {suggestion.get('dimension', '建议')}: {suggestion.get('suggestion', '')}", chinese_style))
            story.append(Spacer(1, 4 * mm))
        story.append(Spacer(1, 10 * mm))

        story.append(Paragraph("四、模拟面试问题", heading_style))
        story.append(Spacer(1, 6 * mm))
        for index, question in enumerate(self.get_interview_questions(top_k=5), start=1):
            story.append(Paragraph(f"{index}. {question.get('question', '')}", chinese_style))
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(f"回答思路：{question.get('suggestion', '')}", chinese_style))
            story.append(Spacer(1, 6 * mm))
        doc.build(story)
        return output_path


def _get_font_properties():
    if FONT_PATH and os.path.exists(FONT_PATH):
        return FontProperties(fname=FONT_PATH)
    return None


def _apply_axis_font(ax, font_prop):
    if not font_prop:
        return
    ax.set_title(ax.get_title(), fontproperties=font_prop)
    ax.set_xlabel(ax.get_xlabel(), fontproperties=font_prop)
    ax.set_ylabel(ax.get_ylabel(), fontproperties=font_prop)
    for label in ax.get_xticklabels():
        label.set_fontproperties(font_prop)
        label.set_rotation(0)
    for label in ax.get_yticklabels():
        label.set_fontproperties(font_prop)
    legend = ax.get_legend()
    if legend:
        for text in legend.get_texts():
            text.set_fontproperties(font_prop)


def _encode_delta(delta: float) -> tuple[str, str]:
    if delta > 0:
        return f"↑ {delta:.3f}", "normal"
    if delta < 0:
        return f"↓ {abs(delta):.3f}", "inverse"
    return "0.000", "off"


def _quality_chart_figure(quality_data: dict):
    font_prop = _get_font_properties()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    overlap_values = [quality_data.get("overlap_user", 0), quality_data.get("overlap_job", 0), quality_data.get("overlap_match", 0)]
    cosine_values = [quality_data.get("cosine_user", 0), quality_data.get("cosine_job", 0), quality_data.get("cosine_match", 0)]
    labels = ["个人特色保留", "优化后匹配", "原始基线"]

    chart_defs = [
        (axes[0], overlap_values, "关键词匹配度对比", ["#60A5FA", "#22C55E", "#F59E0B"]),
        (axes[1], cosine_values, "语义相似度对比", ["#818CF8", "#14B8A6", "#FB7185"]),
    ]
    for ax, values, title, colors_ in chart_defs:
        bars = ax.bar(labels, values, color=colors_, width=0.56)
        ax.set_ylim(0, 1)
        ax.set_ylabel("得分")
        ax.set_title(title)
        ax.grid(axis="y", linestyle="--", alpha=0.25)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.3f}", ha="center", fontsize=8)
        _apply_axis_font(ax, font_prop)
    fig.tight_layout()
    return fig


def _render_quality_metric_section(title: str, prefix: str, quality_data: dict) -> None:
    st.markdown(f"#### {title}")
    preserve = quality_data.get(f"{prefix}_user", 0)
    current = quality_data.get(f"{prefix}_job", 0)
    baseline = quality_data.get(f"{prefix}_match", 0)
    delta_text, delta_color = _encode_delta(current - baseline)
    col1, col2, col3 = st.columns(3)
    col1.metric("个人特色保留度", f"{preserve:.3f}")
    col2.metric("优化后人岗匹配度", f"{current:.3f}", delta=delta_text, delta_color=delta_color)
    col3.metric("原始匹配度", f"{baseline:.3f}")


def _render_quality_term_explanations():
    with st.expander("查看指标术语说明", expanded=False):
        st.dataframe(pd.DataFrame(TERM_EXPLANATIONS), use_container_width=True, hide_index=True)


def _split_interview_reply_segments(reply: str) -> list[str]:
    normalized = (reply or "").replace("\r\n", "\n").strip()
    if not normalized:
        return []

    paragraph_blocks = [block.strip() for block in normalized.split("\n\n") if block.strip()]
    if len(paragraph_blocks) > 1:
        return paragraph_blocks

    lines = [line.strip() for line in normalized.split("\n") if line.strip()]
    if len(lines) <= 1:
        return [normalized]

    trigger_prefixes = ("总体评价", "亮点", "不足", "改进建议", "建议", "下一题", "下一问", "本轮总结", "总结")
    segments = []
    current = []
    for line in lines:
        if current and (line.startswith(trigger_prefixes) or line[:2].isdigit() or line[:1].isdigit()):
            segments.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        segments.append("\n".join(current))
    return segments or [normalized]


def _build_interview_fallback_reply(next_question: str | None) -> str:
    fallback_lines = [
        "你的回答已经覆盖了一部分关键点，但还可以再更像面试现场一些。",
        "建议补充：",
        "1. 明确你在项目中的个人职责，而不是只说团队结果。",
        "2. 给出量化结果，例如性能提升、效率提升或业务收益。",
        "3. 更直接地把回答和岗位要求里的技术关键词挂钩。",
    ]
    if next_question:
        fallback_lines.append(f"下一题：{next_question}")
    else:
        fallback_lines.append("这一轮已经完成，整体建议是把表达再聚焦到岗位价值和个人贡献上。")
    return "\n".join(fallback_lines)


def _render_interview_assistant(analyzer) -> None:
    st.markdown("#### AI 面试助手")
    st.caption("助手会结合你的简历、岗位要求和模拟面试题，逐题追问，并对你的回答给出点评与改进建议。")

    questions = analyzer.get_interview_questions(top_k=5) if analyzer else []
    llm_instance = st.session_state.get("llm_instance")
    state = st.session_state.setdefault("interview_assistant_state", {"messages": [], "question_index": 0, "current_question": None})

    def seed_conversation():
        opener = "你好，我是你的 AI 面试官。我们会围绕这份简历做一轮模拟面试。"
        first_question = (
            questions[0].get("question", "请先做一个简短的自我介绍，并结合岗位谈谈你的优势。")
            if questions
            else "请先做一个简短的自我介绍，并结合岗位谈谈你的优势。"
        )
        opener += f"\n\n第一题：{first_question}"
        state["current_question"] = first_question
        state["question_index"] = 0
        state["messages"] = [{"role": "assistant", "content": opener}]

    if not state["messages"]:
        seed_conversation()

    _, restart_col = st.columns([0.7, 0.3])
    with restart_col:
        if st.button("重新开始模拟", key="interview_restart", use_container_width=True):
            seed_conversation()
            st.rerun()

    for message in state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_reply = st.chat_input("输入你的回答，AI 面试官会继续追问并点评。", key="interview_chat_input")
    if not user_reply:
        return

    state["messages"].append({"role": "user", "content": user_reply})
    with st.chat_message("user"):
        st.markdown(user_reply)

    current_question = state.get("current_question") or "请做一个与岗位相关的自我介绍。"
    question_hint = questions[state["question_index"]].get("suggestion", "") if questions and state["question_index"] < len(questions) else ""
    next_index = state["question_index"] + 1
    next_question = questions[next_index].get("question") if questions and next_index < len(questions) else None

    prompt = f"""
你现在扮演一位专业、友好、会给反馈的技术面试官。
【岗位信息】{json.dumps(st.session_state.get("temp_job_details", {}), ensure_ascii=False)[:2200]}

【候选人简历】{json.dumps(st.session_state.get("generated_result", {}).get("resume_details", {}), ensure_ascii=False)[:3200]}

【当前问题】{current_question}

【推荐回答思路】{question_hint or "无"}

【候选人回答】{user_reply}

【下一题】{next_question or "如果没有下一题，请做本轮总结。"}

请输出一段自然中文回复：
1. 先评价这次回答的亮点和不足。
2. 给出 2-3 条具体改进建议。
3. 如果还有下一题，直接抛出下一题；否则做本轮总结。
4. 不要输出 JSON，不要表格。
"""

    assistant_reply = None
    with st.chat_message("assistant"):
        phase_placeholder = st.empty()
        reply_placeholder = st.empty()

        phase_placeholder.info("AI 面试官正在阅读你的回答...")
        time.sleep(0.08)

        if llm_instance:
            phase_placeholder.info("AI 面试官正在结合岗位要求和简历经历分析...")
            try:
                assistant_reply = llm_instance.get_response(prompt=prompt, expecting_longer_output=True, need_json_output=False)
            except Exception as exc:
                assistant_reply = (
                    "这次回答的关键信息还不够聚焦。建议你补充更具体的项目细节、量化结果和岗位相关性。\n\n"
                    f"我先用兜底模式继续。错误信息：{exc}"
                )

        if not assistant_reply:
            assistant_reply = _build_interview_fallback_reply(next_question)

        phase_placeholder.success("AI 面试官已完成分析，正在分段整理反馈...")
        segments = _split_interview_reply_segments(assistant_reply)
        rendered_segments = []
        for index, segment in enumerate(segments, start=1):
            rendered_segments.append(segment)
            reply_placeholder.markdown("\n\n".join(rendered_segments))
            if index < len(segments):
                phase_placeholder.info(f"AI 面试官正在输出第 {index + 1}/{len(segments)} 段反馈...")
                time.sleep(0.12)
        phase_placeholder.success("AI 面试官回复完成")

    state["messages"].append({"role": "assistant", "content": assistant_reply})
    state["question_index"] = min(next_index, len(questions) - 1 if questions else 0)
    state["current_question"] = next_question or current_question


def render_generation_config(res: dict) -> None:
    with st.expander("本次生成配置", expanded=False):
        st.markdown(f"- **简历风格**：{res.get('style', '未指定')}")
        optimized_fields = res.get("optimized_fields") or []
        st.markdown(f"- **优化字段**：{', '.join(optimized_fields) if optimized_fields else '仅排版，不做内容优化'}")
        st.markdown("---")
        st.markdown("### 大模型配置")
        llm_config = st.session_state.get("llm_config", {})
        if not llm_config:
            st.caption("未找到本次生成时的大模型配置。")
            return
        st.markdown(f"- **提供商**：{llm_config.get('display_provider') or llm_config.get('provider', '未指定')}")
        st.markdown(f"- **模型**：{llm_config.get('display_model') or llm_config.get('model', '未指定')}")
        api_key = llm_config.get("api_key")
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            st.markdown(f"- **API Key**：{masked}")
        else:
            st.markdown("- **API Key**：未显式填写，可能使用环境变量或本地模型。")


def render_quick_actions(res: dict) -> None:
    st.markdown("### 常用操作")
    action_cols = st.columns(4)
    resume_file = res.get("resume_path")
    cv_file = res.get("cv_path")
    if resume_file and os.path.exists(resume_file):
        action_cols[0].download_button("下载简历 PDF", data=read_file(resume_file, "rb"), file_name=os.path.basename(resume_file), mime="application/pdf", use_container_width=True, key="quick_download_resume_pdf")
    else:
        action_cols[0].button("下载简历 PDF", disabled=True, use_container_width=True, key="quick_download_resume_pdf_disabled")
    if cv_file and os.path.exists(cv_file):
        action_cols[1].download_button("下载求职信 PDF", data=read_file(cv_file, "rb"), file_name=os.path.basename(cv_file), mime="application/pdf", use_container_width=True, key="quick_download_cv_pdf")
    else:
        action_cols[1].button("下载求职信 PDF", disabled=True, use_container_width=True, key="quick_download_cv_pdf_disabled")
    if action_cols[2].button("重新生成", use_container_width=True, key="quick_regenerate"):
        set_step(STEP_GENERATION)
        st.rerun()
    if action_cols[3].button("稍后保存到历史", use_container_width=True, key="quick_save_hint"):
        st.info("页面底部可以把完整分析结果保存到数据库。")


def get_results_analyzer(res: dict):
    has_cached_analysis = any([res.get("analyzer_scores"), res.get("analyzer_suggestions"), res.get("analyzer_questions"), res.get("analyzer_radar"), res.get("analyzer_wordcloud")])
    if has_cached_analysis:
        return CachedAnalyzer(
            scores=res.get("analyzer_scores", {}),
            suggestions=res.get("analyzer_suggestions", []),
            questions=res.get("analyzer_questions", []),
            radar=res.get("analyzer_radar"),
            wordcloud=res.get("analyzer_wordcloud"),
        )
    if "resume_details" not in res or not st.session_state.get("temp_job_details"):
        return None
    try:
        from wbq.utils.resume_analyzer import analyze_resume

        return analyze_resume(
            resume_details=res["resume_details"],
            job_details=st.session_state["temp_job_details"],
            user_data=st.session_state.get("temp_user_data"),
            llm_instance=st.session_state.get("llm_instance"),
        )
    except Exception as exc:
        st.warning(f"分析器初始化失败，将仅展示基础分析：{str(exc)[:100]}")
        return None


def render_resume_preview_tab(res: dict) -> None:
    resume_path = res.get("resume_path")
    if resume_path:
        st.markdown("### 生成的简历")
        col1, col2, col3, col4 = st.columns(4)
        if os.path.exists(resume_path):
            with col1:
                st.download_button(
                    label="下载 PDF",
                    data=read_file(resume_path, "rb"),
                    file_name=os.path.basename(resume_path),
                    key="download_pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            with col2:
                word_key = f"word_converted_{os.path.basename(resume_path)}"
                st.session_state.setdefault(word_key, None)
                if st.session_state.get(word_key) and os.path.exists(st.session_state[word_key]):
                    st.download_button(
                        label="下载 Word",
                        data=read_file(st.session_state[word_key], "rb"),
                        file_name=os.path.basename(st.session_state[word_key]),
                        key="download_word",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                else:
                    if st.button("生成 Word", key="btn_convert_word", use_container_width=True):
                        with st.spinner("正在将 PDF 转换为 Word，请稍候..."):
                            word_path = convert_pdf_to_word(resume_path)
                            if word_path and os.path.exists(word_path):
                                st.session_state[word_key] = word_path
                                st.success("Word 转换完成。")
                                st.rerun()
                            else:
                                st.error("Word 转换失败，请稍后重试。")
            with col3:
                create_overleaf_button(resume_path)
            with col4:
                st.caption(os.path.basename(resume_path))
            display_pdf(resume_path, type="image")
        else:
            st.error(f"简历 PDF 不存在：{resume_path}")

    cv_path = res.get("cv_path")
    if cv_path:
        st.divider()
        st.markdown("### 生成的求职信")
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.markdown(res.get("cv_details", "暂无内容"), unsafe_allow_html=True)
        with col2:
            if os.path.exists(cv_path):
                st.download_button(
                    label="下载求职信 PDF",
                    data=read_file(cv_path, "rb"),
                    file_name=os.path.basename(cv_path),
                    key="download_cv",
                    mime="application/pdf",
                    use_container_width=True,
                )


def render_quality_analysis_tab(res: dict) -> None:
    st.subheader("简历质量分析")
    user_data = st.session_state.get("temp_user_data")
    job_data = st.session_state.get("temp_job_details")
    resume_details = res.get("resume_details", {})
    if not (user_data and job_data):
        st.info("缺少用户原始数据或 JD 缓存，暂时无法计算质量指标。")
        return

    quality_data = _build_quality_analysis_data(res)
    if quality_data:
        _render_quality_term_explanations()
        render_left, render_right = st.columns([1.1, 0.9])
        with render_left:
            _render_quality_metric_section("关键词匹配度", "overlap", quality_data)
            st.markdown("")
            _render_quality_metric_section("语义相似度", "cosine", quality_data)
        with render_right:
            fig = _quality_chart_figure(quality_data)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

    st.divider()
    st.markdown("#### 质量检查")
    st.dataframe(resume_quality_checks(resume_details, job_data or {}), use_container_width=True, hide_index=True)
    keyword_summary = compare_resume_keywords(user_data or {}, resume_details, job_data or {})
    if any(keyword_summary.values()):
        st.markdown("#### 优化关键词摘要")
        c1, c2, c3 = st.columns(3)
        c1.metric("新增关键词", len(keyword_summary["新增关键词"]))
        c2.metric("保留关键词", len(keyword_summary["保留关键词"]))
        c3.metric("仍待补充", len(keyword_summary["仍待补充"]))
        if keyword_summary["新增关键词"]:
            st.success("新增关键词：" + "、".join(keyword_summary["新增关键词"][:10]))
        if keyword_summary["仍待补充"]:
            st.warning("仍待补充：" + "、".join(keyword_summary["仍待补充"][:10]))


def render_match_analysis_tab(res: dict, analyzer) -> None:
    st.subheader("匹配度分析")
    st.markdown("雷达图用于从多个维度观察优化后简历和目标岗位之间的契合情况。分值越高，说明该维度越贴近岗位要求。")
    coverage_rows = keyword_coverage(res.get("resume_details", {}), st.session_state.get("temp_job_details", {}))
    if coverage_rows:
        st.markdown("#### 岗位关键词覆盖表")
        st.dataframe(coverage_rows, use_container_width=True, hide_index=True)
    if not analyzer:
        st.info("当前没有可用的分析器，请重新生成后查看雷达图和评分。")
        return

    try:
        radar_img = analyzer.get_radar_chart()
        if radar_img and not st.session_state["generated_result"].get("analyzer_radar"):
            st.session_state["generated_result"]["analyzer_radar"] = radar_img
        scores = getattr(analyzer, "scores", None) or {}
        if scores and not st.session_state["generated_result"].get("analyzer_scores"):
            st.session_state["generated_result"]["analyzer_scores"] = scores

        left, right = st.columns([1.15, 0.85])
        with left:
            if radar_img:
                st.image(radar_img, use_column_width=True)
            else:
                st.info("暂无雷达图数据。")
        with right:
            if scores:
                st.markdown("#### 评分详情")
                for dim, score in scores.items():
                    st.progress(score / 100, text=f"{dim}: {score}%")
            else:
                st.info("暂无评分详情。")
        if scores:
            interpretation_rows = score_interpretations(scores)
            if interpretation_rows:
                st.markdown("#### 指标含义与建议")
                st.dataframe(interpretation_rows, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.warning(f"匹配度图表生成失败：{exc}")


def render_wordcloud_tab(analyzer) -> None:
    st.subheader("词云分析")
    st.markdown("词云可以帮助你快速观察简历与岗位描述中的高频关键词。词越大，代表它在文本中出现得越频繁，也越可能是当前岗位最看重的内容。")
    tip_cols = st.columns(3)
    tip_cols[0].info("看大词：优先关注最大、最显眼的关键词，它们通常代表岗位核心技能。")
    tip_cols[1].info("看缺口：如果 JD 关键技术没有明显出现，说明简历还可以补强相关表达。")
    tip_cols[2].info("看重合：同时在简历与 JD 中反复出现的词，往往是你最该突出展示的竞争力。")
    if not analyzer:
        st.info("当前没有可用的分析器，无法生成词云。")
        return
    try:
        wordcloud_img = analyzer.get_wordcloud()
        if wordcloud_img and not st.session_state["generated_result"].get("analyzer_wordcloud"):
            st.session_state["generated_result"]["analyzer_wordcloud"] = wordcloud_img
        if wordcloud_img:
            st.image(wordcloud_img, use_column_width=True)
            st.caption("如果岗位核心技能没有在词云中明显出现，通常意味着简历里还缺少对应关键词或项目场景。")
        else:
            st.info("暂无词云数据。")
    except Exception as exc:
        st.warning(f"词云生成失败：{exc}")


def _build_quality_analysis_data(res: dict):
    user_data = st.session_state.get("temp_user_data")
    job_data = st.session_state.get("temp_job_details")
    resume_details = res.get("resume_details", {})
    if not (user_data and job_data):
        return None
    try:
        return {
            "overlap_user": overlap_coefficient(json.dumps(resume_details, ensure_ascii=False), json.dumps(user_data, ensure_ascii=False)),
            "overlap_job": overlap_coefficient(json.dumps(resume_details, ensure_ascii=False), json.dumps(job_data, ensure_ascii=False)),
            "overlap_match": overlap_coefficient(json.dumps(user_data, ensure_ascii=False), json.dumps(job_data, ensure_ascii=False)),
            "cosine_user": cosine_similarity(json.dumps(resume_details, ensure_ascii=False), json.dumps(user_data, ensure_ascii=False)),
            "cosine_job": cosine_similarity(json.dumps(resume_details, ensure_ascii=False), json.dumps(job_data, ensure_ascii=False)),
            "cosine_match": cosine_similarity(json.dumps(user_data, ensure_ascii=False), json.dumps(job_data, ensure_ascii=False)),
        }
    except Exception as exc:
        st.warning(f"质量分析数据计算失败：{exc}")
        return None


def render_suggestions_tab(res: dict, analyzer) -> None:
    st.subheader("AI 改进建议")
    if not analyzer:
        st.info("当前没有可用的分析器，无法生成改进建议。")
        return
    try:
        suggestions = analyzer.get_improvement_suggestions()
        if suggestions and not st.session_state["generated_result"].get("analyzer_suggestions"):
            st.session_state["generated_result"]["analyzer_suggestions"] = suggestions
        if suggestions:
            for suggestion in suggestions:
                title = suggestion.get("dimension", "建议")
                message = suggestion.get("suggestion", "")
                level = suggestion.get("level")
                if level == "error":
                    st.error(f"**{title}**\n\n{message}")
                elif level == "warning":
                    st.warning(f"**{title}**\n\n{message}")
                elif level == "info":
                    st.info(f"**{title}**\n\n{message}")
                else:
                    st.success(f"**{title}**\n\n{message}")
        else:
            st.info("暂无改进建议。")
        st.divider()
        if st.button("导出完整分析报告（PDF）", use_container_width=True, key="export_analysis_report"):
            with st.spinner("正在生成分析报告..."):
                resume_path = res.get("resume_path", "")
                if not resume_path or not os.path.exists(resume_path):
                    st.error("未找到简历文件，无法生成报告。")
                    return
                report_path = os.path.join(os.path.dirname(resume_path), "resume_analysis_report.pdf")
                analyzer.export_report(report_path, quality_analysis_data=_build_quality_analysis_data(res))
                if os.path.exists(report_path):
                    st.download_button("点击下载分析报告", data=read_file(report_path, "rb"), file_name="resume_analysis_report.pdf", mime="application/pdf", use_container_width=True, key="download_analysis_report")
                    st.success("分析报告已生成。")
                else:
                    st.error("分析报告生成失败，请稍后重试。")
    except Exception as exc:
        st.warning(f"改进建议生成失败：{exc}")


def render_interview_tab(analyzer) -> None:
    st.subheader("模拟面试问答")
    st.markdown("这里会根据你的简历内容和岗位要求给出典型面试问题、回答思路，以及一位可以追问和点评的 AI 面试官。")
    if not analyzer:
        st.info("当前没有可用的分析器，无法生成面试问答。")
        return
    try:
        questions = analyzer.get_interview_questions(top_k=5)
        if questions and not st.session_state["generated_result"].get("analyzer_questions"):
            st.session_state["generated_result"]["analyzer_questions"] = questions
        if questions:
            st.markdown("#### 典型面试问题")
            for index, question in enumerate(questions, start=1):
                with st.expander(f"问题 {index}：{question.get('question', '未提供问题')}", expanded=index == 1):
                    st.markdown(
                        f"""
                        <div style="padding:10px 12px; border-radius:10px; background:#EEF4FF; color:#1D4ED8; font-weight:600; margin-bottom:10px;">
                            问题：{question.get('question', '未提供问题')}
                        </div>
                        <div style="padding:10px 12px; border-radius:10px; background:#ECFDF5; color:#047857;">
                            回答思路：{question.get('suggestion', '暂无建议')}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("暂无面试问题。")
        st.divider()
        _render_interview_assistant(analyzer)
    except Exception as exc:
        st.warning(f"面试问答生成失败：{exc}")


def render_comparison_tab(res: dict) -> None:
    st.subheader("原始简历 vs 优化后简历")
    st.markdown("对比摘要会帮助你判断本次 AI 优化主要加强了哪些内容。")
    raw_resume_path = res.get("raw_resume_path")
    optimized_resume_path = res.get("resume_path")
    if not raw_resume_path or not optimized_resume_path:
        st.warning("缺少原始简历或优化后简历，无法进行对比。")
        return
    if not os.path.exists(raw_resume_path):
        st.error(f"原始简历文件不存在：{raw_resume_path}")
        return
    if not os.path.exists(optimized_resume_path):
        st.error(f"优化后简历文件不存在：{optimized_resume_path}")
        return

    @st.cache_data
    def load_resume_texts(original_path, optimized_path):
        return extract_text_from_pdf(original_path), extract_text_from_pdf(optimized_path)

    with st.spinner("正在提取 PDF 文本内容..."):
        original_text, optimized_text = load_resume_texts(raw_resume_path, optimized_resume_path)
    if original_text is None or optimized_text is None:
        st.error("无法提取 PDF 文本内容，请确认文件未加密且格式正确。")
        return
    with st.spinner("正在分析简历差异..."):
        changes, diff_html = compare_resumes(original_text, optimized_text)
    st.markdown("### 对比统计")
    display_comparison_changes(changes)
    st.markdown("### 关键变化摘要")
    st.markdown(
        f"""
- **保留内容**：约 {changes['similarity'] * 100:.1f}% 的原有内容被保留
- **新增内容**：新增了 {changes['added']} 行内容，主要用于贴合岗位要求
- **删减内容**：删减了 {changes['removed']} 行内容，通常是弱相关信息
- **修改内容**：修改了 {changes['modified']} 行内容，用于提升表述的专业度和针对性
"""
    )
    st.markdown("### 详细差异对比")
    st.caption("绿色表示新增，红色表示删减。")
    st.components.v1.html(diff_html, height=600, scrolling=True)
    st.divider()
    if st.button("导出对比报告（HTML）", use_container_width=True, key="export_comparison_report"):
        report_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>简历对比报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #1E88E5; }}
        .stats {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .metric {{ display: inline-block; margin-right: 30px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ color: #666; }}
    </style>
</head>
<body>
    <h1>简历优化对比报告</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <div class="stats">
        <h2>对比统计</h2>
        <div class="metric"><div class="metric-value">{changes['similarity'] * 100:.1f}%</div><div class="metric-label">相似度</div></div>
        <div class="metric"><div class="metric-value">{changes['added']}</div><div class="metric-label">新增内容</div></div>
        <div class="metric"><div class="metric-value">{changes['removed']}</div><div class="metric-label">删减内容</div></div>
        <div class="metric"><div class="metric-value">{changes['modified']}</div><div class="metric-label">修改内容</div></div>
    </div>
    <h2>详细差异对比</h2>
    {diff_html}
</body>
</html>
"""
        st.download_button("点击下载对比报告", data=report_html.encode("utf-8"), file_name=f"resume_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", mime="text/html", use_container_width=True, key="download_comparison_report")
        st.success("对比报告已生成。")


def render_save_section(res: dict) -> None:
    st.divider()
    if st.session_state.get("analysis_saved_to_db"):
        st.success("当前分析结果已保存到数据库。")
    else:
        st.info("点击下方按钮可将本次分析结果保存到数据库。")
    _, center, _ = st.columns([1, 2, 1])
    with center:
        if st.button("保存分析结果到数据库", use_container_width=True, type="primary", key="save_results_to_db"):
            with st.spinner("正在保存..."):
                radar_img = st.session_state["generated_result"].get("analyzer_radar")
                if radar_img and not isinstance(radar_img, str):
                    buffered = BytesIO()
                    radar_img.save(buffered, format="PNG")
                    st.session_state["generated_result"]["analyzer_radar"] = base64.b64encode(buffered.getvalue()).decode()
                wordcloud_img = st.session_state["generated_result"].get("analyzer_wordcloud")
                if wordcloud_img and not isinstance(wordcloud_img, str):
                    buffered = BytesIO()
                    wordcloud_img.save(buffered, format="PNG")
                    st.session_state["generated_result"]["analyzer_wordcloud"] = base64.b64encode(buffered.getvalue()).decode()
                try:
                    llm_config = st.session_state.get("llm_config", {})
                    record_id = db.save_resume_record(
                        st.session_state.get("user_id"),
                        st.session_state.get("resume_source"),
                        st.session_state["generated_result"].get("original_resume_path"),
                        st.session_state.get("form_data", {}),
                        st.session_state["generated_result"].get("resume_details"),
                        st.session_state["generated_result"].get("resume_path"),
                        st.session_state["generated_result"].get("cv_path"),
                        st.session_state["generated_result"].get("raw_resume_path"),
                        st.session_state["generated_result"].get("cv_details"),
                        st.session_state.get("selected_style"),
                        st.session_state["generated_result"].get("optimized_fields"),
                        st.session_state["generated_result"].get("jd_url", ""),
                        st.session_state["generated_result"].get("jd_text", ""),
                        st.session_state["generated_result"].get("analyzer_scores"),
                        st.session_state["generated_result"].get("analyzer_suggestions"),
                        st.session_state["generated_result"].get("analyzer_questions"),
                        st.session_state["generated_result"].get("analyzer_radar"),
                        st.session_state["generated_result"].get("analyzer_wordcloud"),
                        llm_config.get("display_provider") or llm_config.get("provider", ""),
                        llm_config.get("display_model") or llm_config.get("model", ""),
                        source_data=st.session_state.get("temp_user_data", {}),
                        job_details=st.session_state.get("temp_job_details", {}),
                    )
                    st.session_state["analysis_saved_to_db"] = True
                    st.session_state["current_record_id"] = record_id
                    st.success(f"分析结果已保存，记录 ID：{record_id}")
                    time.sleep(1)
                    st.rerun()
                except Exception as exc:
                    st.error(f"保存失败：{exc}")


def render_footer_actions() -> None:
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("重新生成", use_container_width=True, key="footer_regenerate"):
            set_step(STEP_GENERATION)
            st.rerun()
    with col2:
        if st.button("清空结果", use_container_width=True, key="footer_clear_results"):
            st.session_state["generated_result"] = {}
            st.session_state["interview_assistant_state"] = {"messages": [], "question_index": 0, "current_question": None}
            st.rerun()
