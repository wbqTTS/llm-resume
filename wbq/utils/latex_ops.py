import jinja2
import os
import shutil
from typing import Optional
import platform
import subprocess
from wbq.utils.utils import write_file


def escape_for_latex(data):
    if isinstance(data, dict):
        new_data = {}
        for key in data.keys():
            new_data[key] = escape_for_latex(data[key])
        return new_data
    elif isinstance(data, list):
        return [escape_for_latex(item) for item in data]
    elif isinstance(data, str):
        # Adapted from https://stackoverflow.com/q/16259923
        latex_special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\^{}",
            "\\": r"\textbackslash{}",
            "\n": "\\newline%\n",
            "-": r"{-}",
            "\xA0": "~",  # Non-breaking space
            "[": r"{[}",
            "]": r"{]}",
        }
        return "".join([latex_special_chars.get(c, c) for c in data])

    return data


def build_latex_environment(templates_path: str | None = None):
    module_dir = os.path.dirname(__file__)
    resolved_templates_path = templates_path or os.path.join(os.path.dirname(module_dir), "templates")
    return jinja2.Environment(
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="\\VAR{",
        variable_end_string="}",
        comment_start_string="\\#{",
        comment_end_string="}",
        line_statement_prefix="%-",
        line_comment_prefix="%#",
        trim_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(resolved_templates_path),
    )


def render_resume_tex(json_resume, template_name="resume_classic.tex.jinja", templates_path: str | None = None):
    escaped_json_resume = escape_for_latex(json_resume)
    return use_template(build_latex_environment(templates_path), escaped_json_resume, template_name)

def json_to_latex_to_pdf(json_resume, dst_path, template_name="resume_classic.tex.jinja"):
    """
    将 JSON 简历数据编译为 PDF

    Args:
        json_resume: 经AI优化后的简历数据字典
        dst_path: 目标PDF文件路径
        template_name: 使用的模板文件名，默认为 "resume_classic.tex.jinja"

    Returns:
        str | None: 成功返回 PDF 路径，失败返回 None
    """
    print(f">>> [DEBUG] 开始生成 PDF，目标路径：{dst_path}")

    try:
        module_dir = os.path.dirname(__file__)
        templates_path = os.path.join(os.path.dirname(module_dir), 'templates')

        # 确保输出目录存在
        output_dir = os.path.dirname(dst_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f">>> [DEBUG] 创建输出目录：{output_dir}")

        latex_jinja_env = build_latex_environment(templates_path)

        print(">>> [DEBUG] 正在转义 LaTeX 特殊字符...")
        escaped_json_resume = escape_for_latex(json_resume)

        print(f">>> [DEBUG] 正在渲染模板: {template_name}")
        resume_latex = use_template(latex_jinja_env, escaped_json_resume, template_name)

        if not resume_latex:
            print(">>> [ERROR] 模板渲染失败，返回内容为空！")
            return None

        print(">>> [DEBUG] 模板渲染成功，准备写入 .tex 文件...")

        # 生成 .tex 文件路径
        tex_filename = os.path.basename(dst_path).replace(".pdf", ".tex")
        tex_temp_path = os.path.join(output_dir, tex_filename)

        print(f">>> [DEBUG] 正在写入临时 .tex 文件：{tex_temp_path}")
        write_file(tex_temp_path, resume_latex)
        print(">>> [DEBUG] .tex 文件写入完成。")

        # 复制必要的 .cls 和 styles 目录到编译目录
        source_cls = os.path.join(templates_path, "resume.cls")
        dest_cls = os.path.join(output_dir, "resume.cls")

        if os.path.exists(source_cls):
            shutil.copy(source_cls, dest_cls)
            print(f">>> [DEBUG] 已复制 resume.cls 到 {dest_cls}")
        else:
            print(f">>> [WARNING] 未找到 resume.cls 在 {source_cls}，编译可能会失败！")

        # 复制 styles 目录
        source_styles = os.path.join(templates_path, "styles")
        dest_styles = os.path.join(output_dir, "styles")

        if os.path.exists(source_styles):
            if not os.path.exists(dest_styles):
                shutil.copytree(source_styles, dest_styles)
                print(f">>> [DEBUG] 已复制 styles 目录到 {dest_styles}")
            else:
                print(f">>> [DEBUG] styles 目录已存在")
        else:
            print(f">>> [WARNING] 未找到 styles 目录在 {source_styles}，编译可能会失败！")

        print(">>> [DEBUG] 开始调用 xelatex 编译 PDF (这一步可能会耗时)...")

        # 调用编译函数
        success = compile_latex_to_pdf(tex_temp_path, dst_path)

        if success:
            print(">>> [SUCCESS] PDF 生成成功！")
            return dst_path  # ✅ 返回 PDF 路径
        else:
            print(">>> [ERROR] PDF 编译失败")
            return None

    except Exception as e:
        print(f">>> [FATAL ERROR] 发生异常：{e}")
        import traceback
        traceback.print_exc()
        return None


