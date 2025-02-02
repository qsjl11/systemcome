from typing import List, Dict
import json
import os
from .llm_service import LLMService
from .logger import setup_logger
from .utils import read_story_file_to_dict


class Character:
    def __init__(self, llm_service: LLMService, story_name: str = None):
        self.logger = setup_logger('Character')
        self.logger.info(f"初始化主角代理，剧本: {story_name}")
        """初始化主角代理

        Args:
            llm_service: LLM服务实例
            story_name: 可选，指定剧本名称
        """
        self.llm_service = llm_service

        # 读取初始化配置
        base_dir = os.path.dirname(os.path.dirname(__file__))
        if story_name:
            story_path = os.path.join(base_dir, 'story', story_name, 'character_init.txt')
        else:
            story_path = os.path.join(base_dir, 'story', 'character_init.txt')
            
        try:
            init_data = read_story_file_to_dict(story_path)
            self.logger.info(f"成功加载角色初始化配置: {story_path}")
            self.profile = init_data.get("主角设定","无")
            self.thoughts = init_data.get("主角当前想法", "初次进入这个世界，充满好奇与期待。")
            self.hidden_profile = init_data.get("隐藏补充设定", "无")
        except Exception as e:
            self.logger.error(f"加载角色初始化配置失败: {e}")
            # 如果加载失败，使用默认配置
            self.profile = "这是一个默认的角色设定"
            self.thoughts = "初次进入这个世界，充满好奇与期待。"
            self.hidden_profile = "无"

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

    async def update_attributes(self, changes: str) -> str:
        """更新角色属性

        Args:
            changes: 属性变更字典
            
        Returns:
            str: 变更的差异信息
        """
        self.logger.info(f"更新角色属性: {changes}")

        # 保存原始档案
        original_profile = self.profile

        # 构建提示让LLM更新角色档案
        prompt = f"""
下面是当前的角色档案：
---

{self.profile}

---

下面是需要变更的内容：
---

{changes}

---

请根据上述变更信息，更新角色档案。保持原有格式，仅在对应块下更新相关内容。注意：
1. 直接更新内容，不用记录更新历史。
2. 需要返回完整的角色档案
3. 最小化根据变更要求，最小化的修改状态，不要修改任何与变更无关的内容。

返回完整的更新后的角色档案："""

        # 使用LLM更新档案
        updated_profile = await self.llm_service.generate_response(prompt)
        updated_profile = updated_profile.replace("#", "").replace("---", "")
        self.profile = updated_profile
        self.logger.debug(f"更新后的档案: {self.profile}")

        return changes

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

    def get_character_info_str(self, show_hidden_info=False) -> str:
        self.logger.info("获取角色信息")
        """获取角色信息

        Returns:
            Dict: 角色信息
        """
        if show_hidden_info:
            hidden_info = self.hidden_profile
        else:
            hidden_info = ""

        info = f"""[[角色档案]]：
{self.profile}

{hidden_info}

[[当前心理]]：
{self.thoughts}"""

        return info
        
    def get_save_data(self) -> dict:
        """获取需要保存的角色状态数据
        
        Returns:
            dict: 角色状态数据
        """
        self.logger.info("获取角色状态存档数据")
        return {
            "profile": self.profile,
            "thoughts": self.thoughts,
            "hidden_profile": self.hidden_profile
        }
        
    def load_save_data(self, save_data: dict):
        """从存档数据恢复角色状态
        
        Args:
            save_data: 存档数据
        """
        self.logger.info("从存档数据恢复角色状态")
        self.profile = save_data["profile"]
        self.thoughts = save_data["thoughts"]
        self.hidden_profile = save_data["hidden_profile"]
