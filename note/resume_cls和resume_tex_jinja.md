这是一个非常核心的概念区分。简单来说：
resume.cls 是 “排版引擎/规则书”（决定长什么样：边距、字体、线条粗细、布局逻辑）。
resume.tex.jinja 是 “内容填充模板”（决定填什么：哪里填名字、哪里循环工作经历、结构顺序）。

如果你要更改简历排版（比如：把两栏改成单栏、改变标题颜色、调整行间距、增加一条分割线），主要修改 resume.cls。

二者关系的详细对比
特性   resume.cls (Class File)   resume.tex.jinja (Template File)
角色比喻   建筑蓝图 + 施工规范(规定墙多厚、窗户多大、用什么砖)   房屋入住清单(规定哪个房间住谁、家具摆哪)

核心功能   定义视觉样式和底层逻辑。包含：页面尺寸、页边距、字体定义、自定义命令（如 section{} 的具体画法）、颜色定义。   定义内容结构和数据注入点。包含：Jinja2 语法 ({{ }}, {% %})，决定数据的先后顺序，调用 .cls 中定义的命令。

代码内容   纯 LaTeX 宏编程。例：renewcommand{section}[1]{Large textbf{#1}}   LaTeX 结构 + Jinja2 逻辑。例：section{VAR{personal.name}}

依赖关系   被依赖者。它不关心具体数据，只负责提供格式工具。   依赖者。它必须引用 .cls 中定义的命令才能工作（第一行通常是 documentclass{resume}）。

修改后果   影响所有使用该模板的简历。改一次，所有生成的 PDF 样式都会变。   仅影响当前逻辑或特定字段。比如决定“是否显示照片”或“工作经历放在教育经历之前”。

实战指南：我要改排版，该动哪个？

场景 A：我要改“长相” (Look & Feel) -> 修改 resume.cls
如果你想做以下修改，请打开 resume.cls：
改边距：觉得页面太挤或太宽。
   操作: 查找 geometry 宏包设置，修改 left=, right= 等参数。
改字体/字号：想把正文从宋体改成黑体，或者把名字变得更大。
   操作: 查找字体定义部分，修改 renewcommand{name}[1] 内部的字体大小命令（如 Huge 改为 LARGE）。
改颜色：想把黑色的标题变成深蓝色。
   操作: 查找颜色定义（通常用了 xcolor 宏包），修改 definecolor 或直接在命令里加颜色代码。
改布局结构：想从“左右两栏”改成“上下单栏”，或者给每个板块加一条横线。
   操作: 这是最复杂的，需要修改 .cls 中定义环境（Environment）的部分，比如 job 环境或 section 命令的内部实现。
增加新命令：想新增一个 skillbar{Python}{90%} 来画进度条。
   操作: 在 .cls 文件中编写这个新命令的逻辑。

场景 B：我要改“内容逻辑” (Content Logic) -> 修改 resume.tex.jinja
如果你想做以下修改，请打开 resume.tex.jinja：
调整顺序：想把“教育经历”放到“工作经历”前面。
   操作: 在 .jinja 文件中剪切粘贴对应的 {% block %} 或段落代码。
条件显示：只有当用户有 GitHub 链接时，才显示 GitHub 图标和链接。
   操作: 在 .jinja 文件中添加 {% if personal.github %} ... {% endif %}。
循环逻辑：想改变工作经历的展示方式（比如以前只显示公司，现在想显示“公司 - 职位”在一行）。
   操作: 修改 {% for job in work_experience %} 循环内部的 LaTeX 代码写法。
增删字段：想在个人信息里多加一个“微信号”。
   操作: 在 .jinja 文件的个人信息区域加一行 VAR{personal.wechat}。

代码示例对比

在 resume.cls 中 (定义规则)
这里定义了 section 命令长什么样。
% resume.cls 片段
renewcommand{section}[1]{%
  vspace{5mm} % 上面留白 5mm
  {Large textbf{color{blue} #1}} % 字体大、加粗、蓝色
  vspace{2mm} % 下面留白 2mm
  hrule % 画一条横线
  vspace{2mm}
}
如果你把这里的 blue 改成 red，所有简历的标题都会变红。

在 resume.tex.jinja 中 (使用规则)
这里决定了什么时候调用这个规则，以及填入什么内容。
% resume.tex.jinja 片段
documentclass{resume} % 引用上面的 cls

begin{document}

% 调用上面定义的 section 命令，填入 "工作经历" 四个字
section{工作经历} 

% 循环填充具体内容
{% for job in work_experience %}
  begin{job}{VAR{job.title}}{VAR{job.company}}
     VAR{job.description}
  end{job}
{% endfor %}

end{document}
如果你在这里把 section{工作经历} 改成 section{我的职场生涯}，只有这一处的标题文字会变，但颜色、字体大小（由 cls 控制）不会变。

总结建议

先动 resume.tex.jinja：如果你只是调整内容顺序、增加字段、做简单的逻辑判断。这比较安全，不容易破坏整体样式。
后动 resume.cls：如果你真的对视觉效果（颜色、间距、字体、线条、分栏）不满意。
    ⚠️ 警告：.cls 文件涉及 LaTeX 宏编程，语法较复杂。修改时建议少量多次，每改一点就运行一次编译看看效果，否则一旦报错很难排查。
如果找不到 .cls：有些简单的模板没有单独的 .cls 文件，所有的样式定义都直接写在了 resume.tex.jinja 的导言区（documentclass 之后，begin{document} 之前的部分）。如果是这种情况，那你就直接在 .jinja 文件头部修改样式即可。但看你的代码里有 shutil.copy(..., "resume.cls")，说明你使用的是独立的 Class 文件模式，所以改样式请直奔 resume.cls。