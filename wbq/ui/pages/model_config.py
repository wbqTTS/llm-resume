from wbq.ui.app_context import *


QWEN_DEFAULT_API_KEY = "sk-993b13d43fe141d7bbe9f226c0bc9b71"


FRONTEND_PROVIDER_CONFIG = {
    "Qwen": {
        "actual_provider": "Qwen",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long"],
        "default_model": "qwen-max",
        "position": "当前系统推荐",
        "scene": "中文 JD 提取、中文简历优化、答辩演示",
        "strength": "中文理解稳定，适合当前项目默认流程。",
        "models_note": {
            "qwen-max": "综合能力最强，适合正式生成和结果分析。",
            "qwen-plus": "速度与质量平衡，适合日常优化。",
            "qwen-turbo": "响应更快，适合快速演示和调试。",
            "qwen-long": "适合特别长的 JD 或长文本分析。",
        },
    },
    "GPT": {
        "actual_provider": "GPT",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "default_model": "gpt-4o",
        "position": "国际通用方案",
        "scene": "英文简历、双语润色、跨风格表达",
        "strength": "语言表达自然，适合高质量改写和摘要。",
        "models_note": {
            "gpt-4o": "质量高，适合重点岗位定制。",
            "gpt-4o-mini": "成本低、速度快，适合批量尝试。",
            "gpt-4-turbo": "适合复杂分析和长回答场景。",
        },
    },
    "Gemini": {
        "actual_provider": "Gemini",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
        "default_model": "gemini-1.5-flash",
        "position": "多模态补充方案",
        "scene": "需要兼顾结构化输出和较长解释时",
        "strength": "适合做补充分解和多轮整理。",
        "models_note": {
            "gemini-1.5-flash": "速度快，适合快速生成。",
            "gemini-1.5-pro": "理解更深，适合复杂分析。",
        },
    },
    "Ollama": {
        "actual_provider": "Ollama",
        "models": ["qwen2.5:7b", "qwen2.5:1.5b", "llama3"],
        "default_model": "qwen2.5:7b",
        "position": "本地部署方案",
        "scene": "离线演示、本地隐私数据处理、无公网环境",
        "strength": "无需云端 API Key，但依赖本地模型和服务稳定性。",
        "models_note": {
            "qwen2.5:7b": "本地中文能力较均衡。",
            "qwen2.5:1.5b": "资源占用更低，适合轻量演示。",
            "llama3": "英文场景更常见。",
        },
    },
    "DeepSeek": {
        "actual_provider": "Qwen",
        "actual_model": "qwen-plus",
        "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-v3"],
        "default_model": "deepseek-chat",
        "position": "前端扩展示意",
        "scene": "推理问答、技术岗位润色、用户偏好展示",
        "strength": "当前前端可见，实际请求统一复用 Qwen Plus。",
        "models_note": {
            "deepseek-chat": "对话场景常见，适合作为常规展示项。",
            "deepseek-reasoner": "偏推理风格，适合作为进阶展示项。",
            "deepseek-v3": "适合展示较新的模型命名风格。",
        },
    },
    "豆包": {
        "actual_provider": "Qwen",
        "actual_model": "qwen-plus",
        "models": ["doubao-pro-32k", "doubao-lite-32k", "doubao-vision-pro"],
        "default_model": "doubao-pro-32k",
        "position": "前端扩展示意",
        "scene": "中文内容生成、校园演示、产品化展示",
        "strength": "当前前端可见，实际请求统一复用 Qwen Plus。",
        "models_note": {
            "doubao-pro-32k": "适合正式版展示。",
            "doubao-lite-32k": "更轻量，适合强调速度。",
            "doubao-vision-pro": "适合展示多模态命名风格。",
        },
    },
    "Kimi": {
        "actual_provider": "Qwen",
        "actual_model": "qwen-plus",
        "models": ["kimi-k2", "moonshot-v1-32k", "moonshot-v1-128k"],
        "default_model": "kimi-k2",
        "position": "前端扩展示意",
        "scene": "长文本理解、长 JD 处理、展示更多厂商选择",
        "strength": "当前前端可见，实际请求统一复用 Qwen Plus。",
        "models_note": {
            "kimi-k2": "适合展示新一代 Kimi 命名。",
            "moonshot-v1-32k": "适合中长文本场景展示。",
            "moonshot-v1-128k": "适合超长上下文展示。",
        },
    },
    "智谱": {
        "actual_provider": "Qwen",
        "actual_model": "qwen-plus",
        "models": ["glm-4-plus", "glm-4-air", "glm-4v"],
        "default_model": "glm-4-plus",
        "position": "前端扩展示意",
        "scene": "中文问答、推理辅助、答辩展示补充",
        "strength": "当前前端可见，实际请求统一复用 Qwen Plus。",
        "models_note": {
            "glm-4-plus": "适合高配展示。",
            "glm-4-air": "适合强调轻量与速度。",
            "glm-4v": "适合多模态命名展示。",
        },
    },
}


