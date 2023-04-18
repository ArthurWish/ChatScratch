import sys
import time
from typing import Dict, List
import json
import openai
import os
from dataclasses import dataclass
from base64 import b64decode

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

mem_dict = {}
agents = {}


def get_api_key():
    openai_key_file = './envs/openai_key'
    with open(openai_key_file, 'r', encoding='utf-8') as f:
        openai_key = json.loads(f.read())
    return openai_key['api']


openai.api_key = get_api_key()


def creat_memory(task: str, messages: List):
    # messages is full history
    global mem_dict

    mem_dict[task] = messages

    with open("memory.json", "w") as f:
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


def build_task(task_name, pre_task=None):
    if pre_task:
        memory = json.load(open("memory.json", "r"))
        if memory[pre_task][-1]["role"] == "assistant":
            content = memory[pre_task][-1]["content"]
        else:
            raise "assistant content is empty"

    if task_name == "story":
        task_first_message = "你是一个资深儿童作家，请你以[user_input]写一个400词左右的儿童故事,为了故事更加有趣,请你在角色、场景的塑造，动作、对话、心理活动的描述上多斟酌。"
        user_topic = input("input topic")
        task_first_message = task_first_message.replace(
            "user_input", user_topic)
    elif task_name == "storyboard":
        task_first_message = "你是一个资深的儿童动画编剧,我有一个儿童故事[ai_generated],我希望你能把故事改编成儿童可以实现的逐帧动画,请用分镜稿的形式展示动画中的重要场景。"
        task_first_message = task_first_message.replace(
            "ai_generated", content)
    elif task_name == "format":
        task_first_message = "你是一个资深的scratch编程专家，这里有一个动画编剧提供的分镜描述：[storyboard] 我希望你能考scratch初学者的编程水平，为每一个场景制定对应的scratch实现方案，同时我希望你把分镜稿结构化输出，以json的形式输出结构如下： {场景：int，角色：{角色名称：str，角色描述：str}，背景描述：str，场景描述：str，scratch实现方案：str}"
        task_first_message = task_first_message.replace("storyboard", content)
    elif task_name == "plan":
        task_first_message = "你是一个资深的scratch编程专家，我有一个动画编剧提供的分镜方案[format]，请你考虑scratch编程初学者的水平，设计具体的实现方案"
        task_first_message = task_first_message.replace("format", content)
    else:
        raise ValueError("Invalid task type")

    _, agent_reply, messages = create_agent(task_name, task_first_message,
                                            "gpt-3.5-turbo")
    full_history_messages = chat_with_ai(task_name)
    creat_memory(task_name, full_history_messages)


@dataclass
class TaskType:
    task1: str = "story"
    task2: str = "storyboard"
    task3: str = "format"
    task4: str = "plan"


if __name__ == "__main__":
    # draw_with_ai("colorful bird character design for Angry Birds game in transparent background")
    # TODO token count

    # build_task(TaskType.task1)  # 处理任务1
    # build_task(TaskType.task2, TaskType.task1)  # 处理任务2并将任务1作为前一个任务
    build_task(TaskType.task3, TaskType.task2)