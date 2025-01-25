from datetime import datetime
from .. import db

class SaveSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_num = db.Column(db.Integer, unique=True)  # 1-10存档位
    save_time = db.Column(db.DateTime, default=datetime.utcnow)
    save_name = db.Column(db.String(50))
    character_data = db.Column(db.LargeBinary)  # 压缩的JSON数据
    event_log = db.Column(db.Text)  # JSON事件日志

    def to_dict(self):
        """将存档数据转换为字典格式"""
        return {
            'slot_num': self.slot_num,
            'save_name': self.save_name,
            'save_time': self.save_time.isoformat()
        }

    @staticmethod
    def get_available_slots():
        """获取所有可用的存档位"""
        used_slots = {save.slot_num for save in SaveSlot.query.all()}
        return [i for i in range(1, 11) if i not in used_slots]

    @staticmethod
    def get_slot(slot_num):
        """获取指定槽位的存档"""
        return SaveSlot.query.filter_by(slot_num=slot_num).first()
