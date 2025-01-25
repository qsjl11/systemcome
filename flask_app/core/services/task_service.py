import random
from ..models import Task
from ..utils.constants import TASK_TYPES, TASK_STATUS
from .character_service import CharacterService
from .. import db

class TaskService:
    @staticmethod
    def create_task(task_type):
        """创建新任务"""
        if task_type not in TASK_TYPES:
            return {"error": "无效的任务类型"}, 400
        
        # 创建新任务
        task = Task(
            type=task_type,
            status=TASK_STATUS["PENDING"],
            reward=random.randint(10, 30)
        )
        db.session.add(task)
        
        # 应用任务效果到角色属性
        CharacterService.apply_task_effects(task_type)
        
        db.session.commit()
        
        return {
            "message": f"成功发布{task_type}任务",
            "reward": task.reward,
            "task": task.to_dict()
        }

    @staticmethod
    def get_active_tasks():
        """获取所有进行中的任务"""
        return [task.to_dict() for task in Task.get_active_tasks()]

    @staticmethod
    def get_completed_tasks():
        """获取所有已完成的任务"""
        return [task.to_dict() for task in Task.get_completed_tasks()]

    @staticmethod
    def complete_task(task_id, success=True):
        """完成任务"""
        task = Task.query.get(task_id)
        if not task:
            return {"error": "任务不存在"}, 404
            
        if task.status != TASK_STATUS["PENDING"]:
            return {"error": "任务已结束"}, 400
            
        task.status = TASK_STATUS["SUCCESS"] if success else TASK_STATUS["FAIL"]
        
        # 如果任务成功，应用奖励
        if success:
            character = CharacterService.get_or_create_character()
            TaskService._apply_task_reward(task, character)
        
        db.session.commit()
        
        return {
            "message": "任务完成" if success else "任务失败",
            "task": task.to_dict()
        }

    @staticmethod
    def _apply_task_reward(task, character):
        """应用任务奖励"""
        reward_multiplier = 1.0
        
        # 根据角色状态调整奖励倍率
        if task.type == "战斗":
            # 压力越高，奖励越少
            reward_multiplier *= max(0.5, 1 - (character.stress / 200))
        elif task.type == "探索":
            # 神识越高，奖励越多
            reward_multiplier *= min(2.0, 1 + (character.consciousness / 100))
        elif task.type == "社交":
            # 信任值越高，奖励越多
            reward_multiplier *= min(2.0, 1 + (character.trust / 200))
        
        # 应用基础效果
        effects = TASK_TYPES[task.type]
        updates = {}
        
        for attr, gain in effects.items():
            if attr.endswith('_gain'):  # 确保只处理增益属性
                attr_name = attr.replace('_gain', '')
                if hasattr(character, attr_name):
                    current_value = getattr(character, attr_name)
                    updates[attr_name] = current_value + int(gain * reward_multiplier)
        
        # 更新角色属性
        CharacterService.update_character_attributes(updates)

    @staticmethod
    def get_task_stats():
        """获取任务统计信息"""
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(status=TASK_STATUS["SUCCESS"]).count()
        failed_tasks = Task.query.filter_by(status=TASK_STATUS["FAIL"]).count()
        pending_tasks = Task.query.filter_by(status=TASK_STATUS["PENDING"]).count()
        
        return {
            "total": total_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "pending": pending_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }

    @staticmethod
    def clear_completed_tasks():
        """清理已完成的任务"""
        Task.query.filter(Task.status != TASK_STATUS["PENDING"]).delete()
        db.session.commit()
        return {"message": "已清理完成的任务"}
