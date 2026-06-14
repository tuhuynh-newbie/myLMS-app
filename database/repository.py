"""
database/repository.py
Lớp truy xuất dữ liệu duy nhất cho toàn bộ LMS.
Mọi module UI chỉ import từ đây — không gọi Supabase trực tiếp.

Thiết kế theo Repository Pattern để dễ chuyển backend (SQLite → Supabase).
"""

import logging
from typing import Any

from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# ===========================================================================
# INTERNAL HELPERS
# ===========================================================================

def _normalize_response(res: Any) -> list[dict]:
    """Chuẩn hoá response từ Supabase, raise nếu có lỗi."""
    if getattr(res, "error", None):
        logger.error("Supabase error: %s", res.error)
        raise Exception(res.error)
    return res.data or []


# ===========================================================================
# STUDENTS
# ===========================================================================

def get_students(class_name: str | None = None, status: str | None = None) -> list[dict]:
    """
    Lấy danh sách học sinh, có thể lọc theo lớp và trạng thái.

    Args:
        class_name: Tên lớp để lọc (None = tất cả lớp).
        status: Trạng thái học sinh (None = tất cả).

    Returns:
        Danh sách dict học sinh, sắp xếp id giảm dần.
    """
    try:
        supabase = get_supabase()
        query = supabase.table("students").select("*").order("id", desc=True)
        if class_name:
            query = query.eq("class_name", class_name)
        if status:
            query = query.eq("status", status)
        res = query.execute()
        return _normalize_response(res)
    except Exception as e:
        logger.exception("get_students thất bại: %s", e)
        raise


def get_classes() -> list[str]:
    """Lấy danh sách tên lớp không trùng, sắp xếp alphabet."""
    try:
        supabase = get_supabase()
        res = supabase.table("students").select("class_name").execute()
        rows = _normalize_response(res)
        return sorted({row["class_name"] for row in rows if row.get("class_name")})
    except Exception as e:
        logger.exception("get_classes thất bại: %s", e)
        raise


def create_student(
    student_code: str,
    full_name: str,
    class_name: str,
    birth_date: str,
    status: str,
) -> list[dict]:
    """
    Thêm học sinh mới vào bảng students.

    Args:
        student_code: Mã học sinh (phải unique).
        full_name: Họ và tên đầy đủ.
        class_name: Tên lớp.
        birth_date: Ngày sinh định dạng YYYY-MM-DD.
        status: "Đang học" hoặc "Nghỉ học".

    Returns:
        Bản ghi vừa tạo.

    Raises:
        Exception: Nếu student_code trùng hoặc lỗi DB.
    """
    _validate_student(student_code, full_name, class_name, birth_date, status)
    try:
        supabase = get_supabase()
        payload = {
            "student_code": student_code.strip(),
            "full_name": full_name.strip(),
            "class_name": class_name.strip(),
            "birth_date": birth_date,
            "status": status,
        }
        res = supabase.table("students").insert(payload).execute()
        logger.info("Tạo học sinh mới: %s - %s", student_code, full_name)
        return _normalize_response(res)
    except Exception as e:
        logger.exception("create_student thất bại: %s", e)
        raise


def update_student(
    student_id: int,
    student_code: str,
    full_name: str,
    class_name: str,
    birth_date: str,
    status: str,
) -> list[dict]:
    """
    Cập nhật thông tin học sinh theo ID.

    Args:
        student_id: ID bản ghi cần cập nhật.
        student_code: Mã học sinh mới.
        full_name: Họ tên mới.
        class_name: Tên lớp mới.
        birth_date: Ngày sinh mới (YYYY-MM-DD).
        status: Trạng thái mới.

    Returns:
        Bản ghi đã cập nhật.
    """
    _validate_student(student_code, full_name, class_name, birth_date, status)
    try:
        supabase = get_supabase()
        payload = {
            "student_code": student_code.strip(),
            "full_name": full_name.strip(),
            "class_name": class_name.strip(),
            "birth_date": birth_date,
            "status": status,
        }
        res = (
            supabase
            .table("students")
            .update(payload)
            .eq("id", student_id)
            .execute()
        )
        logger.info("Cập nhật học sinh id=%s", student_id)
        return _normalize_response(res)
    except Exception as e:
        logger.exception("update_student thất bại id=%s: %s", student_id, e)
        raise


def delete_student(student_id: int) -> list[dict]:
    """
    Xóa học sinh theo ID.

    Args:
        student_id: ID bản ghi cần xóa.

    Returns:
        Bản ghi đã xóa.
    """
    if not isinstance(student_id, int) or student_id <= 0:
        raise ValueError(f"student_id không hợp lệ: {student_id}")
    try:
        supabase = get_supabase()
        res = (
            supabase
            .table("students")
            .delete()
            .eq("id", student_id)
            .execute()
        )
        logger.info("Xóa học sinh id=%s", student_id)
        return _normalize_response(res)
    except Exception as e:
        logger.exception("delete_student thất bại id=%s: %s", student_id, e)
        raise


# ===========================================================================
# ATTENDANCE
# ===========================================================================

