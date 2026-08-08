"""
配置读取模块
从腾讯文档读取超声波传感器数据，控制连廊开关
"""
import requests
import re
import streamlit as st
from datetime import datetime
import pandas as pd
from io import StringIO

class ConfigReader:
    """腾讯文档配置读取器 - 读取超声波传感器数据"""
    
    def __init__(self, doc_url, cache_duration=10):
        """
        初始化配置读取器
        
        Args:
            doc_url: 腾讯文档链接
            cache_duration: 缓存时间（秒），超声波数据需要快速响应，设短一些
        """
        self.doc_url = doc_url
        self.cache_duration = cache_duration
        self._cache = None
        self._cache_time = None
        self._last_status = None
    
    def get_corridor_status(self):
        """
        获取连廊状态
        
        Returns:
            dict: {
                'level2_disabled': True/False,  # True=禁用2楼连廊
                'status_value': 0/1,            # 原始STATUS值
                'timestamp': '2026-08-08 10:00', # 数据时间
                'distance': 65.3                # 距离值（可选）
            }
        """
        # 检查缓存
        if self._cache is not None and self._cache_time is not None:
            if (datetime.now() - self._cache_time).seconds < self.cache_duration:
                return self._cache
        
        try:
            # 从腾讯文档读取数据
            data = self._fetch_from_tencent()
            
            if data:
                # STATUS=1 表示人流多，禁用2楼连廊
                result = {
                    'level2_disabled': (data['status'] == 1),
                    'status_value': data['status'],
                    'timestamp': data['time'],
                    'distance': data['distance']
                }
            else:
                # 读取失败，使用默认值（不禁用）
                result = {
                    'level2_disabled': False,
                    'status_value': 0,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'distance': 0
                }
                st.warning("⚠️ 无法读取传感器数据，使用默认配置（连廊开放）")
            
            # 更新缓存
            self._cache = result
            self._cache_time = datetime.now()
            self._last_status = result
            
            return result
            
        except Exception as e:
            st.error(f"读取配置失败: {str(e)}")
            return {
                'level2_disabled': False,
                'status_value': 0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'distance': 0
            }
    
    def _fetch_from_tencent(self):
        """从腾讯文档获取最新数据"""
        # 尝试多种URL格式
        urls = [
            f"{self.doc_url.replace('/sheet/', '/export/')}?format=csv",
            f"{self.doc_url}&format=csv",
            f"{self.doc_url}?format=csv",
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = self._parse_csv(response.text)
                    if data:
                        return data
            except:
                continue
        
        return None
    
    def _parse_csv(self, content):
        """解析CSV，提取最后一行数据"""
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        
        if len(lines) < 2:
            return None
        
        # 检查表头
        header = lines[0].upper()
        if not ('TIME' in header and 'DISTANCE' in header and 'STATUS' in header):
            return None
        
        # 获取最后一行
        last_line = lines[-1]
        
        # 解析：支持逗号、制表符分隔
        parts = re.split(r'[,\t]+', last_line)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) >= 3:
            try:
                time_str = parts[0]
                distance = float(parts[1]) if parts[1] else 0
                status = int(re.search(r'(\d+)', parts[2]).group(1)) if re.search(r'(\d+)', parts[2]) else 0
                
                return {
                    'time': time_str,
                    'distance': distance,
                    'status': status
                }
            except:
                return None
        
        return None
    
    def is_corridor_open(self):
        """快捷方法：判断连廊是否开放"""
        status = self.get_corridor_status()
        return not status['level2_disabled']
    
    def get_status_display(self):
        """获取显示用的状态文字"""
        status = self.get_corridor_status()
        if status['level2_disabled']:
            return "🚫 人流量大，2楼连廊已关闭"
        else:
            return "✅ 人流量正常，2楼连廊开放"
