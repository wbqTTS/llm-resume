# 项目知识记录

## 项目概览

本项目是一个基于 Python、Streamlit 和大语言模型的智能简历生成与优化系统。它源自 ResumeFlow / Job-LLM 思路，并在当前代码中做了中文化、本地化和毕业设计展示增强。

系统主要目标是：根据用户简历或手动填写的个人信息，以及目标岗位 JD，自动生成更匹配岗位的简历、求职信，并提供匹配度分析、词云、雷达图、简历比对和历史记录管理。

## 技术栈

- 语言：Python
- Web 框架：Streamlit
- LLM 提供商：Qwen、GPT、Gemini、Ollama
- 简历渲染：Jinja2 + LaTeX + xelatex
- 数据库：SQLite，默认文件为 `resume_system.db`
- 文档解析：PyPDF2、PyMuPDF、pdf2docx 等
- 网页抓取：Playwright、BeautifulSoup、requests
- 分析能力：scikit-learn、NLTK、jieba、matplotlib、wordcloud

## 主要入口

- `web_app.py`：Streamlit Web 应用主入口，是当前最重要的用户界面文件。
- `main.py`：命令行入口，调用 `wbq.AutoApplyModel` 执行简历与求职信生成流程。
- `wbq/__init__.py`：导出公共 API `AutoApplyModel`。
- `wbq/core.py`：核心业务类，包含简历解析、JD 解析、简历生成、求职信生成等流程。

## 核心模块

- `wbq/core.py`
  - 定义 `AutoApplyModel`。
  - 根据 provider 创建 Qwen、GPT、Gemini 或 Ollama 模型实例。
  - 支持 PDF/JSON/URL 用户数据提取。
  - 支持岗位 JD 抽取。
  - 使用 RAG + CoT 分章节优化简历。
  - 调用 LaTeX 模板生成 PDF。

- `wbq/utils/llm_models.py`
  - 封装 Qwen、OpenAI GPT、Gemini、Ollama。
  - 统一提供 `get_response` 和部分 embedding 能力。
  - Qwen 默认使用 DashScope，环境变量名为 `DASHSCOPE_API_KEY`。

- `wbq/utils/latex_ops.py`
  - 将结构化简历 JSON 渲染为 LaTeX。
  - 使用 `xelatex` 编译 PDF。
  - 会复制 `resume.cls` 和 `styles/` 到输出目录。

- `wbq/utils/db_manager.py`
  - 管理用户和历史生成记录。
  - 主要表包括 `users` 和 `resume_history`。
  - 支持创建用户、保存记录、加载记录、删除记录。

- `wbq/utils/resume_analyzer.py`
  - 负责匹配度评分、关键词分析、雷达图、词云、改进建议、面试问题和 PDF 分析报告导出。

- `wbq/utils/app_support.py`
  - 当前新增的应用辅助模块。
  - 包含一键演示数据、优化强度配置、模板说明、生成阶段、友好错误提示、关键词覆盖和质量检查逻辑。

- `wbq/utils/metrics.py`
  - 提供 Jaccard、Overlap、Cosine 等文本相似度计算。

- `wbq/utils/retriever.py`
  - 将简历章节切块。
  - 根据 JD 检索相关经历片段。
  - 为 LLM 优化 prompt 提供 RAG 上下文。

## 模板与资源

- `wbq/templates/`
  - `resume_classic.tex.jinja`
  - `resume_creative.tex.jinja`
  - `resume_academic.tex.jinja`
  - `resume_minimal.tex.jinja`
  - `resume.cls`
  - `styles/`

- `assets/templates/`
  - 存放四种模板预览图。

- `wbq/templates/config/templates_config.json`
  - 描述模板名称、适用场景、标签和特性。

## 当前 Web 应用流程

Streamlit 页面按步骤组织：

1. 用户中心
   - 登录或注册简单用户名。
   - 显示工作台状态。
   - 支持载入演示数据。
   - 支持查看、加载、删除历史记录。

2. 数据输入
   - 输入 JD 文本或招聘链接。
   - 上传 PDF/JSON 简历。
   - 手动填写简历信息并导出 JSON。
   - 可以将当前表单直接保存为本次简历输入。

3. 模型配置
   - 选择 Qwen、GPT、Gemini、Ollama。
   - 选择模型。
   - 配置 API Key。
   - Qwen 支持从 `DASHSCOPE_API_KEY` 环境变量读取。

4. 生成简历
   - 选择优化强度：保守优化、标准优化、强匹配优化。
   - 自定义需要优化的章节。
   - 选择模板风格。
   - 生成前显示确认摘要。
   - 生成时显示阶段进度。

5. 结果分析
   - 下载简历 PDF 和求职信。
   - 预览简历。
   - 查看质量分析、关键词覆盖、雷达图、词云、改进建议、面试问题。
   - 对比原始版和优化版简历。
   - 保存分析结果到数据库。

## 数据流

