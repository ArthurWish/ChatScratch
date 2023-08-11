import base64
from urllib import response
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
from code_generation import *
from image_generation import *
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
    """ transform audio to text and add story info"""
    blob = request.files['file']
    act = request.form.get('act')
    print("act", act)
    assert act == "1" or act == "2" or act == "3" or act == "4"
    type = request.form.get('type')
    assert type == "role" or type == "background" or type == "event" or type == "code"
    blob.save(f'static/{act}+{type}.webm')
    with open(f'static/{act}+{type}.webm', 'rb') as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    content = transcript["text"]
    print(content)
    story_info.add(act, type, content)
    return jsonify({'status': 'success', 'content': content})


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """return images and sounds"""
    draft_url = request.form.get("draft_url")
    if draft_url!='placeholder':
        base_img = request.form.get("draft_url").split(',')[1]  # base64
        base_img_bytes = base64.b64decode(base_img)
        img = Image.open(io.BytesIO(base_img_bytes)).convert('RGBA')
        bg = Image.new('RGBA', img.size, (255, 255, 255))
        # TODO 角色背景分开
        # 在背景上粘贴原图像（使用原图像作为遮罩以保留其透明度）
        combined = Image.alpha_composite(bg, img)
        combined.convert('RGB').save('static/base_draft.png', 'PNG')
        current_sketch=extract_from_sketch(img='static/base_draft.png')
        current_sketch_content=','.join(current_sketch.split(',')[0:-4])
        current_sketch_style=','.join(current_sketch.split(',')[-4:])
        print(current_sketch)
        has_img=True
    else:
        has_img=False
        
    id = request.form.get('id') # part id   第一幕第二幕第三幕
    index_id = request.form.get('index_id') # current part, which image 
    index_id = int(index_id)
    assert id == "1" or id == "2" or id == "3"
    assests_path = f"static/{id}"
    os.makedirs(assests_path, exist_ok=True)
    askterm = request.form.get('askterm')
    assert askterm == "role" or askterm == "background" or askterm == "event"
    output = {'sound': [], 'image': []}
    temp_memory = []
    # query
    content = story_info.get_act(act_name=id, key=askterm)
    print("content", content)   #当前类别内的描述
    print("index_id", index_id)  
    # user already input
    if has_img==True:  # 存在草图
        if len(content) >= index_id+1: #存在语音输入的定义，结合两者给出灵感
            current_drawing = content[index_id]
            print("current_drawing", current_drawing)
        else:
            current_drawing=''
        print(current_drawing)
        msg=[]
        msg.append({"role":
            "user",
            "content":
            f"""你是一个儿童故事编剧。这里有一个描述<{current_drawing},{current_sketch_content}>，请给出你根据描述联想的4个相关的{askterm}，不超过75字.Respond the prompt only, in English.
        """})    
        agent_reply = create_chat_completion(model=MODEL,
                                         messages=msg,
                                         temperature=0.3)
        #print(related_content)
        print("agent: ", agent_reply)
        if '\n' not in agent_reply:
            raise f"ERROR! Please check {agent_reply}"
        reply_splited = split_to_parts(agent_reply)
        if len(reply_splited) != 4:
            return "the reply is not 4"
        assert len(reply_splited) == 4
        for index, reply in enumerate(reply_splited):    
            
            output["sound"].append(text_to_speech(
                translate_to_chinese(reply), f"{assests_path}/sound-{index}"))
            prompt="very cute illustration for a children's Scratch project,"+reply+current_sketch_style
            print(prompt)
            output["image"].append(
                generate_draw_with_stable_v2(prompt= prompt,
                                             save_path=f'{assests_path}/image-{index}'))
            
                # generate_draw(drawing_type=askterm,
                #               drawing_content=current_drawing,
                #               save_path=f'{assests_path}/image-{index}'))
    # user not input
    elif len(content) < index_id+1:   #没有草图，也没有相关描述
        prompt = story_info.get_prompt(id, askterm)
        print("story_info.get_prompt:\n", prompt)
        temp_memory.append(prompt)
        agent_reply = create_chat_completion(model=MODEL,
                                             messages=temp_memory,
                                             temperature=0.3)
        print("agent: ", agent_reply)
        if '\n' not in agent_reply:
            raise f"ERROR! Please check {agent_reply}"
        reply_splited = split_to_parts(agent_reply)
        if len(reply_splited) != 4:
            return "the reply is not 4"
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
    index_id = request.form.get("index_id")
    assests_path = f"static/{id}"
    assert id == "1" or id == "2" or id == "3"
    askterm = request.form.get('askterm')
    assert askterm == "role" or askterm == "background" or askterm == "event"
    os.makedirs(assests_path, exist_ok=True)
    base_img = request.form.get("url").split(',')[1]  # base64
    base_img_bytes = base64.b64decode(base_img)
    img = Image.open(io.BytesIO(base_img_bytes)).convert('RGBA')
    bg = Image.new('RGBA', img.size, (255, 255, 255))
    # TODO 角色背景分开
    # 在背景上粘贴原图像（使用原图像作为遮罩以保留其透明度）
    combined = Image.alpha_composite(bg, img)
    combined.convert('RGB').save('static/temp.png', 'PNG')
    content = story_info.get_act(act_name=id, key=askterm)
    current_role = content[int(index_id)]
    print("current_role", current_role)
    
    current_role=translate_to_english(current_role)
    print("current_role", current_role)
    if askterm=="role":
        content=rule_refine_drawing_prompt_for_role(current_role)
    else:
        content = rule_refine_drawing_prompt(current_role)
   
    # content = rule_refine_drawing_prompt(translate_to_english(current_role))
    # content = content +  ['Vivid Colors, white background']
    # content = ['a cat, Highly detailed, Vivid Colors, white background']
    if content != []:
        # image_base64 = generate_image_to_image_v2(
        image_base64 = generate_controlnet(
            prompt=content, base_image="static/temp.png")
        if askterm == "role":
            # rmbg_image = rm_img_bg(image_base64)
            rmbg_image = rm_img_bg_local("image_to_image.png", "rmbg_image.png")
            return jsonify({'status': 'success', 'url': rmbg_image})
        else:
            return jsonify({'status': 'success', 'url': image_base64})
    else:
        return jsonify({'status': 'failed', 'url': None})


