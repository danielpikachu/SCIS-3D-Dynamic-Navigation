"""
配置读取模块
使用腾讯文档Open API读取数据
"""
import requests
import streamlit as st
from datetime import datetime
import re

class ConfigReader:
    """腾讯文档Open API配置读取器"""
    
    def __init__(self, doc_url, cache_duration=10):
        self.doc_url = doc_url
        self.cache_duration = cache_duration
        self._cache = None
        self._cache_time = None
        
        # 从文档URL中提取文档ID
        match = re.search(r'/sheet/([A-Za-z0-9]+)', doc_url)
        self.doc_id = match.group(1) if match else None
        
        # 不在 __init__ 中读取 secrets，改为在方法中读取
        self._client_id = None
        self._access_token = None
        self._open_id = None
    
    def _get_credentials(self):
        """获取API凭证，每次调用时从 st.secrets 读取"""
        if self._client_id is None:
            try:
                self._client_id = st.secrets["tencent_doc"]["client_id"]
                self._access_token = st.secrets["tencent_doc"]["access_token"]
                self._open_id = st.secrets["tencent_doc"]["open_id"]
            except Exception as e:
                st.error(f"读取腾讯文档凭证失败: {e}")
                self._client_id = None
                self._access_token = None
                self._open_id = None
        return self._client_id, self._access_token, self._open_id
    
    def get_corridor_status(self):
        """获取连廊状态"""
        if self._cache is not None and self._cache_time is not None:
            if (datetime.now() - self._cache_time).seconds < self.cache_duration:
                return self._cache
        
        # 获取凭证
        client_id, access_token, open_id = self._get_credentials()
        
        if not client_id or not access_token:
            st.warning("⚠️ 腾讯文档API凭证不完整，使用默认配置（连廊开放）")
            return {
                'level2_disabled': False,
                'status_value': 0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'distance': 0
            }
        
        try:
            data = self._fetch_via_api(client_id, access_token, open_id)
            
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
                st.warning("⚠️ API返回空数据，使用默认配置（连廊开放）")
            
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
    
    def _fetch_via_api(self, client_id, access_token, open_id):
        """使用腾讯文档Open API读取数据"""
        try:
            url = "https://docs.qq.com/openapi/v2/sheet/get_values"
            
            headers = {
                'Access-Token': access_token,
                'Client-Id': client_id,
                'Open-Id': open_id,
                'Content-Type': 'application/json'
            }
            
            params = {
                'doc_id': self.doc_id,
                'sheet_id': 'BB08J2',
                'range': 'A:C'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                values = data.get('values', [])
                if len(values) >= 2:
                    last_row = values[-1]
                    if len(last_row) >= 3:
                        return {
                            'time': last_row[0],
                            'distance': float(last_row[1]) if last_row[1] else 0,
                            'status': int(last_row[2]) if last_row[2] else 0
                        }
            else:
                st.warning(f"API请求失败: {response.status_code}")
            return None
        except Exception as e:
            st.warning(f"API读取失败: {str(e)}")
            return None