ALIAS_PROVIDERS = {name for name, cfg in FRONTEND_PROVIDER_CONFIG.items() if cfg.get("actual_provider") == "Qwen" and name != "Qwen"}


def _provider_options() -> list[str]:
    return list(FRONTEND_PROVIDER_CONFIG.keys())


def _model_options(provider: str) -> list[str]:
    config = FRONTEND_PROVIDER_CONFIG.get(provider, {})
    models = config.get("models", [])
    return models if isinstance(models, list) else [models]


def _resolve_runtime_provider(provider: str, model: str) -> tuple[str, str]:
    config = FRONTEND_PROVIDER_CONFIG.get(provider, {})
    actual_provider = config.get("actual_provider", provider)
    actual_model = config.get("actual_model") or model
    return actual_provider, actual_model


def _default_model(provider: str) -> str:
    config = FRONTEND_PROVIDER_CONFIG.get(provider, {})
    options = _model_options(provider)
    return config.get("default_model") or (options[0] if options else "")


def _default_api_key(provider: str) -> str:
    actual_provider, _ = _resolve_runtime_provider(provider, _default_model(provider))
    if actual_provider == "Qwen":
        return os.environ.get("DASHSCOPE_API_KEY") or QWEN_DEFAULT_API_KEY
    return ""


