from openai import AsyncOpenAI
import asyncio
import os
from .logger import setup_logger


class LLMService:
    def __init__(self):
        self.logger = setup_logger('LLMService')
        self.client = AsyncOpenAI(
            base_url=os.getenv('MODEL_URL', 'https://api.deepseek.com/v1'),
            api_key=os.getenv('MODEL_KEY', '')
        )
        self.model = os.getenv('MODEL_NAME', 'deepseek-chat')
        self.max_retries = 3
        self.retry_delay = 1  # 初始重试延迟(秒)

    async def generate_response(self, prompt):
        retries = 0
        while retries < self.max_retries:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    self.logger.error(f"LLM API Error after {retries} retries: {e}")
                    raise
                await asyncio.sleep(self.retry_delay * (2 ** (retries - 1)))  # 指数退避

    async def calculate_energy_cost(self, action_type: str, context: str) -> float:
        """计算能量消耗

        Args:
            action_type: 动作类型 (modify/query/communicate)
            context: 相关上下文信息

        Returns:
            float: 消耗的能量值
        """
        self.logger.info(f"计算能量消耗 - 动作类型: {action_type}")

        # 根据action_type和context的复杂度计算能量消耗
        prompt = f"""
        请根据以下动作类型和上下文计算能量消耗（返回一个1-100的数值）：
        动作类型：{action_type}
        上下文：{context}
        注意，仅返回1-100之间的数值，表示消耗的能量值，不要返回其他任何内容。
        """
        try:
            response = await self.generate_response(prompt)
            # 提取数值
            cost = float(response.strip())
            cost = min(max(cost, 1), 100)  # 确保在1-100范围内
            self.logger.debug(f"计算的能量消耗: {cost}")
            return cost
        except Exception as e:
            self.logger.error(f"能量消耗计算失败: {e}")
            return 10.0

    async def detect_task(self, message: str) -> tuple[bool, str, str]:
        """从对话中检测任务

        Args:
            message: 对话内容

        Returns:
            tuple[bool, str]: (是否包含任务, 任务描述)
        """
        self.logger.info("检测对话中的任务")
        prompt = f"""
        请分析以下对话内容，判断是否包含任务和对应的奖励：
        {message}

        如果包含任务，请提取出任务描述；如果不包含任务，请返回"无任务"。
        注意：任务通常包含明确的目标、要求或请求。

        仅返回以下两种格式之一：
        任务：[任务描述]
        奖励：[奖励描述]
        或
        无任务
        """

        try:
            response = await self.generate_response(prompt)
            if response.startswith("任务："):
                task_desc = response.split("任务：")[1].split("奖励：")[0].strip()
                reward_des = response.split("奖励：")[1].strip()
                self.logger.debug(f"检测到任务: {task_desc}->{reward_des}")
                return True, task_desc, reward_des
            return False, "", ""
        except Exception as e:
            self.logger.error(f"任务检测失败: {e}")
            return False, "", ""

    async def check_task_status(self, task_desc: str, context: str) -> bool:
        """检查任务是否完成

        Args:
            task_desc: 任务描述
            context: 相关上下文（对话内容或故事进展）

        Returns:
            bool: 任务是否完成
        """
        self.logger.info(f"检查任务状态 - 任务: {task_desc}")
        prompt = f"""
        请判断以下任务是否已经完成：

        [任务描述]
        {task_desc}

        [相关上下文]
        {context}

        请仅返回"已完成"或"未完成"：
        """

        try:
            response = await self.generate_response(prompt)
            is_completed = "已完成" in response
            self.logger.debug(f"任务状态检查结果: {'已完成' if is_completed else '未完成'}")
            return is_completed
        except Exception as e:
            self.logger.error(f"任务状态检查失败: {e}")
            return False

    async def format_task(self, task_description: str) -> tuple[str, str]:
        """格式化任务描述和奖励

        Args:
            task_description: 原始任务描述

        Returns:
            tuple[str, str]: (格式化后的任务描述, 奖励描述)
        """
        self.logger.info("格式化任务描述")
        self.logger.debug(f"原始任务描述: {task_description}")

        prompt = f"""
        请将以下任务描述格式化为标准格式，并生成合适的奖励：
        {task_description}

        返回格式：
        任务：[格式化的任务描述]
        奖励：[奖励描述]
        """
        try:
            response = await self.generate_response(prompt)
            # 解析响应
            lines = response.strip().split('\n')
            task = lines[0].replace('任务：', '').strip()
            reward = lines[1].replace('奖励：', '').strip()
            self.logger.debug(f"格式化结果 - 任务: {task}, 奖励: {reward}")
            return task, reward
        except Exception as e:
            self.logger.error(f"任务格式化失败: {e}")
            return task_description, "完成任务可获得系统点数奖励"
