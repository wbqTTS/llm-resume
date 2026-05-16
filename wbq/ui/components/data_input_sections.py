from wbq.ui.app_context import *


ROLE_TAGS = ["前端工程师", "后端工程师", "算法工程师", "数据分析师", "产品经理", "测试工程师"]
TECH_TAGS = ["Python", "Java", "Spring Boot", "React", "MySQL", "Redis", "Docker", "LLM"]


def _split_lines(value: str):
    return [line.strip() for line in value.splitlines() if line.strip()]


def _ensure_upload_dir() -> str:
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _save_photo(uploaded_photo):
    if uploaded_photo is None:
        return None
    upload_dir = _ensure_upload_dir()
    file_ext = os.path.splitext(uploaded_photo.name)[1]
    safe_filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
    save_path = os.path.join(upload_dir, safe_filename)
    with open(save_path, "wb") as f:
        f.write(uploaded_photo.getbuffer())
    return os.path.abspath(save_path)


def _append_jd_tag(tag: str):
    current = st.session_state.get("jd_text_input", "").strip()
    if tag in current:
        return
    if current:
        current = f"{current}\n{tag}"
    else:
        current = tag
    st.session_state["jd_text_input"] = current
    st.session_state["jd_text"] = current


def _render_jd_tag_group(title: str, tags: list[str], key_prefix: str):
    st.caption(title)
    color_tokens = ["🔵", "🟢", "🟠", "🟣", "🔷", "🟡", "🟤", "🟦"]
    cols_per_row = 3
    for start in range(0, len(tags), cols_per_row):
        cols = st.columns(cols_per_row)
        for offset, tag in enumerate(tags[start : start + cols_per_row]):
            color_label = f"{color_tokens[(start + offset) % len(color_tokens)]} {tag}"
            with cols[offset]:
                if st.button(color_label, key=f"{key_prefix}_{start + offset}", use_container_width=True):
                    _append_jd_tag(tag)
                    st.rerun()


def render_demo_banner():
    demo_col, tip_col = st.columns([1, 2])
    with demo_col:
        if st.button("一键载入 Demo 数据", use_container_width=True, type="primary"):
            apply_demo_data()
            st.success("演示用 JD 和简历 JSON 已载入，可以直接继续到模型配置。")
            st.rerun()
    # with tip_col:
    #     st.info("答辩演示建议先使用 Demo 数据跑通流程，再替换为你自己的 JD 和简历。")


def render_jd_section():
    st.subheader("A. 目标岗位 JD")
    if "jd_text_input" not in st.session_state:
        st.session_state["jd_text_input"] = st.session_state.get("jd_text", "")

    jd_mode = st.toggle("使用招聘链接自动抓取", value=False, key="jd_toggle")
    col1, col2 = st.columns([1.05, 2])
    jd_url = ""
    jd_text = ""
    with col1:
        if jd_mode:
            jd_url = st.text_input("招聘链接 URL", placeholder="https://www.linkedin.com/jobs/...", key="jd_url_input")
        else:
            st.info("请在右侧直接粘贴岗位描述文本。")
            _render_jd_tag_group("职位标签推荐", ROLE_TAGS, "jd_role_tag")
            _render_jd_tag_group("技术关键词补充", TECH_TAGS, "jd_tech_tag")
    with col2:
        if not jd_mode:
            jd_text = st.text_area(
                "岗位描述文本",
                height=180,
                placeholder="请粘贴完整 JD 内容...",
                key="jd_text_input",
            )
            voice_col, help_col = st.columns([1, 2])
            with voice_col:
                st_voice_input(button_key="voice_jd_input", target_state_key_path=[], label="🎤 语音输入")
            with help_col:
                st.caption("语音识别结果会自动复制到剪贴板，可直接粘贴到岗位描述文本框。")
    st.session_state["jd_url"] = jd_url
    st.session_state["jd_text"] = jd_text if not jd_mode else ""
    return jd_url, jd_text


