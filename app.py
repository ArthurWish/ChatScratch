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
import hashlib
from PIL import Image
import shutil

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
    print('111')
    id = request.form.get("id")
    assests_path = f"static/{id}"
    assert id == "1" or id == "2" or id == "3"
    askterm = request.form.get('askterm')
    assert askterm == "role" or askterm == "background" or askterm == "event"
    os.makedirs(assests_path, exist_ok=True)
    base_img = request.form.get("url").split(',')[1] # base64
    print(base_img)
    with open("static/temp.png", "wb") as f:
        f.write(b64decode(base_img))
    content = story_info.get_act(act_name=id, key=askterm)
    content = ['rabbit with red carrot']
    if content != []:
        image_base64 = generate_image_to_image(prompt=content, base_image="static/temp.png")
        return jsonify({'status':'success', 'url': image_base64})
    else:
        return jsonify({'status':'failed', 'url': None})
    
@app.route('/save_drawings', methods=['GET', 'POST'])
def save_drawings():
    role_list = json.loads(request.form['role'])
    project_path = 'C:/Users/11488/Desktop/react_try/scratch-gui/src/lib/default-project/'
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
        svg_str = toSVG(png_path)
        svg_path = os.path.join(assests_path, f'{get_str_md5(svg_str)}.svg')
        pro_path = os.path.join(project_path, f'{get_str_md5(svg_str)}.svg')
        with open(svg_path, "w") as f:
            f.write(svg_str)
        with open(pro_path, "w") as f:
            f.write(svg_str)
        os.remove(png_path)  # 删除原始PNG图片

    # 处理scene_list
    scene_list = json.loads(request.form['scene'])
    assests_path =  f"static/scene/"
    if os.path.exists(assests_path):
        shutil.rmtree(assests_path)
    os.makedirs(assests_path, exist_ok=True)
    for i, img in enumerate(scene_list):
        img = img.split(',')[1]
        png_path = os.path.join(assests_path, f'{i}.png')
        with open(png_path, "wb") as f:
            f.write(b64decode(img))
        svg_str = toSVG(png_path)
        svg_path = os.path.join(assests_path, f'{get_str_md5(svg_str)}.svg')
        pro_path = os.path.join(project_path, f'{get_str_md5(svg_str)}.svg')
        with open(svg_path, "w") as f:
            f.write(svg_str)
        with open(pro_path, "w") as f:
            f.write(svg_str)
        os.remove(png_path)  # 删除原始PNG图片

    
    
        
    generate_js()
    generate_js_project()
    return jsonify({'status':'success'})

def toSVG(infile):
    image = Image.open(infile).convert('RGBA')
    data = image.load()
    width, height = image.size
    svg_str = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg_str += '<svg id="svg2" xmlns="http://www.w3.org/2000/svg" version="1.1" \
                width="%(x)i" height="%(y)i" viewBox="0 0 %(x)i %(y)i">\n' % \
              {'x': width, 'y': height}
    for y in range(height):
        for x in range(width):
            rgba = data[x, y]
            rgb = '#%02x%02x%02x' % rgba[:3]
            if rgba[3] > 0:
                svg_str += '<rect width="1" height="1" x="%i" y="%i" fill="%s" \
                    fill-opacity="%.2f" />\n' % (x, y, rgb, rgba[3]/255.0)
    svg_str += '</svg>\n'
    return svg_str

# 计算字符串的MD5哈希值的函数
def get_str_md5(input_str):
    md5_obj = hashlib.md5()
    md5_obj.update(input_str.encode())
    return md5_obj.hexdigest()


def generate_js():
    backdrop_files = os.listdir('static/scene')
    costume_files = os.listdir('static/role')
   
    with open('C:/Users/11488/Desktop/react_try/scratch-gui/src/lib/default-project/index.js', 'w') as f:
        f.write('import projectData from \'./project-data\';\n')
        for i, file in enumerate(backdrop_files):
            f.write('import backdrop' + str(i + 1) + ' from \'!raw-loader!./' + file + '\';\n')
        for i, file in enumerate(costume_files):
            f.write('import costume' + str(i + 1) + ' from \'!raw-loader!./' + file + '\';\n')

        f.write('\nconst defaultProject = translator => {\n')
        f.write('let _TextEncoder;\n')
        f.write('if (typeof TextEncoder === \'undefined\') {\n')
        f.write('    _TextEncoder = require(\'text-encoding\').TextEncoder;\n')
        f.write('} else {\n')
        f.write('    _TextEncoder = TextEncoder;\n')
        f.write('}\n')
        f.write('const encoder = new _TextEncoder();\n\n')
        f.write('const projectJson = projectData(translator);\n\n')
        f.write('    return [{\n')
        f.write('        id: 0,\n')
        f.write('        assetType: \'Project\',\n')
        f.write('        dataFormat: \'JSON\',\n')
        f.write('        data: JSON.stringify(projectJson)\n')
        f.write('    },\n')

        for i, file in enumerate(backdrop_files):
            f.write('    {\n')
            f.write('        id: \'' + file.split('.')[0] + '\',\n')
            f.write('        assetType: \'ImageVector\',\n')
            f.write('        dataFormat: \'SVG\',\n')
            f.write('        data: encoder.encode(backdrop' + str(i + 1) + ')\n')
            f.write('    },\n')
        
        for i, file in enumerate(costume_files):
            f.write('    {\n')
            f.write('        id: \'' + file.split('.')[0] + '\',\n')
            f.write('        assetType: \'ImageVector\',\n')
            f.write('        dataFormat: \'SVG\',\n')
            f.write('        data: encoder.encode(costume' + str(i + 1) + ')\n')
            f.write('    },\n')

        f.write('];\n};\n\nexport default defaultProject;\n')
        
        
