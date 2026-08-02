import json
import numpy as np
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import copy
import base64
import plotly.graph_objects as go

# ====================== 全局页面配置 固定优先 ======================
st.set_page_config(
    page_title="SCIS Navigation System",
    layout="wide",
    initial_sidebar_state="auto"
)

# ====================== Google Sheets 访问统计模块 ======================
SHEET_NAME = 'Navigation visitors'
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    try:
        service_account_info = st.secrets["google_service_account"]
        return Credentials.from_service_account_info(service_account_info, scopes=SCOPE)
    except Exception:
        return None

def init_google_sheet():
    creds = get_credentials()
    if not creds:
        return None
    try:
        client = gspread.authorize(creds)
        try:
            sheet = client.open(SHEET_NAME)
        except gspread.exceptions.SpreadsheetNotFound:
            sheet = client.create(SHEET_NAME)
        try:
            ws = sheet.worksheet("Access_Stats")
        except gspread.exceptions.WorksheetNotFound:
            ws = sheet.add_worksheet("Access_Stats", 1000, 3)
            ws.append_row(["Timestamp", "Access_Count", "Total_Accesses"])
            ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1, 1])
        return ws
    except Exception:
        return None

def update_access_count(worksheet):
    if not worksheet:
        return 0
    try:
        rows = worksheet.get_all_values()
        if len(rows) < 2:
            total = 0
        else:
            total = int(rows[-1][2]) if rows[-1][2].isdigit() else 0
        new_total = total + 1
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1, new_total])
        return new_total
    except Exception:
        return 0

# ====================== 全局配色常量 ======================
COLORS = {
    'building': {'A': 'lightblue', 'B': 'lightgreen', 'C': 'lightcoral', 'Gate': 'gold'},
    'floor_z': {-9: 'darkgray', -6: 'blue', -3: 'cyan', 2: 'green', 7: 'orange', 12: 'purple', 17: 'teal'},
    'corridor_line': {'A': 'cyan', 'B': 'forestgreen', 'C': 'salmon', 'Gate': 'darkgoldenrod'},
    'corridor_node': 'navy',
    'stair': {
        'Stairs1': '#FF5733','Stairs2': '#33FF57','Stairs3': '#3357FF','Stairs4': '#FF33F5',
        'Stairs5': '#F5FF33','StairsB1': '#33FFF5','StairsB2': '#FF9933','GateStairs': '#FFD700'
    },
    'elevator': {'ElevatorB1': '#00BFFF'},
    'path': 'red','start_marker': 'limegreen','end_marker': 'magenta','connect_corridor': 'gold'
}

# ====================== 数据加载 ======================
def load_school_data_detailed(filename="school_data_detailed.json"):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

