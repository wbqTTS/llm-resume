import os
from datetime import datetime

from wbq.ui.app_context import *
from wbq.ui.constants import STEP_RESULTS


STYLE_CONFIG = {
    "classic": {"label": "经典商务 (Classic)", "image": "assets/templates/classic_preview.png"},
    "creative": {"label": "创意设计 (Creative)", "image": "assets/templates/creative_preview.png"},
    "academic": {"label": "学术严谨 (Academic)", "image": "assets/templates/academic_preview.png"},
    "minimal": {"label": "极简现代 (Minimal)", "image": "assets/templates/minimal_preview.png"},
}


DEFAULT_OPTIMIZATION_FIELDS = {
    "education": False,
    "work_experience": True,
    "projects": True,
    "skill_section": False,
    "research_experience": False,
    "teaching_experience": False,
    "academic_service": False,
}


@st.cache_resource
def get_model_instance(api_key, provider, model, downloads_dir):
    return AutoApplyModel(
        api_key=api_key,
        provider=provider,
        model=model,
        downloads_dir=downloads_dir,
    )


def _ensure_generation_state():
    st.session_state.setdefault("selected_style", "classic")
    st.session_state.setdefault("optimization_fields", dict(DEFAULT_OPTIMIZATION_FIELDS))


def _resolve_input_sources():
    generated_result = st.session_state.get("generated_result", {})
    resume_path = generated_result.get("original_resume_path") or st.session_state.get("resume_source")
    jd_url = generated_result.get("jd_url") or st.session_state.get("jd_url", "")
    jd_text = generated_result.get("jd_text") or st.session_state.get("jd_text", "")
    return resume_path, jd_url, jd_text


def _render_optimization_controls():
    st.subheader("优化策略配置")
    st.caption("选择优化强度和 AI 重点润色的模块。未选中的模块将保留原始内容。")

    preset_name = st.radio(
        "优化强度",
        list(OPTIMIZATION_PRESETS.keys()),
        index=1,
        horizontal=True,
        key="optimization_preset",
        help="保守适合小幅调整，标准适合日常投递，强匹配适合针对岗位做定向增强。",
    )
    preset = OPTIMIZATION_PRESETS[preset_name]
    st.caption(preset["caption"])

    if st.button("应用当前优化强度到字段选择", use_container_width=True):
        for key, value in preset["fields"].items():
            st.session_state["optimization_fields"][key] = value
        st.rerun()

    with st.expander("自定义优化范围", expanded=False):
        current_style = st.session_state.get("selected_style", "classic")
        base_options = [
            ("education", "教育背景"),
            ("work_experience", "工作经历"),
            ("projects", "项目经历"),
            ("skill_section", "专业技能"),
        ]
        academic_options = [
            ("research_experience", "研究经历"),
            ("teaching_experience", "教学经历"),
            ("academic_service", "学术服务"),
        ]

        if current_style == "academic":
            field_options = base_options + academic_options
            st.info("当前为学术风格，已开放研究经历、教学经历和学术服务字段。")
        else:
            field_options = base_options
            st.info("当前为通用风格，默认展示教育、工作、项目和技能字段。")

        for row_start in range(0, len(field_options), 3):
            cols = st.columns(3)
            for col, (key, label) in zip(cols, field_options[row_start : row_start + 3]):
                with col:
                    st.session_state["optimization_fields"][key] = st.checkbox(
                        label,
                        value=st.session_state["optimization_fields"].get(key, False),
                        key=f"opt_check_{key}",
                    )

        st.caption("注：姓名、联系方式等个人基础信息默认不经过 AI 改写。")

    return preset_name


def _render_style_selector():
    st.markdown("### 选择简历风格")
    st.caption("点击下方卡片选择你希望使用的简历模板。")

    def set_style(style_key):
        st.session_state["selected_style"] = style_key

    cols = st.columns(4)
    for col, (style_key, style_info) in zip(cols, STYLE_CONFIG.items()):
        with col:
            st.button(
                style_info["label"],
                key=f"style_{style_key}",
                use_container_width=True,
                type="primary" if st.session_state["selected_style"] == style_key else "secondary",
                on_click=set_style,
                args=(style_key,),
            )

            image_path = style_info["image"]
            if os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
            else:
                st.markdown(
                    "<div style='height:150px; background:#f0f0f0; display:flex; align-items:center; justify-content:center; border-radius:8px; border:2px dashed #ccc;'>No Preview</div>",
                    unsafe_allow_html=True,
                )

            detail = STYLE_DETAILS.get(style_key, {})
            st.caption(detail.get("scene", ""))
            st.caption(detail.get("tone", ""))

    st.success(f"当前选中风格：**{STYLE_CONFIG[st.session_state['selected_style']]['label']}**")


