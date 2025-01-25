from .. import db

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 基础五维属性
    vitality = db.Column(db.Integer, default=100)    # 气血
    spiritual_power = db.Column(db.Integer, default=100)  # 灵力
    consciousness = db.Column(db.Integer, default=1)   # 神识
    physique = db.Column(db.Integer, default=1)       # 体魄
    fortune = db.Column(db.Integer, default=1)        # 气运
    
    # 境界系统
    cultivation_stage = db.Column(db.Integer, default=0)  # 境界阶段
    cultivation_realm = db.Column(db.String(10), default='初期')  # 小境界
    breakthrough_chance = db.Column(db.Float, default=0.0)  # 破境成功率
    
    # 灵根资质
    metal_affinity = db.Column(db.Float, default=0.0)  # 金灵根
    wood_affinity = db.Column(db.Float, default=0.0)   # 木灵根
    water_affinity = db.Column(db.Float, default=0.0)  # 水灵根
    fire_affinity = db.Column(db.Float, default=0.0)   # 火灵根
    earth_affinity = db.Column(db.Float, default=0.0)  # 土灵根
    
    # 性格维度
    alignment = db.Column(db.Float, default=0.0)       # 正邪倾向 -100到100
    decision_style = db.Column(db.Float, default=50.0)  # 决策风格 0到100
    social_mode = db.Column(db.Float, default=50.0)     # 社交模式 0到100
    fortune_sensitivity = db.Column(db.Float, default=50.0) # 机缘敏感 0到100
    dao_heart = db.Column(db.String(20), default='求知')  # 道心类型
    
    # 原有属性
    trust = db.Column(db.Integer, default=50)       # 信任值
    stress = db.Column(db.Integer, default=0)       # 压力值

    def to_dict(self):
        """将角色数据转换为字典格式"""
        return {
            # 基础五维
            'vitality': self.vitality,
            'spiritual_power': self.spiritual_power,
            'consciousness': self.consciousness,
            'physique': self.physique,
            'fortune': self.fortune,
            
            # 境界信息
            'cultivation_stage': self.cultivation_stage,
            'cultivation_realm': self.cultivation_realm,
            'breakthrough_chance': self.breakthrough_chance,
            
            # 灵根资质
            'affinities': {
                'metal': self.metal_affinity,
                'wood': self.wood_affinity,
                'water': self.water_affinity,
                'fire': self.fire_affinity,
                'earth': self.earth_affinity
            },
            
            # 性格维度
            'personality': {
                'alignment': self.alignment,
                'decision_style': self.decision_style,
                'social_mode': self.social_mode,
                'fortune_sensitivity': self.fortune_sensitivity,
                'dao_heart': self.dao_heart
            },
            
            # 原有属性
            'trust': self.trust,
            'stress': self.stress
        }
