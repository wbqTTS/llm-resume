## 一、**常见 LaTeX 命令**

### 1.1 文档结构和格式

| 命令 | 作用 | 示例 | 说明 |
|------|------|------|------|
| `\documentclass{}` | 指定文档类型 | `\documentclass{article}` | 简历中用的是自定义的 `resume` |
| `\usepackage{}` | 加载宏包 | `\usepackage{xcolor}` | 在 `.cls` 文件中使用 |
| `\begin{}` | 环境开始 | `\begin{document}` | 最常用的是 `document` 环境 |
| `\end{}` | 环境结束 | `\end{document}` | 必须和 `\begin` 配对 |
| `\input{}` | 导入外部文件 | `\input{styles/style_classic.tex}` | 类似于Python的 `import` |

### 1.2 字体样式

| 命令 | 作用 | 示例 | 效果 |
|------|------|------|------|
| `\textbf{}` | 粗体 | `\textbf{重要内容}` | **重要内容** |
| `\textit{}` | 斜体 | `\textit{斜体文字}` | *斜体文字* |
| `\underline{}` | 下划线 | `\underline{下划线}` | <u>下划线</u> |
| `\texttt{}` | 等宽字体 | `\texttt{code}` | `code` |
| `\textsc{}` | 小型大写 | `\textsc{Name}` | NAME（小大写） |
| `\textrm{}` | 罗马字体 | `\textrm{normal}` | normal |
| `\textsf{}` | 无衬线字体 | `\textsf{sans}` | sans |

### 1.3 字体大小

| 命令 | 相对大小 | 示例 |
|------|---------|------|
| `\tiny` | 极小 | `{\tiny 极小文字}` |
| `\scriptsize` | 脚注大小 | `{\scriptsize 脚注大小}` |
| `\footnotesize` | 脚注大小 | `{\footnotesize 脚注}` |
| `\small` | 小号 | `{\small 小号文字}` |
| `\normalsize` | 正常大小 | `{\normalsize 正常}` |
| `\large` | 大号 | `{\large 大号文字}` |
| `\Large` | 更大 | `{\Large 更大文字}` |
| `\LARGE` | 很大 | `{\LARGE 很大文字}` |
| `\huge` | 巨大 | `{\huge 巨大文字}` |
| `\Huge` | 超大 | `{\Huge 超大文字}` |

### 1.4 颜色（需加载 xcolor 宏包）

| 命令 | 作用 | 示例 |
|------|------|------|
| `\color{名称}` | 设置颜色 | `{\color{red} 红色文字}` |
| `\textcolor{名称}{文本}` | 给文本着色 | `\textcolor{blue}{蓝色文字}` |
| `\colorbox{颜色}{文本}` | 背景色 | `\colorbox{yellow}{黄色背景}` |
| `\definecolor{名称}{RGB}{r,g,b}` | 定义颜色 | `\definecolor{primary}{RGB}{44,62,80}` |

### 1.5 列表环境

| 命令 | 作用 | 示例 |
|------|------|------|
| `\begin{itemize}` | 无序列表开始 | `\begin{itemize}` |
| `\end{itemize}` | 无序列表结束 | `\end{itemize}` |
| `\begin{enumerate}` | 有序列表开始 | `\begin{enumerate}` |
| `\end{enumerate}` | 有序列表结束 | `\end{enumerate}` |
| `\item` | 列表项 | `\item 第一项` |
| `\textbullet` | 实心圆点 • | `\textbullet\ 项目点` |

### 1.6 间距和布局

| 命令 | 作用 | 示例 |
|------|------|------|
| `\vspace{长度}` | 垂直间距 | `\vspace{12pt}` |
| `\hspace{长度}` | 水平间距 | `\hspace{1cm}` |
| `\hfill` | 水平弹性填充 | `左 \hfill 右`（左右分开）|
| `\noindent` | 取消首行缩进 | `\noindent 这行不缩进` |
| `\par` | 新段落 | `第一段\par 第二段` |
| `\\` | 换行 | `第一行 \\ 第二行` |
| `\newpage` | 新的一页 | `\newpage` |

### 1.7 对齐环境

