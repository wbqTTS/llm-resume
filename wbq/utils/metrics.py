import re
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise

# 尝试导入项目内部工具，如果路径不对请根据实际情况调整或注释掉
try:
    from wbq.utils.utils import key_value_chunking
except ImportError:
    # 如果没有这个模块，定义一个默认的 fallback 函数，防止报错
    def key_value_chunking(data):
        if isinstance(data, dict):
            return " ".join([f"{k}: {v}" for k, v in data.items()])
        return str(data)
    print("Warning: 'wbq.utils.utils.key_value_chunking' not found. Using default fallback.")

import nltk
import jieba  # 用于中文分词
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# --- 配置 NLTK 资源 (自动下载) ---
def download_nltk_resources():
    resources = ['stopwords', 'punkt', 'punkt_tab']
    for resource in resources:
        try:
            nltk.data.find(f'corpora/{resource}' if 'stop' in resource else f'tokenizers/{resource}')
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception:
                pass # 忽略下载失败，后续逻辑会处理

download_nltk_resources()

# --- 自定义中文停用词表 ---
# 包含了通用停用词以及简历中常见但无实际语义的动词/介词
CHINESE_STOPWORDS = set([
    '的', '了', '和', '是', '就', '都', '而', '及', '与', '着', '那',
    '你', '我', '他', '她', '它', '们', '这', '有', '在', '为', '上',
    '也', '很', '到', '说', '要', '去', '人', '个', '一', '不', '大', '来',
    '自己', '之', '后', '把', '被', '让', '给', '用', '看', '想', '能',
    '可以', '可能', '应该', '必须', '以及', '而且', '或者', '但是', '如果',
    '因为', '所以', '虽然', '即使', '无论', '如何', '什么', '哪里', '哪个',
    '怎样', '怎么', '多少', '几', '位', '次', '下', '回', '年', '月', '日', '号',
    # 简历高频无意义动词/介词 (关键优化点)
    '负责', '进行', '通过', '利用', '采用', '基于', '针对', '参与', '协助',
    '完成', '实现', '工作', '内容', '主要', '相关', '其他', '以上', '以下'
])

def remove_urls(list_of_strings):
    """Removes strings containing URLs from a list using regular expressions."""
    if not isinstance(list_of_strings, list):
        return list_of_strings
    filtered_list = [string for string in list_of_strings if not re.search(r"https?://\S+", string)]
    return filtered_list

def detect_language(text):
    """
    简单检测文本主要语言。
    如果中文字符占比超过 20%，视为中文文本，否则视为英文。
    """
    if not text:
        return 'en'
    # 匹配常用汉字范围
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text.replace(" ", "")) # 去除空格计算总字符数

    if total_chars == 0:
        return 'en'

    ratio = chinese_chars / total_chars
    return 'zh' if ratio > 0.2 else 'en'

def normalize_text(text: str) -> list:
    """Normalize the input text (Supports both English and Chinese).

    This function tokenizes the text, removes stopwords and punctuations,
    and applies stemming (for English) or filtering (for Chinese).

    Args:
        text (str): The text to normalize. Can be raw text or a JSON string.

    Returns:
        list: The list of normalized words.
    """
    if not text:
        return []

    # 如果传入的是 JSON 字符串，尝试解析并展平，以便提取所有文本内容
    # 这一步使得函数可以直接接收 resume.json 字符串
    if isinstance(text, str):
        try:
            # 尝试解析 JSON
            data = json.loads(text)
            # 如果是 JSON 对象，递归提取所有字符串值
            if isinstance(data, (dict, list)):
                text = _flatten_json_to_text(data)
        except json.JSONDecodeError:
            pass # 不是 JSON，当作普通字符串处理

    lang = detect_language(text)
    words = []

    if lang == 'zh':
        # --- 中文处理流程 ---
        # 1. 分词 (使用 jieba)
        raw_words = jieba.lcut(text)

        # 2. 清洗：去除标点、数字、特殊符号，只保留中文和英文字母
        cleaned_words = []
        for word in raw_words:
            w = word.strip()
            if not w:
                continue
            # 保留纯中文 或 纯英文单词 (例如简历中的 "Python", "Java")
            if re.match(r'^[\u4e00-\u9fa5]+$', w) or re.match(r'^[a-zA-Z]+$', w):
                cleaned_words.append(w.lower())

        # 3. 去除停用词
        words = [word for word in cleaned_words if word not in CHINESE_STOPWORDS]

    else:
        # --- 英文处理流程 ---
        # 1. 分词
        try:
            raw_words = word_tokenize(text)
        except Exception:
            # 如果 nltk 分词失败，退化为空格分割
            raw_words = text.split()

        # 2. 清洗：去除非字母字符，转小写
        cleaned_words = []
        for word in raw_words:
            clean_w = re.sub('[^a-zA-Z]', '', word).lower()
            if clean_w:
                cleaned_words.append(clean_w)

        # 3. 去除停用词
        try:
            stop_words = set(stopwords.words('english'))
        except:
            stop_words = set() # 防止 NLTK 资源未下载导致报错

        cleaned_words = [word for word in cleaned_words if word not in stop_words]

        # 4. 词干提取 (Stemming)
        stemmer = PorterStemmer()
        words = [stemmer.stem(word) for word in cleaned_words]

    return words

