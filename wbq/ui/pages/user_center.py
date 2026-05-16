from __future__ import annotations

from collections import Counter

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd

from wbq.ui.app_context import *
from wbq.ui.constants import STEP_DATA_INPUT, STEP_GENERATION, STEP_RESULTS
from wbq.ui.pages.model_config import _resolve_runtime_provider


SESSION_KEYS_TO_CLEAR = [
    "resume_source",
    "resume_type",
    "form_data",
    "jd_url",
    "jd_text",
    "jd_text_input",
    "temp_user_data",
    "temp_job_details",
    "generated_result",
    "selected_style",
    "optimization_fields",
    "llm_instance",
    "manual_resume_form",
    "llm_config",
    "login_password",
    "analysis_saved_to_db",
    "interview_assistant_state",
]


def _font_prop():
    try:
        if FONT_PATH and os.path.exists(FONT_PATH):
            return fm.FontProperties(fname=FONT_PATH)
    except Exception:
        pass
    return None


def _clear_user_work_state(include_identity: bool = False):
    keys = list(SESSION_KEYS_TO_CLEAR)
    if include_identity:
        keys.extend(["user_id", "username", "current_step", "nav_radio"])
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def _load_history_record(record_id: int):
    with st.spinner("正在从数据库加载记录..."):
        data = db.load_resume_data(record_id)
    if not data:
        st.error("加载失败，记录可能已损坏。")
        return

    source_user_data = data.get("source_data") or data.get("form_data") or data.get("optimized_data") or {}
    job_details = data.get("job_details") or {}
    if not job_details:
        raw_jd_text = data.get("jd_text", "")
        raw_jd_url = data.get("jd_url", "")
        job_details = {
            "job_description": raw_jd_text,
            "jd_url": raw_jd_url,
            "keywords": [],
        }

    if source_user_data:
        st.session_state["temp_user_data"] = source_user_data
        st.session_state["form_data"] = source_user_data
        st.session_state["manual_resume_form"] = resume_data_to_form(source_user_data)

    if job_details:
        st.session_state["temp_job_details"] = job_details
    st.session_state["resume_source"] = data.get("original_resume_path") or data.get("pdf_path") or ""
    st.session_state["jd_url"] = data.get("jd_url", "")
    st.session_state["jd_text"] = data.get("jd_text", "")

    st.session_state["generated_result"] = {
        "style": data.get("template_style"),
        "optimized_fields": data.get("optimized_fields"),
        "resume_path": data.get("pdf_path"),
        "resume_details": data.get("optimized_data", {}),
        "raw_resume_path": data.get("raw_resume_path"),
        "cv_path": data.get("cv_path"),
        "cv_details": data.get("cv_content"),
        "jd_url": data.get("jd_url"),
        "jd_text": data.get("jd_text"),
        "original_resume_path": data.get("original_resume_path"),
    }

    for key in [
        "analyzer_scores",
        "analyzer_suggestions",
        "analyzer_questions",
        "analyzer_radar",
        "analyzer_wordcloud",
    ]:
        value = data.get(key)
        if value:
            st.session_state["generated_result"][key] = value

    if data.get("template_style"):
        st.session_state["selected_style"] = data["template_style"]

    provider_name = data.get("provider_name", "")
    model_name = data.get("model_name", "")
    if provider_name or model_name:
        actual_provider, actual_model = _resolve_runtime_provider(provider_name or "Qwen", model_name or "qwen-max")
        st.session_state["llm_config"] = {
            "provider": actual_provider,
            "model": actual_model,
            "display_provider": provider_name or actual_provider,
            "display_model": model_name or actual_model,
            "api_key": st.session_state.get("llm_config", {}).get("api_key", ""),
        }

    st.session_state["analysis_saved_to_db"] = True
    st.session_state["trigger_jump"] = True
    st.toast("历史记录加载成功，正在跳转到结果分析。")


