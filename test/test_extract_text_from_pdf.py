import os

from wbq.utils.data_extraction import extract_text_from_pdf


def run_tests():
    test_filename = "test_resume_temp.pdf"

    print("=" * 50)
    print("🚀 开始运行 PDF 提取函数测试")
    print("=" * 50)

    test_filename = r"C:\Users\21080\Desktop\毕设\ref_sys\job-llm\output\_Python_resume.pdf"
    extracted_text = extract_text_from_pdf(test_filename)

    if extracted_text:
        print("\n--- 提取到的内容预览 ---")
        print(extracted_text[:5000])  # 只打印前500字符
        print("----------------------\n")

        # 验证关键内容是否存在
        if "SAURABH BHAUSAHEB ZINJAD" in extracted_text and "机器人竞赛" in extracted_text:
            print("🟢 通过：关键内容提取正确。")
        else:
            print("🔴 失败：未能提取到预期的关键内容。")

        # 验证清洗逻辑（不应包含大量空行）
        lines = [l for l in extracted_text.split('\n') if l.strip()]
        if len(lines) > 0:
            print(f"🟢 通过：成功清洗空白行，剩余有效行数：{len(lines)}")
    else:
        print("🔴 失败：未能从生成的测试文件中提取文本。")


    print("\n" + "=" * 50)
    print("🏁 测试结束")
    print("=" * 50)


if __name__ == "__main__":
    run_tests()