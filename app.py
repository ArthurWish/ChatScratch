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
    return [act, story_info.get_act(act_name=act)]


@app.route('/test_query', methods=['GET', 'POST'])
def test_query():
    id = request.form.get("id")
    ask_term = request.form.get('ask_term')
    return story_info.get_prompt(id, ask_term)


@app.route('/get_audio', methods=['GET', 'POST'])
def get_audio():
    """ transform audio to text and return"""
    blob = request.files['file']
    act = request.form.get('act')
    assert act == "1" or act == "2" or act == "3" or act == "4"
    type = request.form.get('type')
    assert type == "role" or type == "background" or type == "event" or type == "code"
    blob.save(f'static/{act}+{type}.webm')
    audio_file = open(f'static/{act}+{type}.webm', 'rb')
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    content = transcript["text"]
    audio_file.close()
    story_info.add(act, type, content)
    return jsonify({'status': 'success', 'content': content})


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """return images and sounds"""
    id = request.form.get('id')
    assert id == "1" or id == "2" or id == "3"
    assests_path = f"static/{id}"
    os.makedirs(assests_path, exist_ok=True)
    askterm = request.form.get('askterm')
    assert askterm == "role" or askterm == "background" or askterm == "event"
    output = {'sound': [], 'image': []}
    temp_memory = []
    # query
    content = story_info.get_act(act_name=id, key=askterm)
    if content == []:
        prompt = story_info.get_prompt(id, askterm)
        temp_memory.append(prompt)
        agent_reply = create_chat_completion(model=MODEL,
                                             messages=temp_memory,
                                             temperature=0)
        print("agent: ", agent_reply)
        if '\n' not in agent_reply:
            raise f"ERROR! Please check {agent_reply}"
        reply_splited = split_to_parts(agent_reply)
        assert len(reply_splited) == 4
        for index, reply in enumerate(reply_splited):
            output["sound"].append(text_to_speech(reply, f"{assests_path}/sound-{index}"))
            output["image"].append(
                generate_draw(drawing_type=askterm,
                              drawing_content=reply,
                              save_path=f'{assests_path}/image-{index}'))
    else:
        content = content[0]
        for index in range(4):
            output["sound"].append(text_to_speech(content, f"{assests_path}/sound-{index}"))
            output["image"].append(
                generate_draw(drawing_type=askterm,
                              drawing_content=content,
                              save_path=f'{assests_path}/image-{index}'))
    return jsonify(output)


def generate_draw(drawing_type, drawing_content, save_path):
    temp_memory = []
    if drawing_type == "role":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是人工智能程序的提示生成器。你的工作是提供简短的一句话描述。这里有一个关于动画风格角色的描述<{drawing_content}>。使用类似英文生成提示："Anime-style human with a transparent background, exploring a magical world with a butterfly companion. Line art, anime, colored, child style."。翻译为英语。
        """
        })
    elif drawing_type == "background":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是人工智能程序的提示生成器。你的工作是提供简短的一句话描述。这里有一个关于动画风格背景的描述<{drawing_content}>，你需要根据<描述>决定：场景发生的地方，重点的景物。使用类似英文生成提示："Forest with running track at the end, featuring trees and a running track. Line art, anime, colored, child style."。翻译为英语。
        """
        })
    else:
        raise "Not valid drawing type"
    # print(temp_memory)
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)
    image_data = generate_draw_with_dalle(agent_reply, save_path)
    return image_data


@app.route('/generate_task', methods=['GET', 'POST'])
def generate_task():
    # 儿童提问，首先生成编程任务
    # data format: json
    question = request.form.get("quesiton")
    try:
        blob = request.files['audio']  # 获取上传的音频文件对象
        blob.save(f'static/code-question-{id}.webm')
        audio_file = open(f'static/code-question-{id}.webm', 'rb')
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        content = transcript["text"]
        audio_file.close()
    except:
        print("not audio found!")
    # only for test
    content = request.form.get("content")
    temp_memory = []
    temp_memory.append({
        "role":
        "user",
        "content":
        f"""你是一个专业的Scratch编程老师。目前数据库里有一些基础事件的Scratch实现：发出声音、键盘控制移动、点击角色发光、发出广播切换场景等，根据问题<{content}>，分点列举3个最有价值的Scratch代码实现，你的目标是模仿数据库的事件来使实现的Scratch代码有逻辑且正确。
        """
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)
    reply_splited = split_to_parts(agent_reply)
    return agent_reply


@app.route('/generate_img_to_img', methods=['GET', 'POST'])
def generate_img_to_img():
    id = request.form.get("id")
    assests_path = f"static/{id}"
    assert id == "1" or id == "2" or id == "3"
    askterm = request.form.get('askterm')
    assert askterm == "role" or askterm == "background" or askterm == "event"
    os.makedirs(assests_path, exist_ok=True)
    base_img = request.form.get("image") # base64
    with open("static/temp.png", "wb") as f:
        f.write(b64decode(base_img))
    content = story_info.get_act(act_name=id, key=askterm)
    if content != []:
        image_base64 = generate_image_to_image(prompt=content, base_image="static/temp.png")
        return image_base64
    else:
        return None


@app.route('/generate_code', methods=['GET', 'POST'])
def generate_code():
    """
    return code_list
    """
    id = request.form.get("id")
    prompt = request.form.get("prompt")
    temp_memory = []
    temp_memory.append({
        "role":
        "user",
        "content":
        f"""你是一个专业的Scratch编程老师。你的任务是以一致的风格回答问题：{PROMPT}
    答案请使用Scratch3.0中的代码块，请补充completion["prompt":{prompt} ->,"completion":]"""
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)
    with open(f"static/agent_reply-{id}.txt", "w", encoding='utf-8') as f:
        f.write(agent_reply)
    audio_base64 = text_to_speech(agent_reply, f"static/agent-reply-{id}.mp3")
    extracted_reply = extract_keywords(agent_reply)
    block_list = cal_similarity(extracted_reply, ass_block)
    # print(block_list)
    with open(f"static/block_suggestion-{id}.txt", 'w') as f:
        list_str = '\n'.join(str(element) for element in block_list)
        f.write(list_str)
    return jsonify({'code': block_list, 'audio': audio_base64})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)