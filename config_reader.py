"""
配置读取模块
使用腾讯文档Open API读取数据
"""
import requests
import streamlit as st
from datetime import datetime
import hashlib
import time

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
            self.app_id = st.secrets["tencent_doc"]["app_id"]
            self.app_key = st.secrets["tencent_doc"]["app_key"]
        except:
            self.app_id = None
            self.app_key = None
            st.warning("未配置腾讯文档API凭证")
    
    def get_corridor_status(self):
        """获取连廊状态"""
        if self._cache is not None and self._cache_time is not None:
            if (datetime.now() - self._cache_time).seconds < self.cache_duration:
                return self._cache
        
        try:
            if self.app_id and self.app_key and self.doc_id:
                data = self._fetch_via_api()
            else:
                data = self._fetch_via_public()
            
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
                st.warning("⚠️ 无法读取数据，使用默认配置")
            
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
            url = f"https://docs.qq.com/openapi/v1/sheets/{self.doc_id}/values"
            
            # 生成签名
            timestamp = str(int(time.time()))
            nonce = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
            sign_str = f"{self.app_id}{self.app_key}{timestamp}{nonce}"
            signature = hashlib.md5(sign_str.encode()).hexdigest()
            
            headers = {
                'X-App-Id': self.app_id,
                'X-Timestamp': timestamp,
                'X-Nonce': nonce,
                'X-Signature': signature,
                'Content-Type': 'application/json'
            }
            
            params = {
                'range': 'A:C',  # 读取A到C列
                'majorDimension': 'ROWS'
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
            return None
        except Exception as e:
            st.warning(f"API读取失败: {str(e)}")
            return None
    
    def _fetch_via_public(self):
        """备用方案：尝试公开导出"""
        try:
            urls = [
                f"https://docs.qq.com/sheet/{self.doc_id}/export?format=csv",
                f"https://docs.qq.com/sheet/{self.doc_id}?format=csv",
            ]
            
            import re
            for url in urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        content = response.text
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        if len(lines) >= 2:
                            last_line = lines[-1]
                            parts = re.split(r'[,\t]+', last_line)
                            parts = [p.strip() for p in parts if p.strip()]
                            if len(parts) >= 3:
                                return {
                                    'time': parts[0],
                                    'distance': float(parts[1]) if parts[1] else 0,
                                    'status': int(parts[2]) if parts[2] else 0
                                }
                except:
                    continue
            return None
        except:
            return None