def generate_js_project():
    backdrop_files = os.listdir('static/scene')
    costume_files = os.listdir('static/role')

    with open('C:/Users/11488/Desktop/react_try/scratch-gui/src/lib/default-project/project-data.js', 'w') as f:
        f.write('import {defineMessages} from \'react-intl\';\n')
        f.write('import sharedMessages from \'../shared-messages\';\n\n')
        f.write('let messages = defineMessages({\n')
        f.write('    meow: {\n')
        f.write('        defaultMessage: \'Meow\',\n')
        f.write('        description: \'Name for the meow sound\',\n')
        f.write('        id: \'gui.defaultProject.meow\'\n')
        f.write('    },\n')
        f.write('    variable: {\n')
        f.write('        defaultMessage: \'my variable\',\n')
        f.write('        description: \'Name for the default variable\',\n')
        f.write('        id: \'gui.defaultProject.variable\'\n')
        f.write('    }\n')
        f.write('});\n\n')
        f.write('messages = {...messages, ...sharedMessages};\n\n')
        f.write('const defaultTranslator = msgObj => msgObj.defaultMessage;\n\n')
        
        f.write('/**\n')
        f.write(' * Generates the project data.\n')
        f.write(' * @param {function} translateFunction - A function to translate the text in the project.\n')
        f.write(' * @return {object} The project data with multiple targets each with its own properties.\n')
        f.write(' */\n')
        
        f.write('const projectData = translateFunction => {\n')
        f.write('    const translator = translateFunction || defaultTranslator;\n')
        f.write('    return ({\n')
        f.write('        targets: [\n')

        # for i, file in enumerate(backdrop_files):
        f.write('            {\n')
        f.write('                isStage: true,\n')
        f.write('                name: \'Stage\',\n')
        f.write('                variables: {\n')
        f.write('                    \'`jEk@4|i[#Fk?(8x)AV.-my variable\': [\n')
        f.write('                        translator(messages.variable),\n')
        f.write('                        0\n')
        f.write('                    ]\n')
        f.write('                },\n')
        f.write('                lists: {},\n')
        f.write('                broadcasts: {},\n')
        f.write('                blocks: {},\n')
        f.write('                currentCostume: 0,\n')
        f.write('                costumes: [\n')
        for i, file in enumerate(backdrop_files):
            f.write('                    {\n')
            f.write('                        assetId: \'' + file.split('.')[0] + '\',\n')
            f.write('                        name: translator(messages.backdrop, {index: ' + str(i+1) + '}),\n')
            f.write('                        md5ext: \'' + file + '\',\n')
            f.write('                        dataFormat: \'svg\',\n')
            f.write('                        rotationCenterX: 500,\n')
            f.write('                        rotationCenterY: 460\n')
            f.write('                    },\n')
        f.write('                ],\n')
        f.write('                sounds: [],\n')
        f.write('                volume: 100\n')
        f.write('            },\n')
        for i, file in enumerate(costume_files):
            f.write('            {\n')
            f.write('                isStage: false,\n')
            f.write('                name: translator(messages.sprite, {index: ' + str(i + 1) + '}),\n')
            f.write('                variables: {},\n')
            f.write('                lists: {},\n')
            f.write('                broadcasts: {},\n')
            f.write('                blocks: {},\n')
            f.write('                currentCostume: 0,\n')
            f.write('                costumes: [\n')
        
            f.write('                    {\n')
            f.write('                        assetId: \'' + file.split('.')[0] + '\',\n')
            f.write('                        name: translator(messages.costume, {index: ' + str(1) + '}),\n')
            f.write('                        bitmapResolution: 1,\n')
            f.write('                        md5ext: \'' + file + '\',\n')
            f.write('                        dataFormat: \'svg\',\n')
            f.write('                        rotationCenterX: 500,\n')
            f.write('                        rotationCenterY: 460\n')
            f.write('                    },\n')
            f.write('                ],\n')
            f.write('                sounds: [],\n')
            f.write('                volume: 100,\n')
            f.write('                visible: true,\n')
            f.write('                x: 0,\n')
            f.write('                y: 0,\n')
            f.write('                size: 100,\n')
            f.write('                direction: 90,\n')
            f.write('                draggable: false,\n')
            f.write('                rotationStyle: \'all around\'\n')
            f.write('            },\n')

        f.write('        ],\n')
        f.write('        meta: {\n')
        f.write('            semver: \'3.0.0\',\n')
        f.write('            vm: \'0.1.0\',\n')
        f.write('            agent: \'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36\'\n')
        f.write('        }\n')
        f.write('    });\n')
        f.write('};\n\n')
        f.write('export default projectData;\n')

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
    # audio_base64 = text_to_speech(agent_reply, f"static/agent-reply-{id}.mp3")
    extracted_reply = extract_keywords(agent_reply)
    block_list = cal_similarity(extracted_reply, ass_block)
    # print(block_list)
    with open(f"static/block_suggestion-{id}.txt", 'w') as f:
        list_str = '\n'.join(str(element) for element in block_list)
        f.write(list_str)
    return jsonify({'code': block_list})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)