典型流程如下：

1. 用户上传简历 PDF/JSON 或手动填写表单。
2. 系统将用户数据整理为结构化 JSON。
3. 用户输入 JD 文本或链接。
4. LLM 将 JD 抽取为结构化岗位信息。
5. 系统按简历章节切块，并根据 JD 检索相关片段。
6. LLM 对选中的章节进行定向优化。
7. 系统保存优化后的 JSON。
8. Jinja2 根据选中的模板渲染 LaTeX。
9. `xelatex` 编译生成 PDF。
10. 系统进行匹配度分析并展示结果。
11. 用户可保存记录到 SQLite。

## 重要目录

- `uploads/`：用户上传文件、演示 JSON、照片等。
- `output/`：生成的 JD、简历 JSON、PDF、求职信等。
- `test/`：测试脚本、样例数据和历史备份。
- `note/`：毕业设计相关笔记和原理说明。
- `resources/`：论文、演示视频、项目报告、依赖说明等资源。
- `venv/`：项目虚拟环境，但当前环境中该虚拟环境指向的 Python 路径不可用。

## 运行与依赖注意事项

- Python 要求：`>=3.11.6,<3.13`。
- 当前机器曾发现 `python` 不在 PATH，项目 `venv` 指向的 Python 也不存在。
- 建议安装 Python 3.11 后重建虚拟环境。
- PDF 生成依赖 `xelatex`，需要安装 TeX Live 或 MiKTeX。
- URL 抓取依赖 Playwright，首次使用需运行 `playwright install`。
- 现场演示时建议使用“粘贴 JD 文本”，比 URL 抓取更稳定。
- Qwen 推荐配置环境变量 `DASHSCOPE_API_KEY`。

## 已知风险

- `web_app.py` 已完成薄入口化；页面逻辑已拆到 `wbq/ui/pages/`。
- 生成 PDF 对本地 LaTeX 环境依赖较强。
- LLM 输出 JSON 仍可能不稳定，虽然已有解析兜底。
- Playwright 抓取招聘网站时可能受登录、反爬或网络影响。
- 代码中仍有部分历史注释和日志风格不统一。
- `pyproject.toml` 包名仍为 `zlm`，但当前代码包名主要为 `wbq`，需要注意一致性。

## 后续建议

- 继续从 `wbq/ui/pages/` 中抽取更细粒度的可复用组件，例如历史记录面板、手动表单区、分析面板和下载操作区。
- 将 `AutoApplyModel` 拆分为 JD 解析、简历解析、章节优化、PDF 渲染、求职信生成等服务。
- 增加完整 pytest 测试并修复本机 Python 环境。
- 增加模型输出 schema 校验和重试机制。
- 增强模板字段缺失提示。
- 进一步整理 README、配置文件和依赖安装脚本。

## 本轮新增模块

- `wbq/utils/ui_components.py`：封装生成进度面板、Demo 数据载入、生成前预览等 Streamlit 组件。
- `wbq/utils/validation.py`：集中校验 JD、简历和章节优化的模型输出；当章节优化失败或格式异常时回退到原始数据。
- `wbq/utils/path_manager.py`：集中处理上传目录、输出目录、模板目录、用户 ID 和时间戳路径。
- `wbq/services.py`：为拆分 `AutoApplyModel` 提供 JD 抽取、简历解析、简历生成、求职信生成服务外壳。
- `test/test_app_support.py`：当前最小测试集，覆盖 JSON、PDF 文本提取、schema、模板渲染、数据库兼容、路径命名和友好错误提示。
# 当前结构说明

- 根目录 `web_app.py` 是薄入口，运行方式仍是 `streamlit run web_app.py`。
- Streamlit 启动、Session State、侧边栏导航和页面分发位于 `wbq/ui/app.py`。
- 页面代码已拆到 `wbq/ui/pages/`：用户中心、数据输入、模型配置、生成简历、结果分析。
- `wbq/ui/legacy_streamlit_app.py` 仅保留兼容包装，不再承载主页面代码。
- Web 辅助函数位于 `wbq/ui/web_helpers.py`。
- 主要目录均已补充 `README.md`，用于说明当前模块职责。

## 最新 UI 架构补充

- `web_app.py`：仅作为 Streamlit 薄入口。
- `wbq/ui/app.py`：负责应用启动、Session State、导航和页面分发。
- `wbq/ui/pages/`：负责页面级编排。
- `wbq/ui/components/`：负责页面内部的细粒度可复用渲染逻辑。
  - `data_input_sections.py`：拆分数据输入页的 Demo、JD、上传、手动表单、导出与完整性检查。
  - `results_sections.py`：拆分结果页的下载区、分析区、对比区、报告导出与数据库保存。

## 目前的结构结论

