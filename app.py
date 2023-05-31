import base64
from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory, render_template
from speech import speech_to_text, text_to_speech
import os
import json
from chat import create_chat_completion
from flask_cors import CORS
from tools import *
from pydub import AudioSegment
from story_dict import StoryInfo

app = Flask(__name__)
CORS(app)
os.makedirs("static", exist_ok=True)
MODEL = "gpt-3.5-turbo"
story_memory = []
story_info = StoryInfo()

motion_blocks = MotionBlocks()
looks_blocks = LooksBlocks()
sound_blocks = SoundBlocks()
events_blocks = EventsBlocks()
control_blocks = ControlBlocks()
sensing_blocks = SensingBlocks()
ass_block = AssembleBlocks(motion_blocks, looks_blocks, sound_blocks,
                           events_blocks, control_blocks, sensing_blocks)


@app.route('/test_set', methods=['GET', 'POST'])
def test_set():
    act = request.form.get('act')
    type = request.form.get('type')
    content = request.form.get('content')
    story_info.add(act, type, content)
    # story_info.print_act('act1')
    # print(story_info.get_prompt(0, "background"))
    return "s"


@app.route('/test_query', methods=['GET', 'POST'])
def test_query():
    id = request.form.get("id")
    ask_term = request.form.get('ask_term')
    # story_info.get_prompt(0, "background")
    return story_info.get_prompt(id, ask_term)


@app.route('/get_audio', methods=['GET', 'POST'])
def get_audio():
    blob = request.files['file']
    act = request.form.get('act')
    type = request.form.get('type')
    blob.save(f'static/{act}+{type}.webm')
    audio_file = open(f'static/{act}+{type}.webm', 'rb')
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    content = transcript["text"]
    audio_file.close()
    story_info.add(act, type, content)
    return jsonify({'status': 'success', 'content': content})


@app.route('/chat_speech', methods=['POST'])
def chat_speech():
    global story_memory
    # TODO 1. 保存user音频和文本 2. 生成对话和保存对话 3. 输出client音频和文本
    # 得到user在讲故事的第几阶段(1-2-3)
    # 语音转文本，保存语音
    speech_content = speech_to_text(request.files, "user_talk")
    print(speech_content)
    story_memory.append({"role": "user", "content": speech_content})
    # chat with ai
    agent_reply = create_chat_completion(
        model=MODEL,
        messages=story_memory,
    )
    print("agent: ", agent_reply)
    story_memory.append({"role": "user", "content": speech_content})
    with open("static/storytelling.json", "w") as f:
        json.dump(story_memory, f, ensure_ascii=False)
    # agent reply to audio
    text_to_speech(agent_reply)
    return agent_reply


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    # return 4 audio files and 4 images
    output = {'sounds': [], 'images': []}
    id = request.form.get('id')
    askterm = request.form.get('askterm')
    temp_memory = []
    temp_memory.append(story_info.get_prompt(int(id), askterm))
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)

    return


@app.route('/generate_story', methods=['GET', 'POST'])
def generate_story():
    data = request.json
    id = data['id']
    role = data['role']
    background = data['background']
    event = data['event']
    temp_memory = []
    if role is None:
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是一个辅助儿童完成故事的编剧，儿童在写一个一句话的故事，故事需要包括人物。请你给我四个人物，人物要符合儿童的认知。
            """
        })
    elif role is not None and background is None:
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是一个辅助儿童完成故事的编剧，儿童在写一个一句话的故事，故事需要包括[人物、场景]。请你给出四种符合故事逻辑的场景供我选择，每种都用一句话。儿童讲述的内容是：{role}
            """
        })
    elif role is not None and background is not None and event is None:
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是一个辅助儿童完成故事的编剧，儿童在写一个一句话的故事，故事需要包括[人物、场景、事件]。请你给出四种符合故事逻辑的事件供我选择，每种都用一句话。儿童讲述的内容是：{role}、{background}
            """
        })
    else:
        raise "Not valid input, please check"
    # print(temp_memory)
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)
    return agent_reply


@app.route('/generate_drawing', methods=['GET', 'POST'])
def generate_role_draw():
    data = request.json
    drawing_type = data["type"]
    drawing_content = data["content"]
    temp_memory = []
    if drawing_type == "role":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""我想让你充当 Stable diffusion 的人工智能程序的提示生成器。你的工作是提供简短的描述。这里有一个关于动画风格角色的描述<{drawing_content}>，你需要根据<描述>决定：角色是什么，角色的朝向，角色的姿态。
        你的输出还需要加上"line art, in a transparent background, anime, colored, child style"，只需要输出最终的提示词，翻译为英文。
        """
        })
    elif drawing_type == "background":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""我想让你充当 Stable diffusion 的人工智能程序的提示生成器。你的工作是提供简短的描述。这里有一个关于动画风格背景的描述<{drawing_content}>，你需要根据<描述>决定：场景发生的地方，重点的景物。
        你的输出还需要加上"line art, anime, colored, child style"，只需要输出最终的提示词，翻译为英文。
        """
        })
    else:
        raise "Not valid drawing type"
    # print(temp_memory)
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)
    generate_draw_with_dalle(agent_reply, drawing_type)
    return agent_reply


@app.route('/split_story', methods=['GET', 'POST'])
def split_story():
    # data format: json
    data = request.json
    part = data['part']  # 获取part字段的值
    role = data['role']  # 获取role字段的值
    background = data['background']  # 获取background字段的值
    event = data['event']  # 获取event字段的值
    try:
        audio = request.files['audio']  # 获取上传的音频文件对象
    except:
        print("not audio found!")
    temp_memory = []
    temp_memory.append({
        "role":
        "user",
        "content":
        f"""你是一个专业的Scratch编程老师。我有一个故事梗概：第{part}幕，角色：{role}，场景：{background}，事件：{event}。我要根据这个故事来创建Scratch3.0项目，目前我有一些基础事件的Scratch实现：发出声音、键盘控制移动、点击角色发光、发出广播切换场景等，在{event}中，生成3个最有价值的Scratch代码，你的目标是参考事件来使Scratch代码丰富且富有创意。
        """
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)
    return agent_reply


@app.route('/send_audio')
def send_audio():
    pass


@app.route('/generate_code', methods=['GET', 'POST'])
def generate_code():
    data = request.json
    prompt = data['prompt']
    temp_memory = []
    temp_memory.append({
        "role":
        "user",
        "content":
        f"""你是一个专业的Scratch编程老师。你的任务是以一致的风格回答问题：{PROMPT}
    答案请使用Scratch3.0中的代码块，请补充completion["prompt":{prompt} ->,"completion":]"""
    })
    # print(temp_memory)
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)
    with open("static/agent_reply.txt", "w", encoding='utf-8') as f:
        f.write(agent_reply)
    extracted_reply = extract_keywords(agent_reply)
    block_list = cal_similarity(extracted_reply, ass_block)
    # print(block_list)
    with open("static/block_suggestion.txt", 'w') as f:
        list_str = '\n'.join(str(element) for element in block_list)
        f.write(list_str)
    return block_list


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)