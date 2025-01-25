from .. import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))  # 战斗/探索/社交
    status = db.Column(db.String(10), default='pending')  # pending/success/fail
    reward = db.Column(db.Integer)

    def to_dict(self):
        """将任务数据转换为字典格式"""
        return {
            'id': self.id,
            'type': self.type,
            'status': self.status,
            'reward': self.reward
        }

    @staticmethod
    def get_active_tasks():
        """获取所有进行中的任务"""
        return Task.query.filter_by(status='pending').all()

    @staticmethod
    def get_completed_tasks():
        """获取所有已完成的任务"""
        return Task.query.filter(Task.status.in_(['success', 'fail'])).all()
