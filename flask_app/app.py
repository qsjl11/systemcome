from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import os
from save_system import create_save_data, restore_save_data

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据模型
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

class SaveSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_num = db.Column(db.Integer, unique=True)  # 1-10存档位
    save_time = db.Column(db.DateTime, default=datetime.utcnow)
    save_name = db.Column(db.String(50))
    character_data = db.Column(db.LargeBinary)  # 压缩的JSON数据
    event_log = db.Column(db.Text)  # JSON事件日志

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))  # 战斗/探索/社交
    status = db.Column(db.String(10), default='pending') # pending/success/fail
    reward = db.Column(db.Integer)

# 路由
@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/get_status')
def get_status():
    character = Character.query.first()
    if not character:
        character = Character()
        db.session.add(character)
        db.session.commit()
    
    # 获取境界名称
    CULTIVATION_STAGES = {
        0: "凡人",
        1: "炼气期",
        3: "筑基期",
        5: "金丹期",
        8: "元婴期"
    }
    current_stage = CULTIVATION_STAGES.get(character.cultivation_stage, "未知境界")
    
    return jsonify({
        # 基础五维
        'vitality': character.vitality,
        'spiritual_power': character.spiritual_power,
        'consciousness': character.consciousness,
        'physique': character.physique,
        'fortune': character.fortune,
        
        # 境界信息
        'cultivation_stage': current_stage,
        'cultivation_realm': character.cultivation_realm,
        'breakthrough_chance': character.breakthrough_chance,
        
        # 灵根资质
        'affinities': {
            'metal': character.metal_affinity,
            'wood': character.wood_affinity,
            'water': character.water_affinity,
            'fire': character.fire_affinity,
            'earth': character.earth_affinity
        },
        
        # 性格维度
        'personality': {
            'alignment': character.alignment,
            'decision_style': character.decision_style,
            'social_mode': character.social_mode,
            'fortune_sensitivity': character.fortune_sensitivity,
            'dao_heart': character.dao_heart
        },
        
        # 原有属性
        'trust': character.trust,
        'stress': character.stress
    })

@app.route('/issue_task', methods=['POST'])
def issue_task():
    task_type = request.form.get('type')
    if not task_type:
        return jsonify({'error': '任务类型不能为空'}), 400
    
    # 创建新任务
    task = Task(type=task_type, reward=random.randint(10, 30))
    db.session.add(task)
    
    # 更新角色状态
    character = Character.query.first()
    if task_type == '战斗':
        character.stress += 10
    elif task_type == '探索':
        character.cultivation += 5
    elif task_type == '社交':
        character.trust += 5
    
    db.session.commit()
    
    return jsonify({
        'message': f'成功发布{task_type}任务',
        'reward': task.reward
    })

@app.route('/get_ai_action')
def get_ai_action():
    character = Character.query.first()
    
    # 简单的决策逻辑
    if character.stress > 70:
        action = random.choice(['逃避', '莽撞行动'])
    elif character.cultivation < 50:
        action = '修炼'
    else:
        action = '探索' if random.random() > 0.3 else '社交'
    
    return jsonify({
        'action': action,
        'reason': f'当前状态: 修为{character.cultivation}, 压力{character.stress}'
    })

@app.route('/save_game', methods=['POST'])
def save_game():
    slot_num = request.form.get('slot_num', type=int)
    save_name = request.form.get('save_name', '')
    
    if not slot_num or not (1 <= slot_num <= 10):
        return jsonify({'error': '无效的存档位置'}), 400
        
    character = Character.query.first()
    tasks = Task.query.all()
    events = []  # TODO: 实现事件日志系统
    
    # 创建存档数据
    save_data = create_save_data(character, tasks, events)
    
    # 更新或创建存档
    save_slot = SaveSlot.query.filter_by(slot_num=slot_num).first()
    if not save_slot:
        save_slot = SaveSlot(slot_num=slot_num)
    
    save_slot.save_name = save_name or f'存档 {slot_num}'
    save_slot.save_time = datetime.utcnow()
    save_slot.character_data = save_data
    save_slot.event_log = '[]'  # TODO: 实现事件日志序列化
    
    db.session.add(save_slot)
    db.session.commit()
    
    return jsonify({
        'message': f'成功保存到存档位 {slot_num}',
        'save_time': save_slot.save_time.isoformat()
    })

@app.route('/load_game', methods=['POST'])
def load_game():
    slot_num = request.form.get('slot_num', type=int)
    
    if not slot_num or not (1 <= slot_num <= 10):
        return jsonify({'error': '无效的存档位置'}), 400
        
    save_slot = SaveSlot.query.filter_by(slot_num=slot_num).first()
    if not save_slot:
        return jsonify({'error': '存档不存在'}), 404
        
    character = Character.query.first()
    events = []  # TODO: 实现事件日志系统
    
    if restore_save_data(character, Task, events, save_slot.character_data, db):
        db.session.commit()
        return jsonify({
            'message': f'成功读取存档 {slot_num}',
            'save_time': save_slot.save_time.isoformat()
        })
    else:
        return jsonify({'error': '存档数据损坏'}), 500

@app.route('/get_saves')
def get_saves():
    saves = SaveSlot.query.all()
    return jsonify([{
        'slot_num': save.slot_num,
        'save_name': save.save_name,
        'save_time': save.save_time.isoformat()
    } for save in saves])

def init_db():
    with app.app_context():
        db.create_all()
        # 如果没有角色，创建一个
        if not Character.query.first():
            character = Character()
            db.session.add(character)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
