import json
import zlib
from datetime import datetime

def serialize_character(character):
    """序列化角色数据"""
    return {
        # 基础五维
        'vitality': character.vitality,          # 气血
        'spiritual_power': character.spiritual_power,  # 灵力
        'consciousness': character.consciousness,      # 神识
        'physique': character.physique,              # 体魄
        'fortune': character.fortune,                # 气运
        
        # 境界系统
        'cultivation_stage': character.cultivation_stage,    # 境界阶段
        'cultivation_realm': character.cultivation_realm,    # 小境界
        'breakthrough_chance': character.breakthrough_chance,  # 破境成功率
        
        # 灵根资质
        'metal_affinity': character.metal_affinity,    # 金
        'wood_affinity': character.wood_affinity,      # 木
        'water_affinity': character.water_affinity,    # 水
        'fire_affinity': character.fire_affinity,      # 火
        'earth_affinity': character.earth_affinity,    # 土
        
        # 性格维度
        'alignment': character.alignment,              # 正邪倾向
        'decision_style': character.decision_style,    # 决策风格
        'social_mode': character.social_mode,          # 社交模式
        'fortune_sensitivity': character.fortune_sensitivity,  # 机缘敏感
        'dao_heart': character.dao_heart,              # 道心类型
        
        # 其他属性
        'trust': character.trust,                      # 信任值
        'stress': character.stress                     # 压力值
    }

def serialize_tasks(tasks):
    """序列化任务数据"""
    return [{
        'type': task.type,
        'status': task.status,
        'reward': task.reward
    } for task in tasks]

def compress_data(data):
    """压缩数据"""
    json_str = json.dumps(data)
    return zlib.compress(json_str.encode('utf-8'))

def decompress_data(compressed_data):
    """解压数据"""
    if not compressed_data:
        return None
    json_str = zlib.decompress(compressed_data).decode('utf-8')
    return json.loads(json_str)

def create_save_data(character, tasks, events):
    """创建存档数据"""
    save_data = {
        'character': serialize_character(character),
        'tasks': serialize_tasks(tasks),
        'events': events
    }
    return compress_data(save_data)

def restore_save_data(character, task_model, events, compressed_data, db):
    """恢复存档数据"""
    if not compressed_data:
        return False
        
    save_data = decompress_data(compressed_data)
    if not save_data:
        return False
        
    # 恢复角色数据
    char_data = save_data.get('character', {})
    
    # 基础五维
    character.vitality = char_data.get('vitality', 100)
    character.spiritual_power = char_data.get('spiritual_power', 100)
    character.consciousness = char_data.get('consciousness', 1)
    character.physique = char_data.get('physique', 1)
    character.fortune = char_data.get('fortune', 1)
    
    # 境界系统
    character.cultivation_stage = char_data.get('cultivation_stage', 0)
    character.cultivation_realm = char_data.get('cultivation_realm', '凡人')
    character.breakthrough_chance = char_data.get('breakthrough_chance', 0.0)
    
    # 灵根资质
    character.metal_affinity = char_data.get('metal_affinity', 0.0)
    character.wood_affinity = char_data.get('wood_affinity', 0.0)
    character.water_affinity = char_data.get('water_affinity', 0.0)
    character.fire_affinity = char_data.get('fire_affinity', 0.0)
    character.earth_affinity = char_data.get('earth_affinity', 0.0)
    
    # 性格维度
    character.alignment = char_data.get('alignment', 0)
    character.decision_style = char_data.get('decision_style', 50)
    character.social_mode = char_data.get('social_mode', 50)
    character.fortune_sensitivity = char_data.get('fortune_sensitivity', 50)
    character.dao_heart = char_data.get('dao_heart', '求知')
    
    # 其他属性
    character.trust = char_data.get('trust', 50)
    character.stress = char_data.get('stress', 0)
    
    # 恢复任务数据
    tasks_data = save_data.get('tasks', [])
    task_model.query.delete()  # 清除当前任务
    for task_data in tasks_data:
        new_task = task_model(
            type=task_data['type'],
            status=task_data['status'],
            reward=task_data['reward']
        )
        db.session.add(new_task)
    
    # 恢复事件日志
    events.clear()  # 清除当前事件
    events.extend(save_data.get('events', []))
    
    return True