# ====================== 3D地图渲染函数 ======================
def plot_3d_map_plotly(school_data, graph=None, display_options=None):
    fig = go.Figure()
    opts = display_options or {
        'show_all': True, 'path': [], 'path_stairs': set(),
        'start_level': None, 'end_level': None
    }
    show_all = opts["show_all"]
    path_set = opts["path_stairs"]
    route_path = opts["path"]

    # 遍历所有楼宇绘制楼层、走廊、设施
    for building_id in school_data:
        if not (building_id.startswith("building") or building_id == "gate"):
            continue
        b_name = "Gate" if building_id == "gate" else building_id.replace("building", "")
        b_data = school_data[building_id]

        for level in b_data["levels"]:
            lev_name = level["name"]
            z_base = level["z"]
            z_draw = z_base + 10
            draw_this_level = show_all

            # 非全局浏览：只渲染起止楼层+途经楼梯电梯楼层
            if not show_all:
                draw_this_level = (lev_name == opts["start_level"]) or (lev_name == opts["end_level"])
                # 判断本楼层是否有途经楼梯/电梯
                for (b, _, lev) in path_set:
                    if b == b_name and lev == lev_name:
                        draw_this_level = True
                        break

            # 绘制楼层底板边框
            fp = level["floorPlane"]
            x_plane = [fp["minX"], fp["maxX"], fp["maxX"], fp["minX"], fp["minX"]]
            y_plane = [fp["minY"], fp["minY"], fp["maxY"], fp["maxY"], fp["minY"]]
            z_plane = [z_draw] * 5
            floor_color = COLORS["floor_z"].get(z_base, "gray")

            if draw_this_level:
                fig.add_trace(go.Scatter3d(
                    x=x_plane, y=y_plane, z=z_plane,
                    mode="lines", line=dict(color=floor_color, width=4), showlegend=False
                ))
                fig.add_trace(go.Mesh3d(
                    x=x_plane[:4], y=y_plane[:4], z=z_plane[:4],
                    color=COLORS["building"][b_name], opacity=0.3, showlegend=False
                ))

                # 绘制走廊线条
                for corr in level["corridors"]:
                    pts = corr["points"]
                    cx = [p[0] for p in pts]
                    cy = [p[1] for p in pts]
                    cz = [p[2]+10 for p in pts]
                    fig.add_trace(go.Scatter3d(
                        x=cx, y=cy, z=cz, mode="lines",
                        line=dict(color=COLORS["corridor_line"][b_name], width=5),
                        showlegend=False
                    ))

                # 教室点位
                for room in level["classrooms"]:
                    x, y, _ = room["coordinates"]
                    fig.add_trace(go.Scatter3d(
                        x=[x], y=[y], z=[z_draw],
                        mode="markers+text", marker=dict(size=7), text=room["name"],
                        textposition="top center", showlegend=False
                    ))

                # 楼梯绘制
                for stair in level["stairs"]:
                    sx, sy, _ = stair["coordinates"]
                    is_on_path = (b_name, stair["name"], lev_name) in path_set
                    size = 12 if is_on_path else 8
                    fig.add_trace(go.Scatter3d(
                        x=[sx], y=[sy], z=[z_draw],
                        mode="markers+text",
                        marker=dict(color=COLORS["stair"][stair["name"]], size=size, symbol="diamond"),
                        text=stair["name"], textposition="top center", showlegend=False
                    ))

                # 电梯绘制
                if "elevators" in level:
                    for elev in level["elevators"]:
                        ex, ey, _ = elev["coordinates"]
                        is_on_path = (b_name, elev["name"], lev_name) in path_set
                        size = 13 if is_on_path else 9
                        fig.add_trace(go.Scatter3d(
                            x=[ex], y=[ey], z=[z_draw],
                            mode="markers+text",
                            marker=dict(color=COLORS["elevator"][elev["name"]], size=size),
                            text=elev["name"], textposition="top center", showlegend=False
                        ))

    # 绘制规划路线+起点终点标记
    if route_path and len(route_path) > 1:
        xs, ys, zs = [], [], []
        for node_id in route_path:
            coord = graph.nodes[node_id]["coordinates"]
            xs.append(coord[0])
            ys.append(coord[1])
            zs.append(coord[2] + 10)
        # 路线红线
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs, mode="lines",
            line=dict(color=COLORS["path"], width=5), name="行走路线"
        ))
        # 起点
        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[ys[0]], z=[zs[0]],
            mode="markers", marker=dict(color=COLORS["start_marker"], size=15), name="起点"
        ))
        # 终点
        fig.add_trace(go.Scatter3d(
            x=[xs[-1]], y=[ys[-1]], z=[zs[-1]],
            mode="markers", marker=dict(color=COLORS["end_marker"], size=15), name="终点"
        ))

    # 相机视角、布局适配移动端
    fig.update_layout(
        scene=dict(
            xaxis_title="X轴", yaxis_title="Y轴", zaxis_title="楼层高度",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.1)),
            aspectratio=dict(x=1, y=1, z=0.75)
        ),
        margin=dict(l=0, r=0, t=20, b=0), height=620, showlegend=False
    )
    return fig

# ====================== 寻路拓扑图结构 ======================
class Graph:
    def __init__(self):
        self.nodes = {}
        self.node_id_map = {}

    def add_node(self, building_id, node_type, name, level, coordinates):
        b_short = "Gate" if building_id == "gate" else building_id.replace("building", "")
        nid = f"{b_short}-{node_type}-{name}@{level}"
        self.nodes[nid] = {
            "building": b_short, "type": node_type, "name": name,
            "level": level, "coordinates": coordinates, "neighbors": {}
        }
        # 双向映射key
        key1 = (building_id, node_type, name, level)
        self.node_id_map[key1] = nid
        if node_type == "classroom":
            key2 = (b_short, name, level)
            self.node_id_map[key2] = nid
        return nid

    def add_edge(self, n1, n2, weight):
        if n1 in self.nodes and n2 in self.nodes:
            self.nodes[n1]["neighbors"][n2] = weight
            self.nodes[n2]["neighbors"][n1] = weight

