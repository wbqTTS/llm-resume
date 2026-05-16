# wbq/prompt_builder.py

def build_rag_prompt(jd_text, retrieved_chunks, original_resume_text):
    """
    构建包含检索上下文的 Prompt。
    """
    # 1. 格式化检索到的证据
    evidence_context = ""
    for i, (score, chunk) in enumerate(retrieved_chunks, 1):
        evidence_context += f"[证据 {i}] (相关度: {score:.2f}): {chunk['content']}\n"

    # 2. 构建最终 Prompt
    prompt = f"""
    # 角色
    你是一位专业的简历优化专家。

    # 任务
    根据提供的【职位描述 (JD)】，利用下方的【相关经历证据】，为用户重写一份简历。

    # 约束 (重要！)
    1. **严格基于证据**：你只能使用【相关经历证据】中提供的信息进行重写和润色。
    2. **禁止幻觉**：如果【相关经历证据】中没有提到的技能或项目，**绝对不要**编造添加到简历中。
    3. **针对性优化**：重点突出【相关经历证据】中与 JD 关键词匹配的部分，使用 STAR 法则描述。
    4. **忽略无关信息**：对于未在【相关经历证据】中出现的旧经历，可以简略提及或省略，以保持简历聚焦。

    # 输入数据
    ## 职位描述 (JD)
    {jd_text}

    ## 相关经历证据 (由系统根据 JD 从原始简历中检索得出)
    {evidence_context}

    ## 用户原始完整简历 (仅供参考背景，请以"相关经历证据"为准)
    {original_resume_text}

    # 输出
    请直接输出优化后的简历内容 (Markdown 格式)。
    """
    return prompt