def use_template(jinja_env, json_resume, template_name="resume_classic.tex.jinja"):
    """
    使用 Jinja2 模板引擎将简历数据渲染为 LaTeX 源代码字符串。

    Args:
        jinja_env (jinja2.Environment): 已配置的 Jinja2 环境对象
        json_resume (dict): 包含完整简历数据的字典
        template_name (str): 要使用的模板文件名

    Returns:
        str | None: 成功返回渲染后的LaTeX源码，失败返回None
    """
    try:
        # 加载指定的模板文件
        resume_template = jinja_env.get_template(template_name)

        # 渲染模板
        resume = resume_template.render(json_resume)

        return resume

    except Exception as e:
        print(f"Error rendering template {template_name}: {e}")
        return None





OS_SYSTEM = platform.system().lower()


def compile_latex_to_pdf(tex_file_path: str, dst_path: str) -> Optional[bool]:
    """
    将 .tex 文件编译为 PDF，并移动到目标位置，同时清理中间文件

    Args:
        tex_file_path: .tex 源文件路径
        dst_path: 目标PDF文件路径

    Returns:
        True (成功), False (失败)
    """
    print(f">>> [PDF] 开始转换: {tex_file_path} -> {dst_path}")

    prev_loc = os.getcwd()
    tex_dir = os.path.dirname(os.path.abspath(tex_file_path))
    tex_filename = os.path.basename(tex_file_path)
    base_name = os.path.splitext(tex_filename)[0]

    try:
        # 切换到 .tex 文件所在目录
        if not os.path.isdir(tex_dir):
            print(f">>> [ERROR] 目录不存在: {tex_dir}")
            return False

        os.chdir(tex_dir)
        print(f">>> [PDF] 已切换工作目录至: {tex_dir}")

        # 编译两次以确保交叉引用正确
        for i in range(2):
            print(f">>> [PDF] 第 {i+1} 次编译...")
            try:
                cmd = [
                    "xelatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    tex_filename
                ]

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=60,
                    encoding='utf-8',
                    errors='replace'
                )

                if result.returncode != 0:
                    print(f">>> [ERROR] ❌ xelatex 编译失败 (第 {i+1} 次)")

                    # 提取错误日志
                    log_lines = result.stdout.split('\n')
                    error_lines = [line for line in log_lines if 'error' in line.lower() or line.strip().startswith('!')]

                    print("--- 关键错误日志 ---")
                    if error_lines:
                        for line in error_lines[-20:]:
                            print(f"  {line}")
                    else:
                        print("  (未检测到标准错误格式，以下是最后 20 行)")
                        print('\n'.join(log_lines[-20:]))

                    # 保存完整日志
                    log_file = os.path.join(tex_dir, f"{base_name}_error.log")
                    with open(log_file, "w", encoding="utf-8") as f:
                        f.write(result.stdout)
                    print(f"   📄 完整日志已保存到: {log_file}")

                    os.chdir(prev_loc)
                    return False

            except subprocess.TimeoutExpired:
                print(f">>> [ERROR] ⏰ 第 {i+1} 次编译超时 (超过60秒)")
                os.chdir(prev_loc)
                return False
            except Exception as e:
                print(f">>> [ERROR] 💥 调用 xelatex 异常: {e}")
                os.chdir(prev_loc)
                return False

        print(">>> [PDF] ✅ xelatex 编译成功")

        # 验证并移动生成的 PDF
        generated_pdf_name = f"{base_name}.pdf"
        full_generated_pdf_path = os.path.join(tex_dir, generated_pdf_name)

        if not os.path.exists(full_generated_pdf_path):
            print(f">>> [ERROR] ❌ 未找到生成的 PDF 文件: {full_generated_pdf_path}")
            os.chdir(prev_loc)
            return False

        # 确保目标目录存在
        dst_dir = os.path.dirname(dst_path)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)

        # 移动 PDF 到目标位置
        shutil.move(full_generated_pdf_path, dst_path)
        print(f">>> [PDF] 📄 PDF 已移动至: {dst_path}")

        # 清理中间文件
        extensions_to_clean = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk', '.synctex.gz']
        files_to_remove = []

        try:
            all_files = os.listdir(tex_dir)
            for f in all_files:
                if f.startswith(base_name) and f != tex_filename and f != os.path.basename(dst_path):
                    if any(f.endswith(ext) for ext in extensions_to_clean):
                        files_to_remove.append(f)

            if files_to_remove:
                print(f">>> [PDF] 🧹 正在清理 {len(files_to_remove)} 个中间文件...")
                for f in files_to_remove:
                    try:
                        os.remove(os.path.join(tex_dir, f))
                    except Exception as clean_err:
                        print(f"   - ⚠️ 无法删除 {f}: {clean_err}")

        except Exception as list_err:
            print(f"   - ⚠️ 清理中间文件时出错: {list_err}")

        # 自动打开PDF
        try:
            if platform.system().lower() == 'windows':
                os.startfile(dst_path)
            elif platform.system().lower() == 'darwin':
                subprocess.run(['open', dst_path])
            else:
                subprocess.run(['xdg-open', dst_path])
            print(">>> [PDF] 📂 已自动打开PDF文件")
        except Exception as e:
            print(f">>> [PDF] ⚠️ 无法自动打开PDF: {e}")

        os.chdir(prev_loc)
        print(">>> [PDF] 🎉 所有步骤完成")
        return True

    except Exception as e:
        print(f">>> [ERROR] 💥 save_latex_as_pdf 异常: {e}")
        import traceback
        traceback.print_exc()
        try:
            os.chdir(prev_loc)
        except:
            pass
        return False
