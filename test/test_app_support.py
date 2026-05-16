import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from wbq.schemas.job_details_schema import JobDetails
from wbq.schemas.sections_schemas import ResumeSchema
from wbq.utils.app_support import (
    DEMO_JOB_TEXT,
    DEMO_RESUME_DATA,
    ensure_demo_resume_file,
    friendly_error_message,
    keyword_coverage,
    normalize_manual_form,
    resume_data_to_form,
    resume_quality_checks,
    score_interpretations,
    compare_resume_keywords,
)
from wbq.utils.db_manager import ResumeDB
from wbq.utils.latex_ops import render_resume_tex
from wbq.utils.path_manager import AppPathManager
from wbq.utils.data_extraction import extract_text_from_pdf
from wbq.utils.utils import job_doc_name, read_json, write_json
from wbq.utils.validation import (
    ModelOutputValidationError,
    extract_section_payload,
    validate_job_details_payload,
    validate_resume_payload,
)


class AppSupportTest(unittest.TestCase):
    def test_demo_resume_matches_schema(self):
        ResumeSchema(**DEMO_RESUME_DATA)
        self.assertIn("Spring Boot", DEMO_JOB_TEXT)

    def test_job_schema_accepts_demo_like_payload(self):
        payload = {
            "job_title": "Java 后端开发工程师",
            "job_purpose": "建设稳定的业务系统",
            "keywords": ["Java", "Spring Boot", "MySQL"],
            "job_duties_and_responsibilities": ["开发后端接口"],
            "required_qualifications": ["熟悉 Java"],
            "preferred_qualifications": ["了解 Docker"],
            "company_name": "星河智联科技有限公司",
            "company_details": "技术驱动型公司",
        }
        job = JobDetails(**payload)
        self.assertEqual(job.company_name, "星河智联科技有限公司")

    def test_json_io_and_demo_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = os.path.join(tmp_dir, "resume.json")
            write_json(target, DEMO_RESUME_DATA)
            self.assertEqual(read_json(target)["personal"]["name"], "张明")

            demo_path = ensure_demo_resume_file(tmp_dir)
            self.assertTrue(os.path.exists(demo_path))
            self.assertEqual(read_json(demo_path)["personal"]["email"], "zhangming@example.com")

    def test_file_naming_is_user_isolated(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            job_details = {"company_name": "星河智联", "job_title": "Java 后端开发工程师"}
            path = job_doc_name(job_details, tmp_dir, "resume", user_id="42", timestamp="123")
            self.assertIn("42", path)
            self.assertIn("123", path)
            self.assertTrue(path.endswith("_resume.json"))

            manager = AppPathManager(project_root=tmp_dir)
            jd_path = manager.job_document_path(job_details, "jd", user_id="42", timestamp="123")
            self.assertTrue(jd_path.endswith("_JD.json"))
            self.assertTrue(os.path.isdir(os.path.dirname(jd_path)))

    def test_quality_and_keyword_coverage(self):
        resume = normalize_manual_form(DEMO_RESUME_DATA)
        job = {"keywords": ["Java", "Spring Boot", "Redis", "Kubernetes"]}
        coverage = keyword_coverage(resume, job)
        self.assertTrue(any(row["关键词"] == "Java" and row["是否覆盖"] == "已覆盖" for row in coverage))
        self.assertTrue(any(row["关键词"] == "Kubernetes" and row["是否覆盖"] == "待补充" for row in coverage))

        checks = resume_quality_checks(resume, job)
        check_names = {row["检查项"] for row in checks}
        self.assertGreaterEqual(len(check_names & {"教育背景", "项目经历", "岗位关键词覆盖"}), 3)
        self.assertIn("动词强度", check_names)

    def test_score_and_comparison_helpers(self):
        rows = score_interpretations({"人岗匹配度": 0.8, "原始匹配度": 0.3})
        self.assertEqual(rows[0]["指标"], "人岗匹配度")
        self.assertIn("表现较好", rows[0]["建议"])

        original = {"projects": [{"description": ["使用 Java 开发系统"]}]}
        optimized = {"projects": [{"description": ["使用 Java、Redis 和 Docker 开发系统"]}]}
        job = {"keywords": ["Java", "Redis", "Docker", "Kubernetes"]}
        summary = compare_resume_keywords(original, optimized, job)
        self.assertEqual(summary["新增关键词"], ["Redis", "Docker"])
        self.assertEqual(summary["仍待补充"], ["Kubernetes"])

    def test_resume_data_to_form_flattens_personal(self):
        form = resume_data_to_form(DEMO_RESUME_DATA)
        self.assertEqual(form["name"], "张明")
        self.assertNotIn("personal", form)

    def test_friendly_errors_are_specific(self):
        self.assertIn("API Key", friendly_error_message("openai invalid api key", "模型调用"))
        self.assertIn("PDF", friendly_error_message("xelatex not found", "生成简历"))
        self.assertIn("JSON", friendly_error_message("json parse failed", "章节优化"))
        self.assertIn("文件路径", friendly_error_message("No such file", "读取文件"))
        self.assertIn("Ollama", friendly_error_message("Error in Ollama Model - qwen2.5:1.5b, (status code: 502)", "生成流程"))

    def test_db_delete_resume_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = ResumeDB(os.path.join(tmp_dir, "resume_system.db"))
            user_id = db.create_user("demo")
            record_id = db.save_resume_record(
                user_id=user_id,
                source_path="source.json",
                original_resume_path="source.json",
                form_data=DEMO_RESUME_DATA,
                optimized_data=DEMO_RESUME_DATA,
                pdf_path="resume.pdf",
                cv_path="cv.pdf",
                raw_resume_path="raw.pdf",
                cv_content="cover letter",
                style="classic",
                optimized_fields=["projects"],
            )
            self.assertTrue(db.delete_resume_record(record_id, user_id))
            self.assertIsNone(db.load_resume_data(record_id))

    def test_db_migrates_old_resume_history_table(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "old_resume_system.db")
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL)")
            conn.execute(
                "CREATE TABLE resume_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.commit()
            conn.close()

            db = ResumeDB(db_path)
            user_id = db.create_user("legacy")
            record_id = db.save_resume_record(
                user_id=user_id,
                source_path="source.json",
                original_resume_path="source.json",
                form_data=DEMO_RESUME_DATA,
                optimized_data=DEMO_RESUME_DATA,
                pdf_path="resume.pdf",
                cv_path="cv.pdf",
                raw_resume_path="raw.pdf",
                cv_content="cover letter",
                style="minimal",
                optimized_fields=["projects"],
            )
            data = db.load_resume_data(record_id)
            self.assertEqual(data["template_style"], "minimal")
            self.assertEqual(data["raw_resume_path"], "raw.pdf")

    def test_admin_db_helpers(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = ResumeDB(os.path.join(tmp_dir, "admin_resume_system.db"))
            user_id = db.create_user("admin-demo")
            db.save_resume_record(
                user_id=user_id,
                source_path="source.json",
                original_resume_path="source.json",
                form_data=DEMO_RESUME_DATA,
                optimized_data=DEMO_RESUME_DATA,
                pdf_path="resume.pdf",
                cv_path="cv.pdf",
                raw_resume_path="raw.pdf",
                cv_content="cover letter",
                style="classic",
                optimized_fields=["projects"],
                provider_name="Qwen",
                model_name="qwen-max",
            )
            users = db.get_all_users_overview()
            self.assertEqual(users[0]["record_count"], 1)
            records = db.get_all_resume_records()
            self.assertEqual(records[0]["provider_name"], "Qwen")
            self.assertTrue(db.update_username(user_id, "admin-demo-2"))
            self.assertTrue(db.delete_user(user_id))

    def test_new_resume_records_use_shanghai_local_time(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = ResumeDB(os.path.join(tmp_dir, "tz_resume_system.db"))
            user_id = db.create_user("tz-demo")
            record_id = db.save_resume_record(
                user_id=user_id,
                source_path="source.json",
                original_resume_path="source.json",
                form_data=DEMO_RESUME_DATA,
                optimized_data=DEMO_RESUME_DATA,
                pdf_path="resume.pdf",
                cv_path="cv.pdf",
                raw_resume_path="raw.pdf",
                cv_content="cover letter",
                style="classic",
                optimized_fields=["projects"],
            )
            history = db.get_user_history(user_id, limit=1)
            self.assertEqual(history[0]["id"], record_id)
            created_at = datetime.strptime(history[0]["time"], "%Y-%m-%d %H:%M:%S")
            now_shanghai = datetime.now(ZoneInfo("Asia/Shanghai"))
            delta_seconds = abs((now_shanghai.replace(tzinfo=None) - created_at).total_seconds())
            self.assertLess(delta_seconds, 120)

    def test_backfill_missing_model_metadata(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = ResumeDB(os.path.join(tmp_dir, "backfill_resume_system.db"))
            user_id = db.create_user("legacy-user")
            db.save_resume_record(
                user_id=user_id,
                source_path="source.json",
                original_resume_path="source.json",
                form_data=DEMO_RESUME_DATA,
                optimized_data=DEMO_RESUME_DATA,
                pdf_path="resume.pdf",
                cv_path="cv.pdf",
                raw_resume_path="raw.pdf",
                cv_content="cover letter",
                style="classic",
                optimized_fields=["projects"],
                provider_name="",
                model_name="",
            )
            updated = db.backfill_missing_model_metadata()
            self.assertGreaterEqual(updated, 1)
            records = db.get_all_resume_records()
            self.assertTrue(records[0]["provider_name"])
            self.assertTrue(records[0]["model_name"])

    def test_validation_helpers(self):
        payload = {
            "job_title": "Java Developer",
            "job_purpose": "Build backend services",
            "keywords": ["Java", "Spring Boot"],
            "job_duties_and_responsibilities": ["Develop APIs"],
            "required_qualifications": ["Java"],
            "preferred_qualifications": ["Docker"],
            "company_name": "Demo Inc",
            "company_details": "Technology company",
        }
        self.assertEqual(validate_job_details_payload(payload)["job_title"], "Java Developer")
        with self.assertRaises(ModelOutputValidationError):
            validate_job_details_payload({"job_title": "missing fields"})

        resume = validate_resume_payload({"name": "Demo User"})
        self.assertEqual(resume["personal"]["name"], "Demo User")
        self.assertEqual(resume["projects"], [])

    def test_extract_section_payload_falls_back(self):
        fallback = [{"name": "Original", "description": ["kept"]}]
        data, analysis = extract_section_payload({"wrong_key": []}, "projects", fallback)
        self.assertEqual(data, fallback)
        self.assertTrue(analysis["fallback"])

        data, analysis = extract_section_payload(
            {"projects": [{"name": "Optimized"}], "analysis": {"keywords_matched": ["Java"]}},
            "projects",
            fallback,
        )
        self.assertEqual(data[0]["name"], "Optimized")
        self.assertEqual(analysis["keywords_matched"], ["Java"])

    def test_all_resume_templates_render_tex(self):
        templates = [
            "resume_classic.tex.jinja",
            "resume_creative.tex.jinja",
            "resume_academic.tex.jinja",
            "resume_minimal.tex.jinja",
        ]
        for template in templates:
            with self.subTest(template=template):
                tex = render_resume_tex(DEMO_RESUME_DATA, template_name=template)
                self.assertIsInstance(tex, str)
                self.assertIn("\\documentclass", tex)
                self.assertIn("张明", tex)

    def test_pdf_text_extraction(self):
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, "demo.pdf")
            c = canvas.Canvas(pdf_path)
            c.drawString(72, 720, "Job LLM Resume Demo")
            c.save()

            text = extract_text_from_pdf(pdf_path)
            self.assertIn("Job LLM Resume Demo", text)


if __name__ == "__main__":
    unittest.main()
