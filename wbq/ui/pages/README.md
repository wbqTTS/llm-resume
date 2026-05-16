# wbq/ui/pages 模块说明

`wbq/ui/pages/` 存放 Streamlit 的页面级模块。

## 当前页面

- `user_center.py`
  - 用户登录/注册、状态概览、快速入口、历史记录加载与删除。

- `data_input.py`
  - 数据输入页入口。
  - 顶层负责组织 JD 输入、简历上传和手动表单；细节已下沉到 `../components/data_input_sections.py`。

- `model_config.py`
  - LLM 提供商、模型和 API Key 配置。

- `generation.py`
  - 生成前预览、优化强度、模板选择，以及简历/求职信生成流程。

- `results.py`
  - 结果页入口。
  - 顶层负责组织下载、分析和保存流程；细节已下沉到 `../components/results_sections.py`。

## 维护约定

- 页面模块主要负责页面编排和交互状态。
- 可复用页面片段优先放入 `wbq/ui/components/`。
- 修改页面后，至少运行一次 `py_compile` 和当前最小测试集。