def render_upload_resume_tab():
    uploaded_resume = st.file_uploader(
        "拖拽文件到这里或点击上传",
        type=["pdf", "json"],
        key="file_uploader_main",
    )
    if uploaded_resume:
        st.success(f"已上传：{uploaded_resume.name}")
        temp_path = os.path.join(_ensure_upload_dir(), uploaded_resume.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_resume.getbuffer())
        st.session_state["resume_source"] = temp_path
        st.session_state["resume_type"] = "upload"
    return uploaded_resume


def render_personal_section(form_data):
    st.subheader("个人信息")
    c1, c2, c3 = st.columns(3)
    form_data["name"] = c1.text_input("姓名", value=form_data.get("name", ""), key="mf_name")
    form_data["birthdate"] = c2.text_input(
        "出生年月", value=form_data.get("birthdate", ""), placeholder="2003.11", key="mf_birthdate"
    )
    form_data["phone"] = c3.text_input("电话", value=form_data.get("phone", ""), key="mf_phone")

    c4, c5, c6 = st.columns(3)
    form_data["politics"] = c4.text_input(
        "政治面貌", value=form_data.get("politics", ""), placeholder="共青团员", key="mf_politics"
    )
    form_data["email"] = c5.text_input("邮箱", value=form_data.get("email", ""), key="mf_email")
    form_data["hometown"] = c6.text_input(
        "籍贯", value=form_data.get("hometown", ""), placeholder="福建福州", key="mf_hometown"
    )

    st.markdown("**证件照上传**")
    upload_col, preview_col = st.columns([2, 1])
    with upload_col:
        uploaded_photo = st.file_uploader(
            "点击上传照片",
            type=["jpg", "jpeg", "png"],
            help="支持 JPG、PNG，建议上传白底证件照",
            key="mf_photo_uploader",
        )
    photo_path = form_data.get("photo", "")
    if uploaded_photo is not None:
        photo_path = _save_photo(uploaded_photo) or photo_path
        with preview_col:
            st.success("照片已上传")
            st.image(uploaded_photo, width=100, caption="预览")
    elif photo_path:
        with preview_col:
            st.info(f"当前使用：{os.path.basename(photo_path)}")
    else:
        with preview_col:
            st.caption("暂无照片")
    form_data["photo"] = photo_path
    st.divider()

    st.subheader("职业信息")
    title_col, summary_col = st.columns(2)
    form_data["title"] = title_col.text_input(
        "职位标题",
        value=form_data.get("title", ""),
        placeholder="例如：Java 后端 / AI 应用开发",
        key="mf_title",
    )
    form_data["summary"] = summary_col.text_area(
        "个人简介",
        value=form_data.get("summary", ""),
        placeholder="用 3-5 句总结你的方向、优势和项目特点",
        height=100,
        key="mf_summary",
    )

    st.markdown("**社交媒体链接**")
    media = form_data.setdefault("media", {})
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    media["github"] = c1.text_input("GitHub", value=media.get("github", ""), key="mf_media_github")
    media["linkedin"] = c2.text_input("LinkedIn", value=media.get("linkedin", ""), key="mf_media_linkedin")
    media["medium"] = c3.text_input("Medium", value=media.get("medium", ""), key="mf_media_medium")
    media["devpost"] = c4.text_input("Devpost", value=media.get("devpost", ""), key="mf_media_devpost")


