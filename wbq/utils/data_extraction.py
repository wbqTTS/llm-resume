'''
-----------------------------------------------------------------------
File: data_extraction.py
Creation Time: Oct 31st 2023 2:17 pm
Author: Saurabh Zinjad, Amey Bhilegonkar
Developer Email: zinjadsaurabh1997@gmail.com, abhilega@asu.edu
Copyright (c) 2023 Saurabh Zinjad. All rights reserved | GitHub: Ztrimus, ameygoes
-----------------------------------------------------------------------
'''
import re
import json
import requests
from bs4 import BeautifulSoup
import streamlit as st
from langchain_community.document_loaders import WebBaseLoader

# 尝试导入 PyPDF2，如果失败则提示
try:
    import PyPDF2
except ImportError:
    st.error("未找到 PyPDF2 库，请运行: pip install PyPDF2")

import subprocess
import sys
import os


def read_data_from_url(url):
    """
    通过 subprocess 调用独立的 scraper_worker.py 脚本进行暴力爬取。
    优势：
    1. 完美避开 Streamlit 的 asyncio 事件循环冲突。
    2. 保留 Playwright 的动态渲染能力。
    3. 不在本函数内进行文本清洗，返回原始粗糙文本供 LLM 处理。
    """
    print(f"🚀 [Scraper-Subprocess] 启动外部爬虫进程: {url}")

    # 获取当前脚本所在的目录，确保能找到同级的 scraper_worker.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print("current_dir:"+current_dir)

    root_dir = os.path.dirname(os.path.dirname(current_dir))
    print("root_dir:"+root_dir)

    worker_path = os.path.join(root_dir, "scraper_worker.py")

    # 如果上面路径不对，可以尝试直接设为当前目录（如果 worker 也在 utils 里）
    if not os.path.exists(worker_path):
        worker_path = os.path.join(current_dir, "scraper_worker.py")

    if not os.path.exists(worker_path):
        print(f"❌ [Scraper-Subprocess] 找不到 scraper_worker.py 脚本！当前尝试路径: {worker_path}")
        return None

    try:
        result = subprocess.run(
            [sys.executable, worker_path, url],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='ignore',
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}  # 新增：强制子进程使用 UTF-8
        )

        # 检查子进程是否有错误输出
        if result.returncode != 0:
            print(f"💥 [Scraper-Subprocess] 外部脚本执行失败:\n{result.stderr}")
            return None

        raw_content = result.stdout

        if not raw_content or len(raw_content.strip()) == 0:
            print("⚠️ [Scraper-Subprocess] 外部脚本返回内容为空。")
            return None

        print(f"✨ [Scraper-Subprocess] 抓取成功！原始内容长度: {len(raw_content)} 字符")
        # 直接返回原始内容，不做任何清洗
        return raw_content

    except subprocess.TimeoutExpired:
        print("⏰ [Scraper-Subprocess] 抓取超时 (超过 60 秒)。")
        return None
    except Exception as e:
        print(f"💥 [Scraper-Subprocess] 调用外部进程出错: {e}")
        return None
def extract_text_from_pdf(pdf_path: str):
    """
    从 PDF 文件中提取文本。
    注意：PyPDF2 对某些复杂的中文排版支持有限。
    如果遇到中文乱码，建议后续切换到 pdfplumber 库。
    """
    resume_text = ""

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                if text:
                    text_lines = text.split("\n")

                    # --- 修改点 2: 同样移除删除非 ASCII 字符的正则 ---
                    # 原代码会删掉所有中文，这里改为只清理空白行
                    cleaned_lines = [line.strip() for line in text_lines if line.strip()]

                    resume_text += '\n'.join(cleaned_lines) + "\n"

            # 如果提取结果为空，可能是加密 PDF 或扫描版图片 PDF
            if not resume_text.strip():
                st.warning("⚠️ 未能从 PDF 中提取到文本。这可能是扫描版图片 PDF 或加密文件。请尝试提供可复制文字的 PDF 版本。")

            return resume_text
    except Exception as e:
        st.error(f"读取 PDF 失败: {str(e)}")
        return ""

def get_url_content(url: str):
    """ Extract text content from any given web page """
    try:
        # --- 修改点 3: 添加 User-Agent 伪装，防止被招聘网站屏蔽 ---
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status() # 检查请求是否成功

        soup = BeautifulSoup(res.content, "html.parser")

        # 移除脚本和样式标签，减少噪音
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()

        tag = soup.body
        if not tag:
            return ""

        text_content = ""

        for string in tag.strings:
            string = string.strip()
            if string:
                text_content += string + "\n"

        return text_content
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None