import json
import zlib
from datetime import datetime
from ..models import SaveSlot, Character, Task
from ..utils.constants import SYSTEM_CONFIG
from .. import db

class SaveService:
    @staticmethod
    def create_save(slot_num, save_name=''):
        """创建新存档"""
        if not (1 <= slot_num <= SYSTEM_CONFIG["MAX_SAVE_SLOTS"]):
            return {"error": "无效的存档位置"}, 400
            
        character = Character.query.first()
        if not character:
            return {"error": "未找到角色数据"}, 404
            
        tasks = Task.query.all()
        events = []  # TODO: 实现事件日志系统
        
        # 创建存档数据
        save_data = SaveService._create_save_data(character, tasks, events)
        
        # 更新或创建存档
        save_slot = SaveSlot.query.filter_by(slot_num=slot_num).first()
        if not save_slot:
            save_slot = SaveSlot(slot_num=slot_num)
        
        save_slot.save_name = save_name or f'存档 {slot_num}'
        save_slot.save_time = datetime.utcnow()
        save_slot.character_data = save_data
        save_slot.event_log = '[]'  # TODO: 实现事件日志序列化
        
        db.session.add(save_slot)
        db.session.commit()
        
        return {
            "message": f"成功保存到存档位 {slot_num}",
            "save_time": save_slot.save_time.isoformat()
        }

    @staticmethod
    def load_save(slot_num):
        """加载存档"""
        if not (1 <= slot_num <= SYSTEM_CONFIG["MAX_SAVE_SLOTS"]):
            return {"error": "无效的存档位置"}, 400
            
        save_slot = SaveSlot.query.filter_by(slot_num=slot_num).first()
        if not save_slot:
            return {"error": "存档不存在"}, 404
            
        character = Character.query.first()
        if not character:
            character = Character()
            db.session.add(character)
        
        events = []  # TODO: 实现事件日志系统
        
        if SaveService._restore_save_data(character, Task, events, save_slot.character_data):
            db.session.commit()
            return {
                "message": f"成功读取存档 {slot_num}",
                "save_time": save_slot.save_time.isoformat()
            }
        else:
            return {"error": "存档数据损坏"}, 500

    @staticmethod
    def get_all_saves():
        """获取所有存档信息"""
        saves = SaveSlot.query.all()
        return [{
            "slot_num": save.slot_num,
            "save_name": save.save_name,
            "save_time": save.save_time.isoformat()
        } for save in saves]

    @staticmethod
    def _create_save_data(character, tasks, events):
        """创建存档数据"""
        save_data = {
            "character": SaveService._serialize_character(character),
            "tasks": SaveService._serialize_tasks(tasks),
            "events": events
        }
        return SaveService._compress_data(save_data)

    @staticmethod
    def _restore_save_data(character, task_model, events, compressed_data):
        """恢复存档数据"""
        if not compressed_data:
            return False
            
        try:
            save_data = SaveService._decompress_data(compressed_data)
            if not save_data:
                return False
                
            # 恢复角色数据
            char_data = save_data.get("character", {})
            for attr, value in char_data.items():
                if hasattr(character, attr):
                    setattr(character, attr, value)
            
            # 恢复任务数据
            tasks_data = save_data.get("tasks", [])
            task_model.query.delete()  # 清除当前任务
            for task_data in tasks_data:
                new_task = task_model(
                    type=task_data["type"],
                    status=task_data["status"],
                    reward=task_data["reward"]
                )
                db.session.add(new_task)
            
            # 恢复事件日志
            events.clear()
            events.extend(save_data.get("events", []))
            
            return True
        except Exception as e:
            print(f"存档恢复错误: {e}")
            return False

    @staticmethod
    def _serialize_character(character):
        """序列化角色数据"""
        return {
            # 基础五维
            'vitality': character.vitality,
            'spiritual_power': character.spiritual_power,
            'consciousness': character.consciousness,
            'physique': character.physique,
            'fortune': character.fortune,
            
            # 境界系统
            'cultivation_stage': character.cultivation_stage,
            'cultivation_realm': character.cultivation_realm,
            'breakthrough_chance': character.breakthrough_chance,
            
            # 灵根资质
            'metal_affinity': character.metal_affinity,
            'wood_affinity': character.wood_affinity,
            'water_affinity': character.water_affinity,
            'fire_affinity': character.fire_affinity,
            'earth_affinity': character.earth_affinity,
            
            # 性格维度
            'alignment': character.alignment,
            'decision_style': character.decision_style,
            'social_mode': character.social_mode,
            'fortune_sensitivity': character.fortune_sensitivity,
            'dao_heart': character.dao_heart,
            
            # 其他属性
            'trust': character.trust,
            'stress': character.stress
        }

    @staticmethod
    def _serialize_tasks(tasks):
        """序列化任务数据"""
        return [{
            "type": task.type,
            "status": task.status,
            "reward": task.reward
        } for task in tasks]

    @staticmethod
    def _compress_data(data):
        """压缩数据"""
        json_str = json.dumps(data)
        return zlib.compress(json_str.encode('utf-8'))

    @staticmethod
    def _decompress_data(compressed_data):
        """解压数据"""
        try:
            json_str = zlib.decompress(compressed_data).decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            print(f"数据解压错误: {e}")
            return None
