from openai import OpenAI
import asyncio
import os
from ..utils.logging_utils import get_logger

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv('MODEL_URL', 'https://api.deepseek.com'),
            api_key=os.getenv('MODEL_KEY', '')
        )
        self.model = os.getenv('MODEL_NAME', 'deepseek-chat')
        self.max_retries = 3
        self.retry_delay = 1  # 初始重试延迟(秒)
        self.logger = get_logger()
        self.logger.info(f"初始化LLM服务 - 模型: {self.model}, API地址: {os.getenv('MODEL_URL')}")

    async def _make_api_call(self, prompt):
        """通用的API调用方法，包含重试逻辑"""
        retries = 0
        while retries < self.max_retries:
            try:
                self.logger.debug(f"发送LLM请求 - 尝试次数: {retries + 1}")
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                self.logger.debug("LLM请求成功")
                return response.choices[0].message.content
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    self.logger.error(f"LLM API调用失败 - 重试{retries}次后错误: {str(e)}")
                    raise
                delay = self.retry_delay * (2 ** (retries - 1))
                self.logger.warning(f"LLM API调用失败 - 重试{retries}/{self.max_retries}, 等待{delay}秒")
                await asyncio.sleep(delay)  # 指数退避

    async def generate_event_options(self, event_context, character_status=None):
        """根据事件上下文和角色状态生成选项"""
        self.logger.info(f"生成事件选项 - 事件: {event_context[:50]}...")
        character_info = ""
        if character_status:
            character_info = f"""
当前角色状态:
- 境界: {character_status.get('cultivation_stage')}
- 正邪倾向: {character_status.get('alignment', 0)}
- 决策风格: {character_status.get('decision_style', 50)}
"""

        prompt = f"""基于以下信息生成2-3个选项:
事件背景: {event_context}
{character_info}
要求:
1. 每个选项都要有具体的后果描述
2. 选项之间要有明显的差异性
3. 选项要符合角色当前的状态和性格特征
4. 每个选项都要包含可能的风险和收益
5. 选项要符合修仙世界的设定
"""
        return await self._make_api_call(prompt)

    async def evaluate_choice(self, event_context, choice, character_status):
        """评估选择的结果"""
        self.logger.info(f"评估选择结果 - 事件: {event_context[:30]}..., 选择: {choice[:30]}...")
        prompt = f"""基于以下信息评估选择的结果:
事件背景: {event_context}
玩家选择: {choice}
角色状态:
- 境界: {character_status.get('cultivation_stage')}
- 正邪倾向: {character_status.get('alignment')}
- 决策风格: {character_status.get('decision_style')}

要求:
1. 详细描述选择的直接结果
2. 分析对角色各项属性的影响
3. 预测可能触发的后续事件
4. 评估对角色修炼道路的长期影响
5. 考虑选择与角色性格的契合度
"""
        return await self._make_api_call(prompt)

    async def generate_task_outcome(self, task_type, character_status):
        """生成任务结果"""
        self.logger.info(f"生成任务结果 - 类型: {task_type}, 境界: {character_status.get('cultivation_stage')}")
        prompt = f"""基于以下信息生成任务结果:
任务类型: {task_type}
角色状态:
- 境界: {character_status.get('cultivation_stage')}
- 灵力: {character_status.get('spiritual_power')}
- 压力: {character_status.get('stress')}

要求:
1. 描述任务执行过程
2. 说明获得的具体收益
3. 分析可能的负面影响
4. 考虑角色当前状态对任务的影响
5. 预测任务对未来发展的影响
"""
        return await self._make_api_call(prompt)
