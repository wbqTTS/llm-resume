import os
import shutil
from typing import Optional
import re
import time
import json
import base64
import platform
import subprocess
import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF
from markdown_pdf import MarkdownPdf, Section
from pathlib import Path
from datetime import datetime
from langchain_core.output_parsers import JsonOutputParser
from wbq.utils.path_manager import AppPathManager, clean_path_part

OS_SYSTEM = platform.system().lower()

def write_file(file_path, data):
    """写入文本文件"""
    with open(file_path, "w", encoding='utf-8') as file:
        file.write(data)

def read_file(file_path, mode='r'):
    """读取文件"""
    if 'b' in mode:
        with open(file_path, mode) as f:
            return f.read()
    else:
        with open(file_path, mode, encoding='utf-8') as f:
            return f.read()

def write_json(file_path, data):
    """写入JSON文件"""
    with open(file_path, "w", encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)

def read_json(file_path: str):
    """读取JSON文件"""
    with open(file_path, encoding='utf-8') as json_file:
        return json.load(json_file)


def job_doc_name(job_details: dict, output_dir: str = "output", type: str = "", user_id: str = None,
                 timestamp: str = None):
    """
    根据职位信息生成标准化的文件保存路径和文件名。

    参数:
        job_details (dict): 包含职位信息的字典，必须包含 'company_name' 和 'job_title'。
        output_dir (str): 根输出目录，默认为 "output"。
        type (str): 文件类型标识。
        user_id (str): 用户ID，用于区分不同用户。
        timestamp (str): 时间戳，用于区分同一用户的多次生成。

    返回:
        str: 完整的文件绝对路径字符串。
    """
    root = os.path.abspath(os.path.dirname(output_dir) or os.getcwd())
    output_name = os.path.basename(os.path.normpath(output_dir)) or "output"
    return AppPathManager(project_root=root, output_dir=output_name).job_document_path(
        job_details,
        document_type=type,
        user_id=user_id,
        timestamp=timestamp,
    )


def clean_string(text: str):
    """清理字符串，保留中文字符、字母和数字"""
    return clean_path_part(text, "")

def open_file(file: str):
    """打开文件（跨平台）"""
    if OS_SYSTEM == "darwin":  # macOS
        os.system(f"open {file}")
    elif OS_SYSTEM == "linux":
        try:
            os.system(f"xdg-open {file}")
        except FileNotFoundError:
            print("Error: xdg-open command not found.")
    elif OS_SYSTEM == "windows":
        try:
            os.startfile(file)
        except AttributeError:
            print("Error: os.startfile is not available.")

def save_log(content: any, file_name: str):
    """保存日志"""
    timestamp = int(datetime.timestamp(datetime.now()))
    file_path = f"logs/{file_name}_{timestamp}.txt"
    write_file(file_path, content)

