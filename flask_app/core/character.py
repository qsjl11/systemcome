from typing import List, Dict
import json
import os
from .task import Task
from .llm_service import LLMService
from .logger import setup_logger
from .utils import read_story_file_to_dict


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
        story_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'story', 'character_init.txt')
        try:
            init_data = read_story_file_to_dict(story_path)
            self.logger.info("成功加载角色初始化配置")
            self.profile = init_data.get("主角设定")
            self.thoughts = init_data.get("主角当前想法", "初次进入这个世界，充满好奇与期待。")
        except Exception as e:
            self.logger.error(f"加载角色初始化配置失败: {e}")
            raise e

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
[行动方案1]=xxxx
[行动方案2]=yyyy
[行动方案3]=zzzz"""

        response = await self.llm_service.generate_response(prompt)
        # 解析响应为行动列表
        actions = [line.split("]=")[1] for line in response.strip().split('\n') if "[行动方案" in line]
        self.logger.debug(f"生成的行动方案: {actions}")
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

    async def update_attributes(self, changes: dict):
        """更新角色属性

        Args:
            changes: 属性变更字典
        """
        self.logger.info(f"更新角色属性: {changes}")

        # 构建提示让LLM更新角色档案
        prompt = f"""
[当前角色档案]
{self.profile}

[需要更新的变更]
{json.dumps(changes, ensure_ascii=False, indent=2)}

请根据上述变更信息，更新角色档案。保持原有格式，仅更新相关内容。
如果变更中包含任务完成信息，请在档案中适当位置添加任务完成记录。

返回完整的更新后的角色档案："""

        # 使用LLM更新档案
        updated_profile = await self.llm_service.generate_response(prompt)
        self.profile = updated_profile

        self.logger.debug(f"更新后的档案: {self.profile}")

    def get_current_thoughts(self) -> str:
        self.logger.debug(f"获取当前心理活动: {self.thoughts}")
        """获取当前心理活动

        Returns:
            str: 当前心理活动描述
        """
        return self.thoughts

    async def update(self, event: str):
        self.logger.info("更新角色状态")
        """更新角色状态（当世界发生变化时调用）"""
        await self._update_thoughts(f"感知到世界发生了变化...{event}")

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

    def get_character_info_str(self) -> str:
        self.logger.info("获取角色信息")
        """获取角色信息

        Returns:
            Dict: 角色信息
        """
        task_info = [str(task) for task in self.pending_tasks]
        info = f"""[[角色档案]]：
{self.profile}

[[当前心理]]：
{self.thoughts}

[[角色任务]]：
{task_info}"""

        return info
