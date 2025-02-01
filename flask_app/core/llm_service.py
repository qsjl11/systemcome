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
        self.small_model = os.getenv('SMALL_MODEL_NAME', 'deepseek-chat')
        self.max_retries = 3
        self.retry_delay = 1  # 初始重试延迟(秒)

    async def generate_response(self, prompt, use_small_model=False):
        if use_small_model:
            model = self.small_model
        else:
            model = self.model
        retries = 0
        while retries < self.max_retries:
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    self.logger.error(f"LLM API Error after {retries} retries: {e}")
                    raise
                await asyncio.sleep(self.retry_delay * (2 ** (retries - 1)))  # 指数退避

    async def detect_task(self, message: str) -> tuple[bool, str]:
        """从对话中检测任务

        Args:
            message: 对话内容

        Returns:
            tuple[bool, str]: (是否包含任务, 任务描述)
        """
        if "任务" not in message:
            return False, ""

        self.logger.info("检测对话中的任务")
        prompt = f"""
        请分析以下对话内容，判断是否包含任务和对应的奖励：
        {message}
        
        如果包含任务，请提取出任务描述；如果不包含任务，请返回"无任务"。注意：
        1. 任务应当包含明确的目标、要求或请求，且同时存在奖励。没有明确的奖励描述不算作任务。隐含奖励不算奖励，因此不算任务。
        2. 文本中必须明确提出发布任务，对于一般的要求或者大的方向性指导不算做任务。

        仅返回以下两种格式之一：
        系统任务内容：[任务描述] -> 奖励：[奖励描述]
        系统任务内容：[任务描述] -> [奖励描述]
        或
        无任务
        """

        try:
            response = await self.generate_response(prompt)
            if "系统任务内容" in response:
                tasks_desc = response
                self.logger.debug(f"检测到任务: {tasks_desc}")
                return True, response
            return False, ""
        except Exception as e:
            self.logger.error(f"任务检测失败: {e}")
            return False, ""

    async def check_task_status(self, task_desc: str, context: str) -> tuple[bool, str]:
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

        # [人物及任务描述]
        {task_desc}

        # [相关上下文]
        {context}

        请返回完成哪些了哪些任务，按照如下格式：
        [完成任务]：[任务描述1]，[任务描述2]，[任务描述3]
        如果没有任务完成，请返回：
        无任务完成
        
        注意：仅考虑[任务]中的内容，其他部分的不是任务描述，不需要考虑。
        """

        try:
            response = await self.generate_response(prompt)
            is_completed = "[完成任务]" in response
            self.logger.info(f"任务状态检查结果: {'已完成' if is_completed else '未完成'}")
            return is_completed, response
        except Exception as e:
            self.logger.error(f"任务状态检查失败: {e}")
            return False, ""
