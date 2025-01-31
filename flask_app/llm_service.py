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

