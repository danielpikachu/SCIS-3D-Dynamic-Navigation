"""
配置读取模块
使用腾讯文档Open API读取数据
"""
import requests
import streamlit as st
from datetime import datetime

class ConfigReader:
    """腾讯文档Open API配置读取器"""
    
    def __init__(self, doc_url, cache_duration=10):
        self.doc_url = doc_url
        self.cache_duration = cache_duration
        self._cache = None
        self._cache_time = None
        
        # 从文档URL中提取文档ID
        # URL格式: https://docs.qq.com/sheet/DRU5PcVZMWkJyaWVE?tab=BB08J2
        import re
        match = re.search(r'/sheet/([A-Za-z0-9]+)', doc_url)
        self.doc_id = match.group(1) if match else None
        
        # 从secrets获取API凭证
        try:
            self.client_id = st.secrets["tencent_doc"]["client_id"]
            self.access_token = st.secrets["tencent_doc"]["access_token"]
            self.open_id = st.secrets["tencent_doc"]["open_id"]
        except:
            self.client_id = None
            self.access_token = None
            self.open_id = None
            st.warning("未配置腾讯文档API凭证")
    
    def get_corridor_status(self):
        """获取连廊状态"""
        if self._cache is not None and self._cache_time is not None:
            if (datetime.now() - self._cache_time).seconds < self.cache_duration:
                return self._cache
        
        try:
            if self.client_id and self.access_token and self.doc_id:
                data = self._fetch_via_api()
            else:
                data = None
            
            if data:
                result = {
                    'level2_disabled': (data['status'] == 1),
                    'status_value': data['status'],
                    'timestamp': data['time'],
                    'distance': data['distance']
                }
            else:
                result = {
                    'level2_disabled': False,
                    'status_value': 0,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'distance': 0
                }
                st.warning("⚠️ 无法读取数据，使用默认配置（连廊开放）")
            
            self._cache = result
            self._cache_time = datetime.now()
            return result
            
        except Exception as e:
            st.error(f"读取失败: {str(e)}")
            return {
                'level2_disabled': False,
                'status_value': 0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'distance': 0
            }
    
    def _fetch_via_api(self):
        """使用腾讯文档Open API读取数据"""
        try:
            # 腾讯文档API - 读取表格内容
            # API文档: https://docs.qq.com/open/document/app/openapi/v2/sheet/get_values.html
            url = f"https://docs.qq.com/openapi/v2/sheet/get_values"
            
            headers = {
                'Access-Token': self.access_token,
                'Client-Id': self.client_id,
                'Open-Id': self.open_id,
                'Content-Type': 'application/json'
            }
            
            params = {
                'doc_id': self.doc_id,
                'sheet_id': 'BB08J2',  # 你的sheet ID（从URL的tab参数获取）
                'range': 'A:C'  # 读取A到C列
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # 根据API返回格式解析数据
                # 不同API版本返回格式可能略有不同
                values = data.get('values', [])
                if len(values) >= 2:
                    # 最后一行数据
                    last_row = values[-1]
                    if len(last_row) >= 3:
                        return {
                            'time': last_row[0],
                            'distance': float(last_row[1]) if last_row[1] else 0,
                            'status': int(last_row[2]) if last_row[2] else 0
                        }
            else:
                st.warning(f"API请求失败: {response.status_code} - {response.text[:200]}")
            return None
        except Exception as e:
            st.warning(f"API读取失败: {str(e)}")
            return None
