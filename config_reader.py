import streamlit as st
import pandas as pd
from supabase import create_client


@st.cache_resource
def init_supabase():
    """初始化 Supabase 客户端（带详细错误信息）"""
    try:
        # 第一步：检查 st.secrets 中是否有 'supabase' 区块
        if "supabase" not in st.secrets:
            st.error("❌ 错误1：st.secrets 中没有 'supabase' 区块")
            return None
        
        supabase_config = st.secrets["supabase"]
        
        # 第二步：检查 'url' 和 'key' 是否存在
        if "url" not in supabase_config:
            st.error("❌ 错误2：'supabase' 区块中没有 'url' 字段")
            return None
        if "key" not in supabase_config:
            st.error("❌ 错误3：'supabase' 区块中没有 'key' 字段")
            return None
        
        url = supabase_config["url"]
        key = supabase_config["key"]
        
        st.success(f"✅ 成功读取配置: url = {url}")
        
        # 第三步：尝试连接 Supabase
        try:
            client = create_client(url, key)
            st.success("✅ Supabase 客户端创建成功")
            return client
        except Exception as e:
            st.error(f"❌ 错误4：创建 Supabase 客户端失败: {e}")
            return None
            
    except Exception as e:
        st.error(f"❌ 错误5：初始化过程出现未知错误: {e}")
        return None


def get_latest_people_flow():
    """获取最新一条记录的人流量标记（带详细错误信息）"""
    
    # 第一步：初始化客户端
    supabase = init_supabase()
    if supabase is None:
        st.error("❌ 错误6：Supabase 客户端初始化失败，无法继续查询")
        return None
    
    try:
        # 第二步：打印要查询的表名
        st.write("🔍 正在查询表: `people_flow`")
        
        # 第三步：执行查询
        response = supabase.table("people_flow")\
            .select("people_flow")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        # 第四步：检查查询结果
        st.write(f"🔍 查询返回的原始数据: {response.data}")
        
        if response.data is None:
            st.warning("⚠️ 查询返回的数据为 None")
            return None
        
        if len(response.data) == 0:
            st.warning("⚠️ 表中没有数据，请先在 Supabase 中插入一条记录")
            return None
        
        # 第五步：提取 people_flow 值
        result = response.data[0].get('people_flow')
        st.write(f"🔍 提取到的 people_flow 值: {result} (类型: {type(result)})")
        
        if result is None:
            st.warning("⚠️ 记录中没有 'people_flow' 字段，请检查列名是否正确")
            return None
        
        return result
        
    except Exception as e:
        st.error(f"❌ 错误7：查询执行失败: {e}")
        return None
