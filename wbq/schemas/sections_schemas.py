from typing import List, Optional
from pydantic import BaseModel, Field

class Education(BaseModel):
    degree: str = Field(description="The degree or qualification obtained and The major or field of study. e.g., 计算机科学与技术（实验班）")
    university: str = Field(description="The name of the institution where the degree was obtained with location. e.g. 福州大学(211)")
    from_date: str = Field(description="The start date of the education period. e.g., 2022.09")
    to_date: str = Field(description="The end date of the education period. e.g., 2026.06")
    gpa: str = Field(description="Grade Point Average. e.g., 3.66/4.00")
    honors: str = Field(description="Honors and awards received. e.g., 第十四届全国大学生数学竞赛省一等奖")
    courses: List[str] = Field(description="Relevant courses or subjects studied during the education period. e.g. [操作系统(92), 计算机组成原理(91)]")

class Project(BaseModel):
    name: str = Field(description="The name or title of the project. e.g., 医院综合管理平台")
    type: str = Field(description="The type or category of the project, such as 全栈开发, 网络安全.")
    from_date: str = Field(description="The start date of the project. e.g. 2024.10")
    to_date: str = Field(description="The end date of the project. e.g. 2024.12")
    description: List[str] = Field(description="A list of bullet points describing the project experience. Use STAR methodology, strong action verbs.")

class SkillSection(BaseModel):
    name: str = Field(description="Name or title of the skill group. e.g., 编程语言, 开发框架, 数据库")
    skills: List[str] = Field(description="Specific skills within the skill group. e.g., Python, Java, SpringBoot")

class Experience(BaseModel):
    role: str = Field(description="The job title or position held. e.g. 高级机器学习工程师")
    company: str = Field(description="The name of the company or organization. e.g. Tiger Analytics")
    location: str = Field(description="The location of the company or organization. e.g. 印度班加罗尔")
    from_date: str = Field(description="The start date of the employment period. e.g., 2022.06")
    to_date: str = Field(description="The end date of the employment period. e.g., 2023.07")
    description: List[str] = Field(description="A list of bullet points describing the work experience. Use STAR methodology, strong action verbs, quantify impact.")

class SocialPractice(BaseModel):
    role: str = Field(description="The role or position in social practice. e.g., 思政课程实践小组主要成员, 院红十字会成员")
    description: List[str] = Field(description="A list of bullet points describing the social practice activities.")

class Personal(BaseModel):
    name: str = Field(description="The full name of the candidate. e.g., 王碧强")
    birthdate: str = Field(description="The birth date of the candidate. e.g., 2003.11")
    phone: str = Field(description="The contact phone number of the candidate. e.g., 19559098287")
    politics: str = Field(description="Political status. e.g., 共青团员")
    email: str = Field(description="The contact email address of the candidate. e.g., 2108095381@qq.com")
    hometown: str = Field(description="Hometown of the candidate. e.g., 福建福州")
    photo: str = Field(description="Path to the photo file. e.g., 报名照片.jpg")

# ===== 学术风格特有 Schema =====

class ResearchExperience(BaseModel):
    """研究经历"""
    role: str = Field(description="研究角色，如：研究助理、博士后、访问学者")
    project: str = Field(description="项目名称")
    institution: str = Field(description="机构名称")
    location: str = Field(description="地点")
    from_date: str = Field(description="开始时间，格式：YYYY.MM")
    to_date: str = Field(description="结束时间，格式：YYYY.MM，或'至今'")
    description: List[str] = Field(description="项目描述，建议使用STAR法则（情境-任务-行动-结果），包含量化成果")

class TeachingExperience(BaseModel):
    """教学经历"""
    role: str = Field(description="教学角色，如：助教、讲师、课程助理")
    course: str = Field(description="课程名称")
    institution: str = Field(description="机构名称")
    date: str = Field(description="时间，格式：YYYY.MM-YYYY.MM")
    responsibilities: List[str] = Field(description="职责描述列表，如：负责习题课、批改作业、实验指导等")

class AcademicService(BaseModel):
    """学术服务"""
    role: str = Field(description="服务角色，如：审稿人、会议组织者、期刊编委")
    journal: Optional[str] = Field(default=None, description="期刊名称（如适用）")
    conference: Optional[str] = Field(default=None, description="会议名称（如适用）")
    date: str = Field(description="服务时间，格式：YYYY-至今 或 YYYY")
    description: Optional[str] = Field(default=None, description="简要描述，如：审稿X篇")

class ResumeSchema(BaseModel):
    personal: Personal = Field(description="Personal information of the candidate.")
    education: List[Education] = Field(description="Educational qualifications, including degree, institution, dates, GPA, honors, and relevant courses.")
    work_experience: List[Experience] = Field(description="Work experiences, including job title, company, location, dates, and description.")
    projects: List[Project] = Field(description="Project experiences, including project name, type, dates, and description.")
    skill_section: List[SkillSection] = Field(description="Skill sections, each containing a group of skills and competencies relevant to the job.")
    social_practice: List[SocialPractice] = Field(description="Social practice experiences, including role and description.")

    # 学术风格特有字段（可选）
    research_experience: Optional[List[ResearchExperience]] = Field(default=None, description="Research experiences for academic style resume")
    teaching_experience: Optional[List[TeachingExperience]] = Field(default=None, description="Teaching experiences for academic style resume")
    academic_service: Optional[List[AcademicService]] = Field(default=None, description="Academic service activities for academic style resume")