# 智简：基于大语言模型的智能简历生成与优化系统

[![Demo Page](https://img.shields.io/badge/Project-Demo-FF4B4B?logo=streamlit)](https://resumeflow.streamlit.app/)
[![ACM Digital Library](https://img.shields.io/badge/ACM-0085CA?logo=acm&logoColor=fff&style=flat)](https://dl.acm.org/doi/10.1145/3626772.3657680)
[![arXiv Paper](https://img.shields.io/badge/arXiv-Paper-B31B1B?logo=arxiv)](https://arxiv.org/abs/2402.06221)
[![License: MIT](https://img.shields.io/badge/License-MIT-success.svg)](LICENSE)

本项目是一个面向中文求职场景的智能简历生成与优化系统。系统可以读取用户简历或手动填写的信息，结合目标岗位 JD，通过大语言模型生成定制化简历、求职信，并提供匹配度分析、关键词覆盖、词云、雷达图、简历比对和历史记录管理。

项目基于 ResumeFlow / Job-LLM 思路进行扩展，当前版本重点服务毕业设计展示和本地可用性。

## 功能特性

- 多步骤 Streamlit Web 界面：用户中心、数据输入、模型配置、简历生成、结果分析。
- 支持上传 PDF/JSON 简历，也支持手动填写并导出 JSON。
- 支持粘贴 JD 文本或通过招聘链接抓取岗位描述。
- 支持 Qwen、GPT、Gemini、Ollama 等模型提供商。
- 支持保守优化、标准优化、强匹配优化三种优化强度。
- 基于 RAG + CoT 按章节优化简历内容。
- 支持四种 LaTeX 简历模板：经典商务、创意设计、学术严谨、极简现代。
- 支持生成简历 PDF、求职信、分析报告和简历比对报告。
- 支持 SQLite 历史记录保存、加载和删除。
- 内置一键演示数据，便于答辩和本地演示。

## 项目结构

```text
job-llm/
├── web_app.py                    # Streamlit Web 应用入口
├── main.py                       # 命令行入口
├── pyproject.toml                # Poetry 依赖配置
├── resources/requirements.txt    # pip 依赖列表
├── resume_system.db              # SQLite 数据库
├── wbq/
│   ├── core.py                   # AutoApplyModel 核心流程
│   ├── variables.py              # 模型和章节配置
│   ├── prompts/                  # JD、简历和章节优化 Prompt
│   ├── schemas/                  # Pydantic 数据结构
│   ├── templates/                # LaTeX / Jinja2 简历模板
│   ├── demo_data/                # 演示数据
│   └── utils/
│       ├── app_support.py        # Web 辅助逻辑和演示数据
│       ├── db_manager.py         # SQLite 历史记录
│       ├── latex_ops.py          # LaTeX 渲染和 PDF 编译
│       ├── llm_models.py         # Qwen/GPT/Gemini/Ollama 封装
│       ├── metrics.py            # 相似度计算
│       ├── resume_analyzer.py    # 简历分析与报告
│       └── retriever.py          # RAG 检索
├── assets/templates/             # 模板预览图
├── uploads/                      # 上传文件和演示文件
├── output/                       # 生成结果
├── test/                         # 测试和样例
└── note/                         # 毕设笔记和原理说明
```

## 环境要求

- Windows、Linux 或 macOS。
- Python：`>=3.11.6,<3.13`。
- 推荐使用 Python 3.11。
- 至少配置一种 LLM：
  - Qwen：配置 `DASHSCOPE_API_KEY`。
  - GPT：配置 `OPENAI_API_KEY`。
  - Gemini：配置 `GEMINI_API_KEY`。
  - Ollama：本地启动 Ollama 服务并拉取模型。
- PDF 生成需要安装 `xelatex`。
- URL 抓取需要 Playwright。

## 安装步骤

### 1. 克隆项目

```powershell
git clone https://github.com/Ztrimus/job-llm.git
cd job-llm
```

如果是在当前本地项目中使用，直接进入项目根目录：

```powershell
cd C:\Users\21080\Desktop\毕设\ref_sys\job-llm
```

### 2. 创建虚拟环境

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

如果当前机器找不到 `python`，请先安装 Python 3.11，并确保加入 PATH。

### 3. 安装 Python 依赖

推荐使用 requirements：

```powershell
pip install -r resources\requirements.txt
```

也可以使用 Poetry：

```powershell
pip install poetry
poetry install
```

### 4. 安装 Playwright 浏览器依赖

```powershell
playwright install
```

### 5. 安装 LaTeX

PDF 生成依赖 `xelatex`。

Windows 推荐安装 MiKTeX 或 TeX Live。安装后检查：

```powershell
xelatex --version
```

Linux 可参考：

```bash
sudo apt-get update
sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-fonts-extra
```

macOS 可参考：

```bash
brew install basictex
sudo tlmgr install enumitem fontawesome
```

## 配置模型

### Qwen

推荐配置环境变量：

```powershell
$env:DASHSCOPE_API_KEY="你的 DashScope API Key"
```

或在 Web 界面的“模型配置”步骤中填写 API Key。

### OpenAI GPT

```powershell
$env:OPENAI_API_KEY="你的 OpenAI API Key"
```

### Gemini

```powershell
$env:GEMINI_API_KEY="你的 Gemini API Key"
```

### Ollama

安装并启动 Ollama 后拉取模型：

```powershell
ollama pull llama3.1
ollama pull bge-m3
```

## 启动 Web 应用

```powershell
streamlit run web_app.py
```

打开 Streamlit 地址后，按照页面步骤操作：

1. 在“用户中心”输入用户名。
2. 在“数据输入”中粘贴 JD 或载入演示数据。
3. 在“模型配置”中选择模型和 API Key。
4. 在“生成简历”中选择优化强度和模板。
5. 在“结果分析”中下载结果并查看分析。

## 一键演示流程

为了答辩和本地测试，系统内置了稳定的中文演示数据。

推荐演示步骤：

1. 启动应用：`streamlit run web_app.py`。
2. 进入“用户中心”，输入任意用户名。
3. 点击“载入演示数据”，或进入“数据输入”点击“一键载入演示数据”。
4. 进入“模型配置”，选择 Qwen 或 Ollama。
5. 进入“生成简历”，选择“标准优化”和任意模板。
6. 点击“生成简历”。
7. 在“结果分析”查看 PDF、关键词覆盖、质量检查、雷达图、词云和简历比对。

现场演示时建议优先使用 JD 文本输入，避免招聘网站登录、反爬或网络波动影响抓取。

## 命令行使用

也可以通过 `main.py` 调用核心流程：

```powershell
python main.py ^
  --url "JOB_POSTING_URL" ^
  --master_data "USER_RESUME_OR_JSON_PATH" ^
  --api_key "YOUR_LLM_PROVIDER_API_KEY" ^
  --downloads_dir "OUTPUT_DIRECTORY" ^
  --provider "Qwen" ^
  --model "qwen-max"
```

参数说明：

- `--url`：岗位链接。
- `--master_data`：用户简历 PDF 或 JSON 路径。
- `--api_key`：模型 API Key，也可以传 `os` 从环境变量读取。
- `--downloads_dir`：输出目录。
- `--provider`：模型提供商，例如 `Qwen`、`GPT`、`Gemini`、`Ollama`。
- `--model`：模型名称。

## 测试

新增的基础测试位于：

```text
test/test_app_support.py
```

运行：

```powershell
python -m unittest discover -s test -p "test_app_support.py" -v
```

## 最新前端结构

- `web_app.py`
  - 现在是 Streamlit 薄入口。

- `wbq/ui/app.py`
  - 负责页面配置、Session State 初始化、侧边栏导航和页面分发。

- `wbq/ui/pages/`
  - 页面级模块目录。
  - 当前包括用户中心、数据输入、模型配置、生成简历、结果分析五个页面入口。

- `wbq/ui/components/`
  - 页面内部的组件级目录。
  - 当前已经拆出：
    - `data_input_sections.py`
    - `results_sections.py`

这意味着当前 UI 结构已经从“单文件大脚本”演进为“入口层 -> 页面层 -> 组件层”。

如果当前机器无法运行 Python，请先修复 Python 环境：

```powershell
winget install -e --id Python.Python.3.11
```

然后重建虚拟环境。

## 常见问题

### 1. `python` 不在 PATH

安装 Python 3.11，并勾选 “Add python.exe to PATH”。安装后重新打开 PowerShell：

```powershell
python --version
where.exe python
```

### 2. 项目 `venv` 无法启动

当前虚拟环境可能指向旧 Python 路径。建议删除并重建：

```powershell
Remove-Item -Recurse -Force .\venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r resources\requirements.txt
```

### 3. PDF 生成失败

请检查：

- 是否安装 `xelatex`。
- LaTeX 是否加入 PATH。
- 模板字段是否完整。
- 简历内容中是否包含特殊字符。

### 4. JD 链接抓取失败

优先改用“粘贴职位描述文本”。部分招聘网站需要登录或有反爬策略，URL 抓取不一定稳定。

### 5. 模型输出 JSON 解析失败

可以尝试：

- 降低优化强度。
- 换用更强的模型。
- 缩短 JD 或简历内容。
- 重新生成。

## 当前已知问题

- `web_app.py` 已完成薄入口化；页面逻辑现位于 `wbq/ui/pages/`，后续重点应转向继续抽取页面内部的复用组件。
- `pyproject.toml` 中包名仍为 `zlm`，但当前代码主要使用 `wbq` 包名。
- PDF 生成强依赖本地 LaTeX 环境。
- Playwright 抓取外部网站不如直接粘贴 JD 稳定。
- 部分历史测试文件和笔记仍保留在仓库中，后续可进一步整理。

## 参考资料

- 原论文：[ResumeFlow: An LLM-facilitated Pipeline for Personalized Resume Generation and Refinement](https://arxiv.org/abs/2402.06221)
- ACM 页面：[SIGIR 2024 Paper](https://dl.acm.org/doi/10.1145/3626772.3657680)
- 原项目：[Ztrimus/job-llm](https://github.com/Ztrimus/job-llm)
- Prompt Engineering 指南：[OpenAI Docs](https://platform.openai.com/docs/guides/prompt-engineering)
- Overleaf 简历模板参考：[Jake's Resume](https://www.overleaf.com/latex/templates/jakes-resume-anonymous/cstpnrbkhndn)

## 引用

如果你在论文或项目中参考 ResumeFlow，可使用以下引用：

```bibtex
@inproceedings{10.1145/3626772.3657680,
author = {Zinjad, Saurabh Bhausaheb and Bhattacharjee, Amrita and Bhilegaonkar, Amey and Liu, Huan},
title = {ResumeFlow: An LLM-facilitated Pipeline for Personalized Resume Generation and Refinement},
series = {SIGIR '24},
booktitle = {Proceedings of the 47th International ACM SIGIR Conference on Research and Development in Information Retrieval},
publisher = {Association for Computing Machinery},
doi = {10.1145/3626772.3657680},
url = {https://doi.org/10.1145/3626772.3657680},
year = {2024},
isbn = {9798400704314},
location = {Washington DC, USA},
address = {New York, NY, USA},
}
```

```bibtex
@misc{zinjad2024resumeflow,
      title={ResumeFlow: An LLM-facilitated Pipeline for Personalized Resume Generation and Refinement},
      author={Saurabh Bhausaheb Zinjad and Amrita Bhattacharjee and Amey Bhilegaonkar and Huan Liu},
      year={2024},
      eprint={2402.06221},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```

## 许可证

本项目基于 MIT License。
## 本地增强模块

- `wbq/utils/app_support.py`：演示数据、错误提示、关键词覆盖、质量检查、指标解释和优化强度配置。
- `wbq/utils/ui_components.py`：生成进度、Demo 数据载入、生成前确认预览等 Web 组件。
- `wbq/utils/validation.py`：JD、简历、章节优化结果的结构化校验与失败兜底。
- `wbq/utils/path_manager.py`：集中管理 `uploads/`、`output/`、模板资源、用户 ID 和时间戳路径。
- `wbq/services.py`：为后续拆分 `AutoApplyModel` 提供 JD 抽取、简历解析、简历生成、求职信生成服务外壳。

## 测试覆盖

当前最小回归测试位于 `test/test_app_support.py`，覆盖 JSON 读写、PDF 文本提取、JD schema、简历 schema、文件命名、路径管理、LLM 输出校验、章节失败兜底、四套模板 `.tex` 渲染、旧数据库兼容迁移和友好错误提示。

运行方式：

```powershell
python -m unittest discover -s test -p "test_app_support.py" -v
```
# 当前结构说明

- 根目录 `web_app.py` 已改为 Streamlit 薄入口，仅负责导入并启动 Web 应用。
- Streamlit 启动、Session State、侧边栏导航和页面分发位于 `wbq/ui/app.py`。
- 页面代码已拆到 `wbq/ui/pages/`：用户中心、数据输入、模型配置、生成简历、结果分析。
- `wbq/ui/legacy_streamlit_app.py` 仅保留兼容包装，不再承载主页面代码。
- Web 通用辅助函数已放入 `wbq/ui/web_helpers.py`。
- 每个主要目录已补充 `README.md`，用于说明模块用途和维护建议。
