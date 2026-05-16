import os
import json
import logging
import validators
import streamlit as st

import concurrent.futures
from wbq.utils.retriever import  chunk_section_data, retrieve_relevant_chunks, format_rag_context
from wbq.schemas.sections_schemas import ResumeSchema
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from wbq.utils import utils
from wbq.utils.latex_ops import json_to_latex_to_pdf
from wbq.utils.llm_models import ChatGPT, Gemini, OllamaModel, QwenModel
from wbq.utils.data_extraction import read_data_from_url, extract_text_from_pdf
from wbq.utils.validation import (
    extract_section_payload,
    validate_job_details_payload,
    validate_resume_payload,
)
from wbq.prompts.sections_prompt import (
    EDUCATION, EXPERIENCE, PROJECTS, SKILLS, SOCIAL_PRACTICE, RESEARCH_EXPERIENCE, TEACHING_EXPERIENCE, ACADEMIC_SERVICE
)
from wbq.prompts.resume_prompt import (
    CV_GENERATOR, RESUME_WRITER_PERSONA, JOB_DETAILS_EXTRACTOR, RESUME_DETAILS_EXTRACTOR
)

from wbq.schemas.job_details_schema import JobDetails
from wbq.variables import DEFAULT_LLM_MODEL, DEFAULT_LLM_PROVIDER, LLM_MAPPING, section_mapping

module_dir = os.path.dirname(__file__)
demo_data_path = os.path.join(module_dir, "demo_data", "user_profile.json")
prompt_path = os.path.join(module_dir, "prompts")
logger = logging.getLogger(__name__)


