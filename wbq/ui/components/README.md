# wbq/ui/components 模块说明

`wbq/ui/components/` 存放 Streamlit 页面内部可复用的组件级逻辑。

## 当前文件

- `data_input_sections.py`
  - 拆分数据输入页内部区域。
  - 负责 Demo 载入、JD 输入、简历上传、手动表单、JSON 导出和完整性检查。

- `results_sections.py`
  - 拆分结果分析页内部区域。
  - 负责结果配置展示、下载区、分析器初始化、质量分析、词云、雷达图、对比分析、报告导出和数据库保存。

## 约定

- `pages/` 负责页面级编排和导航。
- `components/` 负责单页内部的细粒度渲染逻辑。
- 核心业务逻辑仍然放在 `wbq/core.py`、`wbq/services.py` 和 `wbq/utils/` 中。

