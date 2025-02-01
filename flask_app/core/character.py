from typing import List, Dict
import json
import os
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

    async def generate_actions(self, time_span_str: str) -> List[str]:
        self.logger.info("生成行动方案")
        """生成三个候选行动方案

        Returns:
            List[str]: 三个候选行动方案
        """
        # 生成行动方案
        prompt = f"""
[角色档案]
{self.profile}

[当前心理]
{self.thoughts}

请生成三个候选行动方案，考虑任务影响但不强制服从。每个方案需要包含行动描述和预期结果。每个行动只有一行，不要多行文本。
行动方案影响时间范围：{time_span_str}

返回格式：
[行动方案1]: xxxx
[行动方案2]: yyyy
[行动方案3]: zzzz"""

        self.logger.info(f"生成行动方案提示: {prompt}")

        response = await self.llm_service.generate_response(prompt)

        self.logger.info(f"生成的行动方案: {response}")
        try:
            # 解析响应为行动列表
            actions = [line.split("]: ")[1] for line in response.strip().split('\n') if "[行动方案" in line]
            self.logger.debug(f"生成的行动方案: {actions}")
            return actions[:3]  # 确保只返回3个方案
        except Exception as e:
            self.logger.error(f"解析行动方案失败: {e}")
            return ["自由行动", "自由行动", "自由行动"]

    async def update_attributes(self, changes: str):
        """更新角色属性

        Args:
            changes: 属性变更字典
        """
        self.logger.info(f"更新角色属性: {changes}")

        # 构建提示让LLM更新角色档案
        prompt = f"""
# [当前角色档案]
{self.profile}

# [需要更新的变更]
{changes}

请根据上述变更信息，更新角色档案。保持原有格式，仅在对应块下更新相关内容。
比如新增系统任务，需要在[系统任务]下新增一条任务描述。
系统任务内容：xxxxx -> 奖励：yyyyy

返回完整的更新后的角色档案："""

        # 使用LLM更新档案
        updated_profile = await self.llm_service.generate_response(prompt)
        self.profile = updated_profile
        await self.update_thoughts(f"更新了...{changes}")
        self.logger.debug(f"更新后的档案: {self.profile}")

    def get_current_thoughts(self) -> str:
        self.logger.debug(f"获取当前心理活动: {self.thoughts}")
        """获取当前心理活动

        Returns:
            str: 当前心理活动描述
        """
        return self.thoughts

    async def update_thoughts(self, trigger: str):
        self.logger.debug(f"更新心理活动 - 触发: {trigger}")
        """更新心理活动

        Args:
            trigger: 触发更新的事件描述
        """
        prompt = f"""
# [当前情况]
{trigger}

#　[角色档案]
{self.profile}

# [当前心理]
{self.thoughts}

请生成一段新的心理活动描述（100字以内）：
        """

        self.thoughts = await self.llm_service.generate_response(prompt, use_small_model=True)
        self.logger.debug(f"新的心理活动: {self.thoughts}")

    def get_character_info_str(self) -> str:
        self.logger.info("获取角色信息")
        """获取角色信息

        Returns:
            Dict: 角色信息
        """
        info = f"""[[角色档案]]：
{self.profile}

[[当前心理]]：
{self.thoughts}"""

        return info
