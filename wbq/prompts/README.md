# wbq/prompts 模块说明

`wbq/prompts/` 存放大语言模型使用的 Prompt 模板。

主要文件：

- `resume_prompt.py`：简历解析、JD 抽取、求职信生成和简历写作 persona。
- `sections_prompt.py`：教育经历、工作经历、项目经历、技能、社会实践、学术经历等章节优化 Prompt。

维护建议：

- Prompt 修改后需要尽量同步更新 schema 或测试样例。
- 输出 JSON 的 Prompt 应明确字段名、格式约束和失败时的返回要求。
