from enum import Enum
from typing import Dict
from .logger import setup_logger

class TaskStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Task:
    def __init__(self, description: str, reward: str, influence: float = 1.0):
        self.logger = setup_logger('Task')
        self.logger.info(f"创建新任务 - 描述: {description}")
        """初始化任务对象

        Args:
            description: 任务目标描述
            reward: 完成奖励描述
            influence: 对主角决策的影响权重（默认1.0）
        """
        self.description = description
        self.status = TaskStatus.PENDING
        self.influence = influence
        self.reward = reward
    
    def apply_influence(self, context: Dict) -> Dict:
        self.logger.debug(f"应用任务影响 - 状态: {self.status.value}")
        """将任务影响注入决策上下文

        Args:
            context: 原始决策上下文

        Returns:
            Dict: 注入任务影响后的上下文
        """
        # 只有处于PENDING或ACCEPTED状态的任务才会影响决策
        if self.status in [TaskStatus.PENDING, TaskStatus.ACCEPTED]:
            context["active_tasks"] = context.get("active_tasks", [])
            task_info = {
                "description": self.description,
                "reward": self.reward,
                "influence": self.influence
            }
            context["active_tasks"].append(task_info)
        
        self.logger.debug(f"更新后的上下文: {context}")
        return context
    
    def accept(self):
        """接受任务"""
        self.logger.info(f"任务被接受 - 描述: {self.description}")
        self.status = TaskStatus.ACCEPTED
    
    def reject(self):
        """拒绝任务"""
        self.logger.info(f"任务被拒绝 - 描述: {self.description}")
        self.status = TaskStatus.REJECTED
    
    def __str__(self) -> str:
        return f"Task(description='{self.description}', status={self.status.value}, reward='{self.reward}')"
