from datetime import datetime
from .. import db

class EventPool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(20))  # 奇遇/劫难/日常/因果
    trigger_conditions = db.Column(db.Text)  # JSON触发条件
    weight = db.Column(db.Float)  # 基础权重
    cooldown = db.Column(db.Integer)  # 冷却时间
    content = db.Column(db.Text)  # 事件内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联的活跃事件
    active_events = db.relationship('ActiveEvent', backref='event', lazy=True)

    def to_dict(self):
        """将事件数据转换为字典格式"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'trigger_conditions': self.trigger_conditions,
            'weight': self.weight,
            'cooldown': self.cooldown,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

class ActiveEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_pool.id'))
    status = db.Column(db.String(10))  # pending/active/completed
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    completion_time = db.Column(db.DateTime)
    result = db.Column(db.Text)  # 事件结果

    def to_dict(self):
        """将活跃事件数据转换为字典格式"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'completion_time': self.completion_time.isoformat() if self.completion_time else None,
            'result': self.result
        }
