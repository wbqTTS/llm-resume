"""
简历分析工具模块 - 深度集成版
充分利用项目已有的 RAG、CoT、LLM 能力

功能：
1. 多维度匹配度计算（复用 metrics.py）
2. RAG 增强的面试问答（复用 retriever.py + LLM）
3. AI 生成改进建议（复用 LLM + CoT）
4. 雷达图可视化（带缓存）
5. 关键词词云（带缓存）
6. PDF 报告导出（支持中文，复用已有分析结果）
"""
import os
import json
import platform
import base64
import io
import re
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import jieba

# 深度集成原项目模块
from wbq.utils.metrics import cosine_similarity, jaccard_similarity, overlap_coefficient, normalize_text
from wbq.utils.utils import key_value_chunking
from wbq.utils.retriever import retrieve_relevant_chunks, chunk_section_data, format_rag_context


# ============================================================
# 跨平台字体配置
# ============================================================
def get_font_path() -> str:
    """根据操作系统获取合适的中文字体路径"""
    system = platform.system()
    if system == 'Windows':
        candidates = [
            "C:/Windows/Fonts/simhei.ttf",      # 黑体
            "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
            "C:/Windows/Fonts/simsun.ttc",      # 宋体
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return "C:/Windows/Fonts/simhei.ttf"
    elif system == 'Darwin':
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return "/System/Library/Fonts/PingFang.ttc"
    else:
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"


FONT_PATH = get_font_path()

# 设置 matplotlib 全局中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False


class ResumeAnalyzer:
    """
    简历分析器 - 深度集成原项目能力

    功能：
    1. 多维度匹配度计算（复用 metrics.py）
    2. RAG 增强的面试问答（复用 retriever.py + LLM）
    3. AI 生成改进建议（复用 LLM + CoT）
    4. 雷达图可视化（带缓存）
    5. 关键词词云（带缓存）
    6. PDF 报告导出（支持中文，复用已有分析结果）
    """

    def __init__(self, resume_details: Dict[str, Any], job_details: Dict[str, Any],
                 user_data: Optional[Dict[str, Any]] = None, llm_instance=None):
        """
        初始化分析器

        Args:
            resume_details: 生成的简历 JSON 数据
            job_details: 职位描述 JSON 数据
            user_data: 原始用户数据（用于对比分析）
            llm_instance: LLM 实例（用于生成 AI 建议和面试问答）
        """
        self.resume_details = resume_details
        self.job_details = job_details
        self.user_data = user_data
        self.llm = llm_instance

        # 缓存 JSON 字符串
        self._resume_json = json.dumps(resume_details, ensure_ascii=False)
        self._job_json = json.dumps(job_details, ensure_ascii=False)

        # 缓存 RAG 检索结果
        self._rag_cache = None

        # ===== 缓存分析结果（避免重复计算）=====
        self._cached_scores = None
        self._cached_suggestions = None
        self._cached_questions = None
        self._cached_radar_img = None
        self._cached_wordcloud_img = None

        # 计算各维度匹配度（只计算一次）
        self.scores = self._calculate_scores()

    def _calculate_scores(self) -> Dict[str, float]:
        """计算多维度匹配度分数"""
        scores = {}

        # 整体匹配度
        overall_cosine = cosine_similarity(self._resume_json, self._job_json)
        scores['整体匹配度'] = round(overall_cosine * 100, 1)

        # 关键词重叠度
        jaccard = jaccard_similarity(self._resume_json, self._job_json)
        scores['关键词匹配度'] = round(jaccard * 100, 1)

        # 核心词覆盖度
        overlap = overlap_coefficient(self._resume_json, self._job_json)
        scores['核心词覆盖度'] = round(overlap * 100, 1)

        # 技术栈匹配度
        resume_skills = self._extract_skills(self.resume_details)
        job_skills = self._extract_skills_from_jd()
        if job_skills:
            skill_match = len(resume_skills & job_skills) / len(job_skills)
        else:
            skill_match = 0.5
        scores['技术栈匹配'] = round(skill_match * 100, 1)

        # 量化成果匹配度
        scores['量化成果匹配'] = self._calculate_quantification_score()

        # 工作经验匹配度
        scores['工作经验匹配'] = self._calculate_experience_score()

        # 项目经验匹配度
        scores['项目经验匹配'] = self._calculate_project_score()

        # 教育背景匹配度
        scores['教育背景匹配'] = self._calculate_education_score()

        return scores

    def _extract_skills(self, data: Dict[str, Any]) -> set:
        """从简历数据中提取技能集合"""
        skills = set()
        for skill_section in data.get('skill_section', []):
            for skill in skill_section.get('skills', []):
                normalized = normalize_text(skill)
                skills.update(normalized)
        return skills

    def _extract_skills_from_jd(self) -> set:
        """从职位描述中提取技能要求"""
        job_text = self._job_json.lower()
        skill_keywords = [
            'python', 'java', 'c++', 'javascript', 'sql', 'mysql', 'postgresql',
            'redis', 'docker', 'kubernetes', 'aws', 'spring', 'django', 'flask',
            'vue', 'react', 'tensorflow', 'pytorch', 'git', 'linux'
        ]
        job_skills = set()
        for skill in skill_keywords:
            if skill in job_text:
                job_skills.add(skill)
        return job_skills

    def _calculate_quantification_score(self) -> float:
        """计算量化成果匹配度"""
        patterns = [r'\d+%', r'\d+倍', r'\d+\.?\d*万', r'\d+\.?\d*千',
                    r'提升\d+', r'降低\d+', r'减少\d+', r'节省\d+']
        resume_text = self._resume_json
        match_count = sum(len(re.findall(p, resume_text)) for p in patterns)
        return min(100, match_count * 10)

    def _calculate_experience_score(self) -> float:
        """计算工作经验匹配度"""
        work_exp = self.resume_details.get('work_experience', [])
        if not work_exp:
            return 30.0
        exp_count = len(work_exp)
        return min(100, exp_count * 25)

    def _calculate_project_score(self) -> float:
        """计算项目经验匹配度"""
        projects = self.resume_details.get('projects', [])
        if not projects:
            return 40.0
        proj_count = len(projects)
        return min(100, proj_count * 20)

    def _calculate_education_score(self) -> float:
        """计算教育背景匹配度"""
        education = self.resume_details.get('education', [])
        if not education:
            return 50.0
        has_gpa = any(edu.get('gpa') for edu in education)
        has_honors = any(edu.get('honors') for edu in education)
        score = 70.0 + (10 if has_gpa else 0) + (10 if has_honors else 0)
        return min(100, score)

    def _get_rag_context(self) -> str:
        """获取 RAG 检索的上下文（缓存）"""
        if self._rag_cache is not None:
            return self._rag_cache

        try:
            sections = ['work_experience', 'projects', 'education']
            all_chunks = []
            for section in sections:
                section_data = self.resume_details.get(section, [])
                if section_data:
                    chunks = chunk_section_data(section_data)
                    all_chunks.extend(chunks)

            if all_chunks:
                job_text = json.dumps(self.job_details, ensure_ascii=False)
                relevant_chunks = retrieve_relevant_chunks(job_text, all_chunks, top_k=3, threshold=0.15)
                self._rag_cache = format_rag_context(relevant_chunks)
            else:
                self._rag_cache = ""
        except Exception as e:
            print(f"RAG 检索失败: {e}")
            self._rag_cache = ""

        return self._rag_cache

    def get_radar_chart(self) -> str:
        """生成雷达图（带缓存）"""
        if self._cached_radar_img is not None:
            return self._cached_radar_img

        categories = ['整体匹配度', '技术栈匹配', '关键词匹配度', '量化成果匹配', '工作经验匹配', '项目经验匹配']
        values = [self.scores.get(cat, 0) for cat in categories]

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
        ax.plot(angles, values, 'o-', linewidth=2, color='#1E88E5')
        ax.fill(angles, values, alpha=0.25, color='#1E88E5')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=9)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], size=8)
        ax.set_title('简历匹配度雷达图', size=14, fontweight='bold', pad=20)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()

        self._cached_radar_img = f"data:image/png;base64,{img_base64}"
        return self._cached_radar_img

    def get_wordcloud(self) -> str:
        """生成词云（带缓存，支持中文，屏蔽无意义字段名）"""
        if self._cached_wordcloud_img is not None:
            return self._cached_wordcloud_img

        # 需要屏蔽的无意义字段名和关键词
        blacklist = {
            # 字段名
            'personal', 'name', 'birthdate', 'phone', 'politics', 'email', 'hometown', 'photo',
            'title', 'summary', 'media', 'linkedin', 'github', 'medium', 'devpost',
            'education', 'university', 'degree', 'from_date', 'to_date', 'gpa', 'honors', 'courses',
            'work_experience', 'role', 'company', 'location', 'description',
            'projects', 'type', 'skill_section', 'skills', 'skill', 'keywords',
            'social_practice', 'certifications', 'achievements', 'date', 'by',
            'work', 'experience', 'project', 'skill', 'section', 'practice', 'certification', 'achievement',
            # 通用无意义词
            '一个', '这个', '那个', '这些', '那些', '没有', '不是', '已经', '还是',
            '可以', '进行', '我们', '他们', '你们', '它们', '自己', '什么', '怎么',
            '为什么', '哪里', '哪个', '多少', '如何', '这样', '那样', '这么', '那么',
            '只是', '只有', '只要', '为了', '由于', '因为', '所以', '如果', '虽然',
            '但是', '然而', '而且', '并且', '或者', '以及', '不仅', '还有'
        }

        # 提取文本
        chunked_resume = " ".join(key_value_chunking(self.resume_details))
        chunked_job = " ".join(key_value_chunking(self.job_details))
        combined_text = chunked_resume + " " + chunked_job

        # 清洗文本：移除 URL、邮箱、数字等
        combined_text = re.sub(r'https?://\S+', '', combined_text)
        combined_text = re.sub(r'\S+@\S+', '', combined_text)
        combined_text = re.sub(r'\d+', '', combined_text)

        # 中文分词
        words = jieba.cut(combined_text)
        word_freq = {}

        for word in words:
            if len(word) < 2:
                continue
            if word.lower() in blacklist:
                continue
            if word in blacklist:
                continue
            if re.match(r'^[a-zA-Z]+$', word) and len(word) < 3:
                continue
            if word.isdigit():
                continue
            word_freq[word] = word_freq.get(word, 0) + 1

        # 如果没有足够的词，返回默认提示
        if not word_freq:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.text(0.5, 0.5, '暂无足够关键词\n请检查简历内容',
                    ha='center', va='center', fontsize=20, color='gray')
            ax.axis('off')
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode()
            plt.close()
            self._cached_wordcloud_img = f"data:image/png;base64,{img_base64}"
            return self._cached_wordcloud_img

        # 生成词云
        try:
            wc = WordCloud(
                width=800, height=400,
                background_color='white',
                font_path=FONT_PATH,
                max_words=50,
                colormap='Blues',
                random_state=42,
                stopwords=blacklist
            ).generate_from_frequencies(word_freq)
        except Exception as e:
            print(f"词云生成失败: {e}")
            wc = WordCloud(
                width=800, height=400,
                background_color='white',
                max_words=50,
                colormap='Blues',
                stopwords=blacklist
            ).generate_from_frequencies(word_freq)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('简历与职位描述关键词云', fontsize=14, fontweight='bold')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()

        self._cached_wordcloud_img = f"data:image/png;base64,{img_base64}"
        return self._cached_wordcloud_img

    def get_improvement_suggestions(self) -> List[Dict[str, str]]:
        """生成 AI 改进建议（带缓存）"""
        if self._cached_suggestions is not None:
            return self._cached_suggestions

        # 获取 RAG 上下文
        rag_context = self._get_rag_context()

        # 如果有 LLM 实例，调用生成建议
        if self.llm:
            suggestion_prompt = f"""
你是一位资深职业顾问。请根据以下信息，为用户提供 3-5 条具体的简历优化建议。

## 职位描述 (JD)
{json.dumps(self.job_details, ensure_ascii=False)[:1500]}

## 简历当前匹配度
{json.dumps(self.scores, ensure_ascii=False)}

## 检索到的高相关度证据 (RAG)
{rag_context[:1000] if rag_context else "无"}

## 要求
1. 每条建议聚焦一个具体问题（如：技术栈匹配、量化成果、项目描述等）
2. 给出可操作的具体修改方向
3. 按优先级排序（最重要的问题放在第一条）

请输出 JSON 数组格式：
[
  {{"dimension": "问题维度", "level": "error/warning/info/success", "suggestion": "具体建议"}}
]
"""
            try:
                response = self.llm.get_response(prompt=suggestion_prompt, need_json_output=True)
                if response and isinstance(response, list):
                    self._cached_suggestions = response
                    return self._cached_suggestions
            except Exception as e:
                print(f"LLM 生成建议失败: {e}")

        # 降级方案：基于规则的建议
        suggestions = []

        overall = self.scores.get('整体匹配度', 0)
        if overall < 50:
            suggestions.append({'dimension': '整体匹配度', 'level': 'error',
                               'suggestion': '简历与职位描述整体匹配度较低。建议重点突出与岗位相关的核心技能和项目经验。'})
        elif overall < 70:
            suggestions.append({'dimension': '整体匹配度', 'level': 'warning',
                               'suggestion': '简历与职位描述匹配度中等。建议强化与岗位最相关的2-3项核心能力描述。'})
        else:
            suggestions.append({'dimension': '整体匹配度', 'level': 'success',
                               'suggestion': '简历整体质量较高！可在面试中重点突出你的技术亮点。'})

        tech_score = self.scores.get('技术栈匹配', 0)
        if tech_score < 50:
            suggestions.append({'dimension': '技术栈匹配', 'level': 'error',
                               'suggestion': '技术栈与岗位要求差距较大。建议补充岗位要求的核心技能，或在项目经历中突出相关技术应用。'})
        elif tech_score < 80:
            suggestions.append({'dimension': '技术栈匹配', 'level': 'info',
                               'suggestion': '技术栈匹配度良好，可进一步强化与岗位最相关的核心技能描述。'})

        quant_score = self.scores.get('量化成果匹配', 0)
        if quant_score < 50:
            suggestions.append({'dimension': '量化成果', 'level': 'warning',
                               'suggestion': '缺少量化成果数据。建议使用具体数字（如"提升30%性能"）来增强说服力。'})

        self._cached_suggestions = suggestions
        return suggestions

    def get_interview_questions(self, top_k: int = 5) -> List[Dict[str, str]]:
        """生成面试问答（带缓存）"""
        if self._cached_questions is not None:
            return self._cached_questions[:top_k]

        questions = []
        rag_context = self._get_rag_context()

        # 如果有 LLM 实例，调用生成问题
        if self.llm:
            interview_prompt = f"""
你是一位资深技术面试官。请根据以下简历和职位描述，生成 {top_k} 个有针对性的面试问题。

## 简历核心内容
{json.dumps(self.resume_details, ensure_ascii=False)[:2000]}

## 职位描述 (JD)
{json.dumps(self.job_details, ensure_ascii=False)[:1000]}

## 检索到的高相关度证据 (RAG)
{rag_context[:800] if rag_context else "无"}

## 要求
1. 问题应针对简历中的具体项目和技能
2. 结合岗位要求，考察候选人的技术深度和项目经验
3. 问题应具有开放性，引导候选人展示能力

请输出 JSON 数组格式：
[
  {{"question": "具体问题", "suggestion": "回答思路/要点"}}
]
"""
            try:
                response = self.llm.get_response(prompt=interview_prompt, need_json_output=True)
                if response and isinstance(response, list):
                    self._cached_questions = response
                    return self._cached_questions[:top_k]
            except Exception as e:
                print(f"LLM 生成面试问题失败: {e}")

        # 降级方案：基于规则生成问题
        tech_stack = []
        for skill_section in self.resume_details.get('skill_section', []):
            tech_stack.extend(skill_section.get('skills', []))
        tech_stack_lower = [s.lower() for s in tech_stack]

        if 'python' in tech_stack_lower:
            questions.append({
                'question': '请介绍一下你在 Python 项目中最有挑战性的技术难点，以及你是如何解决的？',
                'suggestion': '按照 STAR 法则回答：背景-任务-行动-结果，突出个人贡献。'
            })

        if any(kw in tech_stack_lower for kw in ['spring', 'springboot', 'java']):
            questions.append({
                'question': '你在 Spring Boot 项目中如何处理高并发场景？用过哪些优化手段？',
                'suggestion': '可提及缓存、异步处理、数据库索引优化、连接池配置等具体措施。'
            })

        projects = self.resume_details.get('projects', [])
        if projects:
            first_project = projects[0].get('name', '你的项目')
            questions.append({
                'question': f'请详细介绍一下"{first_project}"项目中你的具体职责和技术贡献。',
                'suggestion': '突出个人贡献和量化成果，使用 STAR 法则回答。'
            })

        questions.append({
            'question': '你如何看待自己与这个岗位的匹配度？你的哪些优势最能胜任这个职位？',
            'suggestion': '结合简历中的亮点和岗位要求，自信地展示核心优势。'
        })

        self._cached_questions = questions
        return questions[:top_k]

    def export_report(self, output_path: str, quality_analysis_data: dict = None) -> str:
        """导出 PDF 分析报告（复用已有分析结果）

        Args:
            output_path: 输出文件路径
            quality_analysis_data: 质量分析数据，包含个人特色保留度、人岗匹配度、原始匹配度
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()

        # 注册中文字体
        font_registered = False
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            FONT_PATH
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    font_registered = True
                    break
                except Exception:
                    continue

        if font_registered:
            chinese_style = ParagraphStyle('ChineseStyle', parent=styles['Normal'], fontName='ChineseFont', fontSize=10, leading=14)
            title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontName='ChineseFont', fontSize=16, leading=20)
            heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading1'], fontName='ChineseFont', fontSize=12, leading=16)
        else:
            chinese_style = styles['Normal']
            title_style = styles['Title']
            heading_style = styles['Heading1']
            print("⚠️ 未找到中文字体，PDF 中的中文可能显示为方框")

        story = []

        # 标题
        story.append(Paragraph("简历诊断报告", title_style))
        story.append(Spacer(1, 12 * mm))

        # 一、匹配度评分
        story.append(Paragraph("一、匹配度评分", heading_style))
        story.append(Spacer(1, 6 * mm))

        score_data = [['维度', '得分']] + [[k, f"{v}%"] for k, v in self.scores.items()]
        col_widths = [100 * mm, 40 * mm]
        score_table = Table(score_data, colWidths=col_widths)
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont' if font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 10 * mm))

        # 二、质量分析
        story.append(Paragraph("二、质量分析", heading_style))
        story.append(Spacer(1, 6 * mm))

        if quality_analysis_data:
            q_data = quality_analysis_data
            story.append(Paragraph("<b>关键词匹配度（重叠系数）</b>", chinese_style))
            story.append(Spacer(1, 3 * mm))

            quality_table_data = [
                ['指标', '个人特色保留度', '人岗匹配度', '原始匹配度'],
                ['关键词匹配度', f"{q_data.get('overlap_user', 0):.3f}", f"{q_data.get('overlap_job', 0):.3f}", f"{q_data.get('overlap_match', 0):.3f}"],
                ['语义相似度', f"{q_data.get('cosine_user', 0):.3f}", f"{q_data.get('cosine_job', 0):.3f}", f"{q_data.get('cosine_match', 0):.3f}"]
            ]

            quality_table = Table(quality_table_data, colWidths=[50 * mm, 45 * mm, 45 * mm, 45 * mm])
            quality_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont' if font_registered else 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(quality_table)
        else:
            story.append(Paragraph("质量分析数据不可用，请重新生成简历。", chinese_style))

        story.append(Spacer(1, 10 * mm))

        # 三、改进建议（使用缓存）
        story.append(Paragraph("三、改进建议", heading_style))
        story.append(Spacer(1, 6 * mm))

        suggestions = self.get_improvement_suggestions()
        for s in suggestions:
            text = f"• {s['dimension']}：{s['suggestion']}"
            story.append(Paragraph(text, chinese_style))
            story.append(Spacer(1, 4 * mm))

        story.append(Spacer(1, 10 * mm))

        # 四、面试问答（使用缓存）
        story.append(Paragraph("四、模拟面试问答", heading_style))
        story.append(Spacer(1, 6 * mm))

        questions = self.get_interview_questions(top_k=5)
        for i, q in enumerate(questions):
            story.append(Paragraph(f"{i + 1}. {q['question']}", chinese_style))
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(f"   💡 回答思路：{q['suggestion']}", chinese_style))
            story.append(Spacer(1, 6 * mm))

        doc.build(story)
        return output_path

    def get_summary_stats(self) -> Dict[str, Any]:
        """获取统计摘要"""
        return {
            'total_score': self.scores.get('整体匹配度', 0),
            'max_dimension': max(self.scores.items(), key=lambda x: x[1]) if self.scores else ('无', 0),
            'min_dimension': min(self.scores.items(), key=lambda x: x[1]) if self.scores else ('无', 0),
            'avg_score': sum(self.scores.values()) / len(self.scores) if self.scores else 0
        }


# ============================================================
# 便捷函数
# ============================================================

def analyze_resume(resume_details: Dict[str, Any], job_details: Dict[str, Any],
                   user_data: Optional[Dict[str, Any]] = None, llm_instance=None) -> ResumeAnalyzer:
    """创建 ResumeAnalyzer 实例"""
    return ResumeAnalyzer(resume_details, job_details, user_data, llm_instance)