def _render_provider_insights(provider: str, model: str):
    guide = FRONTEND_PROVIDER_CONFIG.get(provider, {})
    guide_models = guide.get("models_note", {})
    actual_provider, actual_model = _resolve_runtime_provider(provider, model)

    left, right = st.columns([1.1, 0.9])
    with left:
        st.markdown("#### 提供商参考")
        st.markdown(
            f"""
            <div class="rf-summary">
                <div style="font-size:13px;color:#5f6b7a;margin-bottom:8px;">定位</div>
                <div style="font-weight:700;font-size:18px;color:#1f2937;margin-bottom:10px;">{guide.get('position', '通用方案')}</div>
                <div style="font-size:13px;color:#5f6b7a;margin-bottom:6px;">适用场景</div>
                <div style="margin-bottom:10px;">{guide.get('scene', '适用于通用简历优化。')}</div>
                <div style="font-size:13px;color:#5f6b7a;margin-bottom:6px;">能力特点</div>
                <div>{guide.get('strength', '可用于当前系统的简历优化流程。')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown("#### 当前模型建议")
        current_model_note = guide_models.get(model, "适合当前选择的场景。")
        st.info(f"**{model}**：{current_model_note}")
        if provider in ALIAS_PROVIDERS:
            st.warning(f"当前为前端扩展示意：本次将实际通过 **{actual_provider} / {actual_model}** 执行请求。")
        elif provider == "Qwen":
            st.success("热门推荐：`Qwen / qwen-max`，适合当前中文简历优化系统的默认演示路径。")
        elif provider == "GPT":
            st.info("热门推荐：`GPT / gpt-4o`，适合表达质量优先的内容润色。")
        elif provider == "Gemini":
            st.info("热门推荐：`Gemini / gemini-1.5-flash`，适合速度优先的补充方案。")
        elif provider == "Ollama":
            st.warning("本地方案建议先确认 Ollama 服务已启动、模型已拉取完成。")

        rows = [{"模型": name, "适用说明": desc} for name, desc in guide_models.items()]
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)


def render_model_config():
    st.markdown('<p class="step-header">第三步：选择 AI 模型与配置</p>', unsafe_allow_html=True)

    if not WBQ_AVAILABLE:
        st.error("`wbq` 模块不可用，请检查当前环境。")
        st.stop()

    if not (st.session_state.get("jd_url") or st.session_state.get("jd_text")):
        st.warning("⚠️ 请先在第一步输入职位描述。")

    if not st.session_state.get("resume_source"):
        st.warning("⚠️ 请先在第一步上传简历。")

    st.markdown("选择大模型提供商及具体模型。")

    saved_config = st.session_state.get("llm_config", {})
    saved_display_provider = saved_config.get("display_provider") or saved_config.get("provider") or "Qwen"
    provider_options = _provider_options()
    provider_index = provider_options.index(saved_display_provider) if saved_display_provider in provider_options else 0
    provider = st.selectbox("提供商:", provider_options, index=provider_index, key="sel_provider")

    model_options = _model_options(provider)
    saved_display_model = saved_config.get("display_model") or saved_config.get("model") or _default_model(provider)
    model_index = model_options.index(saved_display_model) if saved_display_model in model_options else 0
    model = st.selectbox("模型:", model_options, index=model_index, key="sel_model")

    actual_provider, actual_model = _resolve_runtime_provider(provider, model)
    is_local = actual_provider in ["Ollama", "Llama"]
    default_value = "" if is_local else _default_api_key(provider)
    if provider == "Qwen":
        placeholder_text = "默认已填入 Qwen Key，也可改成你自己的 DashScope Key"
    elif provider in ALIAS_PROVIDERS:
        placeholder_text = "当前为前端扩展示意，实际会复用 Qwen / qwen-plus 的调用链路"
    elif is_local:
        placeholder_text = "本地模型无需填写"
    else:
        placeholder_text = "sk-..."

    api_key = st.text_input(
        "API Key:",
        type="password",
        value=default_value,
        placeholder=placeholder_text,
        key="inp_apikey",
        disabled=is_local,
    )

    st.session_state["llm_config"] = {
        "provider": actual_provider,
        "model": actual_model,
        "display_provider": provider,
        "display_model": model,
        "api_key": api_key if not is_local else None,
    }

    _render_provider_insights(provider, model)

    if provider in ALIAS_PROVIDERS:
        st.caption(f"说明：你当前看到的是 **{provider} / {model}** 的前端展示选项；真正执行时会统一走 **{actual_provider} / {actual_model}**。")

    st.divider()
    cards = st.columns(3)
    cards[0].markdown(
        """
        <div class="rf-summary">
            <div style="font-size:13px;color:#5f6b7a;">中文简历优化</div>
            <div style="font-weight:700;margin:8px 0 6px;">推荐 Qwen</div>
            <div>更适合中文岗位、中文经历改写和关键词贴合。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cards[1].markdown(
        """
        <div class="rf-summary">
            <div style="font-size:13px;color:#5f6b7a;">表达质量优先</div>
            <div style="font-weight:700;margin:8px 0 6px;">推荐 GPT</div>
            <div>适合英文简历、双语润色和较强的语言表达场景。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cards[2].markdown(
        """
        <div class="rf-summary">
            <div style="font-size:13px;color:#5f6b7a;">本地演示 / 离线</div>
            <div style="font-weight:700;margin:8px 0 6px;">推荐 Ollama</div>
            <div>适合无公网或强调隐私的环境，但要注意本地服务稳定性。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.success("✅ 配置已保存，前往第四步生成。")