| 命令 | 作用 | 示例 |
|------|------|------|
| `\begin{center}` | 居中 | `\begin{center} 居中内容 \end{center}` |
| `\begin{flushleft}` | 左对齐 | `\begin{flushleft} 左对齐 \end{flushleft}` |
| `\begin{flushright}` | 右对齐 | `\begin{flushright} 右对齐 \end{flushright}` |
| `\raggedleft` | 右对齐（单行） | `{\raggedleft 右对齐}` |
| `\raggedright` | 左对齐（单行） | `{\raggedright 左对齐}` |
| `\centering` | 居中（单行） | `{\centering 居中}` |

### 1.8 盒子与多栏

| 命令 | 作用 | 示例 |
|------|------|------|
| `\begin{minipage}[位置]{宽度}` | 创建小页面 | `\begin{minipage}[t]{0.7\textwidth}` |
| `\parbox{宽度}{内容}` | 段落盒子 | `\parbox{5cm}{内容}` |
| `\makebox[宽度][位置]{内容}` | 水平盒子 | `\makebox[3cm][c]{居中内容}` |
| `\rule[抬升]{宽度}{高度}` | 绘制横线 | `\rule{\textwidth}{0.8pt}` |

### 1.9 超链接和引用

| 命令 | 作用 | 示例 |
|------|------|------|
| `\href{URL}{文本}` | 超链接 | `\href{https://github.com}{GitHub}` |
| `\url{URL}` | 显示URL | `\url{https://example.com}` |
| `\label{标签}` | 设置标签 | `\label{sec:intro}` |
| `\ref{标签}` | 引用标签 | `参见第\ref{sec:intro}节` |

### 1.10 特殊符号

| 命令 | 符号 | 说明 |
|------|------|------|
| `\#` | # | 井号（需要转义）|
| `\$` | $ | 美元符号 |
| `\%` | % | 百分号 |
| `\&` | & | and符号 |
| `\_` | _ | 下划线 |
| `\{` | { | 左大括号 |
| `\}` | } | 右大括号 |
| `\textbackslash` | \ | 反斜杠 |
| `\textasciitilde` | ~ | 波浪号 |
| `\textasciicircum` | ^ | 脱字符 |
| `\textbullet` | • | 实心圆点 |
| `\textendash` | – | 短破折号 |
| `\textemdash` | — | 长破折号 |

---

## 二、**常见 Jinja2 关键字**

### 2.1 变量输出

| 语法 | 作用 | 示例 | 输出 |
|------|------|------|------|
| `\VAR{变量}` | 输出变量值 | `\VAR{personal.name}` | 张三 |
| `\VAR{变量.属性}` | 输出对象属性 | `\VAR{job.role}` | 工程师 |
| `\VAR{列表[索引]}` | 输出列表元素 | `\VAR{skills[0]}` | Python |
| `\VAR{变量 \| 过滤器}` | 应用过滤器 | `\VAR{name \| upper}` | 张三 → ZHANG SAN |

### 2.2 常用过滤器

| 过滤器 | 作用 | 示例 | 结果 |
|--------|------|------|------|
| `upper` | 转大写 | `"hello" \| upper` | HELLO |
| `lower` | 转小写 | `"HELLO" \| lower` | hello |
| `capitalize` | 首字母大写 | `"hello" \| capitalize` | Hello |
| `title` | 每个单词首字母大写 | `"hello world" \| title` | Hello World |
| `trim` | 去除首尾空格 | `" hello " \| trim` | hello |
| `replace(a,b)` | 替换字符串 | `"C#" \| replace("#", "\#")` | C\# |
| `default('默认值')` | 设置默认值 | `phone \| default('N/A')` | 无电话时显示 N/A |
| `length` | 获取长度 | `skills \| length` | 5 |
| `join(', ')` | 连接列表 | `skills \| join(', ')` | Python, Java, C++ |

### 2.3 控制结构