# 欧式距离 + 楼层高差惩罚
def calc_distance(p1, p2, floor_penalty=12):
    planar = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    z_diff = abs(p1[2] - p2[2])
    return planar + z_diff * floor_penalty

# 行走方向文字
def get_step_direction(graph, curr_nid, next_nid):
    curr = graph.nodes[curr_nid]
    nxt = graph.nodes[next_nid]
    cx, cy, cz = curr["coordinates"]
    nx, ny, nz = nxt["coordinates"]

    # 电梯/楼梯上下行
    if (curr["type"] in ["stair","elevator"]) and (nxt["type"] in ["stair","elevator"]):
        if nz > cz:
            return "<b style='color:darkgoldenrod'>向上</b>"
        elif nz < cz:
            return "<b style='color:darkgoldenrod'>向下</b>"
        else:
            return ""
    # 平面左右前后
    dx = nx - cx
    dy = ny - cy
    threshold = 0.2
    if dy > threshold:
        return "<b style='color:darkgoldenrod'>直行</b>"
    elif dy < -threshold:
        return "<b style='color:darkgoldenrod'>后退</b>"
    elif dx > threshold:
        return "<b style='color:darkgoldenrod'>右转</b>"
    elif dx < -threshold:
        return "<b style='color:darkgoldenrod'>左转</b>"
    return ""