def _flatten_json_to_text(data):
    """Helper function to recursively extract all string values from a JSON object."""
    if isinstance(data, str):
        return data
    elif isinstance(data, dict):
        parts = []
        for key, value in data.items():
            # 可以选择跳过某些字段，如 media links，这里暂时保留所有文本
            if key == 'media':
                continue
            parts.append(_flatten_json_to_text(value))
        return " ".join(parts)
    elif isinstance(data, list):
        return " ".join([_flatten_json_to_text(item) for item in data])
    else:
        return str(data)

def overlap_coefficient(document1: str, document2: str) -> float:
    """Calculate the overlap coefficient between two documents."""
    words_in_document1 = set(normalize_text(document1))
    words_in_document2 = set(normalize_text(document2))

    if not words_in_document1 or not words_in_document2:
        return 0.0

    intersection = words_in_document1.intersection(words_in_document2)

    try:
        overlap_coefficient = float(len(intersection)) / min(len(words_in_document1), len(words_in_document2))
    except ZeroDivisionError:
        overlap_coefficient = 0.0

    return overlap_coefficient

def jaccard_similarity(document1: str, document2: str) -> float:
    """Calculate the Jaccard similarity between two documents."""
    words_in_document1 = set(normalize_text(document1))
    words_in_document2 = set(normalize_text(document2))

    if not words_in_document1 and not words_in_document2:
        return 0.0

    intersection = words_in_document1.intersection(words_in_document2)
    union = words_in_document1.union(words_in_document2)

    if len(union) == 0:
        return 0.0

    return float(len(intersection)) / len(union)


def cosine_similarity(document1: str, document2: str) -> float:
    """Calculate the cosine similarity between two documents using TF-IDF."""
    # ========== 调试代码开始 ==========
    print(f"🔍 [metrics] cosine_similarity 被调用")
    print(f"🔍 [metrics] document1 长度: {len(document1)}")
    print(f"🔍 [metrics] document2 长度: {len(document2)}")
    import sys
    sys.stdout.flush()
    # ========== 调试代码结束 ==========

    """Calculate the cosine similarity between two documents using TF-IDF.

    Supports mixed Chinese/English by pre-tokenizing with normalize_text.
    """
    # 1. 预处理：分词、去停用词、词干提取（英文）
    tokens1 = normalize_text(document1)
    tokens2 = normalize_text(document2)

    if not tokens1 or not tokens2:
        return 0.0

    # 2. 将分词结果用空格连接，形成新的“文档字符串”
    # 例如: ["python", "engineer"] -> "python engineer"
    doc1_processed = " ".join(tokens1)
    doc2_processed = " ".join(tokens2)

    # 3. 使用 TfidfVectorizer
    # analyzer='word' 会按照空格分割，正好对应我们上面处理好的 tokens
    vectorizer = TfidfVectorizer(analyzer='word')

    try:
        tfidf_matrix = vectorizer.fit_transform([doc1_processed, doc2_processed])
        score = pairwise.cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        return float(score)
    except ValueError:
        # 如果词汇表为空（极端情况）
        return 0.0

def vector_embedding_similarity(llm, document1: str, document2: str) -> float:
    """Calculate similarity based on LLM embeddings."""
    if not llm:
        return 0.0

    try:
        doc1_processed = document1
        doc2_processed = document2

        # 如果输入是 JSON 字符串，尝试利用 key_value_chunking 进行结构化提取
        if isinstance(document1, str):
            try:
                d1_data = json.loads(document1)
                d2_data = json.loads(document2)
                # 确保 key_value_chunking 可用
                if 'key_value_chunking' in globals() or 'key_value_chunking' in locals():
                     doc1_processed = key_value_chunking(d1_data)
                     doc2_processed = key_value_chunking(d2_data)
                else:
                    # Fallback if function not imported correctly
                    doc1_processed = _flatten_json_to_text(d1_data)
                    doc2_processed = _flatten_json_to_text(d2_data)
            except json.JSONDecodeError:
                pass # Not JSON, use as is

        # 获取 Embedding
        # 注意：不同的 LLM 库 API 可能不同，这里保持原逻辑假设
        emb_1 = llm.get_embedding(doc1_processed, task_type="retrieval_query")
        emb_2 = llm.get_embedding(doc2_processed, task_type="retrieval_query")

        # 提取向量数据
        list1 = emb_1.embedding if hasattr(emb_1, 'embedding') else []
        list2 = emb_2.embedding if hasattr(emb_2, 'embedding') else []

        if not list1 or not list2:
            return 0.0

        df1 = pd.DataFrame([list1])
        df2 = pd.DataFrame([list2])

        emb_sem = pairwise.cosine_similarity(df1, df2)
        return float(emb_sem.mean())
    except Exception as e:
        print(f"Error calculating embedding similarity: {e}")
        return 0.0