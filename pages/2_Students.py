"""
2_Students.py — Quản lý học sinh
Chạy: streamlit run 2_Students.py
"""

# ===========================================================================
# CẤU HÌNH TRANG — phải là lệnh Streamlit ĐẦU TIÊN
# ===========================================================================
import streamlit as st

st.set_page_config(
    page_title="Quản lý học sinh",
    page_icon="🎓",
    layout="wide"
)

# ===========================================================================
# IMPORTS
# ===========================================================================
import logging
from datetime import date

import pandas as pd

from database import repository as repo

logger = logging.getLogger(__name__)

# ===========================================================================
# DATA LAYER WRAPPERS
# ===========================================================================

def load_students() -> pd.DataFrame:
    """Lấy toàn bộ danh sách học sinh, trả về DataFrame."""
    try:
        data = repo.get_students()
        if not data:
            return pd.DataFrame(
                columns=["id", "student_code", "full_name", "class_name", "birth_date", "status"]
            )
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Không thể tải danh sách học sinh: {e}")
        logger.exception("load_students thất bại")
        return pd.DataFrame(
            columns=["id", "student_code", "full_name", "class_name", "birth_date", "status"]
        )


def add_student(
    student_code: str,
    full_name: str,
    class_name: str,
    birth_date: str,
    status: str,
) -> bool:
    """Thêm học sinh mới. Trả về True nếu thành công."""
    try:
        repo.create_student(student_code, full_name, class_name, birth_date, status)
        st.success("✅ Thêm học sinh thành công!")
        return True
    except ValueError as e:
        st.error(f"❌ Dữ liệu không hợp lệ: {e}")
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg or "duplicate" in msg:
            st.error("❌ Mã học sinh đã tồn tại. Vui lòng dùng mã khác.")
        else:
            st.error(f"❌ Lỗi: {e}")
        logger.exception("add_student thất bại")
    return False


def edit_student(
    student_id: int,
    student_code: str,
    full_name: str,
    class_name: str,
    birth_date: str,
    status: str,
) -> bool:
    """Cập nhật thông tin học sinh. Trả về True nếu thành công."""
    try:
        repo.update_student(student_id, student_code, full_name, class_name, birth_date, status)
        st.success("✅ Cập nhật thành công!")
        return True
    except ValueError as e:
        st.error(f"❌ Dữ liệu không hợp lệ: {e}")
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg or "duplicate" in msg:
            st.error("❌ Mã học sinh đã tồn tại.")
        else:
            st.error(f"❌ Lỗi: {e}")
        logger.exception("edit_student thất bại id=%s", student_id)
    return False


def remove_student(student_id: int) -> bool:
    """Xóa học sinh theo ID. Trả về True nếu thành công."""
    try:
        repo.delete_student(student_id)
        st.success("✅ Xóa học sinh thành công!")
        return True
    except Exception as e:
        st.error(f"❌ Lỗi khi xóa: {e}")
        logger.exception("remove_student thất bại id=%s", student_id)
    return False


# ===========================================================================
# UI
# ===========================================================================

st.title("🎓 Quản lý học sinh")

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Danh sách",
    "➕ Thêm học sinh",
    "✏️ Sửa học sinh",
    "🗑️ Xóa học sinh",
])

# ---------------------------------------------------------------------------
# TAB 1 — DANH SÁCH
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Danh sách học sinh")

    df = load_students()

    col1, col2 = st.columns(2)
    search_name = col1.text_input("🔍 Tìm theo họ tên")
    search_code = col2.text_input("🔍 Tìm theo mã học sinh")

    filtered = df.copy()
    if search_name:
        filtered = filtered[
            filtered["full_name"].str.contains(search_name, case=False, na=False)
        ]
    if search_code:
        filtered = filtered[
            filtered["student_code"].str.contains(search_code, case=False, na=False)
        ]

    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.info(f"Tổng: **{len(filtered)}** học sinh")

# ---------------------------------------------------------------------------
# TAB 2 — THÊM HỌC SINH
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Thêm học sinh mới")

    with st.form("form_add_student", clear_on_submit=True):
        c1, c2 = st.columns(2)
        new_code = c1.text_input("Mã học sinh *")
        new_name = c2.text_input("Họ và tên *")

        c3, c4 = st.columns(2)
        new_class = c3.text_input("Lớp *")
        new_birth = c4.date_input("Ngày sinh", value=date(2015, 1, 1))

        new_status = st.selectbox("Trạng thái", ["Đang học", "Nghỉ học"])

        if st.form_submit_button("💾 Lưu học sinh", use_container_width=True):
            if add_student(new_code, new_name, new_class, str(new_birth), new_status):
                st.rerun()

# ---------------------------------------------------------------------------
# TAB 3 — SỬA HỌC SINH
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Sửa thông tin học sinh")

    df_edit = load_students()

    if df_edit.empty:
        st.warning("Chưa có học sinh nào.")
    else:
        options_edit = {
            f"{row['student_code']} — {row['full_name']}": int(row["id"])
            for _, row in df_edit.iterrows()
        }
        selected_edit = st.selectbox("Chọn học sinh", list(options_edit.keys()), key="sel_edit")
        sid_edit = options_edit[selected_edit]
        student = df_edit[df_edit["id"] == sid_edit].iloc[0]

        with st.form("form_edit_student"):
            c1, c2 = st.columns(2)
            e_code = c1.text_input("Mã học sinh", value=student["student_code"])
            e_name = c2.text_input("Họ và tên", value=student["full_name"])

            c3, c4 = st.columns(2)
            e_class = c3.text_input("Lớp", value=student["class_name"])
            e_birth = c4.text_input("Ngày sinh (YYYY-MM-DD)", value=str(student["birth_date"]))

            e_status = st.selectbox(
                "Trạng thái",
                ["Đang học", "Nghỉ học"],
                index=0 if student["status"] == "Đang học" else 1,
            )

            if st.form_submit_button("✏️ Cập nhật", use_container_width=True):
                if edit_student(sid_edit, e_code, e_name, e_class, e_birth, e_status):
                    st.rerun()

# ---------------------------------------------------------------------------
# TAB 4 — XÓA HỌC SINH
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Xóa học sinh")

    df_del = load_students()

    if df_del.empty:
        st.warning("Không có dữ liệu học sinh.")
    else:
        options_del = {
            f"{row['student_code']} — {row['full_name']}": int(row["id"])
            for _, row in df_del.iterrows()
        }
        selected_del = st.selectbox("Chọn học sinh cần xóa", list(options_del.keys()), key="sel_del")
        sid_del = options_del[selected_del]

        st.warning("⚠️ Hành động này **không thể hoàn tác**.")
        confirm = st.checkbox("Tôi xác nhận muốn xóa học sinh này")

        if st.button("🗑️ Xóa học sinh", use_container_width=True, type="primary"):
            if not confirm:
                st.error("Vui lòng tick xác nhận trước khi xóa.")
            else:
                if remove_student(sid_del):
                    st.rerun()
