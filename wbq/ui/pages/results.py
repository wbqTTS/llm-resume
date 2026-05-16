from wbq.ui.app_context import *
from wbq.ui.components.results_sections import (
    get_results_analyzer,
    render_comparison_tab,
    render_footer_actions,
    render_generation_config,
    render_interview_tab,
    render_match_analysis_tab,
    render_quality_analysis_tab,
    render_quick_actions,
    render_resume_preview_tab,
    render_save_section,
    render_suggestions_tab,
    render_wordcloud_tab,
)
from wbq.ui.constants import STEP_GENERATION


def render_results():
    st.markdown('<p class="step-header">第五步：查看和下载结果</p>', unsafe_allow_html=True)
    if not st.session_state.get("generated_result"):
        st.info("暂时还没有生成结果。请先到“生成简历”页面完成一次生成。")
        if st.button("前往生成简历", use_container_width=True):
            set_step(STEP_GENERATION)
            st.rerun()
        st.stop()

    res = st.session_state["generated_result"]
    st.session_state.setdefault("analysis_saved_to_db", False)

    render_generation_config(res)
    st.divider()
    render_quick_actions(res)
    st.divider()

    analyzer = get_results_analyzer(res)
    preview_tab, quality_tab, match_tab, wordcloud_tab, suggestions_tab, interview_tab, comparison_tab = st.tabs(
        ["简历预览", "质量分析", "匹配度分析", "词云分析", "改进建议", "面试问答", "简历对比"]
    )

    with preview_tab:
        render_resume_preview_tab(res)
    with quality_tab:
        render_quality_analysis_tab(res)
    with match_tab:
        render_match_analysis_tab(res, analyzer)
    with wordcloud_tab:
        render_wordcloud_tab(analyzer)
    with suggestions_tab:
        render_suggestions_tab(res, analyzer)
    with interview_tab:
        render_interview_tab(analyzer)
    with comparison_tab:
        render_comparison_tab(res)

    render_save_section(res)
    render_footer_actions()
