
"""
scores.py - LMS Professional Version
Chạy:
streamlit run scores.py
"""

import sqlite3
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "data/lms.db"

# =========================
# DATABASE
# =========================
def get_connection():
    Path("data").mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def create_scores_table():
    try:
        conn = get_connection()
        conn.execute("""
        CREATE TABLE IF NOT EXISTS scores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            math_score REAL,
            literature_score REAL,
            english_score REAL,
            average_score REAL,
            rank_level TEXT,
            semester TEXT,
            school_year TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id,semester,school_year)
        )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Lỗi tạo bảng: {e}")


def calculate_average(m, l, e):
    return round((m + l + e) / 3, 2)


def calculate_rank(avg):
    if avg >= 8:
        return "Giỏi"
    elif avg >= 6.5:
        return "Khá"
    return "Trung bình"


def get_students():
    try:
        conn = get_connection()
        df = pd.read_sql("""
        SELECT *
        FROM students
        ORDER BY class_name, full_name
        """, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()


def save_score(student_id, math, lit, eng, semester, school_year):
    try:
        conn = get_connection()
        avg = calculate_average(math, lit, eng)
        rank = calculate_rank(avg)

        conn.execute("""
        INSERT INTO scores(
            student_id, math_score, literature_score,
            english_score, average_score,
            rank_level, semester, school_year
        )
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(student_id,semester,school_year)
        DO UPDATE SET
            math_score=excluded.math_score,
            literature_score=excluded.literature_score,
            english_score=excluded.english_score,
            average_score=excluded.average_score,
            rank_level=excluded.rank_level
        """, (
            student_id, math, lit, eng,
            avg, rank, semester, school_year
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(e)
        return False


def get_scores():
    try:
        conn = get_connection()
        df = pd.read_sql("""
        SELECT
            s.id,
            st.student_code,
            st.full_name,
            st.class_name,
            s.math_score,
            s.literature_score,
            s.english_score,
            s.average_score,
            s.rank_level,
            s.semester,
            s.school_year,
            s.student_id
        FROM scores s
        INNER JOIN students st
        ON st.id=s.student_id
        """, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()


def update_score(score_id, math, lit, eng, semester, school_year):
    try:
        conn = get_connection()

        avg = calculate_average(math, lit, eng)
        rank = calculate_rank(avg)

        conn.execute("""
        UPDATE scores
        SET math_score=?,
            literature_score=?,
            english_score=?,
            average_score=?,
            rank_level=?,
            semester=?,
            school_year=?
        WHERE id=?
        """, (
            math, lit, eng,
            avg, rank,
            semester, school_year,
            score_id
        ))

        conn.commit()
        conn.close()

    except Exception as e:
        st.error(e)


def delete_score(score_id):
    try:
        conn = get_connection()
        conn.execute("DELETE FROM scores WHERE id=?", (score_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(e)


def load_statistics(df):
    if df.empty:
        return {
            "total": 0,
            "avg": 0,
            "gioi": 0,
            "kha": 0,
            "tb": 0
        }

    return {
        "total": len(df),
        "avg": round(df["average_score"].mean(), 2),
        "gioi": len(df[df["rank_level"] == "Giỏi"]),
        "kha": len(df[df["rank_level"] == "Khá"]),
        "tb": len(df[df["rank_level"] == "Trung bình"])
    }


def export_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Scores")
    return output.getvalue()


# =========================
# UI
# =========================

st.set_page_config(
    page_title="Quản lý điểm học sinh",
    page_icon="📚",
    layout="wide"
)

create_scores_table()

students_df = get_students()
scores_df = get_scores()

st.title("📚 Quản lý điểm học sinh")

# Sidebar LMS
st.sidebar.header("Bộ lọc")

semester_filter = st.sidebar.selectbox(
    "Học kỳ",
    ["Tất cả", "Học kỳ 1", "Học kỳ 2"]
)

school_years = ["Tất cả"]
if not scores_df.empty:
    school_years += sorted(scores_df["school_year"].unique())

year_filter = st.sidebar.selectbox(
    "Năm học",
    school_years
)

class_list = ["Tất cả"]
if not students_df.empty:
    class_list += sorted(students_df["class_name"].dropna().unique())

class_filter = st.sidebar.selectbox(
    "Lớp",
    class_list
)

tab1, tab2, tab3 = st.tabs(
    ["Nhập điểm", "Danh sách điểm", "Thống kê học lực"]
)

# =========================
# TAB 1
# =========================
with tab1:

    c1, c2, c3 = st.columns(3)

    selected_class = c1.selectbox(
        "Lớp",
        class_list[1:] if len(class_list) > 1 else [""]
    )

    semester = c2.selectbox(
        "Học kỳ",
        ["Học kỳ 1", "Học kỳ 2"]
    )

    school_year = c3.text_input(
        "Năm học",
        "2025-2026"
    )

    student_filter = students_df.copy()

    if selected_class:
        student_filter = student_filter[
            student_filter["class_name"] == selected_class
        ]

    student_map = {
        f"{r.student_code} - {r.full_name}": r.id
        for _, r in student_filter.iterrows()
    }

    if student_map:

        selected_student = st.selectbox(
            "Chọn học sinh",
            list(student_map.keys())
        )

        m1, m2, m3 = st.columns(3)

        math = m1.number_input(
            "Điểm Toán", 0.0, 10.0, 0.0, 0.1
        )

        literature = m2.number_input(
            "Điểm Văn", 0.0, 10.0, 0.0, 0.1
        )

        english = m3.number_input(
            "Điểm Anh", 0.0, 10.0, 0.0, 0.1
        )

        avg = calculate_average(
            math,
            literature,
            english
        )

        rank = calculate_rank(avg)

        st.info(
            f"Điểm TB: {avg} | Xếp loại: {rank}"
        )

        if st.button("💾 Lưu điểm", use_container_width=True):

            ok = save_score(
                student_map[selected_student],
                math,
                literature,
                english,
                semester,
                school_year
            )

            if ok:
                st.success("Lưu thành công")
                st.rerun()

# =========================
# TAB 2
# =========================
with tab2:

    df = scores_df.copy()

    search = st.text_input(
        "Tìm học sinh"
    )

    if search:
        df = df[
            df["student_code"].str.contains(search, case=False)
            |
            df["full_name"].str.contains(search, case=False)
        ]

    rank_filter = st.selectbox(
        "Học lực",
        ["Tất cả", "Giỏi", "Khá", "Trung bình"]
    )

    if class_filter != "Tất cả":
        df = df[df["class_name"] == class_filter]

    if semester_filter != "Tất cả":
        df = df[df["semester"] == semester_filter]

    if year_filter != "Tất cả":
        df = df[df["school_year"] == year_filter]

    if rank_filter != "Tất cả":
        df = df[df["rank_level"] == rank_filter]

    st.dataframe(df, use_container_width=True, height=400)

    st.subheader("Chỉnh sửa điểm")

    if not df.empty:

        edit_map = {
            f"{r.student_code} - {r.full_name} - {r.semester}": r.id
            for _, r in df.iterrows()
        }

        edit_item = st.selectbox(
            "Chọn bản ghi",
            list(edit_map.keys())
        )

        row = df[df["id"] == edit_map[edit_item]].iloc[0]

        c1, c2, c3 = st.columns(3)

        e_math = c1.number_input(
            "Toán",
            value=float(row.math_score),
            key="em"
        )

        e_lit = c2.number_input(
            "Văn",
            value=float(row.literature_score),
            key="el"
        )

        e_eng = c3.number_input(
            "Anh",
            value=float(row.english_score),
            key="ee"
        )

        e_sem = st.text_input(
            "Học kỳ",
            row.semester
        )

        e_year = st.text_input(
            "Năm học",
            row.school_year
        )

        cc1, cc2 = st.columns(2)

        if cc1.button("✏️ Cập nhật", use_container_width=True):
            update_score(
                row.id,
                e_math,
                e_lit,
                e_eng,
                e_sem,
                e_year
            )
            st.success("Đã cập nhật")
            st.rerun()

        confirm = cc2.checkbox("Xác nhận xóa")

        if cc2.button("🗑 Xóa", use_container_width=True):
            if confirm:
                delete_score(row.id)
                st.success("Đã xóa")
                st.rerun()

# =========================
# TAB 3
# =========================
with tab3:

    stat_df = scores_df.copy()

    if class_filter != "Tất cả":
        stat_df = stat_df[stat_df["class_name"] == class_filter]

    if semester_filter != "Tất cả":
        stat_df = stat_df[stat_df["semester"] == semester_filter]

    if year_filter != "Tất cả":
        stat_df = stat_df[stat_df["school_year"] == year_filter]

    stats = load_statistics(stat_df)

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("Tổng học sinh", stats["total"])
    k2.metric("Điểm TB", stats["avg"])
    k3.metric("Giỏi", stats["gioi"])
    k4.metric("Khá", stats["kha"])
    k5.metric("Trung bình", stats["tb"])

    if not stat_df.empty:

        rank_data = (
            stat_df.groupby("rank_level")
            .size()
            .reset_index(name="student_count")
        )

        fig1 = px.bar(
            rank_data,
            x="rank_level",
            y="student_count",
            title="Phân bố học lực học sinh"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

        class_avg = (
            stat_df.groupby("class_name")["average_score"]
            .mean()
            .reset_index()
        )

        fig2 = px.bar(
            class_avg,
            x="class_name",
            y="average_score",
            title="Điểm trung bình theo lớp"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

        top10 = stat_df.sort_values(
            by="average_score",
            ascending=False
        ).head(10)

        fig3 = px.bar(
            top10,
            x="full_name",
            y="average_score",
            title="Top 10 học sinh xuất sắc"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

    excel_data = export_excel(scores_df)

    st.download_button(
        "📥 Xuất Excel",
        data=excel_data,
        file_name="scores_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
