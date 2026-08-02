import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import copy

# ====================== 移动端适配核心：页面全局配置 ======================
st.set_page_config(
    page_title="SCIS Navigation System",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)

plt.switch_backend('Agg')

# --------------------------
# Google Sheets 访问统计配置 --------------------------
SHEET_NAME = 'Navigation visitors'
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    try:
        service_account_info = st.secrets["google_service_account"]
        return Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPE
        )
    except KeyError:
        st.error("google_service_account 未配置在Streamlit Secrets中，请检查密钥格式")
        return None
    except Exception as e:
        st.error(f"密钥加载失败: {str(e)}")
        return None

def init_google_sheet():
    try:
        creds = get_credentials()
        if not creds:
            return None
        client = gspread.authorize(creds)
        
        try:
            sheet = client.open(SHEET_NAME)
        except gspread.exceptions.SpreadsheetNotFound:
            sheet = client.create(SHEET_NAME)
        
        try:
            stats_worksheet = sheet.worksheet("Access_Stats")
        except gspread.exceptions.WorksheetNotFound:
            stats_worksheet = sheet.add_worksheet(title="Access_Stats", rows="1000", cols=3)
            stats_worksheet.append_row(["Timestamp", "Access_Count", "Total_Accesses"])
            stats_worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1, 1])
        
        return stats_worksheet
    except Exception as e:
        return None

def update_access_count(worksheet):
    if not worksheet:
        return 0
        
    try:
        records = worksheet.get_all_values()
        if len(records) < 2:
            return 0
            
        last_row = records[-1]
        total = int(last_row[2]) if last_row[2].isdigit() else 0
        new_total = total + 1
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([current_time, 1, new_total])
        
        return new_total
    except Exception as e:
        return 0

def get_total_accesses(worksheet):
    if not worksheet:
        return 0
        
    try:
        records = worksheet.get_all_values()
        if len(records) < 2:
            return 0
            
        last_row = records[-1]
        return int(last_row[2]) if last_row[2].isdigit() else 0
    except Exception as e:
        return 0

# --------------------------
# 全局配色方案（楼梯、电梯、走廊、路线区分） --------------------------
COLORS = {
    'building': {'A': 'lightblue', 'B': 'lightgreen', 'C': 'lightcoral', 'Gate': 'gold'},
    'floor_z': {-9: 'darkgray', -6: 'blue', -3: 'cyan', 2: 'green', 7: 'orange', 12: 'purple', 17: 'teal'},
    'corridor_line': {'A': 'cyan', 'B': 'forestgreen', 'C': 'salmon', 'Gate': 'darkgoldenrod'},
    'corridor_node': 'navy',
    'corridor_label': 'darkblue',
    'stair': {
        'Stairs1': '#FF5733',
        'Stairs2': '#33FF57',
        'Stairs3': '#3357FF',
        'Stairs4': '#FF33F5',
        'Stairs5': '#F5FF33',
        'StairsB1': '#33FFF5',
        'StairsB2': '#FF9933',
        'GateStairs': '#FFD700'
    },
    'stair_label': 'darkred',
    'classroom_label': 'black',
    'path': 'red',
    'start_marker': 'limegreen',
    'start_label': 'green',
    'end_marker': 'magenta',
    'end_label': 'purple',
    'connect_corridor': 'gold',
    'building_label': {'A': 'darkblue', 'B': 'darkgreen', 'C': 'darkred', 'Gate': 'darkgoldenrod'},
    'elevator': {
        'ElevatorB1': '#00BFFF'
    },
    'elevator_label': 'darkblue',
    'path_elevator': 'deepskyblue'
}

# 读取校园JSON地图数据
def load_school_data_detailed(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"地图数据文件加载失败: {str(e)}")
        return None

