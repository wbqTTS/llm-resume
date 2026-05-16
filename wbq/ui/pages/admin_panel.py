from __future__ import annotations

from datetime import datetime
from io import BytesIO
from textwrap import shorten

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd

from wbq.ui.app_context import *


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "job-llm-admin"

CN_USER_COLUMNS = {
    "user_id": "用户ID",
    "username": "用户名",
    "record_count": "生成记录数",
    "last_active": "最近活跃时间",
}

CN_RECORD_COLUMNS = {
    "record_id": "记录ID",
    "user_id": "用户ID",
    "created_at": "生成时间",
    "template_style": "模板风格",
    "provider_name": "模型提供商",
    "model_name": "模型名称",
    "pdf_path": "简历PDF路径",
    "cv_path": "求职信路径",
    "status": "状态",
    "jd_url": "JD链接",
}

MODEL_COLORS = ["#5B8FF9", "#61DDAA", "#65789B", "#F6BD16", "#7262FD", "#78D3F8", "#9661BC", "#F6903D"]
PIE_COLORS = ["#5B8FF9", "#5AD8A6", "#5D7092", "#F6BD16", "#E8684A", "#6DC8EC", "#9270CA", "#FF9D4D"]


def _font_prop():
    try:
        if FONT_PATH and os.path.exists(FONT_PATH):
            return fm.FontProperties(fname=FONT_PATH)
    except Exception:
        pass
    return None


def _apply_cn_axes_style(ax, title: str | None = None, xlabel: str | None = None):
    font_prop = _font_prop()
    if title:
        if font_prop:
            ax.set_title(title, fontproperties=font_prop, fontsize=12, pad=14)
        else:
            ax.set_title(title, fontsize=12, pad=14)
    if xlabel:
        if font_prop:
            ax.set_xlabel(xlabel, fontproperties=font_prop)
        else:
            ax.set_xlabel(xlabel)
    if font_prop:
        for label in ax.get_xticklabels():
            label.set_fontproperties(font_prop)
            label.set_rotation(0)
        for label in ax.get_yticklabels():
            label.set_fontproperties(font_prop)


