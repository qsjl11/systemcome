from typing import List, Dict
from datetime import datetime
import json
import os
from .logger import setup_logger
from .utils import read_story_file_to_dict


class World:
    def __init__(self):
        self.logger = setup_logger('World')
        self.logger.info("初始化世界模型")
        """初始化世界模型"""
        # 读取初始化配置
        story_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'story', 'world_init.txt')
        init_data = read_story_file_to_dict(story_path)
        self.logger.info("成功加载世界初始化配置")

        self.background = init_data.get("世界设定")  # 背景描述
        self.current_state = init_data.get("当前场景")  # 当前世界状态
        self.history: List[str] = init_data.get("世界事件").split("\n")  # 历史事件记录
        self.story_framework = init_data.get("故事大纲")  # 故事框架描述
        self.character = None  # 将由System类注入主角引用

    def apply_change(self, change_prompt: str, timestamp: str) -> str:
        self.logger.info(f"应用世界变更: {change_prompt}")
        """应用世界变更

        Args:
            change_prompt: 变更描述

        Returns:
            str: 变更结果描述
        """
        # 记录变更
        event = f"世界变化事件({timestamp}): {change_prompt}"

        self.history.append(event)

        # 如果已注入主角引用，通知主角更新
        if self.character:
            self.logger.debug("通知主角更新状态")
            self.character.update(event)

        return f"世界状态已更新：{change_prompt}"

    def get_current_context(self, length=100, show_hide_info=False) -> str:
        self.logger.debug("获取当前世界状态")
        """获取当前完整世界状态

        Args:
            length: 返回的历史事件数量

        Returns:
            Dict: 包含当前状态和相关历史的上下文
        """
        # 获取最近的历史事件
        hidden_info = f"""
        [[故事大纲]]
        {self.story_framework}
        """
        recent_history = self.history[-length:] if self.history else []
        history_info = "\n".join(recent_history)
        info = f"""
        [[世界背景]]：
        {self.background}

        [[历史事件]]：
        {history_info}
        
        {hidden_info if show_hide_info else ""}
        
        [[当前场景]]：
        {self.current_state}"""

        return info

    def save_query_result(self, query: str, result: str):
        self.logger.info(f"保存查询结果 - 查询: {query}")
        """保存世界状态查询结果

        Args:
            query: 查询内容
            result: 查询结果
        """
        # 记录查询结果作为事件
        event = f"查询事件: {query} -> {result}"
        self.history.append(event)

    def log_history(self, event_text: str, type='event'):
        self.logger.info(f"记录历史事件: {event_text}")
        """记录历史事件

        Args:
            event: 事件描述
        """
        event = f"历史事件: {event_text}"
        self.history.append(event)

    def set_character(self, character):
        self.logger.info("设置主角引用")
        """注入主角引用

        Args:
            character: 主角对象
        """
        self.character = character

    def get_world_info(self):
        history_info = "\n".join(self.history)

        info = f"""
[[世界背景]]：
{self.background}

[[历史事件]]：
{history_info}

[[当前场景]]：
{self.current_state}"""

        return info