| 语法 | 作用 | 示例 |
|------|------|------|
| `\BLOCK{for 变量 in 列表}` | 循环开始 | `\BLOCK{for job in work_experience}` |
| `\BLOCK{endfor}` | 循环结束 | `\BLOCK{endfor}` |
| `\BLOCK{if 条件}` | 条件判断开始 | `\BLOCK{if personal.phone}` |
| `\BLOCK{elif 条件}` | 否则如果 | `\BLOCK{elif personal.mobile}` |
| `\BLOCK{else}` | 否则 | `\BLOCK{else}` |
| `\BLOCK{endif}` | 条件结束 | `\BLOCK{endif}` |

### 2.4 循环中的特殊变量

| 变量 | 作用 | 示例 |
|------|------|------|
| `loop.index` | 当前循环次数（从1开始） | `第 \VAR{loop.index} 项` |
| `loop.index0` | 当前循环次数（从0开始） | `\VAR{loop.index0}` |
| `loop.first` | 是否是第一次循环 | `\BLOCK{if loop.first}第一次\BLOCK{endif}` |
| `loop.last` | 是否是最后一次循环 | `\BLOCK{if loop.last}最后一次\BLOCK{endif}` |
| `loop.length` | 循环总次数 | `共 \VAR{loop.length} 项` |

### 2.5 注释

| 语法 | 作用 | 示例 |
|------|------|------|
| `(((` | 注释开始 | `((( 这是注释 )))` |
| `)))` | 注释结束 | `((( 这行在生成的.tex中不会出现 )))` |

### 2.6 数学运算

| 运算符 | 作用 | 示例 |
|--------|------|------|
| `+` | 加法 | `\VAR{score + 10}` |
| `-` | 减法 | `\VAR{price - discount}` |
| `*` | 乘法 | `\VAR{count * 2}` |
| `/` | 除法 | `\VAR{total / 3}` |
| `//` | 整除 | `\VAR{10 // 3}` （结果是3）|
| `%` | 取余 | `\VAR{10 % 3}` （结果是1）|

### 2.7 比较运算符

| 运算符 | 作用 | 示例 |
|--------|------|------|
| `==` | 等于 | `\BLOCK{if score == 100}` |
| `!=` | 不等于 | `\BLOCK{if role != 'intern'}` |
| `>` | 大于 | `\BLOCK{if years > 5}` |
| `<` | 小于 | `\BLOCK{if age < 18}` |
| `>=` | 大于等于 | `\BLOCK{if score >= 60}` |
| `<=` | 小于等于 | `\BLOCK{if price <= 1000}` |

### 2.8 逻辑运算符

| 运算符 | 作用 | 示例 |
|--------|------|------|
| `and` | 与 | `\BLOCK{if phone and email}` |
| `or` | 或 | `\BLOCK{if phone or email}` |
| `not` | 非 | `\BLOCK{if not phone}` |
| `in` | 属于 | `\BLOCK{if 'Python' in skills}` |

---

## 三、**LaTeX 和 Jinja2 的协作示例**

```latex
\documentclass{resume}
\input{styles/style_classic.tex}

\begin{document}

% Jinja2: 输出姓名（变量）
\name{\VAR{personal.name}}

% Jinja2: 条件判断 + 循环
\section{Professional Experience}
\BLOCK{for job in work_experience}
  % LaTeX: 使用样式文件中定义的命令
  \entry{
    \VAR{job.role}  % Jinja2: 变量
  }{
    \VAR{job.from_date} -- \VAR{job.to_date}
  }{
    \VAR{job.company}, \VAR{job.location}
  }{
    \begin{itemize}  % LaTeX: 列表环境
    \BLOCK{for d in job.description}
      \item \VAR{d}  % LaTeX的\item + Jinja2的变量
    \BLOCK{endfor}
    \end{itemize}
  }
\BLOCK{endfor}

\end{document}
```

---

## 四、**快速记忆口诀**

### LaTeX 命令：
- **\text...**：字体样式（`\textbf`粗体、`\textit`斜体）
- **\begin...\end**：环境开始结束
- **\section、\subsection**：章节标题
- **\vspace、\hspace**：垂直/水平间距
- **\color、\textcolor**：颜色设置

### Jinja2 语法：
- **\VAR{}**：输出变量（Variable）
- **\BLOCK{}**：控制块（Block）
- **for...endfor**：循环
- **if...endif**：条件判断
- **| 过滤器**：处理变量