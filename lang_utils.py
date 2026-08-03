# lang_utils.py
import streamlit as st
from languages import LANGUAGES, SUPPORTED_LANGUAGES, LANGUAGE_NAMES

def init_language():
    """初始化语言设置"""
    if 'language' not in st.session_state:
        st.session_state['language'] = 'en'

def get_lang():
    """获取当前语言"""
    return st.session_state.get('language', 'en')

def get_text(key):
    """获取当前语言的文本"""
    lang = get_lang()
    if lang not in LANGUAGES:
        lang = 'en'
    return LANGUAGES[lang].get(key, key)

def language_selector():
    """语言选择器组件"""
    init_language()
    current_lang = get_lang()
    
    # 创建语言选择下拉菜单
    lang_options = list(LANGUAGE_NAMES.keys())
    
    # 使用selectbox
    selected = st.selectbox(
        "🌐 Language / 语言",
        options=lang_options,
        format_func=lambda x: LANGUAGE_NAMES[x],
        index=lang_options.index(current_lang) if current_lang in lang_options else 0
    )
    
    if selected != current_lang:
        st.session_state['language'] = selected
        st.rerun()
    
    return selected

def get_direction_text(direction_key, lang=None):
    """获取方向文本（带HTML样式）"""
    if lang is None:
        lang = get_lang()
    
    direction_map = {
        'up': ('<span style="color:DarkGoldenRod; font-weight:bold;">up</span>', 
               '<span style="color:DarkGoldenRod; font-weight:bold;">上</span>'),
        'down': ('<span style="color:DarkGoldenRod; font-weight:bold;">down</span>',
                '<span style="color:DarkGoldenRod; font-weight:bold;">下</span>'),
        'forward': ('<span style="color:DarkGoldenRod; font-weight:bold;">forward</span>',
                   '<span style="color:DarkGoldenRod; font-weight:bold;">向前</span>'),
        'backward': ('<span style="color:DarkGoldenRod; font-weight:bold;">backward</span>',
                    '<span style="color:DarkGoldenRod; font-weight:bold;">向后</span>'),
        'right': ('<span style="color:DarkGoldenRod; font-weight:bold;">right</span>',
                 '<span style="color:DarkGoldenRod; font-weight:bold;">向右</span>'),
        'left': ('<span style="color:DarkGoldenRod; font-weight:bold;">left</span>',
                '<span style="color:DarkGoldenRod; font-weight:bold;">向左</span>')
    }
    
    if direction_key in direction_map:
        return direction_map[direction_key][0 if lang == 'en' else 1]
    return direction_key

def get_node_type_text(node_type, lang=None):
    """获取节点类型文本"""
    if lang is None:
        lang = get_lang()
    
    type_map = {
        'stair': ('Stair', '楼梯'),
        'elevator': ('Elevator', '电梯'),
        'classroom': ('Classroom', '教室'),
        'corridor': ('Corridor', '走廊')
    }
    
    if node_type in type_map:
        return type_map[node_type][0 if lang == 'en' else 1]
    return node_type