class AutoApplyModel:
    """
    A class that represents an Auto Apply Model for job applications.

    Args:
        api_key (str): The OpenAI API key.
        downloads_dir (str, optional): The directory to save downloaded files. Defaults to the default download folder.
        provider (str, optional): The LLM provider to use. Defaults to "Gemini".
        model (str, optional): The LLM model to use. Defaults to "gemini-1.5-flash-latest".

    Methods:
        get_prompt(system_prompt_path: str) -> str: Returns the system prompt from the specified path.
        resume_to_json(pdf_path: str) -> dict: Extracts resume details from the specified PDF path.
        user_data_extraction(user_data_path: str) -> dict: Extracts user data from the specified path.
        job_details_extraction(url: str) -> dict: Extracts job details from the specified job URL.
        resume_builder(job_details: dict, user_data: dict) -> dict: Generates a resume based on job details and user data.
        cover_letter_generator(job_details: dict, user_data: dict) -> str: Generates a cover letter based on job details and user data.
        resume_cv_pipeline(job_url: str, user_data_path: str) -> None: Runs the Auto Apply Pipeline.
    """

    def __init__(
        self, api_key: str = None, provider: str = None, model: str = None, downloads_dir: str = utils.get_default_download_folder(), system_prompt: str = RESUME_WRITER_PERSONA
    ):
        self.system_prompt = system_prompt
        self.provider = DEFAULT_LLM_PROVIDER if provider is None or provider.strip() == "" else provider
        self.model = DEFAULT_LLM_MODEL if model is None or model.strip() == "" else model
        self.downloads_dir = utils.get_default_download_folder() if downloads_dir is None or downloads_dir.strip() == "" else downloads_dir

        if api_key is None or api_key.strip() == "os":
                api_env = LLM_MAPPING[self.provider]["api_env"]
                if api_env != None and api_env.strip() != "":
                    self.api_key = os.environ.get(LLM_MAPPING[self.provider]["api_env"])
                else:
                    self.api_key = None
        else:
            self.api_key = api_key

        self.llm = self.get_llm_instance()

    def get_llm_instance(self):
        if self.provider == "Qwen":
            return QwenModel(api_key=self.api_key, model=self.model, system_prompt=self.system_prompt)
        elif self.provider == "GPT":
            return ChatGPT(api_key=self.api_key, model=self.model, system_prompt=self.system_prompt)
        elif self.provider == "Gemini":
            return Gemini(api_key=self.api_key, model=self.model, system_prompt=self.system_prompt)
        elif self.provider == "Ollama":
            return OllamaModel(model=self.model, system_prompt=self.system_prompt)
        else:
            raise Exception("Invalid LLM Provider")


    @utils.measure_execution_time
    def resume_to_json(self, pdf_path):
        """
        Converts a resume in PDF format to JSON format.

        Args:
            pdf_path (str): The path to the PDF file.

        Returns:
            dict: The resume data in JSON format.
        """
        resume_text = extract_text_from_pdf(pdf_path)

        json_parser = JsonOutputParser(pydantic_object=ResumeSchema)

        prompt = PromptTemplate(
            template=RESUME_DETAILS_EXTRACTOR,
            input_variables=["resume_text"],
            partial_variables={"format_instructions": json_parser.get_format_instructions()}
            ).format(resume_text=resume_text)

        resume_json = self.llm.get_response(prompt=prompt, need_json_output=True)
        return resume_json

    @utils.measure_execution_time
    def user_data_extraction(self, user_data_path: str = demo_data_path, is_st=False):
        """
        Extracts user data from the given file path.

        Args:
            user_data_path (str): The path to the user data file.

        Returns:
            dict: The extracted user data in JSON format.
        """
        if user_data_path is None or (type(user_data_path) is str and user_data_path.strip() == ""):
            user_data_path = demo_data_path

        extension = os.path.splitext(user_data_path)[1]

        if extension == ".pdf":
            user_data = self.resume_to_json(user_data_path)
        elif extension == ".json":
            user_data = utils.read_json(user_data_path)
        elif validators.url(user_data_path):
            user_data = read_data_from_url([user_data_path])
            pass
        else:
            raise Exception("Invalid file format. Please provide a PDF, JSON file or url.")

        if isinstance(user_data, dict):
            return validate_resume_payload(user_data)

        return user_data


    @utils.measure_execution_time
    def job_details_extraction(self, url: str = None, job_site_content: str = None, is_st=False, user_id: str = None):
        """
        Extracts job details from the specified job URL.

        Args:
            url (str): The URL of the job posting.
            job_site_content (str): The content of the job posting.
            is_st (bool): Whether running in Streamlit.
            user_id (str): User ID for file isolation.

        Returns:
            dict: A dictionary containing the extracted job details.
        """
        try:
            if url is not None and url.strip() != "":
                job_site_content = read_data_from_url(url)
            if job_site_content:
                json_parser = JsonOutputParser(pydantic_object=JobDetails)

                prompt = PromptTemplate(
                    template=JOB_DETAILS_EXTRACTOR,
                    input_variables=["job_description"],
                    partial_variables={"format_instructions": json_parser.get_format_instructions()}
                ).format(job_description=job_site_content)

                job_details = validate_job_details_payload(
                    self.llm.get_response(prompt=prompt, need_json_output=True)
                )

                job_details_to_save = dict(job_details)
                if url is not None and url.strip() != "":
                    job_details_to_save["url"] = url

                # 生成时间戳
                import time
                timestamp = str(int(time.time()))

                # 生成 JD 文件路径（传入 user_id 和 timestamp）
                jd_path = utils.job_doc_name(job_details_to_save, self.downloads_dir, "jd", user_id=user_id,
                                             timestamp=timestamp)

                utils.write_json(jd_path, job_details_to_save)

                return job_details, jd_path
            else:
                raise Exception("Unable to web scrape the job description.")

        except Exception as e:
            if is_st:
                st.error(f"JD 解析失败：{e}")
                return None, None
            raise

    @utils.measure_execution_time
    def cover_letter_generator(self, job_details: dict, user_data: dict, need_pdf: bool = True, is_st=False,
                               user_id: str = None):
        """
        Generates a cover letter based on the provided job details and user data.

        Args:
            job_details (dict): A dictionary containing the job description.
            user_data (dict): A dictionary containing the user's resume or work information.
            need_pdf (bool): Whether to generate PDF.
            is_st (bool): Whether running in Streamlit.
            user_id (str): User ID for file isolation.

        Returns:
            str: The generated cover letter.
        """
        try:
            prompt = PromptTemplate(
                template=CV_GENERATOR,
                input_variables=["my_work_information", "job_description"],
            ).format(job_description=job_details, my_work_information=user_data)

            cover_letter = self.llm.get_response(prompt=prompt, expecting_longer_output=True)
            if not cover_letter:
                raise ValueError("求职信生成为空。")

            # 生成时间戳
            import time
            timestamp = str(int(time.time()))

            # 生成求职信文件路径（传入 user_id 和 timestamp）
            cv_path = utils.job_doc_name(job_details, self.downloads_dir, "cv", user_id=user_id, timestamp=timestamp)
            utils.write_file(cv_path, cover_letter)

            if need_pdf:
                pdf_path = cv_path.replace(".txt", ".pdf")
                utils.text_to_pdf(cover_letter, pdf_path)
                return cover_letter, pdf_path

            return cover_letter, cv_path.replace(".txt", ".pdf")
        except Exception as e:
            if is_st:
                st.error(f"求职信生成失败：{e}")
            return None, None

    @utils.measure_execution_time
    def resume_builder(self, job_details: dict, user_data: dict, template_style='classic', is_st=False,
                       optimize_fields: list = None, user_id: str = None, section_callback=None):
        """
        生成简历的核心逻辑 (集成 RAG + CoT + 并发优化)

        Args:
            optimize_fields (list): 需要优化的字段列表 (如 ['work_experience', 'projects']).
                                    如果为 None 或空，则默认优化所有配置的章节。
                                    不在列表中的字段将直接保留原始数据。
            user_id (str): User ID for file isolation.
        """
        # --- 风格映射 ---
        style_map = {
            'classic': 'resume_classic.tex.jinja',
            'creative': 'resume_creative.tex.jinja',
            'academic': 'resume_academic.tex.jinja',
            'minimal': 'resume_minimal.tex.jinja'
        }
        selected_template = style_map.get(template_style, 'resume_classic.tex.jinja')
        logger.info("当前选择风格：%s -> 使用模板：%s", template_style, selected_template)

        # 处理 optimize_fields 参数
        should_optimize_all = (optimize_fields is None or len(optimize_fields) == 0)
        if not should_optimize_all:
            logger.info("用户指定优化范围: %s", optimize_fields)

        resume_path = None
        resume_details = {}

        try:
            logger.info("Generating Resume Details (RAG + CoT Mode)")
            if is_st: st.toast("正在智能分析并生成简历...")

            resume_details = dict()

            # ===== 个人信息部分：直接使用用户输入，不经过LLM =====
            if is_st: st.toast("Processing Resume's Personal Info Section...")

            personal_data = user_data.get("personal", {})

            # 图片路径处理逻辑
            original_photo = personal_data.get("photo", "")
            if original_photo:
                import os
                exists = os.path.exists(original_photo)
                if not exists:
                    cwd = os.getcwd()
                    basename = os.path.basename(original_photo)
                    local_path = os.path.join(cwd, basename)
                    if os.path.exists(local_path):
                        original_photo = local_path
                    else:
                        output_dir = os.path.join(cwd, "output", "技术研发部")
                        local_path_output = os.path.join(output_dir, basename)
                        if os.path.exists(local_path_output):
                            original_photo = local_path_output

            # 将所有字段合并到 personal 对象中
            resume_details["personal"] = {
                "name": personal_data.get("name", ""),
                "birthdate": personal_data.get("birthdate", ""),
                "phone": personal_data.get("phone", ""),
                "politics": personal_data.get("politics", ""),
                "email": personal_data.get("email", ""),
                "hometown": personal_data.get("hometown", ""),
                "photo": original_photo,
                "title": personal_data.get("title", ""),
                "summary": personal_data.get("summary", ""),
                "media": personal_data.get("media", {})
            }

            # ===== 直接保留的顶层字段（不经过 LLM 优化）=====
            resume_details["certifications"] = user_data.get("certifications", [])
            resume_details["achievements"] = user_data.get("achievements", [])

            # ===== 生成时间戳（优化版和 raw 版共用同一个时间戳）=====
            import time
            timestamp = str(int(time.time()))

            # ===== 提前生成 raw 版本（原始数据，不经过 LLM 优化）=====
            # 构建 raw 版本数据
            raw_resume_details = {
                "personal": resume_details.get("personal", {}),
                "education": user_data.get("education", []),
                "work_experience": user_data.get("work_experience", []),
                "projects": user_data.get("projects", []),
                "skill_section": user_data.get("skill_section", []),
                "social_practice": user_data.get("social_practice", []),
                "certifications": user_data.get("certifications", []),
                "achievements": user_data.get("achievements", [])
            }

            # 生成 raw 版本 JSON 路径
            raw_json_path = utils.job_doc_name(job_details, self.downloads_dir, "resume", user_id=user_id,
                                               timestamp=timestamp)
            raw_json_path = raw_json_path.replace(".json", "_raw.json")
            utils.write_json(raw_json_path, raw_resume_details)

            # 生成 raw 版本 PDF 路径
            raw_pdf_path = raw_json_path.replace(".json", ".pdf")

            # 生成 raw 版本 PDF
            raw_latex_source = json_to_latex_to_pdf(
                json_resume=raw_resume_details,
                dst_path=raw_pdf_path,
                template_name=selected_template
            )

            if raw_latex_source and "generated_result" in st.session_state:
                st.session_state['generated_result']['raw_resume_path'] = raw_pdf_path

            # ===== 2. 定义配置 =====
            base_sections_config = [
                {"name": "education", "prompt": EDUCATION},
                {"name": "work_experience", "prompt": EXPERIENCE},
                {"name": "projects", "prompt": PROJECTS},
                {"name": "skill_section", "prompt": SKILLS},
                {"name": "social_practice", "prompt": SOCIAL_PRACTICE}
            ]

            # 学术风格特有章节配置
            academic_sections_config = [
                {"name": "research_experience", "prompt": RESEARCH_EXPERIENCE},
                {"name": "teaching_experience", "prompt": TEACHING_EXPERIENCE},
                {"name": "academic_service", "prompt": ACADEMIC_SERVICE}
            ]

            # 根据模板风格选择配置
            if template_style == 'academic':
                sections_config = base_sections_config + academic_sections_config
                logger.info("学术风格模式：已添加研究经历、教学经历、学术服务字段")
            else:
                sections_config = base_sections_config

            # ===== 3. 定义单个章节处理函数 (用于并发) =====
            def process_single_section(section_cfg):
                import json
                section_name = section_cfg["name"]
                prompt_template_str = section_cfg["prompt"]
                user_section_data = user_data.get(section_name, [])

                if not user_section_data:
                    logger.info("跳过 %s：无数据", section_name)
                    return section_name, None, None

                needs_optimization = should_optimize_all or (section_name in optimize_fields)

                if not needs_optimization:
                    logger.info("跳过 %s 的 LLM 优化：用户指定保留原始内容", section_name)
                    if section_name == "skill_section":
                        user_section_data = [s for s in user_section_data if s.get("skills")]
                    return section_name, user_section_data, {"skipped": True, "reason": "User configuration"}

                if is_st: st.toast(f"正在智能优化 {section_name}...")

                try:
                    chunks = chunk_section_data(user_section_data)

                    jd_parts = []
                    for k, v in job_details.items():
                        if isinstance(v, str):
                            jd_parts.append(f"{k}: {v}")
                        elif isinstance(v, list):
                            jd_parts.append(f"{k}: {', '.join(map(str, v))}")
                    jd_text = " | ".join(jd_parts)

                    relevant_chunks = retrieve_relevant_chunks(jd_text, chunks, top_k=3, threshold=0.15)
                    rag_context = format_rag_context(relevant_chunks)

                    section_data_json = json.dumps(user_section_data, ensure_ascii=False)
                    jd_json = json.dumps(job_details, ensure_ascii=False)

                    final_prompt = prompt_template_str.format(
                        section_data=section_data_json,
                        job_description=jd_json,
                        retrieval_context=rag_context,
                        section_key=section_name,
                        format_instructions="请严格按照 JSON 格式输出，不要包含 Markdown 标记。"
                    )

                    response = self.llm.get_response(
                        prompt=final_prompt,
                        expecting_longer_output=True,
                        need_json_output=True
                    )

                    processed_data, analysis_info = extract_section_payload(
                        response=response,
                        section_name=section_name,
                        fallback=user_section_data,
                    )

                    if response and isinstance(response, dict) and processed_data is None:
                        if section_name in response:
                            processed_data = response[section_name]
                        elif isinstance(response, list):
                            processed_data = response

                        if "analysis" in response:
                            analysis_info = response["analysis"]

                        if section_name == "skill_section" and processed_data:
                            processed_data = [s for s in processed_data if s.get("skills")]

                    if processed_data is None:
                        logger.warning("%s 优化失败，回退到原始数据。", section_name)
                        processed_data = user_section_data
                        analysis_info = {"error": "LLM output parsing failed", "fallback": True}

                    return section_name, processed_data, analysis_info

                except Exception as e:
                    logger.warning("Error processing %s: %s", section_name, e)
                    return section_name, user_section_data, {"error": str(e), "fallback": True}

            # ===== 4. 并发执行所有章节 =====
            resume_sections = {}
            all_analysis = {}

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_section = {executor.submit(process_single_section, cfg): cfg for cfg in sections_config}

                for future in concurrent.futures.as_completed(future_to_section):
                    section_name, data, analysis = future.result()

                    if data is not None:
                        resume_sections[section_name] = data
                        if analysis:
                            all_analysis[section_name] = analysis

                        if section_callback:
                            try:
                                section_callback(section_name, data, analysis)
                            except Exception as callback_error:
                                logger.warning("Error in section_callback for %s: %s", section_name, callback_error)

                        if is_st:
                            if analysis and analysis.get("skipped"):
                                st.info(f"ℹ️ **{section_name.replace('_', ' ').title()}**: 已按您的要求保留原始内容。")
                            elif analysis and not analysis.get("fallback"):
                                st.markdown(f"**✅ {section_name.replace('_', ' ').title()} 优化完成**")
                                with st.expander(f"🧠 查看 AI 优化思路 ({section_name})"):
                                    if isinstance(analysis, dict):
                                        keywords = analysis.get("keywords_matched", [])
                                        strategy = analysis.get("optimization_strategy", "")
                                        if keywords:
                                            st.write(f"**🎯 匹配关键词**: `{', '.join(keywords)}`")
                                        if strategy:
                                            st.write(f"**💡 优化策略**: {strategy}")
                                        if analysis.get("gap_analysis"):
                                            st.write(f"**⚠️ 发现差距**: {analysis.get('gap_analysis')}")
                                    else:
                                        st.write(str(analysis))
                            elif analysis and analysis.get("fallback"):
                                st.warning(
                                    f"⚠️ {section_name} 优化未生效，已保留原始数据。原因：{analysis.get('error', 'Unknown')}")

            resume_details.update(resume_sections)

            # ===== 5. 添加关键词 =====
            resume_details['keywords'] = ', '.join(job_details.get('keywords', []))

            # ===== 6. 保存与生成 PDF =====

            # 生成简历 JSON 路径（传入 user_id 和 timestamp）
            resume_json_path = utils.job_doc_name(job_details, self.downloads_dir, "resume", user_id=user_id,
                                                  timestamp=timestamp)
            utils.write_json(resume_json_path, resume_details)

            resume_pdf_path = resume_json_path.replace(".json", ".pdf")

            resume_latex_source = json_to_latex_to_pdf(
                json_resume=resume_details,
                dst_path=resume_pdf_path,
                template_name=selected_template
            )

            if not resume_latex_source:
                raise Exception("PDF 生成失败：请检查 xelatex 是否安装，以及模板字段是否完整。")

            return resume_pdf_path, resume_details

        except Exception as e:
            logger.warning("Error in resume_builder: %s", e)
            if is_st:
                st.error(f"生成失败：{str(e)}")
            return resume_path, resume_details

    def resume_cv_pipeline(self, job_url: str, user_data_path: str = demo_data_path):
        """Run the Auto Apply Pipeline.

        Args:
            job_url (str): The URL of the job to apply for.
            user_data_path (str, optional): The path to the user profile data file.
                Defaults to os.path.join(module_dir, "master_data','user_profile.json").

        Returns:
            None: The function prints the progress and results to the console.
        """
        try:
            if user_data_path is None or user_data_path.strip() == "":
                user_data_path = demo_data_path

            logger.info("Starting Auto Resume and CV Pipeline")
            if job_url is None and len(job_url.strip()) == 0:
                logger.warning("Job URL is required.")
                return

            # Extract user data
            user_data = self.user_data_extraction(user_data_path)

            # Extract job details
            job_details, jd_path = self.job_details_extraction(url=job_url)

            # Build resume
            resume_path, resume_details = self.resume_builder(job_details, user_data)

            # Generate cover letter
            cv_details, cv_path = self.cover_letter_generator(job_details, user_data)

            # Calculate metrics
            for metric in ['jaccard_similarity', 'overlap_coefficient', 'cosine_similarity']:
                logger.info("Calculating %s", metric)

                if metric == 'vector_embedding_similarity':
                    llm = self.get_llm_instance()
                    user_personlization = globals()[metric](llm, json.dumps(resume_details), json.dumps(user_data))
                    job_alignment = globals()[metric](llm, json.dumps(resume_details), json.dumps(job_details))
                    job_match = globals()[metric](llm, json.dumps(user_data), json.dumps(job_details))
                else:
                    user_personlization = globals()[metric](json.dumps(resume_details), json.dumps(user_data))
                    job_alignment = globals()[metric](json.dumps(resume_details), json.dumps(job_details))
                    job_match = globals()[metric](json.dumps(user_data), json.dumps(job_details))

                logger.info("User Personlization Score(resume,master_data): %s", user_personlization)
                logger.info("Job Alignment Score(resume,JD): %s", job_alignment)
                logger.info("Job Match Score(master_data,JD): %s", job_match)

            logger.info("Done")
            return resume_path, cv_path, jd_path

        except Exception as e:
            logger.warning("Error in resume_cv_pipeline: %s", e)
            return None, None, None