@app.route('/save_drawings', methods=['GET', 'POST'])
def save_drawings():
    role_list = json.loads(request.form['role'])
    project_path = "/media/sda1/cyn-workspace/scratch-gui/src/lib/default-project"
    assests_path = f"/media/sda1/cyn-workspace/Scratch-project/ScratchGPT/static/role"
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
    assests_path = f"/media/sda1/cyn-workspace/Scratch-project/ScratchGPT/static/scene/"
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
    print(id, audio_blob)
    audio_blob.save(f'static/codes/code-question-{id}.webm')
    audio_file = open(f'static/codes/code-question-{id}.webm', 'rb')
    transript = openai.Audio.transcribe("whisper-1", audio_file)
    content = transript["text"]
    print(content)
    # test
    # content = '一个男孩打篮球'
    step1 = generate_code_step(content, "step1")
    step2 = generate_code_step(content, "step2")
    # step1, step2 = extract_step(content)
    print("step1", step1)
    print("step2", step2)
    extracted_step1 = chatgpt_extract_step1(step1)
    print("extracted_step1", extracted_step1)
    
    # step1
    with open(f"static/codes/agent_reply-{id}.json", "w", encoding='utf-8') as f:
        json.dump(extracted_step1, f)
        # f.write(extracted_step1)
    audio_base64 = text_to_speech(step1, f"static/codes/agent-reply-{id}.mp3")
    # f.write(step2)
    # step2
    extracted_reply = chatgpt_extract_code(step2)
    block_list = cal_similarity(extracted_reply, ass_block)
    block_list = [block for block in block_list if block]
    print(block_list)

    # refine_agent = []
    # refine_agent.append({
    #     "role":
    #     "user",
    #     "content":
    #     f"""帮助我提取这段文本的信息，分点，需要精简文本，不要显示原文本：{agent_reply}
    #     """
    # })
    # refine_reply = create_chat_completion(model=MODEL,
    #                                       messages=refine_agent,
    #                                       temperature=0)
    # print("agent: ", refine_reply)
    # audio_base64 = text_to_speech(
    #     refine_reply, f"static/codes/agent-reply-{id}.mp3")

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
    # text_to_speech("第一幕", f"第一幕.mp3")
    # text_to_speech("第二幕", f"第二幕.mp3")
    # text_to_speech("第三幕", f"第三幕.mp3")
    app.run(host='0.0.0.0', port=5500, debug=True)
    # extracted_reply = ['event_whenflagclicked', 'switchcostumeto', 'control_wait', 'switchcostumeto', 'control_wait', 'switchcostumeto', 'control_wait', 'switchcostumeto', 'control_wait']
    # block_list = cal_similarity(extracted_reply, ass_block)
    # block_list = [block for block in block_list if block]
    # print(block_list)
    
