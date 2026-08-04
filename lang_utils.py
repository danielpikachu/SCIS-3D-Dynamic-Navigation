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
        "🌐 Language / 语言 / Langue",
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
    
    # 方向映射：支持英文、中文、法语
    direction_map = {
        'up': (
            '<span style="color:DarkGoldenRod; font-weight:bold;">up</span>',      # English
            '<span style="color:DarkGoldenRod; font-weight:bold;">上</span>',       # 中文
            '<span style="color:DarkGoldenRod; font-weight:bold;">monter</span>'    # Français
        ),
        'down': (
            '<span style="color:DarkGoldenRod; font-weight:bold;">down</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">下</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">descendre</span>'
        ),
        'forward': (
            '<span style="color:DarkGoldenRod; font-weight:bold;">forward</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">向前</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">tout droit</span>'
        ),
        'backward': (
            '<span style="color:DarkGoldenRod; font-weight:bold;">backward</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">向后</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">reculer</span>'
        ),
        'right': (
            '<span style="color:DarkGoldenRod; font-weight:bold;">right</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">向右</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">à droite</span>'
        ),
        'left': (
            '<span style="color:DarkGoldenRod; font-weight:bold;">left</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">向左</span>',
            '<span style="color:DarkGoldenRod; font-weight:bold;">à gauche</span>'
        )
    }
    
    # 语言到索引的映射
    lang_index = {
        'en': 0,
        'zh': 1,
        'fr': 2
    }
    
    # 获取当前语言的索引，如果语言不在映射中则默认为英文
    idx = lang_index.get(lang, 0)
    
    if direction_key in direction_map:
        return direction_map[direction_key][idx]
    return direction_key

def get_node_type_text(node_type, lang=None):
    """获取节点类型文本"""
    if lang is None:
        lang = get_lang()
    
    # 节点类型映射：支持英文、中文、法语
    type_map = {
        'stair': (
            'Stair',           # English
            '楼梯',            # 中文
            'Escalier'         # Français
        ),
        'elevator': (
            'Elevator',        # English
            '电梯',            # 中文
            'Ascenseur'        # Français
        ),
        'classroom': (
            'Classroom',       # English
            '教室',            # 中文
            'Salle de classe'  # Français
        ),
        'corridor': (
            'Corridor',        # English
            '走廊',            # 中文
            'Couloir'          # Français
        )
    }
    
    # 语言到索引的映射
    lang_index = {
        'en': 0,
        'zh': 1,
        'fr': 2
    }
    
    # 获取当前语言的索引，如果语言不在映射中则默认为英文
    idx = lang_index.get(lang, 0)
    
    if node_type in type_map:
        return type_map[node_type][idx]
    return node_type

def get_building_text(building, lang=None):
    """获取建筑名称文本"""
    if lang is None:
        lang = get_lang()
    
    # 建筑名称映射
    building_map = {
        'A': ('A', 'A楼', 'Bâtiment A'),
        'B': ('B', 'B楼', 'Bâtiment B'),
        'C': ('C', 'C楼', 'Bâtiment C'),
        'Gate': ('Gate', '校门', 'Porte')
    }
    
    lang_index = {
        'en': 0,
        'zh': 1,
        'fr': 2
    }
    
    idx = lang_index.get(lang, 0)
    
    if building in building_map:
        return building_map[building][idx]
    return building

def get_floor_text(floor, lang=None):
    """获取楼层名称文本"""
    if lang is None:
        lang = get_lang()
    
    # 楼层名称映射
    floor_map = {
        'level1': ('Level 1', '1楼', 'Niveau 1'),
        'level2': ('Level 2', '2楼', 'Niveau 2'),
        'level3': ('Level 3', '3楼', 'Niveau 3'),
        'level4': ('Level 4', '4楼', 'Niveau 4'),
        'level5': ('Level 5', '5楼', 'Niveau 5'),
        'level6': ('Level 6', '6楼', 'Niveau 6'),
        'level7': ('Level 7', '7楼', 'Niveau 7'),
        'level8': ('Level 8', '8楼', 'Niveau 8'),
        'level9': ('Level 9', '9楼', 'Niveau 9'),
        'level10': ('Level 10', '10楼', 'Niveau 10'),
        'level11': ('Level 11', '11楼', 'Niveau 11'),
        'level12': ('Level 12', '12楼', 'Niveau 12'),
        'level13': ('Level 13', '13楼', 'Niveau 13'),
        'level14': ('Level 14', '14楼', 'Niveau 14'),
        'level15': ('Level 15', '15楼', 'Niveau 15'),
        'level16': ('Level 16', '16楼', 'Niveau 16'),
        'level17': ('Level 17', '17楼', 'Niveau 17'),
        'level18': ('Level 18', '18楼', 'Niveau 18'),
        'level19': ('Level 19', '19楼', 'Niveau 19'),
        'level20': ('Level 20', '20楼', 'Niveau 20'),
        'B1': ('B1', 'B1', 'Sous-sol 1'),
        'B2': ('B2', 'B2', 'Sous-sol 2'),
        'B3': ('B3', 'B3', 'Sous-sol 3'),
        'B4': ('B4', 'B4', 'Sous-sol 4')
    }
    
    lang_index = {
        'en': 0,
        'zh': 1,
        'fr': 2
    }
    
    idx = lang_index.get(lang, 0)
    
    if floor in floor_map:
        return floor_map[floor][idx]
    return floor
