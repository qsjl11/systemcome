import json
import zlib
from datetime import datetime

def serialize_character(character):
    """序列化角色数据"""
    return {
        'cultivation': character.cultivation,
        'trust': character.trust,
        'stress': character.stress
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

def restore_save_data(character, compressed_data):
    """恢复存档数据"""
    if not compressed_data:
        return False
        
    save_data = decompress_data(compressed_data)
    if not save_data:
        return False
        
    # 恢复角色数据
    char_data = save_data.get('character', {})
    character.cultivation = char_data.get('cultivation', 0)
    character.trust = char_data.get('trust', 50)
    character.stress = char_data.get('stress', 0)
    
    return True
