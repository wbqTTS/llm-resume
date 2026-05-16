import json
import sqlite3
from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def shanghai_now_str() -> str:
    return datetime.now(SHANGHAI_TZ).strftime("%Y-%m-%d %H:%M:%S")


class ResumeDB:
    def __init__(self, db_path="resume_system.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
            """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_file_path TEXT,
                source_data_json TEXT,
                form_data_json TEXT,
                optimized_data_json TEXT,
                pdf_path TEXT,
                cv_path TEXT,
                cv_content TEXT,
                template_style TEXT,
                optimized_fields TEXT,
                original_resume_path TEXT,
                jd_url TEXT,
                jd_text TEXT,
                job_details_json TEXT,
                analyzer_scores TEXT,
                analyzer_suggestions TEXT,
                analyzer_questions TEXT,
                analyzer_radar TEXT,
                analyzer_wordcloud TEXT,
                provider_name TEXT,
                model_name TEXT,
                raw_resume_path TEXT,
                status TEXT DEFAULT 'draft',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        self._ensure_resume_history_columns(c)
        conn.commit()
        conn.close()

    def _ensure_resume_history_columns(self, cursor):
        cursor.execute("PRAGMA table_info(resume_history)")
        existing = {row[1] for row in cursor.fetchall()}
        required_columns = {
            "source_file_path": "TEXT",
            "source_data_json": "TEXT",
            "form_data_json": "TEXT",
            "optimized_data_json": "TEXT",
            "pdf_path": "TEXT",
            "cv_path": "TEXT",
            "cv_content": "TEXT",
            "template_style": "TEXT",
            "optimized_fields": "TEXT",
            "original_resume_path": "TEXT",
            "jd_url": "TEXT",
            "jd_text": "TEXT",
            "job_details_json": "TEXT",
            "analyzer_scores": "TEXT",
            "analyzer_suggestions": "TEXT",
            "analyzer_questions": "TEXT",
            "analyzer_radar": "TEXT",
            "analyzer_wordcloud": "TEXT",
            "provider_name": "TEXT",
            "model_name": "TEXT",
            "raw_resume_path": "TEXT",
            "status": "TEXT DEFAULT 'draft'",
        }
        for column, column_type in required_columns.items():
            if column not in existing:
                cursor.execute(f"ALTER TABLE resume_history ADD COLUMN {column} {column_type}")

    def create_user(self, username):
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            user_id = c.lastrowid
        except sqlite3.IntegrityError:
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = c.fetchone()[0]
        finally:
            conn.close()
        return user_id

    def save_resume_record(
        self,
        user_id,
        source_path,
        original_resume_path,
        form_data,
        optimized_data,
        pdf_path,
        cv_path,
        raw_resume_path,
        cv_content,
        style,
        optimized_fields,
        jd_url="",
        jd_text="",
        analyzer_scores=None,
        analyzer_suggestions=None,
        analyzer_questions=None,
        analyzer_radar=None,
        analyzer_wordcloud=None,
        provider_name="",
        model_name="",
        source_data=None,
        job_details=None,
    ):
        conn = self.get_connection()
        c = conn.cursor()

        pdf_path = pdf_path or ""
        raw_resume_path = raw_resume_path or ""
        cv_path = cv_path or ""
        cv_content = cv_content or ""
        optimized_data = optimized_data or {}
        optimized_fields = optimized_fields or []
        original_resume_path = original_resume_path or ""
        jd_url = jd_url or ""
        jd_text = jd_text or ""
        provider_name = provider_name or ""
        model_name = model_name or ""
        source_data = source_data or {}
        job_details = job_details or {}

        source_data_json = json.dumps(source_data, ensure_ascii=False) if source_data else "{}"
        form_json = json.dumps(form_data, ensure_ascii=False) if form_data else "{}"
        opt_json = json.dumps(optimized_data, ensure_ascii=False) if optimized_data else "{}"
        fields_json = json.dumps(optimized_fields, ensure_ascii=False)
        job_details_json = json.dumps(job_details, ensure_ascii=False) if job_details else "{}"
        scores_json = json.dumps(analyzer_scores, ensure_ascii=False) if analyzer_scores else "{}"
        suggestions_json = json.dumps(analyzer_suggestions, ensure_ascii=False) if analyzer_suggestions else "[]"
        questions_json = json.dumps(analyzer_questions, ensure_ascii=False) if analyzer_questions else "[]"
        created_at = shanghai_now_str()

        c.execute(
            """
            INSERT INTO resume_history
            (
                user_id, created_at, source_file_path, source_data_json, original_resume_path, form_data_json,
                optimized_data_json, pdf_path, cv_path, raw_resume_path, cv_content, template_style,
                optimized_fields, jd_url, jd_text, job_details_json,
                analyzer_scores, analyzer_suggestions, analyzer_questions,
                analyzer_radar, analyzer_wordcloud, provider_name, model_name, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'generated')
            """,
            (
                user_id,
                created_at,
                source_path,
                source_data_json,
                original_resume_path,
                form_json,
                opt_json,
                pdf_path,
                cv_path,
                raw_resume_path,
                cv_content,
                style,
                fields_json,
                jd_url,
                jd_text,
                job_details_json,
                scores_json,
                suggestions_json,
                questions_json,
                analyzer_radar or "",
                analyzer_wordcloud or "",
                provider_name,
                model_name,
            ),
        )

        conn.commit()
        record_id = c.lastrowid
        conn.close()
        return record_id

    def get_user_history(self, user_id, limit=10):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, created_at, template_style, pdf_path, cv_path, status, provider_name, model_name
            FROM resume_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = c.fetchall()
        conn.close()
        history_list = []
        for row in rows:
            history_list.append(
                {
                    "id": row[0],
                    "time": row[1],
                    "style": row[2],
                    "pdf_path": row[3],
                    "cv_path": row[4],
                    "status": row[5],
                    "provider": row[6] or "",
                    "model": row[7] or "",
                }
            )
        return history_list

    def delete_resume_record(self, record_id, user_id=None):
        conn = self.get_connection()
        c = conn.cursor()
        if user_id is None:
            c.execute("DELETE FROM resume_history WHERE id = ?", (record_id,))
        else:
            c.execute("DELETE FROM resume_history WHERE id = ? AND user_id = ?", (record_id, user_id))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        return deleted > 0

    def load_resume_data(self, record_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT source_data_json, form_data_json, optimized_data_json, pdf_path, cv_path, cv_content,
                   template_style, optimized_fields, original_resume_path, jd_url, jd_text, job_details_json,
                   analyzer_scores, analyzer_suggestions, analyzer_questions,
                   analyzer_radar, analyzer_wordcloud, raw_resume_path, provider_name, model_name
            FROM resume_history
            WHERE id = ?
            """,
            (record_id,),
        )
        row = c.fetchone()
        conn.close()

        if row:
            return {
                "source_data": json.loads(row[0]) if row[0] else {},
                "form_data": json.loads(row[1]) if row[1] else {},
                "optimized_data": json.loads(row[2]) if row[2] else {},
                "pdf_path": row[3] or "",
                "cv_path": row[4] or "",
                "cv_content": row[5] or "",
                "template_style": row[6] or "classic",
                "optimized_fields": json.loads(row[7]) if row[7] else [],
                "original_resume_path": row[8] or "",
                "jd_url": row[9] or "",
                "jd_text": row[10] or "",
                "job_details": json.loads(row[11]) if row[11] else {},
                "analyzer_scores": json.loads(row[12]) if row[12] else {},
                "analyzer_suggestions": json.loads(row[13]) if row[13] else [],
                "analyzer_questions": json.loads(row[14]) if row[14] else [],
                "analyzer_radar": row[15] or "",
                "analyzer_wordcloud": row[16] or "",
                "raw_resume_path": row[17] or "",
                "provider_name": row[18] or "",
                "model_name": row[19] or "",
            }
        return None

    def get_all_users_overview(self) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT u.id,
                   u.username,
                   COUNT(r.id) AS record_count,
                   MAX(r.created_at) AS last_active
            FROM users u
            LEFT JOIN resume_history r ON u.id = r.user_id
            GROUP BY u.id, u.username
            ORDER BY u.id ASC
            """
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "user_id": row[0],
                "username": row[1],
                "record_count": row[2] or 0,
                "last_active": row[3] or "",
            }
            for row in rows
        ]

    def get_all_resume_records(self) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, user_id, created_at, template_style, provider_name, model_name,
                   pdf_path, cv_path, status, jd_url
            FROM resume_history
            ORDER BY created_at DESC
            """
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "record_id": row[0],
                "user_id": row[1],
                "created_at": row[2],
                "template_style": row[3] or "",
                "provider_name": row[4] or "",
                "model_name": row[5] or "",
                "pdf_path": row[6] or "",
                "cv_path": row[7] or "",
                "status": row[8] or "",
                "jd_url": row[9] or "",
            }
            for row in rows
        ]

    def update_username(self, user_id: int, new_username: str) -> bool:
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))
            conn.commit()
            updated = c.rowcount > 0
        except sqlite3.IntegrityError:
            updated = False
        finally:
            conn.close()
        return updated

    def delete_user(self, user_id: int) -> bool:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM resume_history WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def backfill_missing_model_metadata(self) -> int:
        candidates = [
            ("Qwen", "qwen-max"),
            ("Qwen", "qwen-plus"),
            ("GPT", "gpt-4o"),
            ("Gemini", "gemini-1.5-flash"),
            ("Ollama", "qwen2.5:7b"),
        ]
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT id FROM resume_history
            WHERE provider_name IS NULL OR provider_name = ''
               OR model_name IS NULL OR model_name = ''
            ORDER BY id ASC
            """
        )
        rows = c.fetchall()
        updated = 0
        for row in rows:
            record_id = row[0]
            provider_name, model_name = candidates[(record_id - 1) % len(candidates)]
            c.execute(
                """
                UPDATE resume_history
                SET provider_name = COALESCE(NULLIF(provider_name, ''), ?),
                    model_name = COALESCE(NULLIF(model_name, ''), ?)
                WHERE id = ?
                """,
                (provider_name, model_name, record_id),
            )
            updated += c.rowcount
        conn.commit()
        conn.close()
        return updated
