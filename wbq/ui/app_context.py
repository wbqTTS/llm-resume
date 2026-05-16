import base64
import json
import os
import time
from datetime import datetime

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

try:
    from wbq import AutoApplyModel
    from wbq.utils.utils import display_pdf, download_pdf, read_file, read_json
    from wbq.utils.metrics import jaccard_similarity, overlap_coefficient, cosine_similarity
    from wbq.utils.voice_input import st_voice_input
    from wbq.utils.db_manager import ResumeDB
    from wbq.variables import LLM_MAPPING
    from wbq.utils.app_support import (
        DEMO_JOB_TEXT,
        DEMO_RESUME_DATA,
        OPTIMIZATION_PRESETS,
        STYLE_DETAILS,
        compare_resume_keywords,
        friendly_error_message,
        keyword_coverage,
        normalize_manual_form,
        resume_data_to_form,
        resume_quality_checks,
        score_interpretations,
        set_step,
    )
    from wbq.utils.ui_components import (
        apply_demo_data,
        render_ai_optimization_details,
        render_generation_progress,
        render_pre_generation_summary,
    )
    from wbq.ui.web_helpers import (
        FONT_PATH,
        compare_resumes,
        convert_pdf_to_word,
        create_overleaf_button,
        display_comparison_changes,
        extract_text_from_pdf,
    )
    WBQ_AVAILABLE = True
except ImportError:
    WBQ_AVAILABLE = False


db = ResumeDB()
