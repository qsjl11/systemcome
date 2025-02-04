from typing import List, Dict
from datetime import datetime
import json
import os
from .logger import setup_logger
from .utils import read_story_file_to_dict
from .llm_service import LLMService

class World:
    def __init__(self, llm_service:LLMService, story_name: str = None):
        self.logger = setup_logger('World')
        self.logger.info(f"初始化世界模型，剧本: {story_name}")
        """初始化世界模型"""
        # 读取初始化配置
        self.llm_service = llm_service
        self.current_time = datetime.now()  # 默认使用当前时间
        base_dir = os.path.dirname(os.path.dirname(__file__))
        if story_name:
            story_path = os.path.join(base_dir, 'story', story_name, 'world_init.txt')
        else:
            story_path = os.path.join(base_dir, 'story', 'world_init.txt')
            
        try:
            init_data = read_story_file_to_dict(story_path)
            self.logger.info(f"成功加载世界初始化配置: {story_path}")
        except Exception as e:
            self.logger.error(f"加载世界初始化配置失败: {e}")
            # 如果加载失败，使用默认配置
            init_data = {
                "世界设定": "这是一个默认的世界设定",
                "世界事件": "无历史事件",
                "故事大纲": "无故事大纲",
                "初始时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        self.background = init_data.get("世界设定","无")  # 背景描述
        self.history: List[str] = init_data.get("世界事件","无").split("\n")  # 历史事件记录
        self.story_readme = init_data.get("玩法说明","无")
        self.character = None  # 将由System类注入主角引用
        
        # 从初始化数据中提取时间
        time_str = init_data.get("初始时间").strip()
        self.logger.info("初始时间: %s" % time_str)
        if time_str:
            try:
                self.current_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                self.logger.info(f"初始化世界时间为: {self.current_time}")
            except Exception as e:
                self.logger.error(f"解析初始时间失败: {e}")

    async def apply_change(self, change_prompt: str) -> str:
        self.logger.info(f"应用世界变更: {change_prompt}")
        """应用世界变更

        Args:
            change_prompt: 变更描述

        Returns:
            str: 变更结果描述
        """
        # 记录变更
        event = f"世界变化事件: {change_prompt}"

        self.history.append(event)

        prompt = f"""
下面是当前的世界情况：
---

{self.background}

---

下面是需要变更的内容：
---

{change_prompt}

---

请根据上述变更信息，更新世界背景。保持原有格式，仅在对应块下更新相关内容。注意：
1. 直接更新内容，不用记录更新历史。
2. 需要返回完整的世界背景
3. 最小化根据变更要求，最小化的修改状态，不要修改任何与变更无关的内容。

返回完整的更新后的世界情况："""

        # 使用LLM更新档案
        updated_profile = await self.llm_service.generate_response(prompt)
        updated_profile = updated_profile.replace("#", "").replace("---", "")
        self.background = updated_profile
        self.logger.debug(f"更新后的档案: {self.background}")

        return f"世界状态已更新：{change_prompt}"

    async def advance_time(self, time_str: str) -> str:
        """推进世界时间
        
        Args:
            time_str: 时间增量字符串，格式如 1s, 1m, 1h, 1d, 1w, 1M, 1y
            也支持自然语言描述，如"三天后"、"下周"等
            
        Returns:
            str: 更新后的时间字符串
        """
        self.logger.info(f"推进世界时间: {time_str}")
        
        # 先尝试标准格式解析
        try:
            unit = time_str[-1]
            value = int(time_str[:-1])
            
            # 根据单位推进时间
            if unit == 's':  # 秒
                self.current_time = self.current_time.replace(second=self.current_time.second + value)
            elif unit == 'm':  # 分钟
                self.current_time = self.current_time.replace(minute=self.current_time.minute + value)
            elif unit == 'h':  # 小时
                self.current_time = self.current_time.replace(hour=self.current_time.hour + value)
            elif unit == 'd':  # 天
                self.current_time = self.current_time.replace(day=self.current_time.day + value)
            elif unit == 'w':  # 周
                self.current_time = self.current_time.replace(day=self.current_time.day + value * 7)
            elif unit == 'M':  # 月
                self.current_time = self.current_time.replace(month=self.current_time.month + value)
            elif unit == 'y':  # 年
                self.current_time = self.current_time.replace(year=self.current_time.year + value)
            else:
                raise ValueError(f"未知的时间单位: {unit}")
                
        except (ValueError, IndexError):
            self.logger.info(f"标准格式解析失败，尝试使用LLM解析时间: {time_str}")
            # 使用LLM解析时间
            prompt = f"""
当前时间是: {self.current_time.strftime("%Y-%m-%d %H:%M:%S")}
用户输入的时间描述是: {time_str}

请分析这个时间描述，并将其转换为具体的时间增量。
只需要返回一个标准格式的时间增量，格式为数字+单位(s/m/h/d/w/M/y)。
例如：
- "三天后" -> "3d"
- "下周" -> "7d"
- "一个月后" -> "1M"
- "明年" -> "1y"

请直接返回转换后的格式，不要包含任何解释："""

            try:
                result = await self.llm_service.generate_response(prompt,use_small_model=True)
                result = result.strip()
                self.logger.info(f"LLM解析结果: {result}")
                
                # 递归调用自身处理LLM解析后的标准格式
                return await self.advance_time(result)
            except Exception as e:
                self.logger.error(f"LLM解析时间失败: {e}")
                return str(self.current_time)
            
        return str(self.current_time)

    def get_current_context(self, length=100, show_hide_info=False) -> str:
        self.logger.debug("获取当前世界状态")
        """获取当前完整世界状态

        Args:
            length: 返回的历史事件数量

        Returns:
            Dict: 包含当前状态和相关历史的上下文
        """
        # 获取最近的历史事件
        recent_history = self.history[-length:] if self.history else []
        history_info = "\n".join(recent_history)

        info = f"""
[[当前时间]]：
{self.current_time.strftime("%Y-%m-%d %H:%M:%S")}

[[世界背景]]：
{self.background}

[[历史事件]]：
{history_info}"""

        return info

    def save_query_result(self, query: str, result: str):
        self.logger.info(f"保存查询结果 - 查询: {query}")
        """保存世界状态查询结果

        Args:
            query: 查询内容
            result: 查询结果
        """
        # 记录查询结果作为事件
        event = f"查询事件: {query} -> {result}".strip()
        event = event.replace("\n"," ")
        self.history.append(event)

    def log_history(self, event_text: str, type='event'):
        self.logger.info(f"记录历史事件: {event_text}")
        """记录历史事件

        Args:
            event: 事件描述
        """
        event = f"历史事件: {event_text}".strip()
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
{history_info}"""

        return info

    def get_save_data(self) -> dict:
        """获取需要保存的世界状态数据
        
        Returns:
            dict: 世界状态数据
        """
        self.logger.info("获取世界状态存档数据")
        return {
            "background": self.background,
            "history": self.history,
            "story_readme": self.story_readme,
            "current_time": self.current_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    def load_save_data(self, save_data: dict):
        """从存档数据恢复世界状态
        
        Args:
            save_data: 存档数据
        """
        self.logger.info("从存档数据恢复世界状态")
        self.background = save_data["background"]
        self.history = save_data["history"]
        self.story_readme = save_data["story_readme"]
        if "current_time" in save_data:
            self.current_time = datetime.strptime(save_data["current_time"], "%Y-%m-%d %H:%M:%S")
