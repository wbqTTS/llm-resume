# scraper_worker.py
# 独立运行的暴力爬虫脚本，供 subprocess 调用
import os
import sys
import io

# ===== 新增：强制 UTF-8 输出（解决 Windows GBK 编码问题）=====
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
# ========================================================

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time


def scrape_job_url(url):
    """
    暴力抓取逻辑：
    1. 启动浏览器渲染页面
    2. 移除 script/style
    3. 提取 Body 所有文本
    4. 进行基础的噪音关键词过滤 (保留核心业务逻辑)
    5. 返回清洗后的文本
    """
    print(f"🚀 [Worker] 开始尝试抓取: {url}", file=sys.stderr)  # 日志打到 stderr，避免污染 stdout 数据

    final_text = ""

    try:
        with sync_playwright() as p:
            # 启动浏览器 (headless=True 适合服务器/后台运行)
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                "--disable-gpu", "--no-first-run", "--no-zygote",
                "--disable-blink-features=AutomationControlled"  # 隐藏自动化特征
            ])

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )

            page = context.new_page()

            try:
                print("⏳ [Worker] 正在加载页面...", file=sys.stderr)
                # 等待网络空闲，给足时间让 JS 执行
                page.goto(url, wait_until="networkidle", timeout=40000)

                # 强制等待，确保动态渲染的内容（如职位描述）已经插入 DOM
                print("💤 [Worker] 等待动态内容完全渲染 (5 秒)...", file=sys.stderr)
                time.sleep(5)

                # 获取渲染后的完整 HTML
                html_content = page.content()

                # 简单检查是否被拦截
                if "验证您的身份" in html_content or "slider" in html_content or "403" in html_content:
                    print("⚠️ [Worker] 检测到可能的验证码拦截，但将继续尝试提取...", file=sys.stderr)

                # 使用 BeautifulSoup 解析
                soup = BeautifulSoup(html_content, 'html.parser')

                # ==============================
                # 🚜 暴力全量提取逻辑
                # ==============================
                print("🚜 [Worker] 启动暴力全量提取模式...", file=sys.stderr)

                # 1. 仅移除纯代码和样式标签
                for tag in soup(['script', 'style', 'noscript']):
                    tag.decompose()

                # 2. 直接定位 body 标签
                body = soup.find('body')

                raw_text = ""
                if body:
                    raw_text = body.get_text(separator='\n', strip=True)
                    print(f"✅ [Worker] 原始文本提取完成，长度：{len(raw_text)} 字符", file=sys.stderr)
                else:
                    raw_text = soup.get_text(separator='\n', strip=True)
                    print("⚠️ [Worker] 未找到 body 标签，已回退至全局提取", file=sys.stderr)

                # 3. 精细化文本清洗 (去除噪音)
                lines = raw_text.split('\n')
                cleaned_lines = []

                # 定义噪音关键词
                noise_keywords = [
                    "登录", "注册", "扫一扫", "分享", "举报", "版权", "ICP", "京公网安备",
                    "APP下载", "在线客服", "返回顶部", "搜索职位", "首页", "收藏本站",
                    "Copyright", "All rights reserved", "京ICP备", "http://", "https://",
                    " Cookies ", "隐私政策", "用户协议", "广告", "推广", "相关推荐",
                    "猜你想看", "热门职位", "职场资讯", "立即投递", "收藏职位", "该公司其他职位",
                    "相似职位",
                    "发布时间", "招聘人数",
                    "五险一金", "带薪年假", "年底双薪", "交通补助", "餐补", "房补", "话补",
                    "节日福利", "生日福利", "团建", "体检", "培训", "晋升", "面试", "简历",
                    "HR", "猎头", "中介", "客服", "电话", "微信", "QQ", "邮箱", "@", ".com",
                    "刷新", "关闭", "取消", "确定", "提交", "保存", "删除", "编辑", "查看",
                    "更多", "收起", "展开", "加载中...", "数据加载中", "暂无数据", "404", "500"
                ]

                for line in lines:
                    line = line.strip()

                    # 规则 1: 空行跳过
                    if not line:
                        continue

                    # 规则 2: 过短的行跳过 (通常是图标、单个字母或乱码)
                    if len(line) < 3:
                        continue

                    # 规则 3: 包含噪音关键词的行跳过
                    if any(k in line for k in noise_keywords):
                        continue

                    # 规则 4: 如果一行里全是特殊符号或网址，也可以跳过 (可选)
                    if line.count("http") > 1:
                        continue

                    cleaned_lines.append(line)

                final_text = "\n".join(cleaned_lines)

                if not final_text:
                    print("❌ [Worker] 经过清洗后内容为空。", file=sys.stderr)
                else:
                    print(f"✨ [Worker] 清洗后有效内容：{len(final_text)} 字符，共 {len(cleaned_lines)} 行。",
                          file=sys.stderr)

            except Exception as e:
                print(f"💥 [Worker] 页面处理错误: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.exit(1)
            finally:
                browser.close()

    except Exception as e:
        print(f"💥 [Worker] 启动浏览器失败: {e}", file=sys.stderr)
        sys.exit(1)

    return final_text


if __name__ == "__main__":
    # ✅ 修改点 1: 从命令行参数获取 URL
    if len(sys.argv) < 2:
        print("Usage: python scraper_worker.py <url>", file=sys.stderr)
        sys.exit(1)

    target_url = sys.argv[1]

    result = scrape_job_url(target_url)

    # 1. 定义目标文件路径 (相对于当前脚本所在目录的上级目录)
    # 假设结构是: project/scraper_worker.py -> project/job_llm/test/extracted_job.txt
    base_dir = os.path.dirname(os.path.abspath(__file__)) # 获取 scraper_worker.py 的绝对路径
    target_dir = os.path.join(base_dir, "")
    file_path = os.path.join(target_dir, "extracted_job.txt")

    # 2. 确保目录存在 (如果 job_llm/test 不存在则自动创建)
    os.makedirs(target_dir, exist_ok=True)

    # 3. 写入文件
    if result:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"💾 [Worker] 文件已保存至: {file_path}", file=sys.stderr)
    else:
        print("⚠️ [Worker] 内容为空，跳过文件保存。", file=sys.stderr)

    # ✅ 修改点 2 & 3: 直接输出完整结果到 stdout，不保存文件，不截断
    # 主程序通过 subprocess 捕获这个输出
    if result:
        try:
            print(result)
        except UnicodeEncodeError:
            # 如果打印失败，使用替换字符编码
            print(result.encode('utf-8', errors='replace').decode('utf-8'))
    else:
        print("")

        # 不再保存文件，不再打印预览，保持 stdout 纯净