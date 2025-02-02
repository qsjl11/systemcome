from flask import Flask, request, render_template, Response
from core import System
import json
from core.logger import setup_logger
import logging

# 初始化日志记录器
logger = setup_logger('WebApp')

app = Flask(__name__)

# 初始化系统
system = System()
logger.info("系统初始化完成")
started = False


@app.route('/')
def index():
    """渲染聊天界面"""
    logger.info("访问主页")
    return render_template('chat.html')


@app.route('/chat', methods=['POST'])
async def chat():
    """处理普通对话请求"""
    try:
        data = request.get_json()
        message = data.get('query', '')
        logger.info(f"收到聊天请求: {message}")
        logging.info(f"Received message: {message}")

        # 普通对话
        response = await system.communicate(message)
        logger.info("对话请求处理成功")
        return json.dumps({"response": response})

    except Exception as e:
        logger.error(f"处理对话请求时出错: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})


@app.route('/chatstream', methods=['GET', 'POST'])
async def chat_stream():
    """处理流式对话请求"""
    global started
    try:
        logger.info("收到流式对话请求")
        if request.method == 'POST':
            data = request.get_json()
            message = data.get('query', '')
        else:
            message = request.args.get('query', '')

        if message.startswith('/story'):
            if len(message) > 6:
                story_name = message[6:].strip()
                response = await system.switch_story(story_name)
                started = False  # 切换剧本后，需要重新/start
                logger.info(f"切换剧本成功: {story_name}")
            else:
                # 获取可用剧本列表
                stories = system.get_available_stories()
                response = "可用剧本列表：\n" + "\n".join([f"- {story}" for story in stories])
                logger.info("获取剧本列表成功")
        elif not started:
            if message == "/start":
                started = True
                response = "【玩法说明】\n"
                response += f"{system.world.story_readme}\n\n"
                response += "\n\n【作为玩家的你将扮演系统，你可以向主角发布对话、修改世界任务状态，或者推动故事发展。】\n【即将进入开始场景，请尽情发挥你的想象力帮助主角或者...】\n\n"
                response += await system.generate_scene_description()
                logger.info("生成开始场景")
            else:
                response = "选择剧本，并点击 /start 开始游戏"
        else:
            # 处理特殊指令
            if message.startswith('/'):
                if message.startswith('/md '):
                    modification = message[3:].strip()
                    response = await system.modify_state(modification)
                    logger.info("修改世界状态")
                elif message.startswith('/qu '):
                    query = message[3:].strip()
                    response = await system.confirm_world_state(query)
                    logger.info("查询世界状态")
                elif message.startswith('/st'):
                    if len(message) > 3:
                        query = message[3:].strip()
                    else:
                        query = ""
                    response = await system.advance_story(query)
                    logger.info("故事演进")
                elif message == '/th':
                    response = system.character.get_current_thoughts()
                    logger.info("获取主角心理活动成功")
                elif message == '/en':
                    logger.info(f"查询系统能量成功: {system.energy}")
                    response = f"当前系统能量：{system.energy}"
                elif message == '/ch':
                    response = system.character.get_character_info_str()
                    logger.info("获取角色信息成功")
                elif message == '/world':
                    response = system.world.get_current_context()
                    logger.info("获取世界信息成功")
                    logger.info("更新角色档案成功")
                elif message == '/des':
                    response = await system.generate_scene_description()
                    logger.info("生成场景描述成功")
                elif message == '/reset':
                    response = await system.reset()
                    started = False  # 重置游戏状态后，需要重新/start
                    logger.info("重置游戏状态成功")
                elif message == '/help':
                    response = system.get_help_info()
                    logger.info("获取帮助信息成功")
                else:
                    logger.warning(f"收到未知指令: {message}")
                    response = "无效指令请重新输入"
            else:
                # 支持普通对话
                response = await system.communicate(message)

        # 流式返回
        def generate():
            # 普通响应转换为流式
            yield 'data: {}\n\n'.format(json.dumps({'content': response}))
            yield 'data: {}\n\n'.format(json.dumps({'conversation_id': ""}))
            yield 'data: {}\n\n'.format(json.dumps({'content': '[DONE]'}))

        logger.info(f"开始流式响应:{response}")
        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"处理流式对话请求时出错: {str(e)}", exc_info=True)

        def generate():
            # 普通响应转换为流式
            yield f"data: Error: {str(e)}\n\n"
            yield 'data: {}\n\n'.format(json.dumps({'conversation_id': ""}))
            yield 'data: {}\n\n'.format(json.dumps({'content': '[DONE]'}))

        return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    logger.info("启动Web服务器")
    app.run(debug=True)
