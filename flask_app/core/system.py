from typing import Optional, List
import json
import os
from .world import World
from .character import Character
from .llm_service import LLMService
from .logger import setup_logger
import re


class System:
    def __init__(self, story_name: str = "默认剧本"):
        self.logger = setup_logger('System')
        self.logger.info("初始化系统控制器")
        """初始化系统控制器"""
        self.llm_service = LLMService()
        self.world = World(story_name)
        self.character = Character(self.llm_service, story_name)
        self.world.set_character(self.character)
        self.energy = 10000.0  # 初始能量值
        self.dialogue_history = []  # 对话历史记录
        self.dialogue_summaries = []  # 对话总结记录
        self.qu_history = []  # qu命令历史记录
        self.current_story = story_name or "默认剧本"

    async def modify_state(self, modification: str) -> str:
        """修改世界或角色状态
        
        Args:
            modification: 修改描述
            
        Returns:
            str: 修改结果
        """
        # 构建提示以判断修改类型和计算能量
        prompt = f"""
[修改内容]
{modification}

请分析这个修改内容属于哪种类型。注意：
1. 分析修改内容是针对世界状态还是角色状态
2. 发布任务是给主角发布任务，因此类型为character

请严格按以下格式回复：
[类型]：world或character"""

        # 获取类型判断和能量计算
        response = await self.llm_service.generate_response(prompt, use_small_model=True)

        # 解析响应
        modification_type = ""
        energy_cost = 1

        for line in response.split("\n"):
            if "[类型]：" in line:
                if "world" in line:
                    modification_type = "world"
                else:
                    modification_type = "character"

        self.logger.info(f"修改类型: {modification_type}, 所需能量: {energy_cost}")

        # 检查能量是否足够
        if self.energy < energy_cost:
            self.logger.warning(f"能量不足 - 需要: {energy_cost}, 当前: {self.energy}")
            return f"能量不足！需要{energy_cost}点能量，当前剩余{self.energy}点能量。"

        # 扣除能量并执行修改
        self.energy -= energy_cost

        try:
            if modification_type == "world":
                self.world.apply_change(modification)
                self.logger.info(f"世界状态修改成功 - 消耗能量: {energy_cost}, 剩余: {self.energy}")
                result_msg = f"世界状态已更新：{modification}"
            else:  # character
                await self.character.update_attributes(modification)
                self.logger.info(f"角色状态修改成功 - 消耗能量: {energy_cost}, 剩余: {self.energy}")
                result_msg = f"角色状态变更如下：{modification}"

            response = await self.communicate(modification)

            return f"[{result_msg}]\n[消耗了{energy_cost}点能量，剩余{self.energy}点能量。]\n\n{response}"
        except Exception as e:
            self.logger.error(f"修改失败: {e}")
            return f"修改失败：{str(e)}"

    async def confirm_world_state(self, query: str) -> str:
        self.logger.info(f"查询世界状态: {query}")
        """查询世界状态

        Args:
            query: 查询内容

        Returns:
            str: 查询结果
        """

        world_current_context = self.world.get_current_context()
        self.logger.debug(f"获取到的世界状态: {world_current_context}")

        character_info = self.character.get_character_info_str()
        self.logger.debug(f"获取到的角色状态: {character_info}")

        # 获取qu历史
        qu_context = self._format_qu_history(10)  # 获取最近10条qu记录
        self.logger.debug(f"获取到的qu历史: {qu_context}")

        # 获取对话历史
        dialogue_context = self._format_recent_history(10)
        self.logger.debug(f"获取到的对话历史: {dialogue_context}")

        # 生成查询响应
        prompt = f"""
{character_info}        

{world_current_context}

[最近对话记录]
{dialogue_context}

[最近查询记录]
{qu_context}

[玩家查询内容]
{query}

你是一个网文系统，你为玩家提供了一种可以直接获得世界信息的能力，因此你需要根据世界的各种信息回答玩家查询的内容，注意要以故事事实的方式进行直接给出陈述结果。具体来说要求如下：
1. 如果查询的内容已经在上文中提及，请按照上文进行回答。
2. 如果查询的内容不包含在上文中，可以进行编造，这个是故事的一部分。
3. 创作时请保持逻辑性和连贯性，不要与上文内容相悖。
4. 你是回答问题，不要用“在这个故事中”、“根据上文”等开头，避免玩家感到不真实。
5. 在之前已有的信息基础之上，查询结果要给出详细信息。

请根据以上信息回答查询："""

        response = await self.llm_service.generate_response(prompt)

        # 保存查询结果到世界历史
        self.world.save_query_result(query, response)

        # 记录查询历史
        self.qu_history.append({
            "query": query,
            "response": response
        })
        
        return response

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
6. 当系统提出能力和物品给予的时候，角色不会立刻获得，而是后续通过命令或任务给予。

以如下格式回复：
[回复内容]：XXXXX
[心理变化]：YYYYY"""

        response = await self.llm_service.generate_response(prompt)
        self.logger.debug(f"主角回复: {response}")

        thoughts = self.character.thoughts
        response_text = ""

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

        response_text = response_text

        return response_text

    async def advance_story(self, time_span_str):
        self.logger.info("触发故事演进")
        """触发自主故事演进

        Returns:
            str: 故事演进结果
        """
        if time_span_str == "":
            time_span_str = "10分钟"

        character_info = self.character.get_character_info_str(show_hidden_info=True)

        # 构建故事演进提示
        world_current_context = self.world.get_current_context(show_hide_info=True)
        prompt = f"""
{character_info}

{world_current_context}


