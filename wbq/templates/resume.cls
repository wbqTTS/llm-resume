\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}

\LoadClass[11pt,a4paper]{article}

\RequirePackage{geometry}
\geometry{left=1.5cm,right=1.5cm,top=0.5cm,bottom=0.5cm}

\RequirePackage{xcolor}
\RequirePackage{titlesec}
\RequirePackage{enumitem}
\RequirePackage{fontspec}
\RequirePackage{xeCJK}
\RequirePackage{hyperref}
\RequirePackage{fontawesome5}
\RequirePackage{parskip}
\RequirePackage{setspace}
\RequirePackage{array}
\RequirePackage{booktabs}
\RequirePackage{graphicx}
\RequirePackage{paracol}

% ===== 字体设置 =====
\setmainfont{Times New Roman}
\setCJKmainfont{SimSun}[AutoFakeBold=2.5]

% ===== 基础颜色定义 =====
\definecolor{heading}{RGB}{44, 62, 80}
\definecolor{subheading}{RGB}{80, 80, 80}
\definecolor{rulecolor}{RGB}{160, 160, 160}

% ===== 基础标题格式 =====
\titleformat{\section}
  {\Large\bfseries\color{heading}}
  {}{0em}{}
  [{\color{rulecolor}\titlerule[0.8pt]}]

\titlespacing*{\section}{0pt}{16pt}{10pt}

% ===== 列表设置 =====
\setlist[itemize]{
  leftmargin=1.8em,
  itemsep=2pt,
  topsep=4pt,
  parsep=0pt,
  label=\textbullet
}

\pagestyle{empty}