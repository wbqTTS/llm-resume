# zlm/retriever.py
import json
from typing import List, Dict, Any, Tuple

# 导入你优秀的 metrics 模块
from wbq.utils.metrics import cosine_similarity, normalize_text


def chunk_section_data(section_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将章节数据（如工作经历列表）拆解为独立的文本块 (Chunks)。
    利用 metrics.py 中的逻辑，将每个字典项转换为用于相似度计算的文本。
    """
    chunks = []
    for item in section_data:
        # 策略：直接将字典转为 JSON 字符串
        # 因为 metrics.normalize_text 内部已经包含了 _flatten_json_to_text 逻辑
        # 它可以自动解析 JSON 并提取所有文本值，非常适合这里
        chunk_json_str = json.dumps(item, ensure_ascii=False)

        chunks.append({
            "original": item,  # 保留原始结构化数据，用于后续生成
            "text_repr": chunk_json_str,  # 用于传给 metrics 计算相似度
            "score": 0.0
        })
    return chunks


def retrieve_relevant_chunks(jd_text: str, chunks: List[Dict[str, Any]], top_k: int = 3, threshold: float = 0.15) -> \
List[Tuple[float, Dict[str, Any]]]:
    """
    根据 JD 文本，从 chunks 中检索最相关的 Top-K 个片段。

    Args:
        jd_text: 职位描述 (可以是字典或字符串，metrics 会自动处理)
        chunks: 分块后的简历数据
        top_k: 返回前 K 个最相关的结果
        threshold: 相似度阈值，低于此分数的将被过滤掉

    Returns:
        排序后的 (score, chunk) 列表
    """
    if not chunks:
        return []

    scored_chunks = []

    # 将 JD 也转为 JSON 字符串，以触发 metrics 中的 JSON 解析逻辑
    # 如果 jd_text 已经是字符串，json.dumps 会加引号，但 normalize_text 能处理
    # 为了保险，如果输入是 dict 才 dumps，否则直接用
    jd_input = json.dumps(jd_text, ensure_ascii=False) if isinstance(jd_text, dict) else str(jd_text)

    # 1. 计算相似度 (利用 metrics.py 的强大功能)
    for chunk in chunks:
        try:
            score = cosine_similarity(jd_input, chunk['text_repr'])
            chunk['score'] = score
            scored_chunks.append((score, chunk))
        except Exception as e:
            print(f"⚠️ 相似度计算出错: {e}")
            continue

    # 2. 降序排序
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    # 3. 截取 Top-K 并过滤低分
    result = []
    for score, chunk in scored_chunks:
        if score >= threshold:
            result.append((score, chunk))

        if len(result) >= top_k:
            break

    return result


def format_rag_context(relevant_chunks: List[Tuple[float, Dict[str, Any]]]) -> str:
    """
    将检索到的片段格式化为 LLM 可读的上下文字符串。
    """
    if not relevant_chunks:
        return "未检索到高度相关的经历片段。"

    context_lines = []
    context_lines.append("【系统检索到的核心证据】(按相关度排序):")

    for i, (score, chunk) in enumerate(relevant_chunks, 1):
        # 为了节省 Token，这里只展示原始数据的关键部分
        # 或者直接展示原始数据的 JSON 缩略版
        original = chunk['original']

        # 简单格式化：职位 | 公司 | 关键描述前 100 字
        title = original.get('title', original.get('project_name', '未知项目'))
        company = original.get('company', original.get('organization', ''))

        # 尝试找描述字段
        desc = ""
        for key in ['description', 'details', 'content', 'achievements']:
            if key in original:
                val = original[key]
                desc = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
                break

        desc_preview = desc[:300] + "..." if len(desc) > 150 else desc

        context_lines.append(f"[证据 {i}] (匹配度: {score:.2f}) - {title}@{company}: {desc_preview}")

    return "\n".join(context_lines)