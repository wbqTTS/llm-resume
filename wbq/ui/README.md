# wbq/ui 模块说明

`wbq/ui/` 存放 Streamlit 前端相关代码。根目录 `web_app.py` 现在只是薄入口，真正的 UI 启动逻辑位于 `wbq/ui/app.py`。

## 当前结构

- `app.py`
  - Streamlit 页面配置、Session State 初始化、侧边栏导航和页面分发。

- `app_context.py`
  - 页面共享依赖和全局对象，例如 `st`、数据库实例、常用工具函数。

- `web_helpers.py`
  - Web 层通用辅助函数，例如 PDF 转 Word、Overleaf 打包、简历差异对比。

- `legacy_streamlit_app.py`
  - 兼容旧路径的轻量包装，不再承载主页面代码。

- `pages/`
  - 页面级模块目录。
  - 当前包括用户中心、数据输入、模型配置、生成简历、结果分析五个页面。

- `components/`
  - 页面内部的组件级模块目录。
  - 当前已拆出数据输入页和结果分析页的细粒度渲染逻辑。

## 分层约定

- 入口层：`web_app.py`
- 页面层：`wbq/ui/pages/`
- 组件层：`wbq/ui/components/`
- 核心逻辑层：`wbq/core.py`、`wbq/services.py`、`wbq/utils/`

## 维护建议

- 页面文件尽量只保留页面流程编排。
- 可复用 UI 逻辑优先下沉到 `components/`。
- 纯业务逻辑不要继续堆到 Streamlit 页面里。