def _build_initial_optimization_events(user_data: dict, template_style: str):
    section_order = [
        "education",
        "work_experience",
        "projects",
        "skill_section",
        "social_practice",
    ]
    if template_style == "academic":
        section_order.extend(
            [
                "research_experience",
                "teaching_experience",
                "academic_service",
            ]
        )

    events = []
    for section_name in section_order:
        section_data = user_data.get(section_name, [])
        if section_data:
            events.append(
                {
                    "section_name": section_name,
                    "status": "waiting",
                    "keywords_matched": [],
                    "optimization_strategy": "",
                    "gap_analysis": "",
                    "error": "",
                }
            )
    return events


def _build_section_progress_callback(detail_panel, optimization_events: list):
    def section_progress_callback(section_name, data, analysis):
        event = next(
            (item for item in optimization_events if item.get("section_name") == section_name),
            None,
        )
        if event is None:
            event = {
                "section_name": section_name,
                "status": "waiting",
                "keywords_matched": [],
                "optimization_strategy": "",
                "gap_analysis": "",
                "error": "",
            }
            optimization_events.append(event)

        event.update(
            {
                "status": "optimized",
                "keywords_matched": [],
                "optimization_strategy": "",
                "gap_analysis": "",
                "error": "",
            }
        )
        if analysis and isinstance(analysis, dict):
            if analysis.get("skipped"):
                event["status"] = "skipped"
            elif analysis.get("fallback"):
                event["status"] = "fallback"
            event["keywords_matched"] = analysis.get("keywords_matched", [])
            event["optimization_strategy"] = analysis.get("optimization_strategy", "")
            event["gap_analysis"] = analysis.get("gap_analysis", "")
            event["error"] = analysis.get("error", "")

        with detail_panel.container():
            render_ai_optimization_details(optimization_events)

    return section_progress_callback


def _generate_resume(
    resume_llm,
    resume_path,
    jd_url,
    jd_text,
    fields_to_optimize,
    status_container,
    progress_panel,
):
    status_container.info(
        f"正在为您生成 **{STYLE_CONFIG[st.session_state['selected_style']]['label']}** 风格简历..."
    )
    progress_panel.empty()
    with progress_panel.container():
        render_generation_progress("AI 优化", 72)

    user_data = st.session_state["temp_user_data"]
    job_details = st.session_state["temp_job_details"]
    optimization_detail_panel = st.empty()
    optimization_events = _build_initial_optimization_events(
        user_data,
        st.session_state["selected_style"],
    )
    with optimization_detail_panel.container():
        render_ai_optimization_details(optimization_events)

    callback = _build_section_progress_callback(optimization_detail_panel, optimization_events)

    resume_result_path, resume_details = resume_llm.resume_builder(
        job_details,
        user_data,
        template_style=st.session_state["selected_style"],
        is_st=False,
        optimize_fields=fields_to_optimize,
        user_id=str(st.session_state.get("user_id", "unknown")),
        section_callback=callback,
    )

    if not resume_result_path:
        st.error("简历生成失败：请检查模型输出、LaTeX 环境和模板字段是否完整。")
        st.stop()

    st.session_state["generated_result"]["resume_path"] = resume_result_path
    st.session_state["generated_result"]["resume_details"] = resume_details
    st.session_state["generated_result"]["style"] = st.session_state["selected_style"]
    st.session_state["generated_result"]["optimized_fields"] = fields_to_optimize
    st.session_state["generated_result"]["original_resume_path"] = resume_path
    st.session_state["generated_result"]["jd_url"] = jd_url
    st.session_state["generated_result"]["jd_text"] = jd_text


def _generate_cover_letter(resume_llm, resume_path, jd_url, jd_text, status_container, progress_panel):
    status_container.info("正在撰写求职信...")
    progress_panel.empty()
    with progress_panel.container():
        render_generation_progress("AI 优化", 80)

    cv_details, cv_result_path = resume_llm.cover_letter_generator(
        st.session_state["temp_job_details"],
        st.session_state["temp_user_data"],
        is_st=False,
        user_id=str(st.session_state.get("user_id", "unknown")),
    )
    if not cv_result_path:
        st.error("求职信生成失败：未返回可下载文件，请检查模型输出或本地 PDF 编译环境。")
        st.stop()

    st.session_state["generated_result"]["cv_path"] = cv_result_path
    st.session_state["generated_result"]["cv_details"] = cv_details
    st.session_state["generated_result"]["original_resume_path"] = resume_path
    st.session_state["generated_result"]["jd_url"] = jd_url
    st.session_state["generated_result"]["jd_text"] = jd_text
    st.success("求职信生成成功，可以前往结果页查看和下载。")


