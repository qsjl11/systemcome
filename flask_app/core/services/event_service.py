import random
from datetime import datetime, timedelta
from ..models import EventPool, ActiveEvent, Character
from ..utils.constants import SYSTEM_CONFIG, EVENT_STATUS
from .. import db

class EventService:
    @staticmethod
    async def refresh_events():
        """刷新事件池，生成新的可用事件"""
        # 清理已完成或过期的事件
        EventService._clean_expired_events()
        
        # 检查活跃事件数量
        active_count = ActiveEvent.query.filter_by(status=EVENT_STATUS["PENDING"]).count()
        if active_count >= SYSTEM_CONFIG["MAX_ACTIVE_EVENTS"]:
            return {"message": "事件池已满"}
        
        # 获取可用事件
        available_events = EventService._get_available_events()
        if not available_events:
            return {"message": "没有可用的新事件"}
        
        # 选择并创建新事件
        selected_event = EventService._select_event(available_events)
        if selected_event:
            new_active = EventService._create_active_event(selected_event)
            return {
                "message": "已生成新事件",
                "event": {
                    "id": new_active.id,
                    "type": selected_event.event_type,
                    "content": selected_event.content
                }
            }
        
        return {"message": "事件生成失败"}

    @staticmethod
    def get_active_events():
        """获取当前所有活跃事件"""
        active_events = db.session.query(
            ActiveEvent, EventPool
        ).join(
            EventPool
        ).filter(
            ActiveEvent.status == EVENT_STATUS["PENDING"]
        ).all()
        
        return [{
            "id": active.id,
            "type": event.event_type,
            "content": event.content,
            "start_time": active.start_time.isoformat()
        } for active, event in active_events]

    @staticmethod
    async def handle_event(event_id, choice, llm_service):
        """处理事件选择"""
        active_event = db.session.query(
            ActiveEvent, EventPool
        ).join(
            EventPool
        ).filter(
            ActiveEvent.id == event_id,
            ActiveEvent.status == EVENT_STATUS["PENDING"]
        ).first()
        
        if not active_event:
            return {"error": "事件不存在或已结束"}, 404
        
        active, event = active_event
        character = Character.query.first()
        
        # 使用LLM评估选择结果
        result = await llm_service.evaluate_choice(
            event.content,
            choice,
            {
                "cultivation_stage": character.cultivation_stage,
                "alignment": character.alignment,
                "decision_style": character.decision_style
            }
        )
        
        # 更新事件状态
        active.status = EVENT_STATUS["COMPLETED"]
        active.completion_time = datetime.utcnow()
        active.result = result
        
        db.session.commit()
        
        return {
            "message": "事件已处理",
            "result": result
        }

    @staticmethod
    def _clean_expired_events():
        """清理已完成或过期的事件"""
        expiry_time = datetime.utcnow() - timedelta(days=SYSTEM_CONFIG["EVENT_COOLDOWN_DAYS"])
        ActiveEvent.query.filter(
            (ActiveEvent.status == EVENT_STATUS["COMPLETED"]) |
            (ActiveEvent.start_time < expiry_time)
        ).delete()
        db.session.commit()

    @staticmethod
    def _get_available_events():
        """获取可用事件列表"""
        return EventPool.query.filter(
            EventPool.id.notin_(
                db.session.query(ActiveEvent.event_id).filter_by(
                    status=EVENT_STATUS["PENDING"]
                )
            )
        ).all()

    @staticmethod
    def _select_event(available_events):
        """根据权重选择事件"""
        character = Character.query.first()
        weighted_events = []
        
        for event in available_events:
            weight = event.weight
            # 根据性格调整权重
            if event.event_type == "奇遇":
                weight *= (1 + character.fortune_sensitivity * 0.01)
            elif event.event_type == "劫难":
                weight *= (1 + character.decision_style * 0.01)
            weighted_events.append((event, weight))
        
        if not weighted_events:
            return None
            
        total_weight = sum(w for _, w in weighted_events)
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for event, weight in weighted_events:
            current_weight += weight
            if r <= current_weight:
                return event
        
        return weighted_events[0][0] if weighted_events else None

    @staticmethod
    def _create_active_event(event):
        """创建新的活跃事件"""
        new_active = ActiveEvent(
            event_id=event.id,
            status=EVENT_STATUS["PENDING"]
        )
        db.session.add(new_active)
        db.session.commit()
        return new_active
