
import sqlite3
from datetime import date
import pandas as pd
import streamlit as st
import plotly.express as px

DB_PATH = "data/lms.db"

st.set_page_config(page_title="Quản lý điểm danh", page_icon="📋", layout="wide")


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def create_table():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            attendance_date TEXT,
            attendance_status TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_unique
        ON attendance(student_id, attendance_date)
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        st.error(f"Lỗi DB: {e}")


def get_students(class_name=None):
    conn = get_connection()
    q = "SELECT * FROM students WHERE status='Đang học'"
    params = []
    if class_name:
        q += " AND class_name=?"
        params.append(class_name)
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df


def get_classes():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT DISTINCT class_name
        FROM students
        WHERE status='Đang học'
        ORDER BY class_name
    """, conn)
    conn.close()
    return df["class_name"].tolist()


def load_attendance(attendance_date):
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM attendance
        WHERE attendance_date=?
    """, conn, params=[str(attendance_date)])
    conn.close()
    return df


def save_attendance(student_id, attendance_date, status, note):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO attendance(
            student_id, attendance_date,
            attendance_status, note
        )
        VALUES(?,?,?,?)
        ON CONFLICT(student_id, attendance_date)
        DO UPDATE SET
            attendance_status=excluded.attendance_status,
            note=excluded.note
        """, (student_id, str(attendance_date), status, note))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        st.error(f"Lỗi lưu dữ liệu: {e}")


def student_statistics(start_date, end_date):
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT s.student_code,s.full_name,s.class_name,
               a.attendance_status
        FROM students s
        LEFT JOIN attendance a
        ON s.id=a.student_id
        AND date(a.attendance_date) BETWEEN date(?) AND date(?)
        WHERE s.status='Đang học'
    """, conn, params=[str(start_date), str(end_date)])
    conn.close()

    if df.empty:
        return pd.DataFrame()

    result = []
    for (code, name, cls), g in df.groupby(
        ["student_code", "full_name", "class_name"]
    ):
        total = len(g[g["attendance_status"].notna()])
        present = (g["attendance_status"] == "Present").sum()
        excused = (g["attendance_status"] == "Excused").sum()
        absent = (g["attendance_status"] == "Absent").sum()
        rate = round((present / total * 100), 2) if total else 0

        result.append({
            "Mã HS": code,
            "Họ tên": name,
            "Lớp": cls,
            "Có mặt": present,
            "Có phép": excused,
            "Không phép": absent,
            "Chuyên cần %": rate
        })

    return pd.DataFrame(result)


def class_statistics(start_date, end_date):
    conn = get_connection()

    students = pd.read_sql_query("""
    SELECT class_name, COUNT(*) total_students
    FROM students
    WHERE status='Đang học'
    GROUP BY class_name
    """, conn)

    attendance = pd.read_sql_query("""
    SELECT s.class_name,
           COUNT(*) total_attendance,
           SUM(CASE WHEN attendance_status='Present' THEN 1 ELSE 0 END) present_count
    FROM attendance a
    JOIN students s ON a.student_id=s.id
    WHERE date(a.attendance_date) BETWEEN date(?) AND date(?)
    GROUP BY s.class_name
    """, conn, params=[str(start_date), str(end_date)])

    conn.close()

    df = students.merge(attendance, on="class_name", how="left").fillna(0)
    df["attendance_rate"] = df.apply(
        lambda r: round(r["present_count"] / r["total_attendance"] * 100, 2)
        if r["total_attendance"] > 0 else 0,
        axis=1
    )
    return df


def today_kpi():
    conn = get_connection()

    total_students = pd.read_sql_query(
        "SELECT COUNT(*) c FROM students WHERE status='Đang học'", conn
    )["c"][0]

    today = str(date.today())

    df = pd.read_sql_query("""
    SELECT attendance_status
    FROM attendance
    WHERE attendance_date=?
    """, conn, params=[today])

    conn.close()

    checked = len(df)
    present = (df["attendance_status"] == "Present").sum() if not df.empty else 0
    absent = len(df[df["attendance_status"].isin(["Absent", "Excused"])]) if not df.empty else 0
    rate = round(present / checked * 100, 2) if checked else 0

    return total_students, checked, rate, absent


def main():
    create_table()

    st.title("📋 Quản lý điểm danh")

    st.sidebar.header("Bộ lọc")
    start_date = st.sidebar.date_input("Từ ngày", date.today().replace(day=1))
    end_date = st.sidebar.date_input("Đến ngày", date.today())

    total_students, checked, rate, absent = today_kpi()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng học sinh", total_students)
    c2.metric("Điểm danh hôm nay", checked)
    c3.metric("Chuyên cần hôm nay", f"{rate}%")
    c4.metric("Vắng hôm nay", absent)

    tab1, tab2, tab3 = st.tabs(
        ["Điểm danh", "Thống kê học sinh", "Thống kê lớp"]
    )

    with tab1:
        cols = st.columns(2)
        attendance_date = cols[0].date_input("Ngày điểm danh", date.today())
        classes = get_classes()
        selected_class = cols[1].selectbox("Lớp", classes)

        students = get_students(selected_class)
        st.caption(f"Số học sinh: {len(students)}")

        records = []

        for _, row in students.iterrows():
            c1, c2, c3, c4 = st.columns([1, 3, 2, 3])
            c1.write(row["student_code"])
            c2.write(row["full_name"])

            status = c3.selectbox(
                "Trạng thái",
                ["Present", "Excused", "Absent"],
                key=f"status_{row['id']}"
            )

            note = c4.text_input(
                "Ghi chú",
                key=f"note_{row['id']}"
            )

            records.append((row["id"], status, note))

        if st.button("💾 Lưu điểm danh"):
            with st.spinner("Đang lưu..."):
                for sid, status, note in records:
                    save_attendance(
                        sid,
                        attendance_date,
                        status,
                        note
                    )
            st.success("Đã lưu điểm danh")

    with tab2:
        keyword = st.text_input("Tìm học sinh")
        df = student_statistics(start_date, end_date)

        if keyword:
            df = df[
                df["Họ tên"].str.contains(keyword, case=False, na=False)
                | df["Mã HS"].str.contains(keyword, case=False, na=False)
            ]

        st.dataframe(df, use_container_width=True)

        if not df.empty:
            fig = px.bar(
                df,
                x="Họ tên",
                y="Chuyên cần %",
                text_auto=True
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        df = class_statistics(start_date, end_date)

        view = pd.DataFrame({
            "Lớp": df["class_name"],
            "Số HS": df["total_students"],
            "Có mặt": df["present_count"],
            "Tổng lượt": df["total_attendance"],
            "Chuyên cần %": df["attendance_rate"]
        })

        st.dataframe(view, use_container_width=True)

        fig = px.bar(
            df,
            x="class_name",
            y="attendance_rate",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