根据以上信息进行行动选择，并描述其展开过程和后续世界的变化，要注意：
1. 直接描述行动内容和世界的推演变化情况。
2. 以第三人称视角描述故事，主角名称应当偶尔直接提及，以确保玩家能理解主人公是谁。
3. 风格上要符合当前世界设定，保持优秀网络小说的描写风格，如果有需要，有适当的心理、环境和他人互动等描写。
4. 描述其展开过程和后续世界的变化前进时间：{time_span_str}
5. 要严格遵循隐藏故事大纲，如果有冲突，以隐藏故事大纲为准。
6. 要给出时间后，故事开展的具体的时间和日期和地点。时间要大于最后一个事件的时间。要按照时间顺序推演后续角色和世界的变化。

请主角以最合理的方案行动，并描述其展开过程（200字以内）："""

        self.logger.info(f"故事演进提示: {prompt}")

        # 生成故事发展
        story_progress = await self.llm_service.generate_response(prompt)

        # 记录到世界历史
        self.world.log_history(story_progress.replace("\n", " "))

        await self.character.update_attributes("故事进展："+story_progress.replace("\n","")+"\n 根据以上故事进展更新主角的状态情况")
        # 更新主角心理状态
        await self.character.update_thoughts(f"世界发生了新的发展...{story_progress}")

        self.logger.info("故事演进完成")
        self.logger.debug(f"故事进展: {story_progress}")
        return story_progress

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

        summary = await self.llm_service.generate_response(prompt, use_small_model=True)
        self.dialogue_summaries.append(summary)
        return summary

    async def clear_dialogue_history(self) -> None:
        """清除当前对话历史，在开始新故事前调用"""
        if self.dialogue_history:
            await self.summarize_current_dialogue()
            self.dialogue_history = []
            self.logger.info("已清除对话历史并保存总结")

    def _format_qu_history(self, count: int) -> str:
        """格式化最近的qu历史

        Args:
            count: 获取的记录数

        Returns:
            str: 格式化的qu历史
        """
        recent = self.qu_history[-count:] if len(self.qu_history) > 0 else []
        formatted = []
        for i, record in enumerate(recent, 1):
            formatted.append(f"第{i}次查询：")
            formatted.append(f"问：{record['query']}")
            formatted.append(f"答：{record['response']}\n")
        return "\n".join(formatted)

    async def reset(self, story_name: str = None) -> str:
        """重置游戏状态
        
        Args:
            story_name: 可选，指定要切换到的剧本名称
            
        Returns:
            str: 重置结果
        """
        self.logger.info(f"开始重置游戏状态，切换剧本: {story_name}")
        try:
            # 重新初始化各个组件
            self.world = World(story_name)
            self.character = Character(self.llm_service, story_name)
            self.world.set_character(self.character)
            
            # 重置系统状态
            self.energy = 10000.0
            self.dialogue_history = []
            self.dialogue_summaries = []
            self.qu_history = []  # 清空qu历史
            
            if story_name:
                self.current_story = story_name
            
            self.logger.info("游戏状态重置成功")
            return f"游戏状态已重置，已切换到剧本「{self.current_story}」。"
        except Exception as e:
            self.logger.error(f"重置游戏状态失败: {e}")
            return f"重置失败: {str(e)}"
            
    def get_available_stories(self) -> List[str]:
        """获取所有可用的剧本列表
        
        Returns:
            List[str]: 剧本名称列表
        """
        story_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'story')
        stories = []
        try:
            for item in os.listdir(story_dir):
                if os.path.isdir(os.path.join(story_dir, item)):
                    stories.append(item)
            self.logger.info(f"获取到可用剧本列表: {stories}")
            return stories
        except Exception as e:
            self.logger.error(f"获取剧本列表失败: {e}")
            return []
            
    async def switch_story(self, story_name: str) -> str:
        """切换到指定剧本
        
        Args:
            story_name: 剧本名称
            
        Returns:
            str: 切换结果
        """
        self.logger.info(f"准备切换到剧本: {story_name}")
        story_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'story', story_name)
        
        if not os.path.isdir(story_dir):
            self.logger.error(f"剧本不存在: {story_name}")
            return f"切换失败：剧本「{story_name}」不存在"
            
        try:
            result = await self.reset(story_name)
            self.logger.info(f"剧本切换成功: {story_name}")
            return result
        except Exception as e:
            self.logger.error(f"切换剧本失败: {e}")
            return f"切换剧本失败: {str(e)}"

    async def generate_scene_description(self) -> str:
        """生成当前场景的描述
        
        Returns:
            str: 场景描述
        """
        self.logger.info("开始生成场景描述")

        # 获取当前世界和角色状态
        world_context = self.world.get_current_context()
        character_info = self.character.get_character_info_str()

        # 构建提示
        prompt = f"""
[当前世界状态]
{world_context}

[角色信息]
{character_info}

请根据以上信息，生成一段生动的场景描述。要求：
1. 以小说叙述的方式描写当前场景
2. 包含环境、氛围、人物状态等要素
3. 突出重要的细节和关键信息
4. 让玩家能够清晰地理解和想象当前场景
5. 保持文学性和画面感
6. 控制在300字以内

请直接给出场景描述："""

        # 生成描述
        try:
            description = await self.llm_service.generate_response(prompt)
            self.dialogue_history.append({
                "system": "[生成场景描述]",
                "character": "[场景描述，非角色回答]: " + description
            })
            self.world.history.append(f"场景描述：{description}")
            self.logger.info("场景描述生成成功")
            return description
        except Exception as e:
            self.logger.error(f"生成场景描述时出错: {e}")
            return f"生成场景描述失败：{str(e)}"
