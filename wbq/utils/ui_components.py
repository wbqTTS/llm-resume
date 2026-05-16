import os

import streamlit as st

from wbq.utils.app_support import (
    DEMO_JOB_TEXT,
    DEMO_RESUME_DATA,
    GENERATION_STEPS,
    ensure_demo_resume_file,
)


SECTION_LABELS = {
    "education": "教育背景",
    "work_experience": "工作经历",
    "projects": "项目经历",
    "skill_section": "专业技能",
    "social_practice": "社会实践",
    "research_experience": "研究经历",
    "teaching_experience": "教学经历",
    "academic_service": "学术服务",
}


def _section_label(section_name: str) -> str:
    return SECTION_LABELS.get(section_name, section_name.replace("_", " ").title())


def render_generation_progress(active_step: str, progress_value: int):
    """渲染生成阶段面板，帮助用户理解当前流程。"""
    st.progress(progress_value)
    cols = st.columns(len(GENERATION_STEPS))
    for index, (step_name, step_progress) in enumerate(GENERATION_STEPS):
        if step_name == active_step:
            state_class = "rf-stage rf-stage-active"
            mark = "进行中"
        elif step_progress < progress_value:
            state_class = "rf-stage rf-stage-done"
            mark = "完成"
        else:
            state_class = "rf-stage"
            mark = "等待"
        cols[index].markdown(
            f"<div class='{state_class}'><div>{step_name}</div><small>{mark}</small></div>",
            unsafe_allow_html=True,
        )


def render_ai_optimization_details(events: list[dict]):
    """渲染 AI 优化阶段的章节级实时详情。"""
    st.markdown("#### AI 优化详情")
    if not events:
        st.caption("章节级优化结果会在这里实时刷新。")
        return

    completed_statuses = {"optimized", "skipped", "fallback"}
    completed_count = sum(1 for event in events if event.get("status") in completed_statuses)
    total_count = len(events)
    latest_completed = next(
        (event for event in reversed(events) if event.get("status") in completed_statuses),
        None,
    )

    if completed_count < total_count:
        latest_text = (
            f"，最近完成：{_section_label(latest_completed.get('section_name', 'unknown'))}"
            if latest_completed
            else ""
        )
        st.caption(
            f"正在并发优化 {total_count} 个章节，已完成 {completed_count}/{total_count}{latest_text}。"
        )
    else:
        st.caption(
            f"全部 {total_count} 个章节已处理完成，最近完成："
            f"{_section_label(latest_completed.get('section_name', 'unknown')) if latest_completed else '无'}。"
        )

    for event in events:
        label = _section_label(event.get("section_name", "unknown"))
        status = event.get("status", "waiting")
        keywords = event.get("keywords_matched", [])
        strategy = event.get("optimization_strategy", "")
        gap_analysis = event.get("gap_analysis", "")
        error = event.get("error", "")

        if status == "waiting":
            st.caption(f"⏳ {label}：等待 AI 处理...")
            continue

        if status == "skipped":
            st.info(f"ℹ️ **{label}**：已按当前配置保留原始内容。")
            continue

        if status == "fallback":
            st.warning(f"⚠️ **{label}**：优化未生效，已保留原始数据。原因：{error or '未知错误'}")
            continue

        st.markdown(f"**✅ {label} 优化完成**")
        with st.expander(f"🧠 查看 AI 优化思路（{label}）", expanded=False):
            if keywords:
                st.write(f"**🎯 匹配关键词**：`{', '.join(keywords)}`")
            if strategy:
                st.write(f"**💡 优化策略**：{strategy}")
            if gap_analysis:
                st.write(f"**⚠️ 发现差距**：{gap_analysis}")
            if not any([keywords, strategy, gap_analysis]):
                st.caption("该章节未返回更详细的优化分析。")


def apply_demo_data():
    """载入稳定演示数据，并写入当前 Streamlit 会话。"""
    demo_path = ensure_demo_resume_file("uploads")
    manual_form = dict(DEMO_RESUME_DATA)
    manual_form.update(DEMO_RESUME_DATA.get("personal", {}))
    manual_form.pop("personal", None)
    st.session_state.manual_resume_form = manual_form
    st.session_state["form_data"] = DEMO_RESUME_DATA
    st.session_state["jd_text"] = DEMO_JOB_TEXT
    st.session_state["jd_url"] = ""
    st.session_state["resume_source"] = demo_path
    st.session_state["resume_type"] = "upload"
    st.session_state["jd_text_input"] = DEMO_JOB_TEXT
    st.session_state["jd_toggle"] = False


def render_pre_generation_summary(resume_path, jd_url, jd_text, fields_to_optimize, style_label, preset_name):
    """生成前展示关键输入，避免用户误用旧数据。"""
    with st.expander("生成前确认", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("简历来源", os.path.basename(resume_path) if resume_path else "未选择")
        c2.metric("JD 输入", "链接抓取" if jd_url else "文本粘贴")
        c3.metric("优化策略", preset_name)
        st.markdown(f"**模板风格**：{style_label}")
        st.markdown(
            f"**优化字段**："
            f"{', '.join(fields_to_optimize) if fields_to_optimize else '不调用 AI 优化章节，仅生成排版'}"
        )
        if jd_text:
            st.caption("JD 预览")
            st.text(jd_text[:500] + ("..." if len(jd_text) > 500 else ""))