def _render_status_card(title: str, ready: bool, pending_text: str, ready_text: str) -> None:
    status_text = ready_text if ready else pending_text
    pill_bg = "#e8f7ee" if ready else "#fff1f1"
    pill_color = "#167c3a" if ready else "#c0392b"
    card_border = "#b9e2c8" if ready else "#f0c4c4"
    st.markdown(
        f"""
        <div style="border:1px solid {card_border}; border-radius:10px; padding:16px 18px; min-height:108px; background:#ffffff;">
            <div style="font-size:14px; color:#5f6b7a; margin-bottom:12px;">{title}</div>
            <div style="display:inline-block; padding:8px 14px; border-radius:999px; background:{pill_bg}; color:{pill_color}; font-weight:600;">
                {status_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_overview_bar_chart(
    title: str,
    values: pd.Series,
    color: str,
    *,
    rotate_labels: int = 0,
) -> None:
    st.caption(title)
    if values.empty:
        st.info("暂无可展示的数据")
        return

    font_prop = _font_prop()
    labels = [str(item) for item in values.index.tolist()]
    positions = list(range(len(labels)))

    fig, ax = plt.subplots(figsize=(4.3, 2.9))
    ax.bar(positions, values.tolist(), color=color, width=0.62)
    ax.set_xticks(positions)
    ax.set_xticklabels(
        labels,
        rotation=rotate_labels,
        ha="right" if rotate_labels else "center",
        fontproperties=font_prop,
        fontsize=9,
    )
    ax.set_ylabel("记录数", fontproperties=font_prop, fontsize=9)
    ax.tick_params(axis="y", labelsize=9)
    if font_prop:
        for tick in ax.get_yticklabels():
            tick.set_fontproperties(font_prop)
    ax.grid(axis="y", linestyle="--", alpha=0.22)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_alpha(0.25)
    ax.spines["bottom"].set_alpha(0.25)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def _render_history_dashboard(history: list[dict]) -> None:
    if not history:
        return

    style_counts = Counter((item.get("style") or "未记录") for item in history)
    provider_counts = Counter(
        f"{item.get('provider') or '未记录'} / {item.get('model') or '未记录'}" for item in history
    )

    history_df = pd.DataFrame(history)
    history_df["created_day"] = history_df["time"].astype(str).str.slice(0, 10)
    day_counts = history_df["created_day"].value_counts().sort_index()

    st.markdown("#### 历史概览")
    c1, c2, c3 = st.columns(3)
    with c1:
        _render_overview_bar_chart("模板风格分布", pd.Series(style_counts, name="record_count"), "#4F8EF7")
    with c2:
        _render_overview_bar_chart("模型配置分布", pd.Series(provider_counts, name="record_count"), "#23B5AF")
    with c3:
        _render_overview_bar_chart(
            "生成时间分布",
            day_counts.rename("record_count"),
            "#F59E0B",
            rotate_labels=20,
        )


def render_user_center():
    st.markdown('<p class="step-header">第一步：登录与历史记录</p>', unsafe_allow_html=True)

    if not WBQ_AVAILABLE:
        st.error("`wbq` 模块不可用，请检查当前环境。")
        st.stop()

    if "user_id" not in st.session_state:
        st.info("欢迎使用智能简历系统，请先输入用户名与密码。")
        account_col, action_col = st.columns([3, 2])
        with account_col:
            username_input = st.text_input("用户名", placeholder="例如：张三", key="login_username")
            st.text_input("密码", type="password", placeholder="请输入密码", key="login_password")
        with action_col:
            st.write("")
            st.write("")
            if st.button("进入系统 / 注册", use_container_width=True, type="primary"):
                if not username_input:
                    st.warning("请输入用户名。")
                else:
                    _clear_user_work_state(include_identity=False)
                    st.session_state["user_id"] = db.create_user(username_input)
                    st.session_state["username"] = username_input
                    st.rerun()
        return

    top_left, top_right = st.columns(2)
    with top_left:
        st.success(f"当前用户：**{st.session_state.get('username', '')}**")
    with top_right:
        if st.button("退出登录", use_container_width=True):
            _clear_user_work_state(include_identity=True)
            st.rerun()

    history = db.get_user_history(st.session_state["user_id"])

    st.divider()
    st.markdown("### 工作台")
    ready_jd = bool(st.session_state.get("jd_url") or st.session_state.get("jd_text"))
    ready_resume = bool(st.session_state.get("resume_source") or st.session_state.get("temp_user_data"))
    ready_model = bool(st.session_state.get("llm_config"))

    metric_col, jd_col, resume_col, model_col = st.columns(4)
    metric_col.metric("历史记录", len(history or []))
    with jd_col:
        _render_status_card("JD", ready_jd, "待输入", "已输入")
    with resume_col:
        _render_status_card("简历", ready_resume, "待上传", "已上传")
    with model_col:
        _render_status_card("模型", ready_model, "待配置", "已配置")

    a1, a2, a3 = st.columns(3)
    if a1.button("载入演示数据", use_container_width=True, type="primary"):
        apply_demo_data()
        st.success("演示数据已载入。")
        st.rerun()
    if a2.button("开始输入数据", use_container_width=True):
        set_step(STEP_DATA_INPUT)
        st.rerun()
    if a3.button("去生成简历", use_container_width=True):
        set_step(STEP_GENERATION)
        st.rerun()

    st.divider()
    st.subheader("历史生成记录")
    _render_history_dashboard(history)

    if history:
        for item in history:
            time_str = item.get("time", "未知时间")
            style_str = item.get("style") or "未指定风格"
            provider = item.get("provider") or "未记录"
            model = item.get("model") or "未记录"
            with st.expander(f"{time_str} - {style_str}", expanded=False):
                st.write(f"**状态**：{item.get('status', 'generated')}")
                st.write(f"**模型配置**：{provider} / {model}")
                if item.get("pdf_path"):
                    st.caption(f"简历文件：{item['pdf_path']}")
                if item.get("cv_path"):
                    st.caption(f"求职信文件：{item['cv_path']}")
                load_col, delete_col = st.columns(2)
                if load_col.button("加载此版本", key=f"load_hist_{item['id']}", use_container_width=True):
                    _load_history_record(item["id"])
                if delete_col.button("删除记录", key=f"delete_hist_{item['id']}", use_container_width=True):
                    if db.delete_resume_record(item["id"], st.session_state.get("user_id")):
                        st.success("记录已删除。")
                        st.rerun()
                    else:
                        st.error("删除失败，请刷新后重试。")
    else:
        st.caption("暂无历史记录，可以从数据输入开始第一次生成。")
        st.info("完成简历生成并保存后，这里会出现可复用的历史版本。")

    if st.session_state.get("trigger_jump"):
        st.session_state["trigger_jump"] = False
        set_step(STEP_RESULTS)
        st.rerun()
