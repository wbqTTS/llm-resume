import requests
import json


def test_ollama_connection():
    # Ollama 默认本地服务地址
    url = "http://localhost:11434/api/generate"

    # 请求数据配置
    # 注意：model 必须与你本地安装的完全一致
    data = {
        "model": "qwen2.5:1.5b",
        "prompt": "这个故事有多少个字",
        "stream": False  # 设置为 False 以获取完整的单次响应，方便测试
    }

    print(f"🚀 正在尝试连接 Ollama 并调用模型: {data['model']} ...")

    try:
        # 发送 POST 请求
        response = requests.post(url, json=data, timeout=60)

        # 检查 HTTP 状态码
        if response.status_code == 200:
            print("✅ 连接成功！API 返回数据如下：\n" + "-" * 30)

            # 解析 JSON 数据
            result = response.json()
            # 提取生成的文本内容
            generated_text = result.get('response', '')

            print(generated_text)
            print("-" * 30)
            print("✅ 测试通过：模型运行正常！")

        else:
            print(f"❌ 请求失败。状态码: {response.status_code}")
            print(f"错误详情: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 连接错误：无法连接到 Ollama 服务。")
        print("💡 请检查：1. Ollama 软件是否已启动？ 2. 服务地址是否正确 (默认 http://localhost:11434)")
    except requests.exceptions.Timeout:
        print("❌ 请求超时：模型响应时间过长。")
        print("💡 提示：如果是首次运行，模型可能需要时间加载到显存中。")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


if __name__ == "__main__":
    test_ollama_connection()