def render_generation():
    st.markdown('<p class="step-header">第四步：生成定制简历</p>', unsafe_allow_html=True)

    if not WBQ_AVAILABLE:
        st.error("'wbq' 模块不可用。")
        st.stop()

    llm_config = st.session_state.get("llm_config")
    if not llm_config:
        st.warning("请先完成模型配置。")
        st.stop()

    resume_path, jd_url, jd_text = _resolve_input_sources()
    if not resume_path:
        st.error("未找到简历文件。")
        st.stop()
    if not jd_url and not jd_text:
        st.error("未找到职位描述。")
        st.stop()

    _ensure_generation_state()
    preset_name = _render_optimization_controls()
    st.divider()

    st.subheader("开始生成")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        btn_resume = st.button("📄 生成简历", type="primary", use_container_width=True, key="btn_gen_resume")
    with col_btn2:
        btn_cl = st.button("✉️ 生成求职信", use_container_width=True, key="btn_gen_cl")

    _render_style_selector()

    fields_to_optimize = [key for key, value in st.session_state["optimization_fields"].items() if value]
    render_pre_generation_summary(
        resume_path=resume_path,
        jd_url=jd_url,
        jd_text=jd_text,
        fields_to_optimize=fields_to_optimize,
        style_label=STYLE_CONFIG[st.session_state["selected_style"]]["label"],
        preset_name=preset_name,
    )

    if not (btn_resume or btn_cl):
        return

    generation_start_time = datetime.now()
    st.session_state["generated_result"] = {}
    st.session_state.pop("temp_user_data", None)
    st.session_state.pop("temp_job_details", None)

    api_key_missing = not llm_config.get("api_key")
    provider_uses_env = llm_config.get("provider") == "Qwen" and os.environ.get("DASHSCOPE_API_KEY")
    if api_key_missing and not provider_uses_env and llm_config["provider"] not in ["Ollama", "Llama"]:
        st.error("请输入有效的 API Key，或在环境变量中配置对应密钥。")
        st.stop()

    status_container = st.empty()
    progress_panel = st.empty()

    try:
        download_resume_path = os.path.join(os.path.dirname(__file__) if "__file__" in globals() else os.getcwd(), "output")
        os.makedirs(download_resume_path, exist_ok=True)

        effective_api_key = llm_config.get("api_key") or "os"
        resume_llm = get_model_instance(
            effective_api_key,
            llm_config["provider"],
            llm_config["model"],
            download_resume_path,
        )
        st.session_state["llm_instance"] = resume_llm.llm

        status_container.info("正在分析您的简历并提取关键信息...")
        with progress_panel.container():
            render_generation_progress("解析简历", 15)
        user_data = resume_llm.user_data_extraction(resume_path, is_st=False)
        st.session_state["temp_user_data"] = user_data
        if not user_data:
            st.error("简历解析失败：请确认上传的是有效 PDF 或 JSON 文件。")
            st.stop()

        status_container.info("正在解析职位描述（JD）...")
        progress_panel.empty()
        with progress_panel.container():
            render_generation_progress("解析 JD", 35)

        if jd_url:
            job_details, _ = resume_llm.job_details_extraction(
                url=jd_url,
                is_st=False,
                user_id=str(st.session_state.get("user_id", "unknown")),
            )
        else:
            job_details, _ = resume_llm.job_details_extraction(
                job_site_content=jd_text,
                is_st=False,
                user_id=str(st.session_state.get("user_id", "unknown")),
            )
        st.session_state["temp_job_details"] = job_details
        if not job_details:
            st.error("JD 解析失败：请优先粘贴完整职位描述文本，或检查招聘链接是否可访问。")
            st.stop()

        if btn_resume:
            _generate_resume(
                resume_llm,
                resume_path,
                jd_url,
                jd_text,
                fields_to_optimize,
                status_container,
                progress_panel,
            )

        if btn_cl:
            _generate_cover_letter(resume_llm, resume_path, jd_url, jd_text, status_container, progress_panel)

        progress_panel.empty()
        with progress_panel.container():
            render_generation_progress("结果分析", 100)

        status_container.success("生成成功！请前往【结果分析】页面查看和下载。")
        generation_duration = (datetime.now() - generation_start_time).total_seconds()
        st.info(f"⏱️ 本次生成耗时：**{generation_duration:.1f} 秒**")
        st.balloons()

        if st.button("📊 前往结果分析", use_container_width=True):
            set_step(STEP_RESULTS)
            st.rerun()

    except Exception as e:
        status_container.error(f"{friendly_error_message(e, '生成流程')}")
        with st.expander("查看技术细节", expanded=False):
            st.code(str(e))
        st.stop()