- `web_app.py` 不再是两千多行巨型页面脚本。
- 页面层和组件层已经形成清晰分层，后续维护可以直接定位到对应目录。
- 当前更值得继续优化的方向，不再是粗粒度拆页，而是：
  1. 为 `user_center.py`、`generation.py` 继续抽取更细的组件；
  2. 给 UI 层增加交互回归测试；
  3. 逐步减少 `app_context.py` 的星号导入依赖。

## 最新补充（2026-05-11）

- `wbq/ui/pages/user_center.py` 已重新整理为干净的 UTF-8 页面文件，避免历史乱码继续扩散到用户中心。
- 历史记录恢复时，会同步恢复：
  - `temp_user_data`
  - `form_data`
  - `manual_resume_form`
  - `temp_job_details`
  - `resume_source`
  - `jd_url`
  - `jd_text`
  - `generated_result`
  - `llm_config`
- 为了让历史记录恢复后的结果分析可继续计算，数据库记录里已经补充保存：
  - `source_data_json`
  - `job_details_json`
- 用户中心“历史概览”当前包含三张图：
  - 模板风格分布
  - 模型配置分布
  - 生成时间分布
- 其中“生成时间分布”已从不稳定的单点线图改为更稳的柱状图，避免只有一天或一条记录时看起来像空白。
- 历史概览三张图当前采用三种不同配色，便于答辩演示时快速区分：
  - 模板风格分布：蓝色
  - 模型配置分布：青绿色
  - 生成时间分布：橙色
- `wbq/ui/app.py` 的侧边栏已做低风险样式升级：
  - 移除“流程指引”整块说明
  - 保留原有导航逻辑不变
  - 通过 CSS 增加渐变背景、圆角导航项和更统一的视觉风格
- 当前策略仍然是“优先稳定，再做美化”，因此侧边栏只做轻量样式层优化，不改动导航状态机和页面分发逻辑。
- 侧边导航的文案已进一步简化：
  - 去掉步骤序号，仅保留图标和名称
  - 通过 CSS 隐藏 radio 默认圆圈，减少视觉噪音
- `wbq/ui/pages/generation.py` 中“前往结果分析”跳转已改为引用 `wbq/ui/constants.py` 里的 `STEP_RESULTS` 常量，避免导航文案调整后出现硬编码失效。
- 关于“AI 优化阶段显示逐字段实时优化过程”：
  - 后续已通过隔离原型验证，确认“主线程章节回调”方案可行。
  - 当前正式实现没有让并发子线程直接操作 Streamlit，而是在 `core.py` 中消费 `as_completed(...)` 结果时，额外触发可选的 `section_callback(section_name, data, analysis)`。
  - 生成页通过这个回调接收每个章节的优化结果，并在 AI 优化阶段展示“章节级优化详情”，包括：
    - 已保留原始内容
    - 优化完成
    - 优化回退
    - 匹配关键词
    - 优化策略
    - 差距分析
  - 这次实现保留了原有线程池结构，不把 UI 更新放进子线程，因此风险相对可控。
  - 隔离验证文件位于：
    - `test/prototype_ai_progress/README.md`
    - `test/prototype_ai_progress/progress_callback_prototype.py`
    - `test/test_ai_progress_prototype.py`
  - 结论：这一功能可以实现，且已经以低破坏方式接入当前版本。

- 2026-05-11 ���䣺AI �Ż���������Ѿ�����Ϊ����չʾ�������½ڣ��ٰ� section_callback ʵʱˢ��״̬�����û����� AI �Ż��׶κ󣬿����ȿ������д������½ڣ����ÿ���½ڻ���������Ϊ���ȴ� AI ���� / �Ѱ����ñ��� / �Ż���� / �Ż����ˡ���

- 2026-05-11 ���䣺resume_history �����ɼ�¼�� created_at �Ѹ�Ϊ��Ӧ�ò���ʽд�뱱��ʱ�䣨Asia/Shanghai���ַ����������ݲ���д������ԭ�������������Ը��Ǹ���Ϊ��

- 2026-05-11 ���䣺AI ���������Ѳ��õͷ��յġ��ֽ׶η��� + �ֶγ��֡��������û��ύ�ش��ҳ����ȼ�ʱ��ʾ�������Ķ��ش� / ���ڽ�ϸ�λҪ����� / ���������������Ƚ׶���ʾ����ģ�ͷ��������ı����ٽ��ظ������������Ƭ����γ��֣��Ը��Ƶȴ���У�ͬʱ���޸ĵײ� LLM ������ʽ���ó���

- 2026-05-14 ���䣺ģ������ҳ������ǰ����չʾ�⳧�̣��� DeepSeek��������Kimi�����ף�����Щ�������̽�����ǰ��չʾ��ѡ��ḻ��������ʵ������ʱͳһӳ�䵽 Qwen / qwen-plus �ĺ�˵�����·��ԭ�� Qwen��GPT��Gemini��Ollama ����ʵ·�ɱ��ֲ��䡣��ʷ��¼�ָ�ʱҲ���Զ���չʾ����ӳ���ʵ��ִ�����á�
