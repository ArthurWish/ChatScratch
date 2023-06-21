import base64
from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory, render_template
from speech import speech_to_text, text_to_speech
import os
import json
from chat import create_chat_completion
from flask_cors import CORS
from tools import *
from story_dict import StoryInfo
from PIL import Image
import shutil
from io import BytesIO
app = Flask(__name__)
CORS(app)

os.makedirs("static", exist_ok=True)
os.makedirs("static/codes", exist_ok=True)
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


@app.route("/hello")
def hello():
    return "hello"


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
            output["sound"].append(text_to_speech(
                reply, f"{assests_path}/sound-{index}"))
            output["image"].append(
                generate_draw(drawing_type=askterm,
                              drawing_content=reply,
                              save_path=f'{assests_path}/image-{index}'))
    else:
        content = content[0]
        for index in range(4):
            output["sound"].append(text_to_speech(
                content, f"{assests_path}/sound-{index}"))
            output["image"].append(
                generate_draw(drawing_type=askterm,
                              drawing_content=content,
                              save_path=f'{assests_path}/image-{index}'))
    return jsonify(output)


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
    base_img = request.form.get("url").split(',')[1]  # base64
    base_img_bytes = base64.b64decode(base_img)
    img = Image.open(io.BytesIO(base_img_bytes)).convert('RGBA')
    bg = Image.new('RGBA', img.size, (255,255,255))

    # 在背景上粘贴原图像（使用原图像作为遮罩以保留其透明度）
    combined = Image.alpha_composite(bg, img)
    combined.convert('RGB').save('static/temp.png', 'PNG')
    content = story_info.get_act(act_name=id, key=askterm)
    # content = content + 'Highly detailed, Vivid Colors, white background'
    content = ['a cat, Highly detailed, Vivid Colors, white background']
    if content != []:
        image_base64 = generate_image_to_image(
            prompt=content, base_image="static/temp.png")
        res_image = []
        response = requests.post(
            'http://10.73.3.223:3848/rm_bg', files={'file': image_base64})
        if response.status_code == 200:
            res_image = Image.open(BytesIO(response.content))
            res_image.save('rm_bg.png')
            res_image = Image.open("rm_bg.png")
            image_bytes = BytesIO()
            res_image.save(image_bytes, format='PNG')
            image_bytes = image_bytes.getvalue()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        return jsonify({'status': 'success', 'url': base64_image})
    else:
        return jsonify({'status': 'failed', 'url': None})


@app.route('/save_drawings', methods=['GET', 'POST'])
def save_drawings():
    role_list = json.loads(request.form['role'])
    project_path = r'c:\Users\YunNong\Desktop\scratch-gui\src\lib\default-project'
    assests_path = f"static/role/"
    if os.path.exists(assests_path):
        shutil.rmtree(assests_path)
    os.makedirs(assests_path, exist_ok=True)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    os.makedirs(project_path, exist_ok=True)
    for i, img in enumerate(role_list):
        img = img.split(',')[1]
        png_path = os.path.join(assests_path, f'{i}.png')
        with open(png_path, "wb") as f:
            f.write(b64decode(img))
        toSVG(png_path, project_path, assests_path)

        os.remove(png_path)  # 删除原始PNG图片

    # 处理scene_list
    scene_list = json.loads(request.form['scene'])
    assests_path = f"static/scene/"
    if os.path.exists(assests_path):
        shutil.rmtree(assests_path)
    os.makedirs(assests_path, exist_ok=True)
    for i, img in enumerate(scene_list):
        img = img.split(',')[1]
        png_path = os.path.join(assests_path, f'{i}.png')
        with open(png_path, "wb") as f:
            f.write(b64decode(img))
        toSVG(png_path, project_path, assests_path)
        os.remove(png_path)  # 删除原始PNG图片
    generate_js()
    generate_js_project()
    return jsonify({'status': 'success'})


@app.route('/generate_code', methods=['GET', 'POST'])
def generate_code():
    """
    return code_list
    """
    os.makedirs('static/codes', exist_ok=True)
    id = request.form.get("id")
    audio_blob = request.files['file']
    audio_blob.save(f'static/codes/code-question-{id}.webm')
    audio_file = open(f'static/codes/code-question-{id}.webm', 'rb')
    transript = openai.Audio.transcribe("whisper-1", audio_file)
    content = transript["text"]

    # test
    # content = '如何实现角色翻转'
    code_agent = []
    code_agent.append({
        "role":
        "user",
        "content":
        f"""你是一个专业的Scratch编程老师。你的任务是以一致的风格回答问题：{PROMPT}
    答案请使用Scratch3.0中的代码块，请补充completion["prompt":{content} ->,"completion":]"""
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=code_agent,
                                         temperature=0)
    with open(f"static/codes/agent_reply-{id}.txt", "w", encoding='utf-8') as f:
        f.write(agent_reply)

    extracted_reply = extract_keywords(agent_reply)
    block_list = cal_similarity(extracted_reply, ass_block)
    block_list = [block for block in block_list if block]
    print(block_list)

    refine_agent = []
    refine_agent.append({
        "role":
        "user",
        "content":
        f"""帮助我提取这段文本的信息，分点，需要精简文本，不要显示原文本：{agent_reply}
        """
    })
    refine_reply = create_chat_completion(model=MODEL,
                                          messages=refine_agent,
                                          temperature=0)
    print("agent: ", refine_reply)
    audio_base64 = text_to_speech(
        refine_reply, f"static/codes/agent-reply-{id}.mp3")

    output_json = 'static/codes/block_suggestion.json'
    data = {}
    if os.path.exists(output_json):
        with open(output_json, 'r') as f:
            data = json.load(f)
    data[str(int(id)-1)] = block_list
    with open(output_json, 'w') as f:
        json.dump(data, f, indent=4)
    # print(block_list)
    # with open(f"static/codes/block_suggestion-{id}.txt", 'w') as f:
    #     list_str = '\n'.join(str(element) for element in block_list)
    #     f.write(list_str)
    return jsonify({'file': audio_base64})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
