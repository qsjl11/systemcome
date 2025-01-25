from openai import OpenAI
import asyncio
import logging
import os

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv('MODEL_URL', 'https://api.deepseek.com'),
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
                    logging.error(f"LLM API Error after {retries} retries: {e}")
                    raise
                await asyncio.sleep(self.retry_delay * (2 ** (retries - 1)))  # 指数退避

    async def generate_event_options(self, event_context):
        """根据事件上下文生成选项"""
        prompt = f"""基于以下事件上下文生成2-3个选项:
事件背景: {event_context}
要求:
1. 每个选项都要有具体的后果
2. 选项之间要有明显的差异
3. 考虑角色当前的状态和性格
"""
        response = await self.generate_response(prompt)
        return response

    async def evaluate_choice(self, event_context, choice, character_status):
        """评估选择的结果"""
        prompt = f"""基于以下信息评估选择的结果:
事件背景: {event_context}
玩家选择: {choice}
角色当前状态: {character_status}
要求:
1. 给出具体的结果描述
2. 包含对角色属性的影响
3. 可能触发的后续事件
"""
        response = await self.generate_response(prompt)
        return response