def _bootstrap_mock_requests():
    st.session_state.setdefault(
        "admin_mock_requests",
        [
            {
                "id": 1,
                "username": "demo_user",
                "reason": "需要查看用户增长趋势并协助答辩展示。",
                "contact": "demo_user@example.com",
                "status": "待审核",
                "applied_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        ],
    )


def _users_df() -> pd.DataFrame:
    users = db.get_all_users_overview()
    return pd.DataFrame(users or [], columns=["user_id", "username", "record_count", "last_active"])


def _records_df() -> pd.DataFrame:
    db.backfill_missing_model_metadata()
    records = db.get_all_resume_records()
    return pd.DataFrame(
        records or [],
        columns=[
            "record_id",
            "user_id",
            "created_at",
            "template_style",
            "provider_name",
            "model_name",
            "pdf_path",
            "cv_path",
            "status",
            "jd_url",
        ],
    )


def _format_export_df(df: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    display_df = df.copy()
    if "created_at" in display_df.columns:
        display_df["created_at"] = display_df["created_at"].astype(str).str.replace("T", " ").str.slice(0, 19)
    if "last_active" in display_df.columns:
        display_df["last_active"] = display_df["last_active"].astype(str).str.replace("T", " ").str.slice(0, 19)
    return display_df.rename(columns=column_map)


def _render_admin_login():
    _bootstrap_mock_requests()
    st.info("管理员面板仅对系统管理员开放，请先完成身份校验。")
    login_tab, apply_tab = st.tabs(["管理员登录", "申请管理员权限"])

    with login_tab:
        left, center, right = st.columns([1, 1.3, 1])
        with center:
            st.markdown("### 管理员登录")
            username = st.text_input("管理员用户名", key="admin_username_input")
            password = st.text_input("管理员密码", type="password", key="admin_password_input")
            if st.button("进入管理员面板", type="primary", use_container_width=True):
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.admin_authenticated = True
                    st.success("管理员身份校验通过。")
                    st.rerun()
                st.error("管理员用户名或密码不正确。")

    with apply_tab:
        st.markdown("### 申请管理员权限")
        st.caption("这里做的是演示用假实现，便于在答辩时展示“申请 - 审核 - 授权”流程。")
        applicant = st.text_input("申请人用户名", value=st.session_state.get("username", ""), key="admin_apply_username")
        contact = st.text_input("联系方式", placeholder="邮箱 / 电话", key="admin_apply_contact")
        reason = st.text_area("申请原因", placeholder="说明你希望获得管理员权限的用途", key="admin_apply_reason")
        if st.button("提交管理员申请", use_container_width=True, key="admin_apply_submit"):
            if not applicant or not reason:
                st.warning("请至少填写申请人和申请原因。")
            else:
                requests = st.session_state["admin_mock_requests"]
                requests.append(
                    {
                        "id": len(requests) + 1,
                        "username": applicant,
                        "reason": reason,
                        "contact": contact,
                        "status": "待审核",
                        "applied_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                )
                st.success("申请已提交。当前为演示模式，等待管理员在授权页审批。")


def _render_admin_metrics(users_df: pd.DataFrame, records_df: pd.DataFrame):
    today = datetime.now().strftime("%Y-%m-%d")
    total_users = len(users_df.index)
    total_records = len(records_df.index)
    today_records = int(records_df["created_at"].astype(str).str.startswith(today).sum()) if not records_df.empty else 0
    active_users = (
        records_df.loc[records_df["created_at"].astype(str).str.startswith(today), "user_id"].nunique()
        if not records_df.empty
        else 0
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("用户总数", total_users)
    m2.metric("今日活跃用户", active_users)
    m3.metric("累计生成记录", total_records)
    m4.metric("今日新增记录", today_records)


def _plot_pie(counts: pd.Series, title: str):
    fig, ax = plt.subplots(figsize=(5.2, 3.8), dpi=140)
    font_prop = _font_prop()
    text_kwargs = {"fontsize": 10}
    if font_prop:
        text_kwargs["fontproperties"] = font_prop
    ax.pie(
        counts.values,
        labels=counts.index.tolist(),
        autopct="%1.0f%%",
        startangle=120,
        colors=PIE_COLORS[: len(counts)],
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
        textprops=text_kwargs,
    )
    _apply_cn_axes_style(ax, title=title)
    ax.axis("equal")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def _plot_horizontal_bar(counts: pd.Series, title: str):
    labels = [shorten(label, width=22, placeholder="...") for label in counts.index.tolist()]
    fig, ax = plt.subplots(figsize=(6.2, 4.2), dpi=140)
    colors = [MODEL_COLORS[i % len(MODEL_COLORS)] for i in range(len(labels))]
    bars = ax.barh(labels, counts.values, color=colors, edgecolor="none")
    _apply_cn_axes_style(ax, title=title, xlabel="记录数")
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.invert_yaxis()
    font_prop = _font_prop()
    for bar, value in zip(bars, counts.values):
        if font_prop:
            ax.text(
                bar.get_width() + 0.05,
                bar.get_y() + bar.get_height() / 2,
                str(int(value)),
                va="center",
                fontsize=9,
                fontproperties=font_prop,
            )
        else:
            ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2, str(int(value)), va="center", fontsize=9)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def _render_admin_charts(users_df: pd.DataFrame, records_df: pd.DataFrame):
    if records_df.empty:
        st.caption("当前还没有可统计的生成记录。")
        return

    chart_col1, chart_col2 = st.columns(2)
    records_df = records_df.copy()
    records_df["created_day"] = records_df["created_at"].astype(str).str.slice(0, 10)
    records_df["provider_model"] = records_df["provider_name"].replace("", "未记录") + " / " + records_df["model_name"].replace("", "未记录")

    with chart_col1:
        st.caption("近 14 天生成趋势")
        trend = records_df["created_day"].value_counts().sort_index().tail(14)
        st.line_chart(trend.rename("记录数"))

        st.caption("模板风格分布")
        style_counts = records_df["template_style"].replace("", "未记录").value_counts()
        _plot_pie(style_counts, "模板风格分布")

    with chart_col2:
        st.caption("模型配置分布")
        model_counts = records_df["provider_model"].value_counts().head(8)
        _plot_horizontal_bar(model_counts, "模型配置分布")

        st.caption("用户记录数 Top 10")
        if not users_df.empty:
            top_users = users_df.sort_values("record_count", ascending=False).head(10).set_index("username")["record_count"]
            st.bar_chart(top_users.rename("记录数"), color="#7C6CF2")


def _render_mock_authorization():
    _bootstrap_mock_requests()
    st.markdown("#### 管理员授权申请")
    st.caption("该模块为演示用前端假实现，不写入数据库。")

    requests = st.session_state["admin_mock_requests"]
    if not requests:
        st.info("当前没有待处理申请。")
        return

    for item in requests:
        badge_color = "#F59E0B" if item["status"] == "待审核" else "#10B981" if item["status"] == "已授权" else "#EF4444"
        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb; border-radius:10px; padding:14px 16px; margin-bottom:12px; background:#fff;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong>{item['username']}</strong>
                    <span style="padding:4px 10px; border-radius:999px; background:{badge_color}18; color:{badge_color}; font-weight:600;">{item['status']}</span>
                </div>
                <div style="color:#475569; font-size:14px; margin-bottom:6px;">申请时间：{item['applied_at']}</div>
                <div style="color:#475569; font-size:14px; margin-bottom:6px;">联系方式：{item['contact'] or '未填写'}</div>
                <div style="color:#334155; font-size:14px;">申请原因：{item['reason']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        if c1.button("授权通过", key=f"approve_{item['id']}", use_container_width=True):
            item["status"] = "已授权"
            st.success(f"已授予 {item['username']} 管理员权限（演示模式）。")
            st.rerun()
        if c2.button("驳回申请", key=f"reject_{item['id']}", use_container_width=True):
            item["status"] = "已驳回"
            st.info(f"已驳回 {item['username']} 的管理员申请（演示模式）。")
            st.rerun()


def _render_user_management(users_df: pd.DataFrame):
    st.markdown("#### 用户数据管理")
    if users_df.empty:
        st.caption("暂无用户数据。")
        return

    display_df = _format_export_df(users_df, CN_USER_COLUMNS)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.markdown("##### 修改用户名")
        user_ids = users_df["user_id"].tolist()
        selected_user = st.selectbox("选择用户 ID", user_ids, key="admin_update_user_id")
        current_name = users_df.loc[users_df["user_id"] == selected_user, "username"].iloc[0]
        new_name = st.text_input("新用户名", value=current_name, key="admin_new_username")
        if st.button("保存用户名修改", use_container_width=True):
            if new_name.strip() and db.update_username(int(selected_user), new_name.strip()):
                st.success("用户名已更新。")
                st.rerun()
            st.error("更新失败，可能是用户名重复。")

    with right:
        st.markdown("##### 删除用户")
        delete_user_id = st.selectbox("选择要删除的用户", users_df["user_id"].tolist(), key="admin_delete_user_id")
        confirm = st.checkbox("我确认删除该用户及其全部历史记录", key="admin_confirm_delete_user")
        if st.button("删除用户", use_container_width=True, type="primary"):
            if not confirm:
                st.warning("请先勾选确认。")
            elif db.delete_user(int(delete_user_id)):
                st.success("用户及其历史记录已删除。")
                st.rerun()
            else:
                st.error("删除失败，请重试。")


def _render_record_management(records_df: pd.DataFrame):
    st.markdown("#### 生成记录管理")
    if records_df.empty:
        st.caption("暂无生成记录。")
        return

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        style_filter = st.selectbox("按模板风格筛选", ["全部"] + sorted(records_df["template_style"].replace("", "未记录").unique().tolist()))
    with filter_col2:
        provider_filter = st.selectbox("按模型提供商筛选", ["全部"] + sorted(records_df["provider_name"].replace("", "未记录").unique().tolist()))

    filtered = records_df.copy()
    if style_filter != "全部":
        filtered = filtered[filtered["template_style"].replace("", "未记录") == style_filter]
    if provider_filter != "全部":
        filtered = filtered[filtered["provider_name"].replace("", "未记录") == provider_filter]

    display_df = _format_export_df(filtered, CN_RECORD_COLUMNS)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    delete_record_id = st.selectbox("选择要删除的记录 ID", filtered["record_id"].tolist(), key="admin_delete_record_id")
    if st.button("删除这条生成记录", use_container_width=True):
        if db.delete_resume_record(int(delete_record_id)):
            st.success("记录已删除。")
            st.rerun()
        st.error("删除失败，请重试。")


def _render_export_panel(users_df: pd.DataFrame, records_df: pd.DataFrame):
    st.markdown("#### 数据导出")
    st.caption("为了避免时间列在表格软件中显示成 ####，这里同时提供标准 CSV 和更适合直接查看的 Excel 文件。")

    export_users = _format_export_df(users_df, CN_USER_COLUMNS)
    export_records = _format_export_df(records_df, CN_RECORD_COLUMNS)
    user_csv = export_users.to_csv(index=False).encode("utf-8-sig")
    record_csv = export_records.to_csv(index=False).encode("utf-8-sig")

    left, right = st.columns(2)
    left.download_button("下载用户统计 CSV", user_csv, "admin_users.csv", "text/csv", use_container_width=True)
    right.download_button("下载记录统计 CSV", record_csv, "admin_records.csv", "text/csv", use_container_width=True)

    try:
        excel_stream = BytesIO()
        with pd.ExcelWriter(excel_stream) as writer:
            export_users.to_excel(writer, sheet_name="用户统计", index=False)
            export_records.to_excel(writer, sheet_name="记录统计", index=False)
        excel_bytes = excel_stream.getvalue()
        xl1, xl2 = st.columns(2)
        xl1.download_button(
            "下载用户统计 Excel",
            excel_bytes,
            "admin_export.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_admin_excel_users",
        )
        xl2.download_button(
            "下载记录统计 Excel",
            excel_bytes,
            "admin_export.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_admin_excel_records",
        )
    except Exception:
        st.caption("当前环境缺少 Excel 导出依赖，已保留 CSV 导出。")


def render_admin_panel():
    st.markdown('<p class="step-header">第六步：管理员数据面板</p>', unsafe_allow_html=True)

    if not WBQ_AVAILABLE:
        st.error("`wbq` 模块不可用，请检查当前环境。")
        st.stop()

    if not st.session_state.get("admin_authenticated"):
        _render_admin_login()
        return

    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.success("管理员身份已验证，可以查看全局运营数据与后台维护功能。")
    with header_right:
        if st.button("退出管理员面板", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.rerun()

    users_df = _users_df()
    records_df = _records_df()

    _render_admin_metrics(users_df, records_df)
    st.divider()
    _render_admin_charts(users_df, records_df)

    tab_users, tab_records, tab_exports, tab_auth = st.tabs(["用户管理", "记录管理", "数据导出", "授权申请"])
    with tab_users:
        _render_user_management(users_df)
    with tab_records:
        _render_record_management(records_df)
    with tab_exports:
        _render_export_panel(users_df, records_df)
    with tab_auth:
        _render_mock_authorization()
