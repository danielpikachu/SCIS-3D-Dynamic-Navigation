# languages.py
# 支持多语言：英文、中文、法语

LANGUAGES = {
    'en': {
        # 导航栏
        'accessibility_setting': '♿ Accessibility Setting',
        'barrier_free_access': 'Are you a user requiring barrier-free access?',
        'select_no': 'Select No: All stairs are available, elevator is disabled. Select Yes: Only Building B stairs are disabled, ElevatorB1 is available',
        'select_locations': '📍 Select Locations',
        'start_point': 'Start Point',
        'end_point': 'End Point',
        'building': 'Building',
        'floor': 'Floor',
        'classroom': 'Classroom',
        'find_path': '🔍 Find Shortest Path',
        'reset_view': '🔄 Reset View',
        'back_to_welcome': '🚪 Back to Welcome',
        
        # 欢迎页面
        'welcome_title': 'NAVIGATE YOUR CAMPUS',
        'welcome_subtitle': 'Find Classrooms, Labs, Resources In Stunning 3D',
        'explore_3d': 'EXPLORE 3D MAP',
        
        # 主页面
        'campus_navigation': '🏫 SCIS Campus Navigation System',
        'data_loaded': '✅ Campus Data Loaded Successfully!',
        'navigation_result': '📊 Navigation Result:',
        'path_details': '🛤️ Path Details',
        'total_distance': 'Total Distance: {:.2f} Units',
        'no_path': 'No available path between the two classrooms',
        'navigation_error': 'Navigation error: {}',
        'loading_error': 'Failed to load data file!',
        'building_not_found': 'Invalid building selection, only Buildings A, B, C and Gate are supported',
        
        # 方向指示
        'up': 'up',
        'down': 'down',
        'forward': 'forward',
        'backward': 'backward',
        'right': 'right',
        'left': 'left',
        'cross_corridor': 'Cross corridor from Building {} to Building {} ({})',
        
        # 节点类型
        'stair': 'Stair',
        'elevator': 'Elevator',
        'classroom': 'Classroom',
        'corridor': 'Corridor',
    },
    'zh': {
        # 导航栏
        'accessibility_setting': '♿ 无障碍设置',
        'barrier_free_access': '您是否需要无障碍通道？',
        'select_no': '选择"否"：所有楼梯可用，电梯禁用。选择"是"：仅B楼楼梯禁用，电梯可用',
        'select_locations': '📍 选择位置',
        'start_point': '起点',
        'end_point': '终点',
        'building': '建筑',
        'floor': '楼层',
        'classroom': '教室',
        'find_path': '🔍 查找最短路径',
        'reset_view': '🔄 重置视图',
        'back_to_welcome': '🚪 返回欢迎页',
        
        # 欢迎页面
        'welcome_title': '校园导航系统',
        'welcome_subtitle': '在3D地图中查找教室、实验室和资源',
        'explore_3d': '探索3D地图',
        
        # 主页面
        'campus_navigation': '🏫 SCIS 校园导航系统',
        'data_loaded': '✅ 校园数据加载成功！',
        'navigation_result': '📊 导航结果：',
        'path_details': '🛤️ 路径详情',
        'total_distance': '总距离：{:.2f} 单位',
        'no_path': '两教室之间没有可用路径',
        'navigation_error': '导航错误：{}',
        'loading_error': '加载数据文件失败！',
        'building_not_found': '无效的建筑选择，仅支持A、B、C楼和校门',
        
        # 方向指示
        'up': '上',
        'down': '下',
        'forward': '向前',
        'backward': '向后',
        'right': '向右',
        'left': '向左',
        'cross_corridor': '从{}楼到{}楼的跨楼走廊 ({})',
        
        # 节点类型
        'stair': '楼梯',
        'elevator': '电梯',
        'classroom': '教室',
        'corridor': '走廊',
    },
    'fr': {
        # 导航栏
        'accessibility_setting': '♿ Paramètres d\'accessibilité',
        'barrier_free_access': 'Avez-vous besoin d\'un accès sans obstacle ?',
        'select_no': 'Sélectionnez "Non" : Tous les escaliers sont disponibles, l\'ascenseur est désactivé. Sélectionnez "Oui" : Seuls les escaliers du bâtiment B sont désactivés, l\'ascenseur est disponible',
        'select_locations': '📍 Sélectionnez les emplacements',
        'start_point': 'Point de départ',
        'end_point': 'Point d\'arrivée',
        'building': 'Bâtiment',
        'floor': 'Étage',
        'classroom': 'Salle de classe',
        'find_path': '🔍 Trouver le chemin le plus court',
        'reset_view': '🔄 Réinitialiser la vue',
        'back_to_welcome': '🚪 Retour à l\'accueil',
        
        # 欢迎页面
        'welcome_title': 'NAVIGUEZ SUR VOTRE CAMPUS',
        'welcome_subtitle': 'Trouvez des salles de classe, des laboratoires et des ressources en 3D',
        'explore_3d': 'EXPLORER LA CARTE 3D',
        
        # 主页面
        'campus_navigation': '🏫 Système de navigation du campus SCIS',
        'data_loaded': '✅ Données du campus chargées avec succès !',
        'navigation_result': '📊 Résultat de la navigation :',
        'path_details': '🛤️ Détails du chemin',
        'total_distance': 'Distance totale : {:.2f} unités',
        'no_path': 'Aucun chemin disponible entre les deux salles de classe',
        'navigation_error': 'Erreur de navigation : {}',
        'loading_error': 'Échec du chargement du fichier de données !',
        'building_not_found': 'Sélection de bâtiment invalide, seuls les bâtiments A, B, C et la porte sont pris en charge',
        
        # 方向指示
        'up': 'monter',
        'down': 'descendre',
        'forward': 'tout droit',
        'backward': 'reculer',
        'right': 'à droite',
        'left': 'à gauche',
        'cross_corridor': 'Couloir de liaison du bâtiment {} au bâtiment {} ({})',
        
        # 节点类型
        'stair': 'Escalier',
        'elevator': 'Ascenseur',
        'classroom': 'Salle de classe',
        'corridor': 'Couloir',
    }
}

# 支持的语言列表
SUPPORTED_LANGUAGES = ['en', 'zh', 'fr']

# 语言名称映射
LANGUAGE_NAMES = {
    'en': 'English',
    'zh': '中文',
    'fr': 'Français'
}

def get_text(key, lang='en'):
    """获取指定语言的文本"""
    if lang not in LANGUAGES:
        lang = 'en'
    return LANGUAGES[lang].get(key, key)
