from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

# ==========================================
# 🔧 配置区域
# ==========================================
TARGET_URL = "https://jobs.51job.com/fuzhou/165579546.html?t=0&timestamp__1258=YqfxnDuD9Dg0qDKDsTiQGkUdc1ChQeqba4D"
# ==========================================

def scrape_job_url(url):
    print(f"🚀 开始尝试抓取: {url}")

    final_text = ""

    with sync_playwright() as p:
        # 建议调试时设为 False，可以看到浏览器是否真的加载出了文字
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
            "--disable-gpu", "--no-first-run", "--no-zygote"
        ])

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )

        page = context.new_page()

        try:
            print("⏳ 正在加载页面...")
            # 等待网络空闲，给足时间让 JS 执行
            page.goto(url, wait_until="networkidle", timeout=40000)

            # 强制等待，确保动态渲染的内容（如职位描述）已经插入 DOM
            print("💤 等待动态内容完全渲染 (5 秒)...")
            time.sleep(5)

            # 获取渲染后的完整 HTML
            html_content = page.content()

            # 简单检查是否被拦截
            if "验证您的身份" in html_content or "slider" in html_content:
                print("⚠️ 检测到可能的验证码拦截，但将继续尝试提取...")

            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(html_content, 'html.parser')

            # ==============================
            # 🚜 修改点：暴力全量提取逻辑
            # ==============================
            print("🚜 启动暴力全量提取模式：跳过结构匹配，直接抓取 Body 所有文本...")

            # 1. 仅移除纯代码和样式标签，保留所有其他 HTML 结构
            # 注意：这里不再移除 header/footer/nav，因为我们要“全部爬取”，稍后通过文本过滤清洗
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()

            # 2. 直接定位 body 标签
            body = soup.find('body')

            raw_text = ""
            if body:
                # 3. 获取 body 内所有文本，使用 separator='\n' 保持换行结构
                raw_text = body.get_text(separator='\n', strip=True)
                print(f"✅ 原始文本提取完成，长度：{len(raw_text)} 字符")
            else:
                # 极端情况：连 body 都没有，直接抓整个 soup
                raw_text = soup.get_text(separator='\n', strip=True)
                print("⚠️ 未找到 body 标签，已回退至全局提取")

            # 4. 精细化文本清洗 (这是去除噪音的关键)
            lines = raw_text.split('\n')
            cleaned_lines = []

            # 定义噪音关键词 (用于过滤菜单、版权、无关链接等)
            noise_keywords = [
                "登录", "注册", "扫一扫", "分享", "举报", "版权", "ICP", "京公网安备",
                "APP下载", "在线客服", "返回顶部", "搜索职位", "首页", "收藏本站",
                "Copyright", "All rights reserved", "京ICP备", "http://"
            ]

            for line in lines:
                line = line.strip()

                # 规则 1: 空行跳过
                if not line:
                    continue

                # 规则 2: 过短的行跳过 (通常是图标、单个字母或乱码)，但保留可能存在的短标题(>2字)
                if len(line) < 2:
                    continue

                # 规则 3: 包含噪音关键词的行跳过
                if any(k in line for k in noise_keywords):
                    continue

                # 规则 4: (可选) 如果一行里全是特殊符号或网址，也可以跳过
                # 这里暂时保留，让大模型后续去处理

                cleaned_lines.append(line)

            final_text = "\n".join(cleaned_lines)

            if not final_text:
                print("❌ 经过清洗后内容为空。可能是页面完全由图片组成或反爬极其严格。")
            else:
                print(f"✨ 清洗后有效内容：{len(final_text)} 字符，共 {len(cleaned_lines)} 行。")

        except Exception as e:
            print(f"💥 发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

    return final_text


if __name__ == "__main__":
    result = scrape_job_url(TARGET_URL)

    print("\n" + "=" * 50)
    print("📄 提取结果预览 (前 2000 字):")
    print("=" * 50)
    if result:
        print(result[:2000])
        if len(result) > 2000:
            print("\n... (内容过长已截断，请查看 extracted_job.txt)")
    else:
        print("无有效内容提取。")

    if result:
        output_file = "extracted_job.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n💾 完整内容已保存至 {output_file}")
        print(
            "💡 提示：如果文件内容依然杂乱，可能是因为该网站使用了字体加密或Canvas渲染，这种情况需要更高级的OCR或字体映射技术。")