def get_attendance(attendance_date: str) -> list[dict]:
    """Lấy toàn bộ điểm danh trong một ngày cụ thể."""
    try:
        supabase = get_supabase()
        res = (
            supabase
            .table("attendance")
            .select("*")
            .eq("attendance_date", attendance_date)
            .execute()
        )
        return _normalize_response(res)
    except Exception as e:
        logger.exception("get_attendance thất bại date=%s: %s", attendance_date, e)
        raise


def get_attendance_range(start_date: str, end_date: str) -> list[dict]:
    """Lấy điểm danh trong khoảng ngày [start_date, end_date]."""
    try:
        supabase = get_supabase()
        res = (
            supabase
            .table("attendance")
            .select("*")
            .gte("attendance_date", start_date)
            .lte("attendance_date", end_date)
            .execute()
        )
        return _normalize_response(res)
    except Exception as e:
        logger.exception("get_attendance_range thất bại: %s", e)
        raise


def upsert_attendance(
    student_id: int,
    attendance_date: str,
    attendance_status: str,
    note: str,
) -> list[dict]:
    """
    Tạo hoặc cập nhật bản ghi điểm danh (upsert).
    Conflict key: (student_id, attendance_date).
    """
    valid_statuses = {"Present", "Excused", "Absent"}
    if attendance_status not in valid_statuses:
        raise ValueError(f"attendance_status không hợp lệ: {attendance_status}")
    try:
        supabase = get_supabase()
        payload = {
            "student_id": student_id,
            "attendance_date": attendance_date,
            "attendance_status": attendance_status,
            "note": note or "",
        }
        res = supabase.table("attendance").upsert(
            payload,
            on_conflict="student_id,attendance_date"
        ).execute()
        return _normalize_response(res)
    except Exception as e:
        logger.exception("upsert_attendance thất bại: %s", e)
        raise


# ===========================================================================
# SCORES
# ===========================================================================

def get_scores() -> list[dict]:
    """Lấy toàn bộ bảng điểm."""
    try:
        supabase = get_supabase()
        res = supabase.table("scores").select("*").execute()
        return _normalize_response(res)
    except Exception as e:
        logger.exception("get_scores thất bại: %s", e)
        raise


def save_score(
    student_id: int,
    math_score: float,
    literature_score: float,
    english_score: float,
    average_score: float,
    rank_level: str,
    semester: str,
    school_year: str,
) -> list[dict]:
    """
    Tạo hoặc cập nhật điểm học sinh (upsert).
    Conflict key: (student_id, semester, school_year).
    """
    try:
        supabase = get_supabase()
        payload = {
            "student_id": student_id,
            "math_score": math_score,
            "literature_score": literature_score,
            "english_score": english_score,
            "average_score": average_score,
            "rank_level": rank_level,
            "semester": semester,
            "school_year": school_year,
        }
        res = supabase.table("scores").upsert(
            payload,
            on_conflict="student_id,semester,school_year"
        ).execute()
        logger.info("Lưu điểm student_id=%s %s %s", student_id, semester, school_year)
        return _normalize_response(res)
    except Exception as e:
        logger.exception("save_score thất bại: %s", e)
        raise


def update_score(
    score_id: int,
    math_score: float,
    literature_score: float,
    english_score: float,
    average_score: float,
    rank_level: str,
    semester: str,
    school_year: str,
) -> list[dict]:
    """Cập nhật bản ghi điểm theo score ID."""
    try:
        supabase = get_supabase()
        payload = {
            "math_score": math_score,
            "literature_score": literature_score,
            "english_score": english_score,
            "average_score": average_score,
            "rank_level": rank_level,
            "semester": semester,
            "school_year": school_year,
        }
        res = (
            supabase
            .table("scores")
            .update(payload)
            .eq("id", score_id)
            .execute()
        )
        logger.info("Cập nhật điểm score_id=%s", score_id)
        return _normalize_response(res)
    except Exception as e:
        logger.exception("update_score thất bại id=%s: %s", score_id, e)
        raise


def delete_score(score_id: int) -> list[dict]:
    """Xóa bản ghi điểm theo score ID."""
    try:
        supabase = get_supabase()
        res = (
            supabase
            .table("scores")
            .delete()
            .eq("id", score_id)
            .execute()
        )
        logger.info("Xóa điểm score_id=%s", score_id)
        return _normalize_response(res)
    except Exception as e:
        logger.exception("delete_score thất bại id=%s: %s", score_id, e)
        raise


# ===========================================================================
# VALIDATORS (internal)
# ===========================================================================

def _validate_student(
    student_code: str,
    full_name: str,
    class_name: str,
    birth_date: str,
    status: str,
) -> None:
    """Validate dữ liệu học sinh trước khi ghi DB."""
    if not full_name or not full_name.strip():
        raise ValueError("Họ tên không được để trống.")
    if not student_code or not student_code.strip():
        raise ValueError("Mã học sinh không được để trống.")
    if not class_name or not class_name.strip():
        raise ValueError("Tên lớp không được để trống.")
    if not birth_date:
        raise ValueError("Ngày sinh không được để trống.")
    valid_statuses = {"Đang học", "Nghỉ học"}
    if status not in valid_statuses:
        raise ValueError(f"Trạng thái không hợp lệ: {status}. Phải là: {valid_statuses}")
