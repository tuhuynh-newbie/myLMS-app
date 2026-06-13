# dashboard.py

import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px


# =====================================================
# CẤU HÌNH TRANG
# =====================================================
st.set_page_config(
    page_title="Dashboard LMS",
    page_icon="📊",
    layout="wide"
)

DB_PATH = "data/lms.db"


# =====================================================
# KẾT NỐI DATABASE
# =====================================================
def create_connection():
    """
    Kết nối tới SQLite Database.
    Trả về đối tượng connection.
    """

    if not os.path.exists(DB_PATH):
        return None

    conn = sqlite3.connect(DB_PATH)

    return conn


# =====================================================
# LOAD DỮ LIỆU HỌC SINH
# =====================================================
def load_students():
    """
    Đọc toàn bộ dữ liệu học sinh từ database
    và trả về DataFrame Pandas.
    """

    conn = create_connection()

    if conn is None:
        return None

    try:
        query = """
        SELECT *
        FROM students
        """

        df = pd.read_sql_query(query, conn)

        return df

    except Exception as e:
        st.error(f"Lỗi khi đọc dữ liệu: {e}")
        return None

    finally:
        conn.close()


# =====================================================
# TÍNH TOÁN THỐNG KÊ
# =====================================================
def get_statistics(df):
    """
    Tính toán các KPI chính.
    """

    total_students = len(df)

    active_students = len(
        df[df["status"] == "Đang học"]
    )

    inactive_students = len(
        df[df["status"] == "Nghỉ học"]
    )

    return {
        "total": total_students,
        "active": active_students,
        "inactive": inactive_students
    }


# =====================================================
# HIỂN THỊ KPI
# =====================================================
def show_kpis(stats):
    """
    Hiển thị KPI trên cùng một hàng.
    """

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="👨‍🎓 Tổng học sinh",
            value=stats["total"]
        )

    with col2:
        st.metric(
            label="✅ Đang học",
            value=stats["active"]
        )

    with col3:
        st.metric(
            label="❌ Nghỉ học",
            value=stats["inactive"]
        )


# =====================================================
# BIỂU ĐỒ THEO LỚP
# =====================================================
def show_class_chart(df):
    """
    Hiển thị biểu đồ số lượng học sinh theo lớp.
    """

    st.subheader("📈 Số lượng học sinh theo lớp")

    class_summary = (
        df.groupby("class_name")
        .size()
        .reset_index(name="count")
        .sort_values("class_name")
    )

    fig = px.bar(
        class_summary,
        x="class_name",
        y="count",
        text="count",
        title="Số lượng học sinh theo lớp",
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        height=500,
        xaxis_title="Lớp",
        yaxis_title="Số học sinh"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================================
# BẢNG DANH SÁCH HỌC SINH
# =====================================================
def show_student_table(df):
    """
    Hiển thị danh sách học sinh.
    """

    st.subheader("Danh sách học sinh")

    display_df = (
        df[
            [
                "student_code",
                "full_name",
                "class_name",
                "status"
            ]
        ]
        .sort_index(ascending=False)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =====================================================
# HÀM CHÍNH
# =====================================================
def main():

    # ---------------------------------------------
    # TIÊU ĐỀ
    # ---------------------------------------------
    st.title("📊 Dashboard LMS")

    st.write(
        "Tổng quan hệ thống quản lý học sinh"
    )

    # ---------------------------------------------
    # KIỂM TRA DATABASE
    # ---------------------------------------------
    if not os.path.exists(DB_PATH):
        st.error("Không tìm thấy database")
        return

    # ---------------------------------------------
    # LOAD DỮ LIỆU
    # ---------------------------------------------
    df = load_students()

    if df is None:
        return

    if df.empty:
        st.warning("Chưa có dữ liệu học sinh")
        return

    # ---------------------------------------------
    # SIDEBAR BỘ LỌC
    # ---------------------------------------------
    st.sidebar.header("Bộ lọc")

    class_list = sorted(
        df["class_name"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_class = st.sidebar.selectbox(
        "Chọn lớp",
        ["Tất cả"] + class_list
    )

    # ---------------------------------------------
    # LỌC DỮ LIỆU
    # ---------------------------------------------
    filtered_df = df.copy()

    if selected_class != "Tất cả":
        filtered_df = filtered_df[
            filtered_df["class_name"] == selected_class
        ]

    # ---------------------------------------------
    # KPI
    # ---------------------------------------------
    stats = get_statistics(filtered_df)

    show_kpis(stats)

    st.divider()

    # ---------------------------------------------
    # BIỂU ĐỒ
    # ---------------------------------------------
    show_class_chart(filtered_df)

    st.divider()

    # ---------------------------------------------
    # BẢNG DỮ LIỆU
    # ---------------------------------------------
    show_student_table(
        filtered_df.sort_values(
            by="id",
            ascending=False
        )
    )


# =====================================================
# CHẠY ỨNG DỤNG
# =====================================================
if __name__ == "__main__":
    main()
