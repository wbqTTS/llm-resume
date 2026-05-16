\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}

\LoadClass[11pt]{article}

\usepackage[a4paper,margin=1in]{geometry}
\usepackage{fontspec}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}

% ====== 基础格式 ======
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}

% ====== Section 样式（可被 style 覆盖）======
\titleformat{\section}
  {\Large\bfseries}
  {}
  {0em}
  {}

% ====== 自定义命令 ======
\newcommand{\name}[1]{
  {\Huge \bfseries #1}
}

\newcommand{\contact}[1]{
  \vspace{4pt}
  {\small #1}
}

\newcommand{\sectiontitle}[1]{
  \vspace{10pt}
  \section*{#1}
}

\newcommand{\entry}[4]{
  \textbf{#1} \hfill #2 \\
  \textit{#3} \\
  #4
}