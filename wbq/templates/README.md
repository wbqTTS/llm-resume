# wbq/templates 模块说明

`wbq/templates/` 存放简历 LaTeX 模板和样式文件。

主要文件：

- `resume_classic.tex.jinja`：经典商务模板。
- `resume_creative.tex.jinja`：创意设计模板。
- `resume_academic.tex.jinja`：学术严谨模板。
- `resume_minimal.tex.jinja`：极简现代模板。
- `resume.cls`：通用 LaTeX class。
- `styles/`：模板样式拆分文件。
- `config/templates_config.json`：模板展示配置。

维护建议：

- 新增模板时同步添加预览图、配置项和模板渲染测试。
- 模板字段应与 `wbq/schemas/sections_schemas.py` 保持一致。
