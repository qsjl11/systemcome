from typing import List, Dict
from datetime import datetime
import json
import os
from .logger import setup_logger


class World:
    def __init__(self):
        self.logger = setup_logger('World')
        self.logger.info("初始化世界模型")
        """初始化世界模型"""
        # 读取初始化配置
        story_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'story', 'world_init.json')
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                init_data = json.load(f)
                self.logger.info("成功加载世界初始化配置")
        except Exception as e:
            self.logger.error(f"加载世界初始化配置失败: {e}")
            init_data = {"current_state": {}, "initial_events": []}

        self.current_state = init_data.get("current_state", {})  # 当前世界状态
        self.history: List[Dict] = init_data.get("initial_events", [])  # 历史事件记录
        self.character = None  # 将由System类注入主角引用

    def apply_change(self, change_prompt: str) -> str:
        self.logger.info(f"应用世界变更: {change_prompt}")
        """应用世界变更

        Args:
            change_prompt: 变更描述

        Returns:
            str: 变更结果描述
        """
        # 记录变更
        timestamp = datetime.now().isoformat()
        event = {
            "type": "world_change",
            "timestamp": timestamp,
            "description": change_prompt
        }
        self.history.append(event)

        # 更新当前状态LLM
        self.current_state["last_change"] = {
            "description": change_prompt,
            "timestamp": timestamp
        }

        # 如果已注入主角引用，通知主角更新
        if self.character:
            self.logger.debug("通知主角更新状态")
            self.character.update()

        return f"世界状态已更新：{change_prompt}"

    def get_current_context(self, length=100) -> Dict:
        self.logger.debug("获取当前世界状态")
        """获取当前完整世界状态

        Args:
            length: 返回的历史事件数量

        Returns:
            Dict: 包含当前状态和相关历史的上下文
        """
        # 获取最近的历史事件
        recent_history = self.history[-length:] if self.history else []

        return {
            "current_state": self.current_state,
            "recent_history": recent_history
        }

    def save_query_result(self, query: str, result: str):
        self.logger.info(f"保存查询结果 - 查询: {query}")
        """保存世界状态查询结果

        Args:
            query: 查询内容
            result: 查询结果
        """
        # 记录查询结果作为事件
        event = {
            "type": "query_result",
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "result": result
        }
        self.history.append(event)

    def log_history(self, event_text: str, type='event'):
        self.logger.info(f"记录历史事件: {event_text}")
        """记录历史事件

        Args:
            event: 事件描述
        """
        event_record = {
            "type": type,
            "timestamp": datetime.now().isoformat(),
            "description": event_text
        }
        self.history.append(event_record)

    def set_character(self, character):
        self.logger.info("设置主角引用")
        """注入主角引用

        Args:
            character: 主角对象
        """
        self.character = character
