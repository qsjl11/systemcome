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
        self.dialogue_history = []  # 对话历史记录
        self.dialogue_summaries = []  # 对话总结记录

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

        # 保存查询结果到世界历史
        self.world.save_query_result(query, response)

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
            "character": str(self.character.profile),
            "tasks": [str(i) for i in self.character.pending_tasks],
            "thoughts": self.character.get_current_thoughts(),
            "dialogue_history": self._format_recent_history(200),  # 获取最近5轮对话
            "dialogue_summaries": "\n".join(self.dialogue_summaries[-3:])  # 最近3个总结
        }

        # 生成回复
        prompt = f"""
        [历史对话总结]
        {context['dialogue_summaries']}
        
        [角色设定]
        {context['character']}
        
        [当前心理状态]
        {context['thoughts']}
        
        [当前任务]
        {context['tasks']}
        
        [最近对话记录]
        {context['dialogue_history']}
        
        [当前系统问出的消息]
        {context['message']}
        
        请以角色的身份，考虑以上背景信息，自然且连贯地回复"系统"的消息。回复时要：
        1. 保持角色性格特征的一致性
        2. 考虑历史对话的上下文
        3. 展现角色当前的心理状态
        4. 确保回复的连贯性和自然度
        5. 同时更新角色的心理状态
        
        以如下格式回复：
        [回复内容]：XXXXX
        [心理变化]：YYYYY
        """

        response = await self.llm_service.generate_response(prompt)
        self.logger.debug(f"主角回复: {response}")

        for i in response.split("\n"):
            if "[回复内容]：" in i:
                response_text = i.split("[回复内容]：")[1].strip()
            if "[心理变化]：" in i:
                thoughts = i.split("[心理变化]：")[1].strip()

        self.character.thoughts = thoughts

        # 记录对话
        self.dialogue_history.append({
            "system": message,
            "character": response_text
        })

        return response_text

    def _format_recent_history(self, count: int) -> str:
        """格式化最近的对话历史

        Args:
            count: 获取的对话轮数

        Returns:
            str: 格式化的对话历史
        """
        recent = self.dialogue_history[-count:] if len(self.dialogue_history) > 0 else []
        formatted = []
        for i, dialogue in enumerate(recent, 1):
            formatted.append(f"第{i}轮对话：")
            formatted.append(f"系统：{dialogue['system']}")
            formatted.append(f"角色：{dialogue['character']}\n")
        return "\n".join(formatted)

    async def summarize_current_dialogue(self) -> str:
        """总结当前对话历史"""
        if not self.dialogue_history:
            return "暂无对话记录"

        prompt = f"""
        请总结以下对话的主要内容（100字以内）：
        
        {self._format_recent_history(len(self.dialogue_history))}
        
        请提供简洁的总结：
        """

        summary = await self.llm_service.generate_response(prompt)
        self.dialogue_summaries.append(summary)
        return summary

    async def clear_dialogue_history(self) -> None:
        """清除当前对话历史，在开始新故事前调用"""
        if self.dialogue_history:
            await self.summarize_current_dialogue()
            self.dialogue_history = []
            self.logger.info("已清除对话历史并保存总结")

    async def advance_story(self):
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
        
        根据以上信息进行行动选择，并描述其展开过程和后续世界的变化，要注意：
        1. 不要回复选择行动1、2、3，而是直接描述行动内容。
        2. 以第三人称视角描述故事，主角名称应当偶尔直接提及，以确保玩家能理解主人公是谁。
        3. 风格上要符合当前世界设定，保持优秀网络小说的描写风格，如果有需要，有适当的心理、环境和他人互动等描写。
        
        请选择一个最合理的行动方案，并描述其展开过程（200字以内）：
        """

        # 生成故事发展
        story_progress = await self.llm_service.generate_response(prompt)

        # 记录到世界历史
        self.world.log_history(story_progress)

        # 更新主角心理状态
        await self.character._update_thoughts(f"故事发生了新的发展...{story_progress}")

        self.logger.info("故事演进完成")
        self.logger.debug(f"故事进展: {story_progress}")
        return story_progress
