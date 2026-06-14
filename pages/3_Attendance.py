
from datetime import date
import pandas as pd
import streamlit as st
import plotly.express as px
from database import repository as repo


st.set_page_config(page_title="Quản lý điểm danh", page_icon="📋", layout="wide")


def get_students(class_name=None):
    data = repo.get_students(class_name=class_name, status="Đang học")
    return pd.DataFrame(data)


def get_classes():
    return repo.get_classes()


def load_attendance(attendance_date):
    data = repo.get_attendance(str(attendance_date))
    return pd.DataFrame(data)


def save_attendance(student_id, attendance_date, status, note):
    try:
        return repo.upsert_attendance(
            student_id,
            str(attendance_date),
            status,
            note
        )
    except Exception as e:
        st.error(f"Lỗi lưu dữ liệu: {e}")
        return None


def student_statistics(start_date, end_date):
    students = get_students()
    attendance = repo.get_attendance_range(str(start_date), str(end_date))

    if students.empty:
        return pd.DataFrame()

    if not attendance:
        attendance_df = pd.DataFrame(columns=["student_id", "attendance_status"])
    else:
        attendance_df = pd.DataFrame(attendance)

    merged = students.merge(
        attendance_df,
        left_on="id",
        right_on="student_id",
        how="left"
    )

    if merged.empty:
        return pd.DataFrame()

    result = []
    grouped = merged.groupby(
        ["student_code", "full_name", "class_name"], dropna=False
    )

    for (code, name, cls), group in grouped:
        total = group["attendance_status"].notna().sum()
        present = (group["attendance_status"] == "Present").sum()
        excused = (group["attendance_status"] == "Excused").sum()
        absent = (group["attendance_status"] == "Absent").sum()
        rate = round((present / total * 100), 2) if total else 0

        result.append({
            "Mã HS": code,
            "Họ tên": name,
            "Lớp": cls,
            "Có mặt": int(present),
            "Có phép": int(excused),
            "Không phép": int(absent),
            "Chuyên cần %": rate
        })

    return pd.DataFrame(result)


def class_statistics(start_date, end_date):
    students = get_students()
    attendance = repo.get_attendance_range(str(start_date), str(end_date))

    if students.empty:
        return pd.DataFrame(
            columns=[
                "class_name",
                "total_students",
                "total_attendance",
                "present_count",
                "attendance_rate"
            ]
        )

    class_counts = (
        students.groupby("class_name", dropna=False)
        .size()
        .reset_index(name="total_students")
    )

    if not attendance:
        attendance_df = pd.DataFrame(columns=["student_id", "attendance_status"])
    else:
        attendance_df = pd.DataFrame(attendance)

    attendance_stats = (
        attendance_df
        .merge(
            students[["id", "class_name"]],
            left_on="student_id",
            right_on="id",
            how="left"
        )
        .groupby("class_name", dropna=False)
        .agg(
            total_attendance=("attendance_status", "size"),
            present_count=("attendance_status", lambda x: (x == "Present").sum())
        )
        .reset_index()
    )

    df = class_counts.merge(attendance_stats, on="class_name", how="left").fillna(0)
    df["attendance_rate"] = df.apply(
        lambda r: round(r["present_count"] / r["total_attendance"] * 100, 2)
        if r["total_attendance"] > 0 else 0,
        axis=1
    )
    return df


def today_kpi():
    students = get_students()
    total_students = len(students)

    today = str(date.today())
    attendance = repo.get_attendance(today)
    attendance_df = pd.DataFrame(attendance)

    checked = len(attendance_df)
    present = (attendance_df["attendance_status"] == "Present").sum() if not attendance_df.empty else 0
    absent = len(attendance_df[attendance_df["attendance_status"].isin(["Absent", "Excused"])]) if not attendance_df.empty else 0
    rate = round(present / checked * 100, 2) if checked else 0

    return total_students, checked, rate, absent


def main():

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
