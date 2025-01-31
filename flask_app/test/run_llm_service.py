from core.llm_service import LLMService
import asyncio

service = LLMService()
prompt = "你好"
response = asyncio.run(service.generate_response(prompt))
print(response)

action_type = "modify"
context = "修改世界状态"
energy_cost = asyncio.run(service.calculate_energy_cost(action_type, context))
print(energy_cost)

task_description = "完成一个简单的任务，奖励是提升1级"
task, reward = asyncio.run(service.format_task(task_description))
print(task, reward)