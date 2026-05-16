# wbq/utils 模块说明

`wbq/utils/` 存放项目通用工具和基础设施代码。

主要文件：

- `app_support.py`：演示数据、优化强度、友好错误提示、关键词覆盖、质量检查和指标解释。
- `ui_components.py`：Streamlit 可复用组件，例如生成进度面板、Demo 数据载入、生成前预览。
- `validation.py`：LLM 输出校验、简历数据校验、章节优化兜底。
- `path_manager.py`：统一管理上传、输出、模板、用户 ID、时间戳等路径。
- `db_manager.py`：SQLite 用户和历史记录管理，包含旧表字段迁移。
- `latex_ops.py`：Jinja2 模板渲染和 xelatex PDF 生成。
- `llm_models.py`：Qwen、GPT、Gemini、Ollama 模型封装。
- `resume_analyzer.py`：匹配度、雷达图、词云、建议、面试问题和报告导出。
- `metrics.py`：文本相似度指标。
- `retriever.py`：RAG 检索辅助。
- `data_extraction.py`、`scraper_worker.py`：PDF 文本提取和网页抓取。

约定：

- 可复用的纯逻辑优先放在这里。
- 与页面展示强相关的组件应优先放入 `wbq/ui/` 或 `ui_components.py`。
