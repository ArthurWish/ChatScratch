import sys
import time
from typing import Dict, List
import json
import openai
import os
from dataclasses import dataclass
from base64 import b64decode
import configparser

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

mem_dict = {}
agents = {}


def get_api_key():
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    return conf.get("openai", "api")


openai.api_key = get_api_key()


def creat_memory(task: str, messages: List):
    # messages is full history

    mem_dict = {f"{task}": messages}

    with open(f"{task}.json", "w") as f:
        json.dump(mem_dict, f, ensure_ascii=False)


def create_chat_completion_stream(messages,
                                  model="gpt-3.5-turbo",
                                  temperature=0,
                                  stream=True,
                                  max_tokens=None):
    start_time = time.time()
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=stream  # again, we set stream=True
    )
    # create variables to collect the stream of chunks
    collected_chunks = []
    collected_messages = []
    # iterate through the stream of events
    for chunk in response:
        chunk_time = time.time(
        ) - start_time  # calculate the time delay of the chunk
        collected_chunks.append(chunk)  # save the event response
        chunk_message = chunk['choices'][0]['delta']  # extract the message
        collected_messages.append(chunk_message)  # save the message
        full_reply_content = ''.join(
            [m.get('content', '') for m in collected_messages])
        time.sleep(0.2)
        print(f'\r{full_reply_content}', end='')
        # print(
        #     f"Message received {chunk_time:.2f} seconds after request: {chunk_message}"
        # )  # print the delay and text
    # print the time delay and text received
    # print(f"Full response received {chunk_time:.2f} seconds after request")
    # full_reply_content = ''.join(
    #     [m.get('content', '') for m in collected_messages])
    # print(f"Full conversation received: {full_reply_content}")


def create_chat_completion(messages,
                           model=None,
                           temperature=0,
                           max_tokens=None) -> str:
    """Create a chat completion using the OpenAI API"""
    response = None
    response = openai.ChatCompletion.create(model=model,
                                            messages=messages,
                                            temperature=temperature,
                                            max_tokens=max_tokens)
    if response is None:
        raise RuntimeError("Failed to get response")

    return response.choices[0].message["content"]


def create_agent(task, prompt, model):
    global agents
    """Create a new agent and return its key"""
    messages = [
        {
            "role": "user",
            "content": prompt
        },
    ]
    # Start GPT instance
    agent_reply = create_chat_completion(
        model=model,
        messages=messages,
    )
    print("agent: ", agent_reply)
    # Update full message history
    messages.append({"role": "assistant", "content": agent_reply})
    agents[task] = (task, messages, model)

    return task, agent_reply, messages


def message_agent(task, message):
    global agents
    task, messages, model = agents[task]
    # user modified the message from agent
    # Add user message to message history before sending to agent
    messages.append({"role": "user", "content": message})
    agent_reply = create_chat_completion(
        model=model,
        messages=messages,
    )
    # Update full message history
    messages.append({"role": "assistant", "content": agent_reply})

    return agent_reply, messages


def init_agent(agent_name, message):
    pass


