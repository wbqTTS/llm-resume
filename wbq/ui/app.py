import os

from wbq.ui.app_context import st
from wbq.ui.constants import (
    STEP_ADMIN_PANEL,
    STEP_DATA_INPUT,
    STEP_GENERATION,
    STEP_MODEL_CONFIG,
    STEP_RESULTS,
    STEP_USER_CENTER,
    STEPS,
)
from wbq.ui.pages.admin_panel import render_admin_panel
from wbq.ui.pages.data_input import render_data_input
from wbq.ui.pages.generation import render_generation
from wbq.ui.pages.model_config import render_model_config
from wbq.ui.pages.results import render_results
from wbq.ui.pages.user_center import render_user_center
from wbq.ui.web_helpers import check_playwright_once, update_step


def configure_page():
    st.set_page_config(
        page_title="智简",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get help": "https://www.youtube.com/watch?v=Agl7ugyu1N4",
            "About": "https://github.com/Ztrimus/job-llm",
            "Report a bug": "https://github.com/Ztrimus/job-llm/issues",
        },
    )
    st.markdown(
        """
<style>
    .main-header { font-size: 2.2rem; font-weight: bold; color: #1E88E5; margin-bottom: 10px; }
    .step-header { font-size: 1.5rem; font-weight: 600; color: #333; margin-top: 20px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; padding: 10px 20px; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; }
    .rf-stage { padding: 10px 12px; border-radius: 8px; border: 1px solid #e9ecef; background: #fff; margin-bottom: 8px; }
    .rf-stage-active { border-color: #1E88E5; background: #eef6ff; font-weight: 600; }
    .rf-stage-done { border-color: #43a047; background: #f1f8f3; }
    .rf-summary { padding: 14px 16px; border: 1px solid #e9ecef; border-radius: 8px; background: #fbfbfd; }
    div[data-baseweb="tag"] { border-radius: 999px; font-weight: 600; border-width: 1px; }
    div[data-baseweb="tag"]:nth-child(4n+1) { background: #eef4ff; color: #2656c8; border-color: #c8d8ff; }
    div[data-baseweb="tag"]:nth-child(4n+2) { background: #effaf4; color: #217a46; border-color: #bfe8cd; }
    div[data-baseweb="tag"]:nth-child(4n+3) { background: #fff4ec; color: #b85a22; border-color: #ffd5bf; }
    div[data-baseweb="tag"]:nth-child(4n) { background: #f7efff; color: #7440b8; border-color: #dbc8ff; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #7c3aed 0%, #b34ccf 52%, #d95f9a 100%);
    }
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 16px;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        border-radius: 16px;
        padding: 10px 12px;
        margin-bottom: 8px;
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.14);
        transition: all 0.18s ease;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.18);
        border-color: rgba(255, 255, 255, 0.28);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
        background: rgba(255, 255, 255, 0.24);
        border-color: rgba(255, 255, 255, 0.38);
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.12);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    [data-testid="stSidebar"] .sidebar-badge {
        margin: 4px 0 18px;
        display: inline-block;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: #ffffff;
        font-size: 13px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.16);
    }
    [data-testid="stSidebar"] .stLinkButton a {
        background: rgba(255, 255, 255, 0.14);
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 14px;
    }
    [data-testid="stSidebar"] .stLinkButton a:hover {
        border-color: rgba(255, 255, 255, 0.36);
        background: rgba(255, 255, 255, 0.20);
    }
</style>
""",
        unsafe_allow_html=True,
    )


def init_session_state():
    if "current_step" not in st.session_state:
        st.session_state.current_step = STEP_USER_CENTER
    if "nav_radio" not in st.session_state:
        st.session_state.nav_radio = STEP_USER_CENTER
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    if "manual_resume_form" not in st.session_state:
        st.session_state.manual_resume_form = {
            "name": "",
            "birthdate": "",
            "phone": "",
            "politics": "",
            "email": "",
            "hometown": "",
            "photo": "",
            "title": "",
            "summary": "",
            "media": {},
            "work_experience": [],
            "education": [],
            "skill_section": [],
            "projects": [],
            "social_practice": [],
            "certifications": [],
            "achievements": [],
            "research_interest": "",
            "publications": [],
            "research_experience": [],
            "conference_presentations": [],
            "honors": [],
            "teaching_experience": [],
            "technical_skills": {"programming": [], "frameworks": [], "tools": [], "languages": []},
            "academic_service": [],
            "references": [],
        }
    if "generated_result" not in st.session_state:
        st.session_state.generated_result = {}


def render_sidebar():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2921/2921226.png", width=70)
        st.title("操作导航")
        st.markdown('<div class="sidebar-badge">答辩演示版</div>', unsafe_allow_html=True)
        st.radio(
            "选择步骤",
            STEPS,
            label_visibility="collapsed",
            key="nav_radio",
            on_change=update_step,
        )
        st.divider()
        st.caption("Job-LLM Resume Studio")
        st.link_button("反馈问题", "https://github.com/wbqTTS", use_container_width=True)


def render_current_page():
    current_step = st.session_state.current_step
    if current_step == STEP_USER_CENTER:
        render_user_center()
    elif current_step == STEP_DATA_INPUT:
        render_data_input()
    elif current_step == STEP_MODEL_CONFIG:
        render_model_config()
    elif current_step == STEP_GENERATION:
        render_generation()
    elif current_step == STEP_RESULTS:
        render_results()
    elif current_step == STEP_ADMIN_PANEL:
        render_admin_panel()
    else:
        st.session_state.current_step = STEP_USER_CENTER
        st.session_state.nav_radio = STEP_USER_CENTER
        st.warning("页面状态异常，已自动返回用户中心。")
        st.rerun()


def main():
    configure_page()
    check_playwright_once()
    os.makedirs("output", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    init_session_state()
    render_sidebar()
    st.markdown('<p class="main-header">📄 AI 智能简历定制系统</p>', unsafe_allow_html=True)
    if st.session_state.nav_radio not in STEPS:
        st.session_state.nav_radio = STEP_USER_CENTER
    st.session_state.current_step = st.session_state.nav_radio
    render_current_page()
    st.markdown("---")
    st.caption("Powered by Job-LLM & Streamlit")