# 构建全校导航拓扑路网
def build_nav_graph(school_data):
    g = Graph()
    # 1.录入所有节点：教室、楼梯、电梯、走廊采样点
    for bid in school_data:
        if not (bid.startswith("building") or bid == "gate"):
            continue
        b_data = school_data[bid]
        for level in b_data["levels"]:
            lev_name = level["name"]
            # 教室
            for room in level["classrooms"]:
                g.add_node(bid, "classroom", room["name"], lev_name, room["coordinates"])
            # 楼梯
            for stair in level["stairs"]:
                g.add_node(bid, "stair", stair["name"], lev_name, stair["coordinates"])
            # 电梯
            if "elevators" in level:
                for elev in level["elevators"]:
                    g.add_node(bid, "elevator", elev["name"], lev_name, elev["coordinates"])
            # 走廊采样点
            for corr_idx, corr in enumerate(level["corridors"]):
                cname = f"corr{corr_idx}"
                for p_idx, point in enumerate(corr["points"]):
                    g.add_node(bid, "corridor", f"{cname}-p{p_idx}", lev_name, point)

    # 2.楼层内走廊互相连通
    for bid in school_data:
        if not (bid.startswith("building") or bid == "gate"):
            continue
        b_data = school_data[bid]
        b_short = "Gate" if bid == "gate" else bid.replace("building", "")
        for level in b_data["levels"]:
            lev_name = level["name"]
            # 获取本层所有走廊节点
            corr_nodes = [
                nid for nid, info in g.nodes.items()
                if info["building"] == b_short and info["type"] == "corridor" and info["level"] == lev_name
            ]
            # 走廊采样点顺序相连
            for c_idx, corr in enumerate(level["corridors"]):
                p_count = len(corr["points"])
                for i in range(p_count - 1):
                    n1_key = (bid, "corridor", f"corr{c_idx}-p{i}", lev_name)
                    n2_key = (bid, "corridor", f"corr{c_idx}-p{i+1}", lev_name)
                    n1 = g.node_id_map.get(n1_key)
                    n2 = g.node_id_map.get(n2_key)
                    if n1 and n2:
                        dist = calc_distance(g.nodes[n1]["coordinates"], g.nodes[n2]["coordinates"], 0)
                        g.add_edge(n1, n2, dist)
            # 教室就近接入走廊
            room_nodes = [n for n,info in g.nodes.items() if info["building"]==b_short and info["type"]=="classroom" and info["level"]==lev_name]
            for rn in room_nodes:
                r_pos = g.nodes[rn]["coordinates"]
                min_d = float("inf")
                near_corr = None
                for cn in corr_nodes:
                    d = calc_distance(r_pos, g.nodes[cn]["coordinates"], 0)
                    if d < min_d:
                        min_d = d
                        near_corr = cn
                if near_corr:
                    g.add_edge(rn, near_corr, min_d)
            # 楼梯接入走廊
            stair_nodes = [n for n,info in g.nodes.items() if info["building"]==b_short and info["type"]=="stair" and info["level"]==lev_name]
            for sn in stair_nodes:
                s_pos = g.nodes[sn]["coordinates"]
                min_d = float("inf")
                near_corr = None
                for cn in corr_nodes:
                    d = calc_distance(s_pos, g.nodes[cn]["coordinates"], 0)
                    if d < min_d:
                        min_d = d
                        near_corr = cn
                if near_corr:
                    g.add_edge(sn, near_corr, min_d)
            # 电梯接入走廊
            elev_nodes = [n for n,info in g.nodes.items() if info["building"]==b_short and info["type"]=="elevator" and info["level"]==lev_name]
            for en in elev_nodes:
                e_pos = g.nodes[en]["coordinates"]
                min_d = float("inf")
                near_corr = None
                for cn in corr_nodes:
                    d = calc_distance(e_pos, g.nodes[cn]["coordinates"], 0)
                    if d < min_d:
                        min_d = d
                        near_corr = cn
                if near_corr:
                    g.add_edge(en, near_corr, min_d)

    # 3.楼梯竖向上下楼层互通
    stair_groups = set()
    for nid, info in g.nodes.items():
        if info["type"] == "stair":
            stair_groups.add((info["building"], info["name"]))
    for b, sname in stair_groups:
        floors = []
        for nid, info in g.nodes.items():
            if info["building"] == b and info["type"] == "stair" and info["name"] == sname:
                floors.append((nid, info["coordinates"][2]))
        floors.sort(key=lambda x: x[1])
        for i in range(len(floors)-1):
            n1, _ = floors[i]
            n2, _ = floors[i+1]
            dist = calc_distance(g.nodes[n1]["coordinates"], g.nodes[n2]["coordinates"])
            g.add_edge(n1, n2, dist)

    # 4.电梯竖向上下楼层互通
    elev_groups = set()
    for nid, info in g.nodes.items():
        if info["type"] == "elevator":
            elev_groups.add((info["building"], info["name"]))
    for b, ename in elev_groups:
        floors = []
        for nid, info in g.nodes.items():
            if info["building"] == b and info["type"] == "elevator" and info["name"] == ename:
                floors.append((nid, info["coordinates"][2]))
        floors.sort(key=lambda x: x[1])
        for i in range(len(floors)-1):
            n1, _ = floors[i]
            n2, _ = floors[i+1]
            dist = calc_distance(g.nodes[n1]["coordinates"], g.nodes[n2]["coordinates"])
            g.add_edge(n1, n2, dist)

    # 5.楼宇之间天桥连通（固定通道）
    # A <-> B
    n1 = g.node_id_map.get(("buildingA","corridor","corr3-p1","level1"))
    n2 = g.node_id_map.get(("buildingB","corridor","corr2-p1","level1"))
    if n1 and n2:
        g.add_edge(n1, n2, calc_distance(g.nodes[n1]["coordinates"], g.nodes[n2]["coordinates"],0))
    # B <-> C
    n1 = g.node_id_map.get(("buildingB","corridor","corr2-p0","level1"))
    n2 = g.node_id_map.get(("buildingC","corridor","corr1-p1","level1"))
    if n1 and n2:
        g.add_edge(n1, n2, calc_distance(g.nodes[n1]["coordinates"], g.nodes[n2]["coordinates"],0))
    # A <-> C 1/3楼天桥
    ac1_a = g.node_id_map.get(("buildingA","corridor","corr4-p3","level1"))
    ac1_c = g.node_id_map.get(("buildingC","corridor","corr0-p0","level1"))
    if ac1_a and ac1_c:
        g.add_edge(ac1_a, ac1_c, calc_distance(g.nodes[ac1_a]["coordinates"], g.nodes[ac1_c]["coordinates"],0))
    ac3_a = g.node_id_map.get(("buildingA","corridor","corr4-p2","level3"))
    ac3_c = g.node_id_map.get(("buildingC","corridor","corr0-p0","level3"))
    if ac3_a and ac3_c:
        g.add_edge(ac3_a, ac3_c, calc_distance(g.nodes[ac3_a]["coordinates"], g.nodes[ac3_c]["coordinates"],0))

    return g

