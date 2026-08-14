import streamlit as st
import pandas as pd
from supabase import create_client


@st.cache_resource
def init_supabase():
    """初始化 Supabase 客户端"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.warning(f"⚠️ Supabase 连接失败: {e}")
        return None


def get_latest_people_flow():
    """
    获取最新一条记录的人流量标记
    
    Returns:
        int: 0 或 1（如果表里有数据）
        None: 如果没数据或读取失败
    """
    supabase = init_supabase()
    if supabase is None:
        return None
    
    try:
        response = supabase.table("people_flow")\
            .select("people_flow")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0].get('people_flow')
        return None
    except Exception as e:
        return None
