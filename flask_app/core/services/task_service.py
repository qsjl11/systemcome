import random
from ..models import Task
from ..utils.constants import TASK_TYPES, TASK_STATUS
from .character_service import CharacterService
from .. import db
from ..utils.logging_utils import get_logger

logger = get_logger()

class TaskService:
    @staticmethod
    def create_task(task_type):
        """创建新任务"""
        if task_type not in TASK_TYPES:
            logger.warning(f"尝试创建无效的任务类型: {task_type}")
            return {"error": "无效的任务类型"}, 400
        
        # 创建新任务
        reward = random.randint(10, 30)
        logger.info(f"创建新任务 - 类型: {task_type}, 奖励: {reward}")
        task = Task(
            type=task_type,
            status=TASK_STATUS["PENDING"],
            reward=reward
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
            logger.warning(f"尝试完成不存在的任务: {task_id}")
            return {"error": "任务不存在"}, 404
            
        if task.status != TASK_STATUS["PENDING"]:
            logger.warning(f"尝试完成已结束的任务: {task_id}, 当前状态: {task.status}")
            return {"error": "任务已结束"}, 400
            
        task.status = TASK_STATUS["SUCCESS"] if success else TASK_STATUS["FAIL"]
        logger.info(f"完成任务 - ID: {task_id}, 类型: {task.type}, 结果: {'成功' if success else '失败'}")
        
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
        logger.info(f"开始计算任务奖励 - 任务类型: {task.type}")
        
        # 根据角色状态调整奖励倍率
        if task.type == "战斗":
            # 压力越高，奖励越少
            reward_multiplier *= max(0.5, 1 - (character.stress / 200))
            logger.debug(f"战斗奖励倍率: {reward_multiplier:.2f} (压力影响)")
        elif task.type == "探索":
            # 神识越高，奖励越多
            reward_multiplier *= min(2.0, 1 + (character.consciousness / 100))
            logger.debug(f"探索奖励倍率: {reward_multiplier:.2f} (神识影响)")
        elif task.type == "社交":
            # 信任值越高，奖励越多
            reward_multiplier *= min(2.0, 1 + (character.trust / 200))
            logger.debug(f"社交奖励倍率: {reward_multiplier:.2f} (信任影响)")
        
        # 应用基础效果
        effects = TASK_TYPES[task.type]
        updates = {}
        
        for attr, gain in effects.items():
            if attr.endswith('_gain'):  # 确保只处理增益属性
                attr_name = attr.replace('_gain', '')
                if hasattr(character, attr_name):
                    current_value = getattr(character, attr_name)
                    new_value = current_value + int(gain * reward_multiplier)
                    updates[attr_name] = new_value
                    logger.debug(f"属性增益 - {attr_name}: {current_value} -> {new_value} (基础增益: {gain}, 倍率: {reward_multiplier:.2f})")
        
        # 更新角色属性
        CharacterService.update_character_attributes(updates)

    @staticmethod
    def get_task_stats():
        """获取任务统计信息"""
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(status=TASK_STATUS["SUCCESS"]).count()
        failed_tasks = Task.query.filter_by(status=TASK_STATUS["FAIL"]).count()
        pending_tasks = Task.query.filter_by(status=TASK_STATUS["PENDING"]).count()
        
        logger.info(f"任务统计 - 总数: {total_tasks}, 完成: {completed_tasks}, 失败: {failed_tasks}, 待处理: {pending_tasks}")
        
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
        completed_count = Task.query.filter(Task.status != TASK_STATUS["PENDING"]).count()
        Task.query.filter(Task.status != TASK_STATUS["PENDING"]).delete()
        db.session.commit()
        logger.info(f"清理已完成任务 - 清理数量: {completed_count}")
        return {"message": "已清理完成的任务"}