def chat_no_memory(message):
    messages = []
    messages.append({"role": "user", "content": message})
    agent_reply = create_chat_completion(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    print(agent_reply)
    return agent_reply


def chat_with_agent(agent_name, message):
    agent_memory = f"{agent_name}.json"
    # init agent
    if not os.path.exists(agent_memory):
        messages = []
        messages.append({"role": "user", "content": message})
        agent_reply = create_chat_completion(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        messages.append({"role": "assistant", "content": agent_reply})
        with open(agent_memory, "w") as f:
            json.dump(messages, f, ensure_ascii=False)
    # chat agent
    else:
        messages: List = json.load(open(agent_memory, "r"))  # List
        # messages = [] # not load memory
        messages.append({"role": "user", "content": message})
        agent_reply = create_chat_completion(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        messages.append({"role": "assistant", "content": agent_reply})
        with open(agent_memory, "w") as f:
            json.dump(messages, f, ensure_ascii=False)
    print(agent_reply)
    if agent_name == "step":
        print(agent_reply + "你能按照这个方案来编程吗？")
    elif agent_name == "detail":
        print("当然，我可以给你一个参考:\n" + agent_reply)


def chat_with_ai(task):
    global agents
    task, messages, model = agents[task]
    while True:
        user_input = input("Please input(press Q to exit):\n")
        if user_input == "Q":
            return messages
        agent_reply, messages = message_agent(task, user_input)
        print("agent: ", agent_reply)
        agents[task] = (task, messages, model)


def draw_with_ai(prompt: str):
    response = openai.Image.create(prompt=prompt,
                                   n=1,
                                   size="256x256",
                                   response_format="b64_json")
    for index, image_dict in enumerate(response["data"]):
        image_data = b64decode(image_dict["b64_json"])
        image_file = "test.png"
        with open(image_file, mode="wb") as png:
            png.write(image_data)


def generate_code(task_name, content):
    if task_name == "code_recommendation":
        task_first_message = "你是一个资深的scratch编程专家，我有一个动画编剧提供的分镜[content]，帮我把它写成Scratch代码"
        task_first_message = task_first_message.replace("content", content)
    else:
        raise f"the {task_name} is invalid."
    _, agent_reply, messages = create_agent(task_name, task_first_message,
                                            "gpt-3.5-turbo")
    full_history_messages = chat_with_ai(task_name)
    creat_memory(task_name, full_history_messages)


def build_task(task_name, pre_task=None):
    if pre_task:
        memory_pre_task = json.load(open(f"{pre_task}.json", "r"))
        if memory_pre_task[pre_task][-1]["role"] == "assistant":
            content = memory_pre_task[pre_task][-1]["content"]
        else:
            raise "assistant content is empty"

    if task_name == "story":
        task_first_message = "你是一个资深儿童作家，请你以[user_input]写一个200词左右的儿童故事,为了故事更加有趣,请你在角色、场景的塑造，动作、对话、心理活动的描述上多斟酌。"
        user_topic = input("input topic:\n")
        task_first_message = task_first_message.replace(
            "user_input", user_topic)
    elif task_name == "storyboard":
        task_first_message = "你是一个资深的儿童动画编剧,我有一个儿童故事[content],我希望你能把故事改编成儿童可以实现的逐帧动画,请用分镜稿的形式展示动画中的重要场景。"
        task_first_message = task_first_message.replace("content", content)
    elif task_name == "format":
        task_first_message = "你是一个资深的scratch编程专家，这里有一个动画编剧提供的分镜描述：[content] 我希望你能考scratch初学者的编程水平，为每一个场景制定对应的scratch实现方案，同时我希望你把分镜稿结构化输出，以json的形式输出结构如下： {场景：int，角色：{角色名称：str，角色描述：str}，背景描述：str，场景描述：str，scratch实现方案：str}"
        task_first_message = task_first_message.replace("content", content)
    elif task_name == "plan":
        task_first_message = "你是一个资深的scratch编程专家，我有一个动画编剧提供的分镜方案[content]，请你考虑scratch编程初学者的水平，设计具体的实现方案"
        task_first_message = task_first_message.replace("content", content)
    else:
        raise ValueError("Invalid task type")

    _, agent_reply, messages = create_agent(task_name, task_first_message,
                                            "gpt-3.5-turbo")
    full_history_messages = chat_with_ai(task_name)
    creat_memory(task_name, full_history_messages)


@dataclass
class TaskType:
    story: str = "story"
    storyboard: str = "storyboard"
    format: str = "format"
    plan: str = "plan"
    image_prompt: str = "image_prompt"
    code_recommendation: str = "code_recommendation"


@dataclass
class TaskMessageStory:
    first: str = ""
    second: str = ""
    third: str = ""


def main():
    build_task(TaskType.story)  # 处理任务1
    build_task(TaskType.storyboard, TaskType.story)  # 处理任务2并将任务1作为前一个任务
    build_task(TaskType.format, TaskType.storyboard)
    build_task(TaskType.plan, TaskType.format)


if __name__ == "__main__":

    # main()
    # input_1 = input("模拟输入儿童的问题:\n")

    text = f"""
    如何使乌龟在跑过终点的时候，兔子停下并说话？
    """
    prompt = f"""你是一个专业的Scratch编程老师。
1-请使用Scratch代码块类别回答下面用<>括起来的问题。
2-推荐每个代码块类别具体的代码块。

请使用以下格式：
问题：<要回答的问题>
类别：<所有的代码块的类别>
指导：<所有的具体的代码块>
名称：<回答所有代码块在Scratch3.0中的名称>
输出 JSON：<带有 类别 和 指导 的 JSON>

Text: <{text}>
"""
    prompt = f"""
你是一个专业的Scratch编程老师。你的任务是以一致的风格回答问题。

<孩子>: 如何实现点击角色，使角色变色？

<老师>: 使用"when this sprite clicked","change color effect by [0.25]"

<孩子>: 如何实现点击角色，使角色跳舞？

<老师>: 使用"when this sprite clicked","move [10] stpes","play drum [Snare drum] for [0.25] beats","move [-10] steps","play drum [Closed Hi-Hat] for [0.25] beats"

<孩子>: 如何实现点击角色，使角色变大和缩小？
"""
    prompt = """
你是一个专业的Scratch编程老师。你的任务是以一致的风格回答问题。
{"prompt":"点击角色，使角色变色 ->","completion":" \"when this sprite clicked\",\"change [color] effect by [25]\"\n"}
{"prompt":"点击角色，使角色一直旋转 ->","completion":" \"when this sprite clicked\",\"repeat [10]\",\"turn [18] degrees\"\n"}
{"prompt":"点击角色，播放音效 ->","completion":" \"when this sprite clicked\",\"play sound [Guitar Strum] until done\" \n"}
{"prompt":"点击角色，使角色跳舞 ->","completion":" \"when this sprite clicked\",\"move [10] steps\",\"play\"\n"}
{"prompt":"点击绿旗，改变背景并使角色说话 ->","completion":" \"when gree flag clicked\",\"switch backdrop to [Savanna]\",\"wait [2] seconds\",\"switch backdrop to [Metro]\",\"say [Let's explore] for [2] seconds\"\n"}
{"prompt":"点击绿旗，播放声音并切换costume ->","completion":" \"when green flag clicked\",\"start sound [your recording]\",\"next costume\",\"say [] for [2] seconds\"\n"}
{"prompt":"点击绿旗，如果触碰到角色就播放声音 ->","completion":" \"when green flag clicked\",\"forever\",\"if touching [star] then\",\"play sound [Collect] until done\"\n"}
我的问题是{"prompt":"当接收到广播(下一个背景)，背景换成大海"}
"""
    #     prompt = f"""
    # 你的任务是以一致的风格回答问题。

    # <孩子>: 教我耐心。

    # <祖父母>: 挖出最深峡谷的河流源于一处不起眼的泉眼；最宏伟的交响乐从单一的音符开始；最复杂的挂毯以一根孤独的线开始编织。

    # <孩子>: 教我韧性。
    # """
    chat_no_memory(prompt)
    exit(0)
    prompt_dict = json.load(open("assets/prompt.json", "r", encoding="gbk"))
    # print(prompt_dict)
    code_main = chat_no_memory(prompt_dict["code_main"].replace(
        "content", "兔子和乌龟赛跑"))
    code_d1 = chat_no_memory(prompt_dict["code_d1"].replace(
        "content", code_main))
    code_d2 = chat_no_memory(prompt_dict["code_d2"].replace(
        "content", code_d1))
    simple = chat_no_memory(prompt_dict["simplifying"].replace(
        "content", code_d2))

    chat_with_agent(
        "test1",
        f"你是一个Scratch编程老师。请用Scratch中的代码块类别（运动、外观、声音、事件、控制、侦测、运算、变量）给儿童提供编程建议。我给你一些模板：问：如何通过键盘实现角色的移动\n答：建议使用运动、侦测和控制类别来实现\n问：小兔子如何奔跑答：建议使用运动类别中的\"以一定速度移\"和\"以一定角度转动\"代码块，通过侦测类别中的\"当某个键按下\"来控制小兔子的奔跑。\n问：小兔子和小乌龟如何对话\n答：建议使用事件类别中的\"当收到信息\"和\"发送信息\"，以及控制类别中的\"等待\"和\"重复\"代码块来实现小兔子和小乌龟之间的对话。下面我会问你问题，你要按照模板来回答。"
    )
    while True:
        inputa = input("Input:\n")
        chat_with_agent("test1", inputa)

        # input_a = input("Input:\n")
        # if input_a == "1":
        #     input_b = input("Step:\n")
        #     chat_with_agent("step", f"你是一个善于和儿童交流的Scratch编程老师，告诉儿童使用Scratch的简略的实现思路，不需要提供具体的编程代码。问题是：{input_b}")
        # elif input_a == "2":
        #     input_b = input("Detail:\n")
        #     chat_with_agent("detail", f"你是一个善于和儿童交流的Scratch编程老师，告诉儿童使用Scratch的详细实现方案，提供详细的编程代码，尽量包含控制、事件、侦测、运算等代码块。问题是：{input_b}")
        # elif input_a == "3":
        #     input_b = input("Simple:\n")
        #     chat_with_agent("simple", f"尽最大努力简化下面一段话，使儿童可以容易地读懂。内容是：{input_b}")
        # if input_a == "y":
        #     input_b = input("\nUser:\n")
        #     # 用Scratch实现一个场景的切换，按
        #     chat_with_agent("step", input_b)
        # elif input_a == "n":
        #     input_b = input("\nUser:\n")
        #     chat_with_agent("detail", f"你是一个编程专家，你会给我一个详细的实现方案，我的问题是:{input_b}")
        # elif input_a == "q":
        #     if os.path.exists("step.json"):
        #         os.remove("step.json")
        #     if os.path.exists("detail.json"):
        #         os.remove("detail.json")
        #     break
        # else:
        #     print("please type valid input(y/n/q)")

    # draw_with_ai("a little cat, front-facing, fishing, line art, colored, anime, simple, child style, in a trasparent background")
    # TODO token count
    # generate_code(task_name=TaskType.code_recommendation, content="设置背景为学校运动会场景，创建小熊和小兔子角色，设置角色的初始位置和动作。")
    # TODO 分镜数据单独存
