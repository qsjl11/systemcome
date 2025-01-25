from flask import Flask, render_template, jsonify, request
from core import init_app, db
from core.services import (
    CharacterService,
    EventService,
    LLMService,
    SaveService,
    TaskService
)
from core.models import Character, Task, EventPool, ActiveEvent, SaveSlot
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
init_app(app)

# 路由
@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/get_status')
def get_status():
    return jsonify(CharacterService.get_character_status())

@app.route('/issue_task', methods=['POST'])
def issue_task():
    task_type = request.form.get('type')
    if not task_type:
        return jsonify({'error': '任务类型不能为空'}), 400
    
    result = TaskService.create_task(task_type)
    return jsonify(result)

@app.route('/get_ai_action')
def get_ai_action():
    return jsonify(CharacterService.calculate_ai_action())

@app.route('/save_game', methods=['POST'])
def save_game():
    slot_num = request.form.get('slot_num', type=int)
    save_name = request.form.get('save_name', '')
    
    result = SaveService.create_save(slot_num, save_name)
    return jsonify(result)

@app.route('/load_game', methods=['POST'])
def load_game():
    slot_num = request.form.get('slot_num', type=int)
    result = SaveService.load_save(slot_num)
    return jsonify(result)

@app.route('/get_saves')
def get_saves():
    return jsonify(SaveService.get_all_saves())

@app.route('/refresh_events')
async def refresh_events():
    result = await EventService.refresh_events()
    return jsonify(result)

@app.route('/get_active_events')
def get_active_events():
    return jsonify(EventService.get_active_events())

@app.route('/handle_event', methods=['POST'])
async def handle_event():
    event_id = request.json.get('event_id')
    choice = request.json.get('choice')
    
    if not event_id or not choice:
        return jsonify({'error': '参数不完整'}), 400
    
    llm_service = LLMService()
    result = await EventService.handle_event(event_id, choice, llm_service)
    return jsonify(result)

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        
        # 如果没有角色，创建一个
        if not Character.query.first():
            character = Character()
            db.session.add(character)
            db.session.commit()
        
        # 初始化事件池
        if not EventPool.query.first():
            initial_events = [
                {
                    'event_type': '奇遇',
                    'trigger_conditions': json.dumps({
                        'min_stage': 0,
                        'max_stage': 2
                    }),
                    'weight': 1.0,
                    'cooldown': 3,
                    'content': '在山中发现一个隐秘洞府，洞口有淡淡的灵气溢出。'
                },
                {
                    'event_type': '劫难',
                    'trigger_conditions': json.dumps({
                        'min_stage': 1,
                        'max_stage': 3
                    }),
                    'weight': 0.8,
                    'cooldown': 5,
                    'content': '一群修为略高的修士似乎对你身上的某件宝物产生了觊觎之心。'
                },
                {
                    'event_type': '日常',
                    'trigger_conditions': json.dumps({
                        'min_stage': 0,
                        'max_stage': 8
                    }),
                    'weight': 1.2,
                    'cooldown': 1,
                    'content': '路过一座小镇，发现镇上正在举办交易会，各种修炼资源琳琅满目。'
                },
                {
                    'event_type': '因果',
                    'trigger_conditions': json.dumps({
                        'min_stage': 2,
                        'max_stage': 5
                    }),
                    'weight': 0.7,
                    'cooldown': 7,
                    'content': '曾经帮助过的凡人商队遭到妖兽袭击，派人来请求援助。'
                }
            ]
            
            for event_data in initial_events:
                event = EventPool(**event_data)
                db.session.add(event)
            
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
