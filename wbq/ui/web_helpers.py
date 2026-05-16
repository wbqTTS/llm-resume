import base64
import difflib
import os
import platform
import zipfile

import streamlit as st
from pdf2docx import Converter


def get_font_path() -> str:
    """Return a usable Chinese font path for report generation."""
    system = platform.system()
    if system == "Windows":
        candidates = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return "C:/Windows/Fonts/simhei.ttf"
    if system == "Darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return "/System/Library/Fonts/PingFang.ttc"

    candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"


FONT_PATH = get_font_path()


def check_playwright_once():
    """Mark the Playwright check as done without mutating the local environment at runtime."""
    if "playwright_checked" not in st.session_state:
        st.session_state.playwright_checked = False

    if st.session_state.playwright_checked:
        return
    st.session_state.playwright_checked = True


def encode_tex_file(file_path):
    """Package the generated TEX file and resume.cls into a Base64 zip for Overleaf."""
    try:
        template_path = os.path.join("wbq", "templates", "resume.cls")
        file_paths = [
            file_path.replace(".pdf", ".tex"),
            template_path,
        ]
        zip_file_path = file_path.replace(".pdf", ".zip")

        with zipfile.ZipFile(zip_file_path, "w") as zipf:
            for f_path in file_paths:
                if os.path.exists(f_path):
                    zipf.write(f_path, os.path.basename(f_path))

        with open(zip_file_path, "rb") as zip_file:
            zip_content = zip_file.read()

        encoded_zip = base64.b64encode(zip_content).decode("utf-8")
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        return encoded_zip
    except Exception:
        return None


def create_overleaf_button(resume_path):
    """Render an embedded Overleaf edit button for the generated TEX package."""
    tex_content = encode_tex_file(resume_path)
    if not tex_content:
        st.button("在 Overleaf 中编辑", disabled=True, help="生成 TEX 文件失败")
        return

    html_code = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: transparent; }}
            .btn-success {{ background-color: #17a645; border-color: #17a645; font-weight: bold; font-size: 14px; }}
            .btn-success:hover {{ background-color: #148f3b; border-color: #148f3b; }}
        </style>
    </head>
    <body style="background: transparent;">
        <form action="https://www.overleaf.com/docs" method="post" target="_blank">
            <input type="text" name="snip_uri" style="display: none;" value="data:application/zip;base64,{tex_content}">
            <input class="btn btn-success rounded-pill w-100 shadow-sm" type="submit" value="在 Overleaf 中编辑">
        </form>
    </body>
    </html>
    """
    st.components.v1.html(html_code, height=45)


def convert_pdf_to_word(pdf_path):
    """Convert a generated PDF resume to a Word document."""
    try:
        word_path = pdf_path.replace(".pdf", ".docx")
        if not word_path.endswith(".docx"):
            word_path = word_path + ".docx"

        cv = Converter(pdf_path)
        cv.convert(word_path, start=0, end=None)
        cv.close()
        return word_path
    except Exception:
        return None


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF for resume comparison."""
    try:
        import fitz

        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception:
        return None


def compare_resumes(original_text, optimized_text):
    """Compare two resume texts and return summary stats plus HTML diff."""
    similarity = difflib.SequenceMatcher(None, original_text, optimized_text).ratio()
    differ = difflib.HtmlDiff()
    diff_html = differ.make_file(
        original_text.splitlines(),
        optimized_text.splitlines(),
        fromdesc="原始简历",
        todesc="优化后简历",
        context=True,
        numlines=3,
    )

    original_lines = original_text.splitlines()
    optimized_lines = optimized_text.splitlines()
    changes = {
        "added": 0,
        "removed": 0,
        "modified": 0,
        "original_length": len(original_text),
        "optimized_length": len(optimized_text),
        "similarity": similarity,
    }

    matcher = difflib.SequenceMatcher(None, original_lines, optimized_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            changes["modified"] += max(i2 - i1, j2 - j1)
        elif tag == "delete":
            changes["removed"] += i2 - i1
        elif tag == "insert":
            changes["added"] += j2 - j1

    return changes, diff_html


def display_comparison_changes(changes):
    """Render resume comparison summary metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("相似度", f"{changes['similarity'] * 100:.1f}%", help="两份简历的文本相似度百分比")
    with col2:
        st.metric("新增内容", changes["added"], help="优化后新增的行数")
    with col3:
        st.metric("删除内容", changes["removed"], help="优化后删除的行数")
    with col4:
        st.metric("修改内容", changes["modified"], help="优化后修改的行数")

    st.markdown("---")
    col5, col6 = st.columns(2)
    with col5:
        st.info(f"原始简历长度：{changes['original_length']} 字符")
    with col6:
        st.success(f"优化后简历长度：{changes['optimized_length']} 字符")


def update_step():
    st.session_state.current_step = st.session_state.nav_radio
