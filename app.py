from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory, render_template
from speech import speech_to_text, text_to_speech
import os
import json
from chat import create_chat_completion, chat_with_agent
from dataclasses import dataclass
from flask_cors import CORS
from tools import *

app = Flask(__name__)
CORS(app)
os.makedirs("public", exist_ok=True)
MODEL = "gpt-3.5-turbo"
story_memory = []
# prompt = "当接收到广播(下一个背景)，背景换成大海"

motion_blocks = MotionBlocks()
looks_blocks = LooksBlocks()
sound_blocks = SoundBlocks()
events_blocks = EventsBlocks()
control_blocks = ControlBlocks()
sensing_blocks = SensingBlocks()
ass_block = AssembleBlocks(motion_blocks, looks_blocks, sound_blocks,
                           events_blocks, control_blocks, sensing_blocks)


# 对话之前的引导问题，转语音
@dataclass
class StoryTelling:
    role = ""
    location = ""
    event = ""


@dataclass
class StoryDrawing:
    pass


def init_story():
    story_memory.append({
        "role":
        "user",
        "content":
        "你是一个儿童故事作家，我在写一个由起因、经过、结果三个部分构成的故事，每一个部分只有一句话。我的故事的起因是:input。我说完之后请以赞美的语气跟我互动。"
    })
    agent_reply = create_chat_completion(
        model=MODEL,
        messages=story_memory,
    )
    print("agent: ", agent_reply)
    text_to_speech(agent_reply)
    story_memory.append({"role": "assistant", "content": agent_reply})


# init_story()


@app.route('/get_audio')
def get_audio():
    return send_file('public/story.mp3', mimetype='audio/mp3')


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
    with open("public/storytelling.json", "w") as f:
        json.dump(story_memory, f, ensure_ascii=False)
    # agent reply to audio
    text_to_speech(agent_reply)
    return agent_reply


@app.route('/chat_image')
def chat_image():
    pass


@app.route('/chat_code')
def chat_code():
    pass


@app.route('/send_audio')
def send_audio():
    pass


@app.route('/chat_once', methods=['GET', 'POST'])
def chat_once():
    data = request.json
    prompt = data.get('prompt')
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
    with open(r"C:\Users\YunNong\Desktop\scratch-gui\public\agent_reply.txt",
              "w") as f:
        f.write(agent_reply)
    extracted_reply = extract_keywords(agent_reply)
    block_list = cal_similarity(extracted_reply, ass_block)
    print(block_list)
    with open(
            r"C:\Users\YunNong\Desktop\scratch-gui\public\block_suggestion.txt",
            'w') as f:
        list_str = '\n'.join(str(element) for element in block_list)
        f.write(list_str)
    return block_list


@app.route("/index")
def index():
    return render_template("demo.html")


if __name__ == '__main__':
    app.run()