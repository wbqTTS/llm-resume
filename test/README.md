# test 目录说明

`test/` 存放项目测试、实验脚本和历史调试样例。

当前推荐运行的最小回归测试：

```powershell
python -m unittest discover -s test -p "test_app_support.py" -v
```

`test_app_support.py` 覆盖：

- JSON 读写。
- PDF 文本提取。
- JD schema 和简历 schema。
- 文件命名和路径管理。
- LLM 输出校验和章节失败兜底。
- 四套模板 `.tex` 渲染。
- 旧数据库字段迁移。
- 友好错误提示。

建议：

- 历史实验脚本可后续迁移到 `test/manual/` 或 `scripts/`，避免和自动化测试混在一起。
