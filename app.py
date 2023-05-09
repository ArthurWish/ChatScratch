from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory, render_template
from speech import speech_to_text, text_to_speech
import os
import json
from chat import create_chat_completion, chat_with_agent
from dataclasses import dataclass

app = Flask(__name__)
os.makedirs("static", exist_ok=True)
MODEL = "gpt-3.5-turbo"
story_memory = []

# 对话之前的引导问题
@dataclass
class StoryTelling:
    role = ""
    location = ""
    event = ""

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


init_story()


@app.route('/get_audio')
def get_audio():
    return send_file('static/story.mp3', mimetype='audio/mp3')


@app.route('/chat_story', methods=['POST'])
def chat_story():
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


@app.route('/chat_image')
def chat_image():
    pass


@app.route('/chat_code')
def chat_code():
    pass


@app.route('/send_audio')
def send_audio():
    pass


@app.route("/index")
def index():
    return render_template("demo.html")


if __name__ == '__main__':
    app.run()