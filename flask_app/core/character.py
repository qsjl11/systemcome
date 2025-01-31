from typing import List, Dict
import json
import os
from .task import Task
from .llm_service import LLMService
from .logger import setup_logger

class Character:
    def __init__(self, llm_service: LLMService):
        self.logger = setup_logger('Character')
        self.logger.info("初始化主角代理")
        """初始化主角代理

        Args:
            llm_service: LLM服务实例
        """
        self.llm_service = llm_service
        self.pending_tasks: List[Task] = []
        
        # 读取初始化配置
        story_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'story', 'character_init.json')
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                init_data = json.load(f)
                self.logger.info("成功加载角色初始化配置")
                self.profile = init_data.get("profile", {
                    "name": "主角",
                    "level": 1,
                    "skills": [],
                    "items": []
                })
                self.thoughts = init_data.get("initial_thoughts", "初次进入这个世界，充满好奇与期待。")
        except Exception as e:
            self.logger.error(f"加载角色初始化配置失败: {e}")
            self.profile = {
                "name": "主角",
                "level": 1,
                "skills": [],
                "items": []
            }
            self.thoughts = "初次进入这个世界，充满好奇与期待。"
    
    async def generate_actions(self) -> List[str]:
        self.logger.info("生成行动方案")
        """生成三个候选行动方案

        Returns:
            List[str]: 三个候选行动方案
        """
        # 构建决策上下文
        context = {
            "profile": self.profile,
            "thoughts": self.thoughts,
            "active_tasks": []
        }
        
        # 注入任务影响
        self.logger.debug(f"当前待处理任务数: {len(self.pending_tasks)}")
        for task in self.pending_tasks:
            context = task.apply_influence(context)
        
        # 生成行动方案
        prompt = f"""
        [角色档案]
        {context['profile']}
        
        [当前心理]
        {context['thoughts']}
        
        [待处理任务]
        {context['active_tasks']}
        
        请生成三个候选行动方案，考虑任务影响但不强制服从。每个方案需要包含行动描述和预期结果。
        
        返回格式：
        1. [行动方案1]
        2. [行动方案2]
        3. [行动方案3]
        """
        
        response = await self.llm_service.generate_response(prompt)
        # 解析响应为行动列表
        actions = [line.strip()[3:] for line in response.strip().split('\n') if line.strip()]
        self.logger.debug(f"生成的行动方案: {actions[:3]}")
        return actions[:3]  # 确保只返回3个方案
    
    async def receive_task(self, task: Task):
        self.logger.info(f"接收新任务: {task.description}")
        """接收任务并存储

        Args:
            task: 任务对象
        """
        self.pending_tasks.append(task)
        # 更新心理活动以反映新任务
        await self._update_thoughts(f"收到新任务：{task.description}")
    
    def get_current_thoughts(self) -> str:
        self.logger.debug(f"获取当前心理活动: {self.thoughts}")
        """获取当前心理活动

        Returns:
            str: 当前心理活动描述
        """
        return self.thoughts
    
    async def update(self):
        self.logger.info("更新角色状态")
        """更新角色状态（当世界发生变化时调用）"""
        await self._update_thoughts("感知到世界发生了变化...")
    
    async def _update_thoughts(self, trigger: str):
        self.logger.debug(f"更新心理活动 - 触发: {trigger}")
        """更新心理活动

        Args:
            trigger: 触发更新的事件描述
        """
        prompt = f"""
        [当前情况]
        {trigger}
        
        [角色档案]
        {self.profile}
        
        [当前心理]
        {self.thoughts}
        
        请生成一段新的心理活动描述（100字以内）：
        """
        
        self.thoughts = await self.llm_service.generate_response(prompt)
        self.logger.debug(f"新的心理活动: {self.thoughts}")
