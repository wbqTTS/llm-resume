from wbq.ui.app_context import *
from wbq.ui.components.data_input_sections import (
    render_completion_status,
    render_demo_banner,
    render_jd_section,
    render_manual_resume_form,
    render_upload_resume_tab,
)


def render_data_input():
    st.markdown('<p class="step-header">第二步：提供岗位描述与个人简历</p>', unsafe_allow_html=True)
    render_demo_banner()
    jd_url, jd_text = render_jd_section()

    st.divider()
    st.subheader("B. 你的简历来源")
    upload_tab, manual_tab = st.tabs(["上传现有简历（PDF / JSON）", "手动填写信息生成 JSON"])
    uploaded_resume = None
    with upload_tab:
        uploaded_resume = render_upload_resume_tab()
    with manual_tab:
        render_manual_resume_form()

    render_completion_status(jd_url, jd_text, uploaded_resume)