# ====================== Plotly 3D地图渲染函数 ======================
def plot_3d_map_plotly(school_data, graph=None, display_options=None):
    fig = go.Figure()

    if display_options is None:
        display_options = {
            'start_level': None,
            'end_level': None,
            'path_stairs': set(),
            'show_all': True,
            'path': [],
            'start_building': None,
            'end_building': None
        }
    
    show_all = display_options['show_all']
    start_level = display_options['start_level']
    end_level = display_options['end_level']
    path_stairs = display_options['path_stairs']
    path = display_options.get('path', [])
    start_building = display_options.get('start_building')
    end_building = display_options.get('end_building')

    building_label_positions = {}
    shown_stairs_legends = set()

    for building_id in school_data.keys():
        if building_id == 'gate':
            building_name = 'Gate'
        elif building_id.startswith('building'):
            building_name = building_id.replace('building', '')
        else:
            continue
            
        building_data = school_data[building_id]
        
        displayed_levels = []
        max_displayed_z = -float('inf')
        max_displayed_y = -float('inf')
        corresponding_x = 0
        level_count = 0
        
        for level in building_data['levels']:
            level_name = level['name']
            raw_z = level['z']
            z = raw_z + 10
            
            show_level = show_all
            if not show_all:
                if building_name == 'B':
                    show_level = (level_name == 'level1') or any((building_name, s, level_name) in path_stairs for s in ['StairsB1','StairsB2','ElevatorB1'])
                elif building_name == 'Gate':
                    show_level = True
                else:
                    show_level = (level_name == start_level) or (level_name == end_level)
            
            if show_level:
                displayed_levels.append(level)
                if z > max_displayed_z:
                    max_displayed_z = z
                
                fp = level['floorPlane']
                current_max_y = fp['maxY']
                if current_max_y > max_displayed_y:
                    max_displayed_y = current_max_y
                    corresponding_x = (fp['minX'] + fp['maxX']) / 2
            
            level_count += 1
            floor_border_color = COLORS['floor_z'].get(raw_z, 'gray')
            building_fill_color = COLORS['building'].get(building_name, 'lightgray')

            if show_level:
                fp = level['floorPlane']
                x_vals = [fp['minX'], fp['maxX'], fp['maxX'], fp['minX'], fp['minX']]
                y_vals = [fp['minY'], fp['minY'], fp['maxY'], fp['maxY'], fp['minY']]
                z_vals = [z] * 5

                # 绘制楼层边框
                fig.add_trace(go.Scatter3d(
                    x=x_vals, y=y_vals, z=z_vals,
                    mode='lines',
                    line=dict(color=floor_border_color, width=4),
                    name=f"Building {building_name}-{level_name}",
                    legendgroup=f"Building {building_name}",
                    showlegend=True
                ))

                # 楼层半透明底面
                fig.add_trace(go.Mesh3d(
                    x=x_vals[:4], y=y_vals[:4], z=z_vals[:4],
                    color=building_fill_color, opacity=0.3, showlegend=False
                ))

                # 绘制走廊
                for corridor in level['corridors']:
                    points = corridor['points']
                    x = [p[0] for p in points]
                    y = [p[1] for p in points]
                    z_coords = [p[2]+10 for p in points]
                    
                    is_external = corridor.get('type') == 'external'
                    is_connect = 'connectToBuilding' in corridor.get('name','') or 'gateTo' in corridor.get('name','')
                    
                    if is_external:
                        corr_line_color = 'gray'
                        corr_line_width = 5
                        dash = 'dash'
                    elif is_connect:
                        corr_line_color = COLORS['connect_corridor']
                        corr_line_width = 7
                        dash = 'solid'
                    else:
                        corr_line_color = COLORS['corridor_line'].get(building_name, 'gray')
                        corr_line_width = 5
                        dash = 'solid'

                    fig.add_trace(go.Scatter3d(
                        x=x, y=y, z=z_coords,
                        mode='lines',
                        line=dict(color=corr_line_color, width=corr_line_width, dash=dash),
                        showlegend=False
                    ))
                    
                    fig.add_trace(go.Scatter3d(
                        x=x, y=y, z=z_coords,
                        mode='markers',
                        marker=dict(color=COLORS['corridor_node'], size=3, symbol='square'),
                        showlegend=False
                    ))

                # 绘制教室点位+轮廓
                for classroom in level['classrooms']:
                    x, y, _ = classroom['coordinates']
                    w, d = classroom['size']
                    name = classroom['name']

                    fig.add_trace(go.Scatter3d(
                        x=[x], y=[y], z=[z],
                        mode='markers+text',
                        marker=dict(color=building_fill_color, size=7, line=dict(color=floor_border_color, width=1)),
                        text=name, textposition="top center", textfont=dict(size=9, color='black'),
                        showlegend=False
                    ))

                    cx = [x, x+w, x+w, x, x]
                    cy = [y, y, y+d, y+d, y]
                    cz = [z]*5
                    fig.add_trace(go.Scatter3d(
                        x=cx, y=cy, z=cz,
                        mode='lines', line=dict(color=floor_border_color, width=1, dash='dash'),
                        opacity=0.6, showlegend=False
                    ))

            # 绘制楼梯
            for stair in level['stairs']:
                s_name = stair['name']
                is_path = (building_name, s_name, level_name) in path_stairs
                
                if show_all or show_level or is_path:
                    x, y, _ = stair['coordinates']
                    color = COLORS['stair'].get(s_name, 'red')
                    size = 12 if is_path else 9
                    
                    legend_name = f"{building_name}-{s_name}"
                    show_legend = legend_name not in shown_stairs_legends
                    if show_legend:
                        shown_stairs_legends.add(legend_name)
                    
                    fig.add_trace(go.Scatter3d(
                        x=[x], y=[y], z=[z],
                        mode='markers+text',
                        marker=dict(color=color, size=size, symbol='diamond', line=dict(color='black', width=2)),
                        text=s_name, textposition="top center", textfont=dict(size=9, color='darkred'),
                        name=legend_name,
                        legendgroup="Stairs",
                        showlegend=show_legend
                    ))

            # 绘制电梯
            if 'elevators' in level:
                for elevator in level['elevators']:
                    elev_name = elevator['name']
                    is_path = (building_name, elev_name, level_name) in path_stairs
                    x, y, _ = elevator['coordinates']
                    z = raw_z + 10
                    elev_color = COLORS['elevator'].get(elev_name, 'deepskyblue')
                    marker_size = 13 if is_path else 10

                    legend_key = f"{building_name}-{elev_name}"
                    show_leg = legend_key not in shown_stairs_legends
                    if show_leg:
                        shown_stairs_legends.add(legend_key)

                    fig.add_trace(go.Scatter3d(
                        x=[x], y=[y], z=[z],
                        mode='markers+text',
                        marker=dict(color=elev_color, size=marker_size, symbol='square-open', line=dict(color='black', width=1.5)),
                        text=elev_name, textposition="top center", textfont=dict(size=9, color=COLORS['elevator_label']),
                        name=legend_key,
                        legendgroup="Elevators",
                        showlegend=show_leg
                    ))
        
        if displayed_levels:
            label_z = max_displayed_z + 1.5
            label_y = max_displayed_y + (3 if building_name != 'B' else -2)
            building_label_positions[building_name] = (corresponding_x, label_y, label_z)

    # 楼宇文字标注
    for bld, (x, y, z) in building_label_positions.items():
        fig.add_trace(go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode='text',
            text=f"Building {bld}",
            textfont=dict(size=14, color=COLORS['building_label'][bld], family='Arial bold'),
            showlegend=False
        ))

    # 绘制规划路线 + 起点终点标记
    if path and graph and not show_all:
        try:
            xs, ys, zs = [], [], []
            labels = []
            for nid in path:
                c = graph.nodes[nid]['coordinates']
                xs.append(c[0])
                ys.append(c[1])
                zs.append(c[2]+10)
                labels.append(graph.nodes[nid]['name'])

            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs,
                mode='lines+markers',
                line=dict(color=COLORS['path'], width=5),
                marker=dict(color=COLORS['path'], size=4),
                name="Path"
            ))
            # 起点
            fig.add_trace(go.Scatter3d(
                x=[xs[0]], y=[ys[0]], z=[zs[0]],
                mode='markers+text', marker=dict(color=COLORS['start_marker'], size=14, symbol='square', line=dict(width=2)),
                text=f"Start\n{labels[0]}", textposition="top center", textfont=dict(size=11, color='green'),
                name="Start"
            ))
            # 终点
            fig.add_trace(go.Scatter3d(
                x=[xs[-1]], y=[ys[-1]], z=[zs[-1]],
                mode='markers+text', marker=dict(color=COLORS['end_marker'], size=14, symbol='square', line=dict(width=2)),
                text=f"End\n{labels[-1]}", textposition="top center", textfont=dict(size=11, color='purple'),
                name="End"
            ))
        except Exception:
            pass

    # 移动端自动隐藏图例，桌面端展示
    is_mobile = False
    try:
        ua = st.context.headers.get("User-Agent", "").lower()
        is_mobile = any(m in ua for m in ["mobile", "android", "iphone", "ipad", "phone"])
    except:
        pass

    fig.update_layout(
        scene=dict(
            xaxis_title="X", yaxis_title="Y", zaxis_title="Floor (Z+10)",
            camera=dict(eye=dict(x=1.4, y=1.4, z=1.0)),
            aspectmode='manual', aspectratio=dict(x=1, y=1, z=0.8)
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=600,
        showlegend=False if is_mobile else True
    )

    return fig

def plot_3d_map(school_data, graph=None, display_options=None):
    fig = plot_3d_map_plotly(school_data, graph, display_options)
    return fig, None

# -------------------------- 寻路图结构 + Dijkstra算法 --------------------------
class Graph:
    def __init__(self):
        self.nodes = {}
        self.node_id_map = {}

    def add_node(self, building_id, node_type, name, level, coordinates):
        if building_id == 'gate':
            building_name = 'Gate'
        else:
            building_name = building_id.replace('building', '')
        
        if node_type == 'corridor':
            node_id = f"{building_name}-corr-{name}@{level}"
        else:
            node_id = f"{building_name}-{node_type}-{name}@{level}"
        
        self.nodes[node_id] = {
            'building': building_name,
            'type': node_type,
            'name': name,
            'level': level,
            'coordinates': coordinates,
            'neighbors': {}
        }
        
        map_key = (building_id, node_type, name, level)
        self.node_id_map[map_key] = node_id
        if node_type == 'classroom':
            class_key = (building_name, name, level)
            self.node_id_map[class_key] = node_id
            
        return node_id

    def add_edge(self, node1_id, node2_id, weight):
        if node1_id in self.nodes and node2_id in self.nodes:
            self.nodes[node1_id]['neighbors'][node2_id] = weight
            self.nodes[node2_id]['neighbors'][node1_id] = weight

# 欧式距离计算（楼层高差惩罚）
def euclidean_distance(coords1, coords2, floor_penalty=15.0):
    base_dist = np.sqrt(sum((a - b)**2 for a, b in zip(coords1, coords2)))
    z1, z2 = coords1[2], coords2[2]
    floor_diff = abs(z1 - z2)
    penalty = floor_diff * floor_penalty
    total_dist = base_dist + penalty
    return total_dist

# 节点之间行走方向文字提示
def get_direction_between_nodes(graph, current_node_id, next_node_id):
    current_node = graph.nodes[current_node_id]
    next_node = graph.nodes[next_node_id]
    
    curr_x, curr_y, curr_z = current_node['coordinates']
    next_x, next_y, next_z = next_node['coordinates']
    
    curr_is_stair = current_node['type'] == 'stair'
    next_is_stair = next_node['type'] == 'stair'
    curr_is_elev = current_node['type'] == 'elevator'
    next_is_elev = next_node['type'] == 'elevator'

    if (curr_is_elev and next_is_elev) or (curr_is_stair and next_is_stair):
        if next_z > curr_z:
            return "<span style='color:DarkGoldenRod; font-weight:bold;'>up</span>"
        elif next_z < curr_z:
            return "<span style='color:DarkGoldenRod; font-weight:bold;'>down</span>"
        else:
            return ""
    
    x_diff = next_x - curr_x
    y_diff = next_y - curr_y
    threshold = 0.1
    
    if abs(x_diff) > threshold or abs(y_diff) > threshold:
        if y_diff > threshold:
            return "<span style='color:DarkGoldenRod; font-weight:bold;'>forward</span>"
        elif y_diff < -threshold:
            return "<span style='color:DarkGoldenRod; font-weight:bold;'>backward</span>"
        elif x_diff > threshold:
            return "<span style='color:DarkGoldenRod; font-weight:bold;'>right</span>"
        elif x_diff < -threshold:
            return "<span style='color:DarkGoldenRod; font-weight:bold;'>left</span>"
    
    return ""

# 构建完整校园导航拓扑图
def build_navigation_graph(school_data):
    graph = Graph()

    for building_id in school_data.keys():
        if not (building_id.startswith('building') or building_id == 'gate'):
            continue
            
        building_data = school_data[building_id]
        
        for level in building_data['levels']:
            level_name = level['name']

            # 添加教室节点
            for classroom in level['classrooms']:
                class_name = classroom['name']
                graph.add_node(
                    building_id=building_id,
                    node_type='classroom',
                    name=class_name,
                    level=level_name,
                    coordinates=classroom['coordinates']
                )

            # 添加电梯节点
            if 'elevators' in level:
                for elevator in level['elevators']:
                    graph.add_node(
                        building_id=building_id,
                        node_type='elevator',
                        name=elevator['name'],
                        level=level_name,
                        coordinates=elevator['coordinates']
                    )

            # 添加楼梯节点
            for stair in level['stairs']:
                graph.add_node(
                    building_id=building_id,
                    node_type='stair',
                    name=stair['name'],
                    level=level_name,
                    coordinates=stair['coordinates']
                )

            # 添加走廊采样点节点
            for corr_idx, corridor in enumerate(level['corridors']):
                corr_name = corridor.get('name', f'corr{corr_idx}')
                for p_idx, point in enumerate(corridor['points']):
                    corridor_point_name = f"{corr_name}-p{p_idx}"
                    graph.add_node(
                        building_id=building_id,
                        node_type='corridor',
                        name=corridor_point_name,
                        level=level_name,
                        coordinates=point
                    )

    # 楼层内部节点互相连通
    for building_id in school_data.keys():
        if not (building_id.startswith('building') or building_id == 'gate'):
            continue
            
        building_name = 'Gate' if building_id == 'gate' else building_id.replace('building', '')
        building_data = school_data[building_id]

        for level in building_data['levels']:
            level_name = level['name']
            
            corr_nodes = [
                node_id for node_id, node_info in graph.nodes.items()
                if node_info['building'] == building_name 
                and node_info['type'] == 'corridor' 
                and node_info['level'] == level_name
            ]

            # 走廊采样点前后相连
            for corr_idx, corridor in enumerate(level['corridors']):
                corr_name = corridor.get('name', f'corr{corr_idx}')
                corr_points = corridor['points']
                for p_idx in range(len(corr_points) - 1):
                    curr_p = f"{corr_name}-p{p_idx}"
                    next_p = f"{corr_name}-p{p_idx + 1}"
                    n1 = graph.node_id_map.get((building_id, 'corridor', curr_p, level_name))
                    n2 = graph.node_id_map.get((building_id, 'corridor', next_p, level_name))
                    if n1 and n2:
                        d = euclidean_distance(graph.nodes[n1]['coordinates'], graph.nodes[n2]['coordinates'], 0)
                        graph.add_edge(n1, n2, d)

            # 近距离走廊节点互通
            for i in range(len(corr_nodes)):
                n1 = corr_nodes[i]
                c1 = graph.nodes[n1]['coordinates']
                for j in range(i + 1, len(corr_nodes)):
                    n2 = corr_nodes[j]
                    c2 = graph.nodes[n2]['coordinates']
                    dist = euclidean_distance(c1, c2, 0)
                    if dist < 3.0:
                        graph.add_edge(n1, n2, dist)

            # 教室就近连接走廊
            class_nodes = [n for n,info in graph.nodes.items() if info['building']==building_name and info['type']=='classroom' and info['level']==level_name]
            for cn in class_nodes:
                cc = graph.nodes[cn]['coordinates']
                min_d = float('inf')
                near_corr = None
                for cr in corr_nodes:
                    dc = euclidean_distance(cc, graph.nodes[cr]['coordinates'],0)
                    if dc < min_d:
                        min_d = dc
                        near_corr = cr
                if near_corr:
                    graph.add_edge(cn, near_corr, min_d)

            # 楼梯绑定走廊
            stair_nodes = [n for n,info in graph.nodes.items() if info['building']==building_name and info['type']=='stair' and info['level']==level_name]
            for sn in stair_nodes:
                sc = graph.nodes[sn]['coordinates']
                min_d = float('inf')
                near_corr = None
                for cr in corr_nodes:
                    dc = euclidean_distance(sc, graph.nodes[cr]['coordinates'],0)
                    if dc < min_d:
                        min_d = dc
                        near_corr = cr
                if near_corr:
                    graph.add_edge(sn, near_corr, min_d)

            # 电梯绑定走廊
            elev_nodes = [n for n,info in graph.nodes.items() if info['building']==building_name and info['type']=='elevator' and info['level']==level_name]
            for en in elev_nodes:
                ec = graph.nodes[en]['coordinates']
                min_d = float('inf')
                near_corr = None
                for cr in corr_nodes:
                    dc = euclidean_distance(ec, graph.nodes[cr]['coordinates'],0)
                    if dc < min_d:
                        min_d = dc
                        near_corr = cr
                if near_corr:
                    graph.add_edge(en, near_corr, min_d)

        # 楼梯竖向跨楼层连通
        stair_groups = set()
        for nid, info in graph.nodes.items():
            if info['type'] == 'stair':
                stair_groups.add((info['building'], info['name']))
        for (b, sname) in stair_groups:
            levels_list = []
            for nid, info in graph.nodes.items():
                if info['building']==b and info['type']=='stair' and info['name']==sname:
                    levels_list.append((nid, info['coordinates']))
            levels_list.sort(key=lambda x: x[1][2])
            for i in range(len(levels_list)-1):
                n1,c1 = levels_list[i]
                n2,c2 = levels_list[i+1]
                d = euclidean_distance(c1,c2,15)
                graph.add_edge(n1,n2,d)

        # 电梯竖向跨楼层连通
        elev_groups = set()
        for nid, info in graph.nodes.items():
            if info['type'] == 'elevator':
                elev_groups.add((info['building'], info['name']))
        for (b, ename) in elev_groups:
            levels_list = []
            for nid, info in graph.nodes.items():
                if info['building']==b and info['type']=='elevator' and info['name']==ename:
                    levels_list.append((nid, info['coordinates']))
            levels_list.sort(key=lambda x: x[1][2])
            for i in range(len(levels_list)-1):
                n1,c1 = levels_list[i]
                n2,c2 = levels_list[i+1]
                d = euclidean_distance(c1,c2,15)
                graph.add_edge(n1,n2,d)

        # 楼宇之间天桥互通逻辑
        for connection in building_data['connections']:
            from_obj_name, from_level = connection['from']
            to_obj_name, to_level = connection['to']
            
            from_obj_type = 'stair' if from_obj_name.startswith(('Stairs','GateStairs')) else 'corridor'
            from_node_name = f"{from_obj_name}-p0" if from_obj_type == 'corridor' else from_obj_name
            from_node_id = graph.node_id_map.get((building_id, from_obj_type, from_node_name, from_level))

            target_build_map = {
                'ENTRANCE': 'buildingA',
                'connectToBuildingAAndC': 'buildingB',
                'SCHOOL CLINIC': 'buildingC',
                'connectToBuildingB': 'buildingB',
                'connectToBuildingC': 'buildingC'
            }
            to_building_id = building_id
            for kw, bid in target_build_map.items():
                if kw in to_obj_name:
                    to_building_id = bid
                    break
            
            to_obj_type = 'stair' if to_obj_name.startswith(('Stairs','GateStairs')) else 'corridor'
            to_node_name = f"{to_obj_name}-p0" if to_obj_type == 'corridor' else to_obj_name
            to_node_id = graph.node_id_map.get((to_building_id, to_obj_type, to_node_name, to_level))

            if from_node_id and to_node_id:
                d = euclidean_distance(graph.nodes[from_node_id]['coordinates'], graph.nodes[to_node_id]['coordinates'], 0)
                graph.add_edge(from_node_id, to_node_id, d)

        # A-B、B-C、A-C固定天桥连接
        # A <-> B
        a_b_n1 = graph.node_id_map.get(('buildingA','corridor','connectToBuildingB-p1','level1'))
        a_b_n2 = graph.node_id_map.get(('buildingB','corridor','connectToBuildingAAndC-p1','level1'))
        if a_b_n1 and a_b_n2:
            dist = euclidean_distance(graph.nodes[a_b_n1]['coordinates'], graph.nodes[a_b_n2]['coordinates'],0)
            graph.add_edge(a_b_n1,a_b_n2,dist)
        # B <-> C
        b_c_n1 = graph.node_id_map.get(('buildingB','corridor','connectToBuildingAAndC-p0','level1'))
        b_c_n2 = graph.node_id_map.get(('buildingC','corridor','connectToBuildingB-p1','level1'))
        if b_c_n1 and b_c_n2:
            dist = euclidean_distance(graph.nodes[b_c_n1]['coordinates'], graph.nodes[b_c_n2]['coordinates'],0)
            graph.add_edge(b_c_n1,b_c_n2,dist)
        # A <-> C 1楼
        ac1_1 = graph.node_id_map.get(('buildingA','corridor','connectToBuildingC-p3','level1'))
        ac1_2 = graph.node_id_map.get(('buildingC','corridor','connectToBuildingA-p0','level1'))
        if ac1_1 and ac1_2:
            dist = euclidean_distance(graph.nodes[ac1_1]['coordinates'], graph.nodes[ac1_2]['coordinates'],0)
            graph.add_edge(ac1_1,ac1_2,dist)
        # A <-> C 3楼
        ac3_1 = graph.node_id_map.get(('buildingA','corridor','connectToBuildingC-p2','level3'))
        ac3_2 = graph.node_id_map.get(('buildingC','corridor','connectToBuildingA-p0','level3'))
        if ac3_1 and ac3_2:
            dist = euclidean_distance(graph.nodes[ac3_1]['coordinates'], graph.nodes[ac3_2]['coordinates'],0)
            graph.add_edge(ac3_1,ac3_2,dist)

    return graph

# Dijkstra最短路径算法
def dijkstra(graph, start_node):
    distances = {node: float('inf') for node in graph.nodes}
    distances[start_node] = 0
    previous_nodes = {node: None for node in graph.nodes}
    nodes = set(graph.nodes.keys())

    while nodes:
        min_node = min(nodes, key=lambda node: distances[node])
        nodes.remove(min_node)
        if distances[min_node] == float('inf'):
            break
        for neighbor, weight in graph.nodes[min_node]['neighbors'].items():
            new_dist = distances[min_node] + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous_nodes[neighbor] = min_node
    return distances, previous_nodes

# 回溯生成完整路线
def construct_path(previous_nodes, end_node):
    path = []
    curr = end_node
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes[curr]
    return path if len(path) > 1 else None

# 导航核心函数：无障碍模式屏蔽楼梯，只走电梯
def navigate(graph, start_building, start_classroom, start_level, end_building, end_classroom, end_level, barrier_free):
    valid_builds = ['A', 'B', 'C', 'Gate']
    if start_building not in valid_builds or end_building not in valid_builds:
        return None, "楼宇选择无效，仅支持 A/B/C/Gate", None, None
        
    try:
        start_key = (start_building, start_classroom, start_level)
        end_key = (end_building, end_classroom, end_level)
        start_node = graph.node_id_map.get(start_key)
        end_node = graph.node_id_map.get(end_key)

        if not start_node or start_node not in graph.nodes:
            return None, f"起点教室不存在：{start_building}{start_classroom}", None, None
        if not end_node or end_node not in graph.nodes:
            return None, f"终点教室不存在：{end_building}{end_classroom}", None, None

        # 拷贝原图，无障碍模式临时禁用所有楼梯（权重无穷大），不污染原始拓扑
        temp_graph = copy.deepcopy(graph)
        if barrier_free:
            for nid, ndata in temp_graph.nodes.items():
                if ndata['type'] == 'stair':
                    for neighbor in list(ndata['neighbors'].keys()):
                        temp_graph.nodes[nid]['neighbors'][neighbor] = float('inf')

        dists, prev_nodes = dijkstra(temp_graph, start_node)
        path = construct_path(prev_nodes, end_node)

        if not path:
            return None, "暂无可行通行路线", None, None

        total_len = dists[end_node]
        path_steps = []
        stair_elev_set = set()
        prev_b = None

        for idx in range(len(path)):
            nid = path[idx]
            info = graph.nodes[nid]
            ntype, nname, nlevel, nb = info['type'], info['name'], info['level'], info['building']
            desc = ""

            if ntype in ['stair','elevator']:
                stair_elev_set.add((nb, nname, nlevel))
                tag = "楼梯" if ntype == "stair" else "电梯"
                desc = f"{nb}栋 {nname}({nlevel}) {tag}"
            elif ntype == 'classroom':
                desc = f"{nb}栋 {nname}({nlevel})"
            elif ntype == 'corridor':
                if 'connectToBuilding' in nname and prev_b and prev_b != nb:
                    desc = f"天桥：{prev_b}栋 → {nb}栋({nlevel})"

            if desc:
                if idx < len(path)-1:
                    dir_txt = get_direction_between_nodes(graph, nid, path[idx+1])
                    desc += f" {dir_txt}"
                path_steps.append(desc)
            prev_b = nb

        full_route = " → ".join(path_steps)
        display_opts = {
            'start_level': start_level,
            'end_level': end_level,
            'path_stairs': stair_elev_set,
            'show_all': False,
            'path': path,
            'start_building': start_building,
            'end_building': end_building
        }
        return path, f"总路程：{total_len:.2f} 单位", full_route, display_opts

    except Exception as e:
        return None, f"导航计算出错：{str(e)}", None, None

# 获取所有楼宇、楼层、教室层级数据
def get_classroom_info(school_data):
    buildings = [b for b in school_data.keys() if b.startswith('building') or b == 'gate']
    build_names = []
    for b in buildings:
        build_names.append('Gate' if b == 'gate' else b.replace('building',''))
    
    level_dict = {}
    class_dict = {}
    for bid in buildings:
        bname = 'Gate' if bid == 'gate' else bid.replace('building','')
        bdata = school_data[bid]
        levels = []
        clz_by_level = {}
        for lev in bdata['levels']:
            lev_name = lev['name']
            levels.append(lev_name)
            clz = [c['name'] for c in lev['classrooms']]
            clz_by_level[lev_name] = clz
        level_dict[bname] = levels
        class_dict[bname] = clz_by_level
    return build_names, level_dict, class_dict

# 重置全部会话状态
def reset_app_state():
    st.session_state['display_options'] = {
        'start_level': None,
        'end_level': None,
        'path_stairs': set(),
        'show_all': True,
        'path': [],
        'start_building': None,
        'end_building': None
    }
    st.session_state['current_path'] = None
    st.session_state['path_result_text'] = ""
    st.session_state['path_detail'] = ""
    st.session_state['is_disabled'] = False
    st.session_state.run_nav = False

# ====================== 主程序入口 ======================
def main():
    # 会话变量初始化
    init_vars = [
        'page', 'display_options', 'current_path', 'is_disabled',
        'run_nav', 'path_result_text', 'path_detail', 'worksheet'
    ]
    for var in init_vars:
        if var not in st.session_state:
            if var == 'page':
                st.session_state[var] = 'welcome'
            elif var == 'display_options':
                st.session_state[var] = {
                    'start_level': None,
                    'end_level': None,
                    'path_stairs': set(),
                    'show_all': True,
                    'path': [],
                    'start_building': None,
                    'end_building': None
                }
            elif var in ['path_result_text','path_detail']:
                st.session_state[var] = ""
            elif var == 'run_nav':
                st.session_state[var] = False
            else:
                st.session_state[var] = None

    # 欢迎首页页面
    if st.session_state['page'] == 'welcome':
        # 加载本地背景图样式
        def add_bg_from_local(image_file):
            try:
                with open(image_file, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                css = """
                <style>
                .stApp {
                    background-image: url("data:image/jpeg;base64,%s");
                    background-size: cover !important;
                    background-position: center !important;
                    background-repeat: no-repeat !important;
                    background-attachment: fixed !important;
                }
                .welcome-container {
                    display: flex !important;
                    flex-direction: column !important;
                    align-items: center !important;
                    text-align: center !important;
                    width: 100%% !important;
                    margin-top: 35vh !important;
                }
                .welcome-title {
                    color: white !important;
                    font-size: clamp(28px, 8vw, 48px) !important;
                    font-weight: 900 !important;
                    white-space: nowrap !important;
                    margin: 0 !important;
                }
                .welcome-subtitle {
                    color: white !important;
                    font-size: clamp(14px, 3vw, 20px) !important;
                    opacity: 0.9 !important;
                    margin: 5px 0 25px 0 !important;
                }
                div.stButton > button:first-child {
                    background-color: #4682B4 !important;
                    color: white !important;
                    font-size: clamp(16px, 4vw, 20px) !important;
                    padding: 16px 24px !important;
                    border-radius: 12px !important;
                    font-weight: bold !important;
                    border: none !important;
                    width: 100%% !important;
                }
                </style>
                """ % encoded
                st.markdown(css, unsafe_allow_html=True)
            except:
                pass

        add_bg_from_local("background.jpg")

        # 初始化访问统计表单
        if st.session_state['worksheet'] is None:
            st.session_state['worksheet'] = init_google_sheet()

        st.markdown("""
        <div class="welcome-container">
            <h1 class="welcome-title">NAVIGATE YOUR CAMPUS</h1>
            <div class="welcome-subtitle">Find Classrooms, Labs, Resources In Stunning 3D</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 0.5, 1])
        with col2:
            if st.button('EXPLORE 3D MAP'):
                update_access_count(st.session_state['worksheet'])
                st.session_state['page'] = 'main'
                st.rerun()

    # 主导航页面
    else:
        # 侧边栏控件
        with st.sidebar:
            st.subheader("♿ 无障碍通行设置")
            access_choice = st.radio(
                "需要无障碍通行（禁止楼梯）？",
                options=["No", "Yes"],
                index=0,
                help="选择Yes：全程仅可乘坐B栋电梯上下楼，所有楼梯无法通行"
            )
            st.session_state['is_disabled'] = (access_choice == "Yes")
            st.divider()

            st.header("📍 起止点位选择")
            school_data = load_school_data_detailed('school_data_detailed.json')
            if school_data is None:
                st.error("地图数据文件缺失！")
                return
            build_list, level_map, class_map = get_classroom_info(school_data)
            
            # 起点选择
            st.subheader("出发地点")
            start_build = st.selectbox("楼宇", build_list, key="start_building")
            start_lvls = level_map.get(start_build, [])
            start_lvl = st.selectbox("楼层", start_lvls, key="start_level")
            start_cls_list = class_map.get(start_build, {}).get(start_lvl, [])
            start_cls = st.selectbox("教室", start_cls_list, key="start_classroom")

            # 终点选择
            st.subheader("目标地点")
            end_build = st.selectbox("楼宇", build_list, key="end_building")
            end_lvls = level_map.get(end_build, [])
            end_lvl = st.selectbox("楼层", end_lvls, key="end_level")
            end_cls_list = class_map.get(end_build, {}).get(end_lvl, [])
            end_cls = st.selectbox("教室", end_cls_list, key="end_classroom")

            st.divider()
            btn_nav = st.button("🔍 计算最短路线", use_container_width=True)
            btn_reset = st.button("🔄 重置视图", use_container_width=True)
            btn_exit = st.button("🚪 返回首页", use_container_width=True)

            # 按钮事件绑定
            if btn_nav:
                st.session_state.run_nav = True
            if btn_reset:
                reset_app_state()
                st.rerun()
            if btn_exit:
                reset_app_state()
                st.session_state['page'] = 'welcome'
                st.rerun()

        # 页面标题
        st.markdown("<h2 style='margin:0; padding:0;'>🏫 SCIS Campus Navigation System</h2>", unsafe_allow_html=True)
        st.divider()
        
        school_data = load_school_data_detailed('school_data_detailed.json')
        if school_data is None:
            st.error("地图数据加载失败，请检查 school_data_detailed.json 文件")
            return
        
        graph = build_navigation_graph(school_data)
        st.success("✅ 校园地图拓扑数据加载完成")

        # 执行寻路计算，结果存入session_state持久保存
        if st.session_state.run_nav:
            path, res_text, detail_text, opts = navigate(
                graph,
                start_build, start_cls, start_lvl,
                end_build, end_cls, end_lvl,
                barrier_free=st.session_state['is_disabled']
            )
            st.session_state['current_path'] = path
            st.session_state['path_result_text'] = res_text
            st.session_state['path_detail'] = detail_text
            st.session_state['display_options'] = opts
            st.session_state.run_nav = False
            st.rerun()

        # 渲染3D地图
        fig, _ = plot_3d_map(school_data, graph, st.session_state['display_options'])
        st.plotly_chart(fig, use_container_width=True)

        # 展示路线文字详情
        if st.session_state['path_result_text']:
            st.info(st.session_state['path_result_text'])
        if st.session_state['path_detail']:
            st.markdown("### 📝 行走步骤指引")
            st.markdown(st.session_state['path_detail'], unsafe_allow_html=True)

if __name__ == "__main__":
    main()