# Dijkstra最短路径
def dijkstra(graph, start):
    INF = float("inf")
    dist = {n: INF for n in graph.nodes}
    prev = {n: None for n in graph.nodes}
    dist[start] = 0
    unvisited = set(graph.nodes.keys())
    while unvisited:
        current = min(unvisited, key=lambda x: dist[x])
        unvisited.remove(current)
        if dist[current] == INF:
            break
        for neighbor, w in graph.nodes[current]["neighbors"].items():
            if dist[neighbor] > dist[current] + w:
                dist[neighbor] = dist[current] + w
                prev[neighbor] = current
    return dist, prev

# 回溯生成路线列表
def build_path(prev_map, end):
    path_list = []
    curr = end
    while curr is not None:
        path_list.insert(0, curr)
        curr = prev_map[curr]
    return path_list if len(path_list) > 1 else None

# ====================== 核心导航函数【已修复无障碍逻辑】 ======================
def route_calculate(graph, s_build, s_room, s_level, e_build, e_room, e_level, barrier_free: bool):
    # 获取起止节点
    start_key = (s_build, s_room, s_level)
    end_key = (e_build, e_room, e_level)
    start_node = graph.node_id_map.get(start_key)
    end_node = graph.node_id_map.get(end_key)

    if not start_node or not end_node:
        return None, "起点或终点教室不存在", "", {}

    # ========== 修复核心：无障碍模式新建副本，彻底禁用所有楼梯通行 ==========
    work_graph = copy.deepcopy(graph)
    if barrier_free:
        # 遍历全部节点，楼梯所有邻接边权重设为无穷大，完全走不通
        for node_id, node_info in work_graph.nodes.items():
            if node_info["type"] == "stair":
                # 清空楼梯所有通行链路
                work_graph.nodes[node_id]["neighbors"] = {}

    # 计算最短路径
    dists, prevs = dijkstra(work_graph, start_node)
    path = build_path(prevs, end_node)
    if not path:
        return None, "未规划出可行路线（无障碍模式仅电梯通行）", "", {}

    total_length = dists[end_node]
    step_text_list = []
    pass_stair_elev = set()

    # 拆解每一步行走指引
    for idx in range(len(path)):
        nid = path[idx]
        info = graph.nodes[nid]
        bld, ntype, name, lev = info["building"], info["type"], info["name"], info["level"]
        desc = ""
        if ntype == "classroom":
            desc = f"{bld}栋 {name}（{lev}）"
        elif ntype == "stair":
            desc = f"{bld}栋 楼梯{name} {lev} 上下楼层"
            pass_stair_elev.add((bld, name, lev))
        elif ntype == "elevator":
            desc = f"{bld}栋 电梯{name} {lev} 上下楼层"
            pass_stair_elev.add((bld, name, lev))

        # 拼接方向指引
        if idx < len(path)-1 and desc:
            dir_txt = get_step_direction(graph, nid, path[idx+1])
            desc += f" → {dir_txt}"
        if desc:
            step_text_list.append(desc)

    walk_detail = " 👉 ".join(step_text_list)
    display_cfg = {
        "show_all": False,
        "start_level": s_level,
        "end_level": e_level,
        "path_stairs": pass_stair_elev,
        "path": path,
        "start_building": s_build,
        "end_building": e_build
    }
    return path, f"总路程：{total_length:.2f} 距离单位", walk_detail, display_cfg

# 获取楼宇、楼层、教室下拉数据
def get_campus_tree(school_data):
    build_list = []
    level_dict = {}
    room_dict = {}
    for bid in school_data:
        if not (bid.startswith("building") or bid == "gate"):
            continue
        b_short = "Gate" if bid == "gate" else bid.replace("building", "")
        build_list.append(b_short)
        levels = []
        lev_rooms = {}
        for lev in school_data[bid]["levels"]:
            lev_n = lev["name"]
            levels.append(lev_n)
            lev_rooms[lev_n] = [r["name"] for r in lev["classrooms"]]
        level_dict[b_short] = levels
        room_dict[b_short] = lev_rooms
    return build_list, level_dict, room_dict

# 重置会话所有导航状态
def reset_state():
    st.session_state["display_config"] = {"show_all": True, "path": [], "path_stairs": set()}
    st.session_state["final_path"] = None
    st.session_state["distance_text"] = ""
    st.session_state["step_detail"] = ""
    st.session_state["need_calc"] = False
    st.session_state["barrier_mode"] = False