def measure_execution_time(func):
    """测量函数执行时间的装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function {func.__name__} took {execution_time:.4f} seconds to execute")
        return result
    return wrapper

def text_to_pdf(text: str, file_path: str):
    """将文本转换为PDF"""
    pdf = MarkdownPdf(toc_level=2)
    encoded_text = text.encode('utf-8').decode('latin-1')
    pdf.add_section(Section(encoded_text), user_css="body {font-size: 12pt; font-family: Calibri; text-align: justify;}")
    pdf.meta["title"] = "Cover Letter"
    pdf.meta["author"] = "Saurabh Zinjad"
    pdf.save(file_path)

def download_pdf(pdf_path: str):
    """提供PDF下载"""
    bytes_data = read_file(pdf_path, "rb")
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')

    dl_link = f"""
    <html>
    <head>
    <title>Start Auto Download file</title>
    <script src="http://code.jquery.com/jquery-3.2.1.min.js"></script>
    <script>
    $('<a href="data:application/pdf;base64,{base64_pdf}" download="{os.path.basename(pdf_path)}">')[0].click().remove();
    </script>
    </head>
    </html>
    """
    components.html(dl_link, height=0)

def display_pdf(file, type="pdf"):
    """在Streamlit中显示PDF"""
    if type == 'image':
        from pdf2image import convert_from_path
        pages = convert_from_path(file)
        for page in pages:
            st.image(page, use_column_width=True)

    if type == "pdf":
        bytes_data = read_file(file, "rb")
        try:
            base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
        except Exception as e:
            base64_pdf = base64.b64encode(bytes_data)

        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" type="application/pdf" style="width:100%; height:100vh;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

def save_latex_as_pdf(tex_file_path: str, dst_path: str) -> Optional[bool]:
    """
    将 .tex 文件编译为 PDF，并移动到目标位置，同时清理中间文件

    Args:
        tex_file_path: .tex 源文件路径
        dst_path: 目标PDF文件路径

    Returns:
        True (成功), False (失败)
    """
    print(f">>> [PDF] 开始转换: {tex_file_path} -> {dst_path}")

    prev_loc = os.getcwd()
    tex_dir = os.path.dirname(os.path.abspath(tex_file_path))
    tex_filename = os.path.basename(tex_file_path)
    base_name = os.path.splitext(tex_filename)[0]

    try:
        # 切换到 .tex 文件所在目录
        if not os.path.isdir(tex_dir):
            print(f">>> [ERROR] 目录不存在: {tex_dir}")
            return False

        os.chdir(tex_dir)
        print(f">>> [PDF] 已切换工作目录至: {tex_dir}")

        # 编译两次以确保交叉引用正确
        for i in range(2):
            print(f">>> [PDF] 第 {i+1} 次编译...")
            try:
                cmd = [
                    "xelatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    tex_filename
                ]

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=60,
                    encoding='utf-8',
                    errors='replace'
                )

                if result.returncode != 0:
                    print(f">>> [ERROR] ❌ xelatex 编译失败 (第 {i+1} 次)")

                    # 提取错误日志
                    log_lines = result.stdout.split('\n')
                    error_lines = [line for line in log_lines if 'error' in line.lower() or line.strip().startswith('!')]

                    print("--- 关键错误日志 ---")
                    if error_lines:
                        for line in error_lines[-20:]:
                            print(f"  {line}")
                    else:
                        print("  (未检测到标准错误格式，以下是最后 20 行)")
                        print('\n'.join(log_lines[-20:]))

                    # 保存完整日志
                    log_file = os.path.join(tex_dir, f"{base_name}_error.log")
                    with open(log_file, "w", encoding="utf-8") as f:
                        f.write(result.stdout)
                    print(f"   📄 完整日志已保存到: {log_file}")

                    os.chdir(prev_loc)
                    return False

            except subprocess.TimeoutExpired:
                print(f">>> [ERROR] ⏰ 第 {i+1} 次编译超时 (超过60秒)")
                os.chdir(prev_loc)
                return False
            except Exception as e:
                print(f">>> [ERROR] 💥 调用 xelatex 异常: {e}")
                os.chdir(prev_loc)
                return False

        print(">>> [PDF] ✅ xelatex 编译成功")

        # 验证并移动生成的 PDF
        generated_pdf_name = f"{base_name}.pdf"
        full_generated_pdf_path = os.path.join(tex_dir, generated_pdf_name)

        if not os.path.exists(full_generated_pdf_path):
            print(f">>> [ERROR] ❌ 未找到生成的 PDF 文件: {full_generated_pdf_path}")
            os.chdir(prev_loc)
            return False

        # 确保目标目录存在
        dst_dir = os.path.dirname(dst_path)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)

        # 移动 PDF 到目标位置
        shutil.move(full_generated_pdf_path, dst_path)
        print(f">>> [PDF] 📄 PDF 已移动至: {dst_path}")

        # 清理中间文件
        extensions_to_clean = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk', '.synctex.gz']
        files_to_remove = []

        try:
            all_files = os.listdir(tex_dir)
            for f in all_files:
                if f.startswith(base_name) and f != tex_filename and f != os.path.basename(dst_path):
                    if any(f.endswith(ext) for ext in extensions_to_clean):
                        files_to_remove.append(f)

            if files_to_remove:
                print(f">>> [PDF] 🧹 正在清理 {len(files_to_remove)} 个中间文件...")
                for f in files_to_remove:
                    try:
                        os.remove(os.path.join(tex_dir, f))
                    except Exception as clean_err:
                        print(f"   - ⚠️ 无法删除 {f}: {clean_err}")

        except Exception as list_err:
            print(f"   - ⚠️ 清理中间文件时出错: {list_err}")

        # 自动打开PDF
        try:
            if platform.system().lower() == 'windows':
                os.startfile(dst_path)
            elif platform.system().lower() == 'darwin':
                subprocess.run(['open', dst_path])
            else:
                subprocess.run(['xdg-open', dst_path])
            print(">>> [PDF] 📂 已自动打开PDF文件")
        except Exception as e:
            print(f">>> [PDF] ⚠️ 无法自动打开PDF: {e}")

        os.chdir(prev_loc)
        print(">>> [PDF] 🎉 所有步骤完成")
        return True

    except Exception as e:
        print(f">>> [ERROR] 💥 save_latex_as_pdf 异常: {e}")
        import traceback
        traceback.print_exc()
        try:
            os.chdir(prev_loc)
        except:
            pass
        return False

def get_default_download_folder():
    """获取默认下载文件夹路径"""
    download_folder_path = os.path.join(str(Path.home()), "Downloads", "JobLLM_Resume_CV")
    os.makedirs(download_folder_path, exist_ok=True)
    return download_folder_path

def parse_json_markdown(json_string: str) -> dict:
    """解析可能包含Markdown标记的JSON字符串"""
    if not json_string or not isinstance(json_string, str):
        return None
    try:
        cleaned = json_string.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json|typescript)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        if 'JSON_OUTPUT_ACCORDING_TO_RESUME_DATA_SCHEMA' in cleaned:
            cleaned = cleaned.replace("JSON_OUTPUT_ACCORDING_TO_RESUME_DATA_SCHEMA", "", 1)

        parser = JsonOutputParser()
        parsed = parser.parse(cleaned)

        if not isinstance(parsed, (dict, list)):
            return None

        return parsed
    except Exception as e:
        print(f"JSON 解析失败：{str(e)[:160]}")
        return None

def get_prompt(system_prompt_path: str) -> str:
    """读取系统提示词文件"""
    with open(system_prompt_path, encoding="utf-8") as file:
        return file.read().strip() + "\n"

def key_value_chunking(data, prefix=""):
    """将字典或列表分块为键值对"""
    chunks = []
    stop_needed = lambda value: '.' if not isinstance(value, (str, int, float, bool, list)) else ''

    if isinstance(data, dict):
        for key, value in data.items():
            if value is not None:
                chunks.extend(key_value_chunking(value, prefix=f"{prefix}{key}{stop_needed(value)}"))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            if value is not None:
                chunks.extend(key_value_chunking(value, prefix=f"{prefix}_{index}{stop_needed(value)}"))
    else:
        if data is not None:
            chunks.append(f"{prefix}: {data}")

    return chunks
