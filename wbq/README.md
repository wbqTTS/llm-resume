# wbq 模块说明

`wbq/` 是项目的核心 Python 包，包含简历生成、岗位解析、模型调用、模板渲染、分析评估和 Streamlit UI 支撑代码。

主要文件：

- `core.py`：保留现有主流程类 `AutoApplyModel`，负责串联简历解析、JD 解析、章节优化、PDF 生成和求职信生成。
- `services.py`：服务层外壳，用于逐步拆分 `AutoApplyModel` 的职责。
- `variables.py`：模型提供商、模型名称和章节映射配置。
- `config.py`：预留配置入口。

主要子目录：

- `ui/`：Web UI 入口、Streamlit 启动逻辑、共享上下文、辅助函数和页面模块。
- `utils/`：通用工具、路径管理、数据库、LaTeX、分析器、LLM 封装等。
- `prompts/`：JD 抽取、简历优化、求职信生成相关 Prompt。
- `schemas/`：Pydantic 数据结构。
- `templates/`：LaTeX/Jinja2 简历模板。
- `demo_data/`：演示数据。
