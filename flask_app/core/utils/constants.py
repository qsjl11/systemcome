# 境界名称映射
CULTIVATION_STAGES = {
    0: "凡人",
    1: "炼气期",
    3: "筑基期",
    5: "金丹期",
    8: "元婴期"
}

# 小境界列表
CULTIVATION_REALMS = ["初期", "中期", "后期", "大圆满"]

# 任务类型
TASK_TYPES = {
    "战斗": {
        "vitality_gain": 5,     # 气血增益
        "stress_gain": 10       # 压力增益
    },
    "探索": {
        "spiritual_power_gain": 10,  # 灵力增益
        "consciousness_gain": 1      # 神识增益
    },
    "社交": {
        "trust_gain": 5,        # 信任增益
        "fortune_gain": 1       # 气运增益
    }
}

# 事件类型
EVENT_TYPES = ["奇遇", "劫难", "日常", "因果"]

# 事件状态
EVENT_STATUS = {
    "PENDING": "pending",
    "ACTIVE": "active",
    "COMPLETED": "completed"
}

# 任务状态
TASK_STATUS = {
    "PENDING": "pending",
    "SUCCESS": "success",
    "FAIL": "fail"
}

# 默认值配置
DEFAULT_VALUES = {
    # 基础属性默认值
    "vitality": 100,           # 气血
    "spiritual_power": 100,    # 灵力
    "consciousness": 1,        # 神识
    "physique": 1,            # 体魄
    "fortune": 1,             # 气运
    
    # 性格维度默认值
    "alignment": 0.0,         # 正邪倾向
    "decision_style": 50.0,   # 决策风格
    "social_mode": 50.0,      # 社交模式
    "fortune_sensitivity": 50.0,  # 机缘敏感
    "dao_heart": "求知",      # 道心类型
    
    # 其他属性默认值
    "trust": 50,              # 信任值
    "stress": 0               # 压力值
}

# 系统配置
SYSTEM_CONFIG = {
    "MAX_SAVE_SLOTS": 10,     # 最大存档数
    "MAX_ACTIVE_EVENTS": 3,   # 最大同时活跃事件数
    "EVENT_COOLDOWN_DAYS": 1  # 事件冷却时间（天）
}