def render_education_section(form_data):
    st.divider()
    st.subheader("教育背景")
    education_list = form_data.setdefault("education", [])
    if st.button("添加教育背景", key="mf_btn_add_education"):
        education_list.append(
            {"university": "", "degree": "", "from_date": "", "to_date": "", "gpa": "", "honors": "", "courses": []}
        )
        st.rerun()

    for index, edu in enumerate(education_list):
        with st.expander(f"教育 #{index + 1}: {edu.get('university') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            edu["university"] = c1.text_input("学校名称", value=edu.get("university", ""), key=f"mf_edu_uni_{index}")
            edu["degree"] = c2.text_input("学位/专业", value=edu.get("degree", ""), key=f"mf_edu_degree_{index}")
            c3, c4 = st.columns(2)
            edu["from_date"] = c3.text_input(
                "开始时间", value=edu.get("from_date", ""), placeholder="2022.09", key=f"mf_edu_from_{index}"
            )
            edu["to_date"] = c4.text_input(
                "结束时间", value=edu.get("to_date", ""), placeholder="2026.06", key=f"mf_edu_to_{index}"
            )
            c5, c6 = st.columns(2)
            edu["gpa"] = c5.text_input("GPA", value=edu.get("gpa", ""), key=f"mf_edu_gpa_{index}")
            edu["honors"] = c6.text_input("荣誉/奖项", value=edu.get("honors", ""), key=f"mf_edu_honors_{index}")
            edu["courses"] = _split_lines(
                st.text_area(
                    "主修课程（每行一项）",
                    value="\n".join(edu.get("courses", [])),
                    height=100,
                    key=f"mf_edu_courses_{index}",
                )
            )
            if st.button("删除这段教育经历", key=f"mf_del_edu_{index}"):
                education_list.pop(index)
                st.rerun()


def render_work_section(form_data):
    st.divider()
    st.subheader("工作经历")
    jobs = form_data.setdefault("work_experience", [])
    if st.button("添加工作经历", key="mf_btn_add_job"):
        jobs.append({"role": "", "company": "", "location": "", "from_date": "", "to_date": "", "description": []})
        st.rerun()
    for index, job in enumerate(jobs):
        with st.expander(f"工作 #{index + 1}: {job.get('role') or '未命名'}", expanded=False):
            c1, c2 = st.columns([2, 1])
            job["role"] = c1.text_input("职位", value=job.get("role", ""), key=f"mf_j_role_{index}")
            job["company"] = c2.text_input("公司", value=job.get("company", ""), key=f"mf_j_comp_{index}")
            c3, c4, c5 = st.columns(3)
            job["location"] = c3.text_input("地点", value=job.get("location", ""), key=f"mf_j_loc_{index}")
            job["from_date"] = c4.text_input(
                "开始时间", value=job.get("from_date", ""), placeholder="2024.06", key=f"mf_j_from_{index}"
            )
            job["to_date"] = c5.text_input(
                "结束时间", value=job.get("to_date", ""), placeholder="2025.03", key=f"mf_j_to_{index}"
            )
            d1, d2 = st.columns([4, 1])
            with d1:
                desc_text = st.text_area(
                    "工作描述（每行一个要点）",
                    value="\n".join(job.get("description", [])),
                    height=120,
                    key=f"mf_j_desc_{index}",
                )
            with d2:
                st_voice_input(button_key=f"voice_job_{index}", target_state_key_path=[], label="语音输入")
                st.caption("录音后会自动复制到剪贴板")
            job["description"] = _split_lines(desc_text)
            if st.button("删除这段工作经历", key=f"mf_del_job_{index}"):
                jobs.pop(index)
                st.rerun()


def render_project_section(form_data):
    st.divider()
    st.subheader("项目经历")
    projects = form_data.setdefault("projects", [])
    if st.button("添加项目经历", key="mf_btn_add_project"):
        projects.append({"name": "", "type": "", "from_date": "", "to_date": "", "description": []})
        st.rerun()
    for index, project in enumerate(projects):
        with st.expander(f"项目 #{index + 1}: {project.get('name') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            project["name"] = c1.text_input("项目名称", value=project.get("name", ""), key=f"mf_p_name_{index}")
            project["type"] = c2.text_input("项目类型", value=project.get("type", ""), key=f"mf_p_type_{index}")
            c3, c4 = st.columns(2)
            project["from_date"] = c3.text_input(
                "开始时间", value=project.get("from_date", ""), placeholder="2025.01", key=f"mf_p_from_{index}"
            )
            project["to_date"] = c4.text_input(
                "结束时间", value=project.get("to_date", ""), placeholder="2025.04", key=f"mf_p_to_{index}"
            )
            d1, d2 = st.columns([4, 1])
            with d1:
                desc_text = st.text_area(
                    "项目描述（每行一个要点）",
                    value="\n".join(project.get("description", [])),
                    height=120,
                    key=f"mf_p_desc_{index}",
                )
            with d2:
                st_voice_input(button_key=f"voice_proj_{index}", target_state_key_path=[], label="语音输入")
                st.caption("录音后会自动复制到剪贴板")
            project["description"] = _split_lines(desc_text)
            if st.button("删除这个项目", key=f"mf_del_proj_{index}"):
                projects.pop(index)
                st.rerun()


def render_skill_section(form_data):
    st.divider()
    st.subheader("专业技能")
    skills = form_data.setdefault("skill_section", [])
    if st.button("添加技能分类", key="mf_btn_add_skill"):
        skills.append({"name": "", "skills": []})
        st.rerun()
    for index, skill in enumerate(skills):
        with st.expander(f"技能 #{index + 1}: {skill.get('name') or '未命名'}", expanded=False):
            skill["name"] = st.text_input("分类名称", value=skill.get("name", ""), key=f"mf_s_name_{index}")
            skill["skills"] = _split_lines(
                st.text_area("技能列表（每行一项）", value="\n".join(skill.get("skills", [])), key=f"mf_s_list_{index}")
            )
            if st.button("删除技能分类", key=f"mf_del_skill_{index}"):
                skills.pop(index)
                st.rerun()


def render_social_and_awards_section(form_data):
    st.divider()
    st.subheader("社会实践")
    social = form_data.setdefault("social_practice", [])
    if st.button("添加社会实践", key="mf_btn_add_social"):
        social.append({"role": "", "description": []})
        st.rerun()
    for index, item in enumerate(social):
        with st.expander(f"实践 #{index + 1}: {item.get('role') or '未命名'}", expanded=False):
            item["role"] = st.text_input("角色", value=item.get("role", ""), key=f"mf_soc_role_{index}")
            item["description"] = _split_lines(
                st.text_area("实践描述", value="\n".join(item.get("description", [])), key=f"mf_soc_desc_{index}")
            )
            if st.button("删除这段实践", key=f"mf_del_soc_{index}"):
                social.pop(index)
                st.rerun()

    st.divider()
    st.subheader("证书")
    certifications = form_data.setdefault("certifications", [])
    if st.button("添加证书", key="mf_btn_add_cert"):
        certifications.append({"name": "", "date": "", "by": ""})
        st.rerun()
    for index, cert in enumerate(certifications):
        with st.expander(f"证书 #{index + 1}: {cert.get('name') or '未命名'}", expanded=False):
            c1, c2, c3 = st.columns(3)
            cert["name"] = c1.text_input("证书名称", value=cert.get("name", ""), key=f"mf_cert_name_{index}")
            cert["date"] = c2.text_input("获得时间", value=cert.get("date", ""), key=f"mf_cert_date_{index}")
            cert["by"] = c3.text_input("颁发机构", value=cert.get("by", ""), key=f"mf_cert_by_{index}")
            if st.button("删除证书", key=f"mf_del_cert_{index}"):
                certifications.pop(index)
                st.rerun()

    st.divider()
    st.subheader("荣誉奖项")
    achievements = form_data.setdefault("achievements", [])
    if st.button("添加荣誉", key="mf_btn_add_achievement"):
        achievements.append({"name": "", "date": ""})
        st.rerun()
    for index, ach in enumerate(achievements):
        with st.expander(f"荣誉 #{index + 1}: {ach.get('name') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            ach["name"] = c1.text_input("奖项名称", value=ach.get("name", ""), key=f"mf_ach_name_{index}")
            ach["date"] = c2.text_input("获得时间", value=ach.get("date", ""), key=f"mf_ach_date_{index}")
            if st.button("删除荣誉", key=f"mf_del_ach_{index}"):
                achievements.pop(index)
                st.rerun()


def render_academic_section(form_data):
    st.divider()
    st.markdown("### 学术信息（学术模板建议填写）")
    st.info("如果你要展示科研、升学、学术岗位能力，这一组字段会很有帮助。")

    form_data["research_interest"] = st.text_area(
        "研究兴趣",
        value=form_data.get("research_interest", ""),
        placeholder="例如：自然语言处理、大语言模型、信息抽取、人机协同写作",
        key="mf_research_interest",
    )

    st.markdown("---")
    st.markdown("### 出版物")
    publications = form_data.setdefault("publications", [])
    if st.button("添加出版物", key="mf_btn_add_publication"):
        publications.append({"title": "", "journal": "", "year": "", "authors": [], "type": "conference", "authorship": ""})
        st.rerun()
    for index, pub in enumerate(publications):
        with st.expander(f"出版物 #{index + 1}: {pub.get('title') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            pub["title"] = c1.text_input("论文标题", value=pub.get("title", ""), key=f"mf_pub_title_{index}")
            pub["journal"] = c2.text_input("期刊/会议名称", value=pub.get("journal", ""), key=f"mf_pub_journal_{index}")
            c3, c4 = st.columns(2)
            pub["year"] = c3.text_input("发表年份", value=pub.get("year", ""), key=f"mf_pub_year_{index}")
            pub["type"] = c4.selectbox(
                "类型",
                ["conference", "journal"],
                index=0 if pub.get("type", "conference") == "conference" else 1,
                key=f"mf_pub_type_{index}",
            )
            pub["authorship"] = st.text_input("作者身份", value=pub.get("authorship", ""), key=f"mf_pub_authorship_{index}")
            authors = st.text_input("作者列表（英文逗号分隔）", value=", ".join(pub.get("authors", [])), key=f"mf_pub_authors_{index}")
            pub["authors"] = [author.strip() for author in authors.split(",") if author.strip()]
            if st.button("删除出版物", key=f"mf_del_pub_{index}"):
                publications.pop(index)
                st.rerun()

    st.markdown("---")
    st.markdown("### 研究经历")
    research_list = form_data.setdefault("research_experience", [])
    if st.button("添加研究经历", key="mf_btn_add_research"):
        research_list.append(
            {"role": "", "project": "", "institution": "", "location": "", "from_date": "", "to_date": "", "description": []}
        )
        st.rerun()
    for index, item in enumerate(research_list):
        with st.expander(f"研究经历 #{index + 1}: {item.get('project') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            item["role"] = c1.text_input("角色/职位", value=item.get("role", ""), key=f"mf_res_role_{index}")
            item["project"] = c2.text_input("项目名称", value=item.get("project", ""), key=f"mf_res_project_{index}")
            c3, c4 = st.columns(2)
            item["institution"] = c3.text_input("机构名称", value=item.get("institution", ""), key=f"mf_res_inst_{index}")
            item["location"] = c4.text_input("地点", value=item.get("location", ""), key=f"mf_res_loc_{index}")
            c5, c6 = st.columns(2)
            item["from_date"] = c5.text_input("开始时间", value=item.get("from_date", ""), key=f"mf_res_from_{index}")
            item["to_date"] = c6.text_input("结束时间", value=item.get("to_date", ""), key=f"mf_res_to_{index}")
            item["description"] = _split_lines(
                st.text_area("项目描述（每行一个要点）", value="\n".join(item.get("description", [])), height=140, key=f"mf_res_desc_{index}")
            )
            if st.button("删除研究经历", key=f"mf_del_res_{index}"):
                research_list.pop(index)
                st.rerun()

    st.markdown("---")
    st.markdown("### 学术会议报告")
    conferences = form_data.setdefault("conference_presentations", [])
    if st.button("添加会议报告", key="mf_btn_add_conference"):
        conferences.append({"title": "", "conference": "", "location": "", "date": "", "type": "口头报告"})
        st.rerun()
    for index, conf in enumerate(conferences):
        with st.expander(f"会议报告 #{index + 1}: {conf.get('title') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            conf["title"] = c1.text_input("报告标题", value=conf.get("title", ""), key=f"mf_conf_title_{index}")
            conf["conference"] = c2.text_input("会议名称", value=conf.get("conference", ""), key=f"mf_conf_name_{index}")
            c3, c4 = st.columns(2)
            conf["location"] = c3.text_input("地点", value=conf.get("location", ""), key=f"mf_conf_loc_{index}")
            conf["date"] = c4.text_input("时间", value=conf.get("date", ""), key=f"mf_conf_date_{index}")
            conf["type"] = st.selectbox(
                "报告类型",
                ["口头报告", "海报展示"],
                index=0 if conf.get("type", "口头报告") == "口头报告" else 1,
                key=f"mf_conf_type_{index}",
            )
            if st.button("删除会议报告", key=f"mf_del_conf_{index}"):
                conferences.pop(index)
                st.rerun()

    st.markdown("---")
    st.markdown("### 荣誉与奖项（学术版）")
    honors = form_data.setdefault("honors", [])
    if st.button("添加荣誉奖项", key="mf_btn_add_honor"):
        honors.append({"name": "", "institution": "", "date": "", "level": "国家级"})
        st.rerun()
    for index, honor in enumerate(honors):
        with st.expander(f"荣誉 #{index + 1}: {honor.get('name') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            honor["name"] = c1.text_input("奖项名称", value=honor.get("name", ""), key=f"mf_honor_name_{index}")
            honor["institution"] = c2.text_input("颁发机构", value=honor.get("institution", ""), key=f"mf_honor_inst_{index}")
            c3, c4 = st.columns(2)
            honor["date"] = c3.text_input("获得时间", value=honor.get("date", ""), key=f"mf_honor_date_{index}")
            honor["level"] = c4.selectbox(
                "级别", ["国家级", "省级", "校级", "其他"],
                index=["国家级", "省级", "校级", "其他"].index(honor.get("level", "国家级")),
                key=f"mf_honor_level_{index}",
            )
            if st.button("删除荣誉奖项", key=f"mf_del_honor_{index}"):
                honors.pop(index)
                st.rerun()

    st.markdown("---")
    st.markdown("### 教学经历")
    teaching = form_data.setdefault("teaching_experience", [])
    if st.button("添加教学经历", key="mf_btn_add_teaching"):
        teaching.append({"role": "", "course": "", "institution": "", "date": "", "responsibilities": []})
        st.rerun()
    for index, item in enumerate(teaching):
        with st.expander(f"教学经历 #{index + 1}: {item.get('course') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            item["role"] = c1.text_input("角色", value=item.get("role", ""), key=f"mf_teach_role_{index}")
            item["course"] = c2.text_input("课程名称", value=item.get("course", ""), key=f"mf_teach_course_{index}")
            c3, c4 = st.columns(2)
            item["institution"] = c3.text_input("机构", value=item.get("institution", ""), key=f"mf_teach_inst_{index}")
            item["date"] = c4.text_input("时间", value=item.get("date", ""), key=f"mf_teach_date_{index}")
            item["responsibilities"] = _split_lines(
                st.text_area("职责描述（每行一个要点）", value="\n".join(item.get("responsibilities", [])), height=120, key=f"mf_teach_resp_{index}")
            )
            if st.button("删除教学经历", key=f"mf_del_teach_{index}"):
                teaching.pop(index)
                st.rerun()

    st.markdown("---")
    st.markdown("### 技术技能（学术版）")
    technical = form_data.setdefault("technical_skills", {"programming": [], "frameworks": [], "tools": [], "languages": []})
    technical["programming"] = _split_lines(st.text_area("编程语言", value="\n".join(technical.get("programming", [])), key="mf_tech_programming"))
    technical["frameworks"] = _split_lines(st.text_area("框架与工具", value="\n".join(technical.get("frameworks", [])), key="mf_tech_frameworks"))
    technical["tools"] = _split_lines(st.text_area("开发工具", value="\n".join(technical.get("tools", [])), key="mf_tech_tools"))
    technical["languages"] = _split_lines(st.text_area("语言能力", value="\n".join(technical.get("languages", [])), key="mf_tech_languages"))

    st.markdown("---")
    st.markdown("### 学术服务")
    services = form_data.setdefault("academic_service", [])
    if st.button("添加学术服务", key="mf_btn_add_service"):
        services.append({"role": "", "journal": "", "conference": "", "date": "", "description": ""})
        st.rerun()
    for index, service in enumerate(services):
        with st.expander(f"学术服务 #{index + 1}: {service.get('role') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            service["role"] = c1.text_input("服务角色", value=service.get("role", ""), key=f"mf_service_role_{index}")
            service["journal"] = c2.text_input("期刊名称", value=service.get("journal", ""), key=f"mf_service_journal_{index}")
            c3, c4 = st.columns(2)
            service["conference"] = c3.text_input("会议名称", value=service.get("conference", ""), key=f"mf_service_conf_{index}")
            service["date"] = c4.text_input("时间", value=service.get("date", ""), key=f"mf_service_date_{index}")
            service["description"] = st.text_input("简要描述", value=service.get("description", ""), key=f"mf_service_desc_{index}")
            if st.button("删除学术服务", key=f"mf_del_service_{index}"):
                services.pop(index)
                st.rerun()

    st.markdown("---")
    st.markdown("### 推荐人")
    references = form_data.setdefault("references", [])
    if st.button("添加推荐人", key="mf_btn_add_reference"):
        references.append({"name": "", "title": "", "email": "", "phone": ""})
        st.rerun()
    for index, ref in enumerate(references):
        with st.expander(f"推荐人 #{index + 1}: {ref.get('name') or '未命名'}", expanded=False):
            c1, c2 = st.columns(2)
            ref["name"] = c1.text_input("姓名", value=ref.get("name", ""), key=f"mf_ref_name_{index}")
            ref["title"] = c2.text_input("头衔/职位", value=ref.get("title", ""), key=f"mf_ref_title_{index}")
            c3, c4 = st.columns(2)
            ref["email"] = c3.text_input("邮箱", value=ref.get("email", ""), key=f"mf_ref_email_{index}")
            ref["phone"] = c4.text_input("电话", value=ref.get("phone", ""), key=f"mf_ref_phone_{index}")
            if st.button("删除推荐人", key=f"mf_del_ref_{index}"):
                references.pop(index)
                st.rerun()


def render_manual_form_actions(form_data):
    export_data = normalize_manual_form(form_data)
    st.session_state["form_data"] = export_data
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"{form_data.get('name', 'resume').replace(' ', '_')}_resume.json"

    st.download_button(
        label="生成并下载 JSON",
        data=json_str,
        file_name=filename,
        mime="application/json",
        key="mf_download_btn",
        type="primary",
        use_container_width=True,
    )
    if st.button("使用当前表单作为简历输入", key="mf_use_current_form", use_container_width=True):
        form_resume_path = os.path.join(_ensure_upload_dir(), filename)
        with open(form_resume_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        st.session_state["resume_source"] = form_resume_path
        st.session_state["resume_type"] = "upload"
        st.success(f"已保存并设为本次简历输入：{form_resume_path}")
    if st.button("预览当前数据", key="mf_preview_btn", use_container_width=True):
        st.json(export_data)


def render_manual_resume_form():
    st.markdown("> 你可以直接把表单保存为本次输入，也可以先下载 JSON 以后复用。")
    form_data = st.session_state.manual_resume_form
    with st.container(border=True):
        st.markdown("#### 基础信息")
        render_personal_section(form_data)
    with st.container(border=True):
        st.markdown("#### 教育背景")
        render_education_section(form_data)
    with st.container(border=True):
        st.markdown("#### 工作经历")
        render_work_section(form_data)
    with st.container(border=True):
        st.markdown("#### 项目经历")
        render_project_section(form_data)
    with st.container(border=True):
        st.markdown("#### 技能与其他经历")
        render_skill_section(form_data)
        render_social_and_awards_section(form_data)
    with st.container(border=True):
        st.markdown("#### 学术信息")
        render_academic_section(form_data)
    st.divider()
    render_manual_form_actions(form_data)


def render_completion_status(jd_url: str, jd_text: str, uploaded_resume) -> None:
    st.divider()
    jd_ok = bool(jd_url or (jd_text and len(jd_text) > 50))
    resume_ok = bool(uploaded_resume) or st.session_state.get("resume_type") == "upload"
    c1, c2 = st.columns(2)
    if jd_ok:
        c1.success("JD 已准备完成")
    else:
        c1.warning("请补充 JD")
    if resume_ok:
        c2.success("简历输入已准备完成")
    else:
        c2.warning("请上传简历或完成表单")