# ====================== 主程序入口 ======================
def main():
    # 会话变量初始化
    init_keys = [
        "page", "worksheet", "display_config", "final_path",
        "distance_text", "step_detail", "need_calc", "barrier_mode"
    ]
    for k in init_keys:
        if k not in st.session_state:
            if k == "page":
                st.session_state[k] = "welcome"
            elif k == "worksheet":
                st.session_state[k] = init_google_sheet()
            elif k == "display_config":
                st.session_state[k] = {"show_all": True, "path": [], "path_stairs": set()}
            elif k in ["distance_text", "step_detail"]:
                st.session_state[k] = ""
            else:
                st.session_state[k] = False

    # 欢迎首页
    if st.session_state["page"] == "welcome":
        try:
            with open("background.jpg", "rb") as f:
                bg = base64.b64encode(f.read()).decode()
            st.markdown(f"""
            <style>.stApp{{background-image:url("data:image/jpeg;base64,{bg}");background-size:cover}}</style>
            """, unsafe_allow_html=True)
        except:
            pass
        st.markdown("""
        <div style="text-align:center;margin-top:35vh;color:white;">
            <h1>SCIS 校园3D导航系统</h1>
            <p>3D可视化校园最短路径导航 | 无障碍电梯通行模式</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入3D地图导航", use_container_width=False):
            update_access_count(st.session_state["worksheet"])
            st.session_state["page"] = "main"
            st.rerun()
        return

    # ========== 主导航页面 ==========
    school_data = load_school_data_detailed()
    if not school_data:
        st.error("缺少 school_data_detailed.json 地图文件！")
        return
    nav_graph = build_nav_graph(school_data)
    builds, lev_map, room_map = get_campus_tree(school_data)

    # 侧边栏控件区
    with st.sidebar:
        st.header("设置与导航")
        # 无障碍开关
        barrier_sel = st.radio("♿ 无障碍通行（仅电梯）", ["No", "Yes"], index=0)
        st.session_state["barrier_mode"] = (barrier_sel == "Yes")
        st.divider()

        # 起点选择
        st.subheader("出发地点")
        s_build = st.selectbox("楼宇", builds, key="sb")
        s_lev = st.selectbox("楼层", lev_map[s_build], key="sl")
        s_room = st.selectbox("教室", room_map[s_build][s_lev], key="sr")

        # 终点选择
        st.subheader("目标地点")
        e_build = st.selectbox("楼宇", builds, key="eb")
        e_lev = st.selectbox("楼层", lev_map[e_build], key="el")
        e_room = st.selectbox("教室", room_map[e_build][e_lev], key="er")

        st.divider()
        btn_calc = st.button("计算最短路线", use_container_width=True)
        btn_reset = st.button("重置视图清空路线", use_container_width=True)
        btn_home = st.button("返回首页", use_container_width=True)

        # 按钮事件绑定
        if btn_calc:
            st.session_state["need_calc"] = True
        if btn_reset:
            reset_state()
            st.rerun()
        if btn_home:
            reset_state()
            st.session_state["page"] = "welcome"
            st.rerun()

    # 标题
    st.title("🏫 SCIS 校园3D导航系统")
    st.divider()

    # 执行路线计算（切换Yes/No均可正常触发）
    if st.session_state["need_calc"]:
        path, dist_txt, step_txt, disp_cfg = route_calculate(
            nav_graph,
            s_build, s_room, s_lev,
            e_build, e_room, e_lev,
            barrier_free=st.session_state["barrier_mode"]
        )
        # 结果存入会话永久保存，不会消失
        st.session_state["final_path"] = path
        st.session_state["distance_text"] = dist_txt
        st.session_state["step_detail"] = step_txt
        st.session_state["display_config"] = disp_cfg
        st.session_state["need_calc"] = False
        st.rerun()

    # 渲染3D画布
    fig = plot_3d_map_plotly(school_data, nav_graph, st.session_state["display_config"])
    st.plotly_chart(fig, use_container_width=True)

    # 底部展示路线文字信息（无论开关切换都保留）
    if st.session_state["distance_text"]:
        st.info(st.session_state["distance_text"])
    if st.session_state["step_detail"]:
        st.markdown("### 📝 完整行走步骤指引")
        st.markdown(st.session_state["step_detail"], unsafe_allow_html=True)

if __name__ == "__main__":
    main()
