import streamlit as st

st.title("Quản lý học sinh")
# students.py
# ==========================================================
# MODULE QUẢN LÝ HỌC SINH - STREAMLIT + SQLITE
#
# Chức năng:
# 1. Xem danh sách học sinh
# 2. Thêm học sinh
# 3. Tìm kiếm học sinh
# 4. Sửa học sinh
# 5. Xóa học sinh
#
# Database:
# data/lms.db
# ==========================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ==========================================================
# CẤU HÌNH TRANG
# ==========================================================

st.set_page_config(
    page_title="Quản lý học sinh",
    page_icon="🎓",
    layout="wide"
)

DB_PATH = "data/lms.db"


# ==========================================================
# KẾT NỐI DATABASE
# ==========================================================
def create_connection():
    """
    Tạo kết nối tới SQLite
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn


# ==========================================================
# TẠO BẢNG NẾU CHƯA TỒN TẠI
# ==========================================================
def create_table():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE,
            full_name TEXT,
            class_name TEXT,
            birth_date TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


# ==========================================================
# ĐỌC DANH SÁCH HỌC SINH
# ==========================================================
def load_students():
    """
    Đọc toàn bộ học sinh từ SQLite
    và trả về DataFrame
    """
    conn = create_connection()

    query = """
    SELECT *
    FROM students
    ORDER BY id DESC
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


# ==========================================================
# THÊM HỌC SINH
# ==========================================================
def add_student(student_code,
                full_name,
                class_name,
                birth_date,
                status):
    """
    Thêm học sinh mới
    """

    if not full_name.strip():
        st.error("Họ tên không được để trống.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO students
            (
                student_code,
                full_name,
                class_name,
                birth_date,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """,
        (
            student_code,
            full_name,
            class_name,
            birth_date,
            status
        ))

        conn.commit()

        st.success("✅ Thêm học sinh thành công!")

    except sqlite3.IntegrityError:
        st.error("❌ Mã học sinh đã tồn tại.")

    except Exception as e:
        st.error(f"Lỗi: {e}")

    finally:
        conn.close()


# ==========================================================
# CẬP NHẬT HỌC SINH
# ==========================================================
def update_student(student_id,
                   student_code,
                   full_name,
                   class_name,
                   birth_date,
                   status):

    if not full_name.strip():
        st.error("Họ tên không được để trống.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE students
            SET
                student_code = ?,
                full_name = ?,
                class_name = ?,
                birth_date = ?,
                status = ?
            WHERE id = ?
        """,
        (
            student_code,
            full_name,
            class_name,
            birth_date,
            status,
            student_id
        ))

        conn.commit()

        st.success("✅ Cập nhật thành công!")

    except sqlite3.IntegrityError:
        st.error("❌ Mã học sinh đã tồn tại.")

    except Exception as e:
        st.error(f"Lỗi: {e}")

    finally:
        conn.close()


# ==========================================================
# XÓA HỌC SINH
# ==========================================================
def delete_student(student_id):

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )

        conn.commit()

        st.success("✅ Xóa học sinh thành công!")

    except Exception as e:
        st.error(f"Lỗi: {e}")

    finally:
        conn.close()


# ==========================================================
# KHỞI TẠO DATABASE
# ==========================================================
create_table()


# ==========================================================
# TIÊU ĐỀ
# ==========================================================
st.title("🎓 Quản lý học sinh")

# ==========================================================
# TABS
# ==========================================================
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📋 Danh sách học sinh",
        "➕ Thêm học sinh",
        "✏️ Sửa học sinh",
        "🗑️ Xóa học sinh"
    ]
)

# ==========================================================
# TAB 1 - DANH SÁCH HỌC SINH
# ==========================================================
with tab1:

    st.subheader("Danh sách học sinh")

    df = load_students()

    col1, col2 = st.columns(2)

    with col1:
        search_name = st.text_input(
            "Tìm theo họ tên"
        )

    with col2:
        search_code = st.text_input(
            "Tìm theo mã học sinh"
        )

    filtered_df = df.copy()

    # Lọc theo tên
    if search_name:
        filtered_df = filtered_df[
            filtered_df["full_name"]
            .str.contains(
                search_name,
                case=False,
                na=False
            )
        ]

    # Lọc theo mã học sinh
    if search_code:
        filtered_df = filtered_df[
            filtered_df["student_code"]
            .str.contains(
                search_code,
                case=False,
                na=False
            )
        ]

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

    st.info(
        f"Tổng số học sinh: {len(filtered_df)}"
    )


# ==========================================================
# TAB 2 - THÊM HỌC SINH
# ==========================================================
with tab2:

    st.subheader("Thêm học sinh")

    with st.form("add_student_form"):

        student_code = st.text_input(
            "Mã học sinh"
        )

        full_name = st.text_input(
            "Họ tên"
        )

        class_name = st.text_input(
            "Lớp"
        )

        birth_date = st.date_input(
            "Ngày sinh",
            value=date(2015, 1, 1)
        )

        status = st.selectbox(
            "Trạng thái",
            [
                "Đang học",
                "Nghỉ học"
            ]
        )

        submitted = st.form_submit_button(
            "Lưu học sinh"
        )

        if submitted:

            add_student(
                student_code,
                full_name,
                class_name,
                str(birth_date),
                status
            )


# ==========================================================
# TAB 3 - SỬA HỌC SINH
# ==========================================================
with tab3:

    st.subheader("Sửa học sinh")

    df = load_students()

    if not df.empty:

        options = {
            f"{row['student_code']} - {row['full_name']}":
            row["id"]
            for _, row in df.iterrows()
        }

        selected = st.selectbox(
            "Chọn học sinh",
            list(options.keys())
        )

        student_id = options[selected]

        student = df[
            df["id"] == student_id
        ].iloc[0]

        code_edit = st.text_input(
            "Mã học sinh",
            value=student["student_code"]
        )

        name_edit = st.text_input(
            "Họ tên",
            value=student["full_name"]
        )

        class_edit = st.text_input(
            "Lớp",
            value=student["class_name"]
        )

        birth_edit = st.text_input(
            "Ngày sinh",
            value=student["birth_date"]
        )

        status_edit = st.selectbox(
            "Trạng thái",
            ["Đang học", "Nghỉ học"],
            index=0
            if student["status"] == "Đang học"
            else 1
        )

        if st.button("Cập nhật"):

            update_student(
                student_id,
                code_edit,
                name_edit,
                class_edit,
                birth_edit,
                status_edit
            )

            st.rerun()

    else:
        st.warning(
            "Chưa có học sinh nào."
        )


# ==========================================================
# TAB 4 - XÓA HỌC SINH
# ==========================================================
with tab4:

    st.subheader("Xóa học sinh")

    df = load_students()

    if not df.empty:

        options = {
            f"{row['student_code']} - {row['full_name']}":
            row["id"]
            for _, row in df.iterrows()
        }

        selected = st.selectbox(
            "Chọn học sinh cần xóa",
            list(options.keys())
        )

        student_id = options[selected]

        st.warning(
            "Hành động này không thể hoàn tác."
        )

        confirm = st.checkbox(
            "Tôi xác nhận muốn xóa"
        )

        if st.button("Xóa học sinh"):

            if confirm:
                delete_student(student_id)
                st.rerun()
            else:
                st.error(
                    "Vui lòng xác nhận trước khi xóa."
                )

    else:
        st.warning(
            "Không có dữ liệu học sinh."
        )