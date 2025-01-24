from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import random
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据模型
class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cultivation = db.Column(db.Integer, default=0)  # 修为
    trust = db.Column(db.Integer, default=50)       # 信任值
    stress = db.Column(db.Integer, default=0)       # 压力值

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
    
    return jsonify({
        'cultivation': character.cultivation,
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
