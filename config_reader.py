import streamlit as st
import pandas as pd
from supabase import create_client


@st.cache_resource
def init_supabase():
    """初始化 Supabase 客户端"""
    try:
        # 检查密钥是否存在
        if "supabase" not in st.secrets:
            st.error("❌ st.secrets 中没有 'supabase' 区块")
            return None
        
        supabase_config = st.secrets["supabase"]
        st.write(f"🔍 读取到 supabase 配置: url = {supabase_config.get('url', '未找到')}")
        
        url = supabase_config["url"]
        key = supabase_config["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Supabase 连接失败: {e}")
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
        st.warning("⚠️ Supabase 客户端初始化失败")
        return None
    
    try:
        # 先打印表名，确认是否正确
        st.write("🔍 正在查询表: people_flow")
        
        response = supabase.table("people_flow")\
            .select("people_flow")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        # 打印查询结果
        st.write(f"🔍 查询返回数据: {response.data}")
        
        if response.data and len(response.data) > 0:
            result = response.data[0].get('people_flow')
            st.write(f"🔍 获取到的 people_flow 值: {result}")
            return result
        else:
            st.warning("⚠️ 表中没有数据或查询结果为空")
            return None
    except Exception as e:
        st.error(f"❌ 查询失败: {e}")
        return None
