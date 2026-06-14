
"""
database/supabase_client.py
Khởi tạo và cache Supabase client.
Đọc credentials từ Streamlit secrets hoặc environment variables.
"""

import logging
import os

from supabase import create_client, Client
import streamlit as st

logger = logging.getLogger(__name__)


@st.cache_resource
def get_supabase() -> Client:
    """
    Trả về Supabase client (cached toàn bộ session).
    Ưu tiên Streamlit secrets, fallback sang environment variables.
    """
    url: str | None = None
    key: str | None = None

    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        pass

    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL và SUPABASE_KEY phải được cấu hình trong "
            ".streamlit/secrets.toml hoặc biến môi trường."
        )

    logger.info("Khởi tạo Supabase client: %s", url[:40])
    return create_client(url, key)
