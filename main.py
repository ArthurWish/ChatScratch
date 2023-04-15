from typing import Dict, List
import json
import openai
import os
import dataclasses

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

mem_dict = {}
agents = {}
full_messages_history = []


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
        json.dump(mem_dict, f)


def create_chat_completion(messages,
                           model=None,
                           temperature=1,
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



if __name__ == "__main__":
    # creat_memory("story")
    task1 = "story"
    _, agent_reply, messages = create_agent(task1, "you are a story teller.", "gpt-3.5-turbo")
    creat_memory(task1, messages)
    # create_agent("storyboard", "you are a storyboard maker.", "gpt-3.5-turbo")
