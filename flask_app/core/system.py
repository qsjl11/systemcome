from typing import Optional
from .world import World
from .character import Character
from .task import Task
from .llm_service import LLMService
from .logger import setup_logger

class System:
    def __init__(self):
        self.logger = setup_logger('System')
        self.logger.info("初始化系统控制器")
        """初始化系统控制器"""
        self.llm_service = LLMService()
        self.world = World()
        self.character = Character(self.llm_service)
        self.world.set_character(self.character)
        self.energy = 10000.0  # 初始能量值
    
    async def modify_world(self, modification: str) -> str:
        self.logger.info(f"尝试修改世界状态: {modification}")
        """修改世界状态

        Args:
            modification: 修改描述

        Returns:
            str: 修改结果
        """
        # 计算能量消耗
        energy_cost = await self.llm_service.calculate_energy_cost(
            action_type="modify",
            context=f"修改内容：{modification}\n当前能量：{self.energy}"
        )
        
        if self.energy < energy_cost:
            self.logger.warning(f"能量不足 - 需要: {energy_cost}, 当前: {self.energy}")
            return f"能量不足！需要{energy_cost}点能量，当前剩余{self.energy}点能量。"
        
        # 扣除能量并执行修改
        self.energy -= energy_cost
        result = self.world.apply_change(modification)
        self.logger.info(f"世界状态修改成功 - 消耗能量: {energy_cost}, 剩余: {self.energy}")
        return f"{result}\n消耗了{energy_cost}点能量，剩余{self.energy}点能量。"
    
    async def confirm_world_state(self, query: str) -> str:
        self.logger.info(f"查询世界状态: {query}")
        """查询世界状态

        Args:
            query: 查询内容

        Returns:
            str: 查询结果
        """

        context = self.world.get_current_context()
        self.logger.debug(f"获取到的世界状态: {context}")
        
        # 生成查询响应
        prompt = f"""
        [查询内容]
        {query}
        
        [当前世界状态]
        {context['current_state']}
        
        [最近事件]
        {context['recent_history']}
        
        请根据以上信息回答查询：
        """
        
        response = await self.llm_service.generate_response(prompt)
        return response
    
    async def create_task(self, description: str) -> Task:
        self.logger.info(f"创建新任务 - 描述: {description}")
        """创建新任务

        Args:
            description: 任务描述
            reward: 可选的奖励描述

        Returns:
            Task: 创建的任务对象
        """
        # 格式化任务描述和奖励
        formatted_desc, formatted_reward = await self.llm_service.format_task(description)
        
        # 创建任务对象
        task = Task(formatted_desc, formatted_reward)
        
        # 将任务发送给主角
        await self.character.receive_task(task)
        
        self.logger.info(f"任务创建完成 - ID: {id(task)}")
        return task
    
    async def communicate(self, message: str) -> str:
        self.logger.info(f"与主角对话: {message}")
        """与主角直接对话

        Args:
            message: 对话内容

        Returns:
            str: 主角的回复
        """
        
        # 构建对话上下文
        context = {
            "message": message,
            "character": self.character.profile,
            "thoughts": self.character.get_current_thoughts()
        }
        
        # 生成回复
        prompt = f"""
        [系统消息]
        {context['message']}
        
        [角色档案]
        {context['character']}
        
        [当前心理]
        {context['thoughts']}
        
        请以角色的身份回复系统的消息：
        """
        
        response = await self.llm_service.generate_response(prompt)
        self.logger.debug(f"主角回复: {response}")
        
        return response
    
    async def advance_story(self) -> str:
        self.logger.info("触发故事演进")
        """触发自主故事演进

        Returns:
            str: 故事演进结果
        """
        # 生成行动方案
        actions = await self.character.generate_actions()
        
        # 构建故事演进提示
        context = self.world.get_current_context()
        prompt = f"""
        [当前世界状态]
        {context['current_state']}
        
        [最近事件]
        {context['recent_history']}
        
        [候选行动]
        1. {actions[0]}
        2. {actions[1]}
        3. {actions[2]}
        
        请选择一个最合理的行动方案，并描述其展开过程（200字以内）：
        """
        
        # 生成故事发展
        story_progress = await self.llm_service.generate_response(prompt)
        
        # 记录到世界历史
        self.world.log_history(story_progress)
        
        # 更新主角心理状态
        await self.character._update_thoughts("故事发生了新的发展...")
        
        self.logger.info("故事演进完成")
        self.logger.debug(f"故事进展: {story_progress}")
        return story_progress
