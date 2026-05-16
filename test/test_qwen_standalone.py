import os
import sys


# 颜色输出辅助函数 (让终端显示更好看)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def main():
    print("=" * 60)
    print(f"{Colors.YELLOW}通义千问 (Qwen) API Key 独立测试工具{Colors.END}")
    print("=" * 60)

    # 1. 获取 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        print_info("未在环境变量中找到 DASHSCOPE_API_KEY")
        api_key = input(f"{Colors.YELLOW}请在此粘贴您的 API Key (以 sk- 开头): {Colors.END}").strip()

    if not api_key.startswith("sk-"):
        print_error("API Key 格式似乎不正确 (通常以 'sk-' 开头)，但仍将尝试连接...")

    # 2. 尝试导入库
    try:
        import dashscope
        from dashscope import Generation, TextEmbedding
    except ImportError:
        print_error("未安装 'dashscope' 库！")
        print("请先运行命令: pip install dashscope")
        return

    # 设置 Key
    dashscope.api_key = api_key
    print_info(f"正在测试 Key: {api_key[:8]}...{api_key[-4:]}")
    print("-" * 60)

    # --- 测试 A: 文本生成 (LLM) ---
    print(f"\n{Colors.BLUE}[测试 1/2] 文本生成能力 (qwen-turbo){Colors.END}")
    try:
        response = Generation.call(
            model="qwen-turbo",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': 'Hello, please reply with only the word "Success" if you can hear me.'}
            ],
            result_format='message'
        )

        if response.status_code == 200:
            content = response.output.choices[0].message.content
            print_success(f"连接成功！模型回复: {content}")
        else:
            print_error(f"请求失败 -> 错误码: {response.code}")
            print_error(f"详细信息: {response.message}")
            print_info("提示: 请检查 Key 是否有效，或账户是否欠费/未实名认证。")
            return  # 生成失败就不测 Embedding 了

    except Exception as e:
        print_error(f"发生异常: {str(e)}")
        return

    # --- 测试 B: 向量嵌入 (Embedding) ---
    # 很多简历项目需要这个功能来计算匹配度
    print(f"\n{Colors.BLUE}[测试 2/2] 向量嵌入能力 (text-embedding-v3){Colors.END}")
    try:
        response = TextEmbedding.call(
            model="text-embedding-v3",
            input=["Test embedding connection.", "测试向量接口是否正常。"]
        )

        if response.status_code == 200:
            embeddings = response.output['embeddings']
            dim = len(embeddings[0]['embedding'])
            print_success(f"嵌入服务正常！返回向量维度: {dim}")
        else:
            print_error(f"嵌入请求失败 -> 错误码: {response.code}")
            print_error(f"详细信息: {response.message}")

    except Exception as e:
        print_error(f"发生异常: {str(e)}")

    print("-" * 60)
    print_success("所有测试完成！如果上面没有报错，您的 API Key 可以正常使用。")


if __name__ == "__main__":
    main()