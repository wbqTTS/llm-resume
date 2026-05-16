# wbq/schemas 模块说明

`wbq/schemas/` 存放结构化数据 schema。

主要文件：

- `job_details_schema.py`：岗位信息结构，包括岗位名称、职责、关键词、任职要求、公司信息等。
- `sections_schemas.py`：简历数据结构，包括个人信息、教育、工作经历、项目、技能等。

用途：

- 约束 LLM JSON 输出。
- 为测试和模板渲染提供稳定字段定义。
- 降低模型返回格式漂移导致的运行错误。
