import configparser
import io
import Levenshtein as lv
import requests
from block_types import *
from dataclasses import asdict
from typing import List
from chat import create_chat_completion
import openai
from base64 import b64decode, b64encode
from PIL import Image
import os
import hashlib
from wand.image import Image as wImage
import xml.etree.ElementTree as ET
from io import BytesIO
MODEL = "gpt-3.5-turbo"
def get_auth_from_stability():
    url = f"https://api.stability.ai/v1/user/account"
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    api_key = conf.get("stability", "api")
    response = requests.get(url,
                            headers={"Authorization": f"Bearer {api_key}"})
    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))
    payload = response.json()
    
def generate_draw_with_stable(prompt, save_path):
    engine_id = "stable-diffusion-v1-5"
    api_host = 'https://api.stability.ai'
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    api_key = conf.get("stability", "api")
    if api_key is None:
        raise Exception("Missing Stability API key.")

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [{
                "text": prompt
            }],
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "height": 512,
            "width": 512,
            "samples": 1,
            "steps": 30,
        },
    )
    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    for i, image in enumerate(data["artifacts"]):
        image_data = image["base64"]
        with open(f"{save_path}.png", "wb") as f:
            f.write(b64decode(image["base64"]))
    return image_data

def rule_refine_drawing_prompt(content):
    """
    very cute illustration for a children's Scratch project, A runnnig bear, Bold and Bright Illustration Styles, Digital Painting, by Pixar style, no background objects
    """
    return f"very cute illustration for a children's Scratch project, {content}, Watercolor Painting, 4k, no background objects"

def chatgpt_refine_drawing_prompt(askterm, content):
    temp_memory = []
    if askterm == "role":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是人工智能程序的提示生成器。这里有一个描述关于：<{content}>。我给你一个模板，然后你根据提示模板生成图像提示。提示模板："[type of art], [subject or topic], [aesthetic details, lighting, and styles], [colors]", 图像提示例子：Children's illustration, a cat, playing, Vivid Colors, white background, soft lines and textures. Respond the prompt only, in English.
        """
        })
    elif askterm == "background":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是人工智能程序的提示生成器。这里有一个描述关于：<{content}>，我给你一个模板，然后你根据提示模板生成图像提示。提示模板："[type of art], [subject or topic], [aesthetic details, lighting, and styles], [colors]"，图像提示例子：Children's illustration, a tree, Vivid Colors, white background, soft lines and textures. Respond the prompt only, in English.
        """
        })
    else:
        raise "Not valid drawing type"
    # print(temp_memory)
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0.7)
    print("agent: ", agent_reply)
    return agent_reply

def generate_image_to_image(prompt, base_image):
    print("[image to image]starting generating image from base image...")
    print("[image to prompt]", prompt)
    image = Image.open(base_image)
    resized_image = image.resize((512, 512))
    with io.BytesIO() as buffer:
        resized_image.save(buffer, format='PNG')
        binary_data = buffer.getvalue()
    engine_id = "stable-diffusion-v1-5"
    api_host = 'https://api.stability.ai'
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    api_key = conf.get("stability", "api")
    if api_key is None:
        raise Exception("Missing Stability API key.")

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/image-to-image",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        files={"init_image": binary_data},
        data={
            "image_strength": 0.35,
            "init_image_mode": "IMAGE_STRENGTH",
            "text_prompts[0][text]": prompt,
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "samples": 1,
            "steps": 30,
        })

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    for i, image in enumerate(data["artifacts"]):
        image_data = image["base64"]
        # only for test
        with open("image_to_image.png", "wb") as f:
            f.write(b64decode(image["base64"]))
    return image_data

def rm_img_bg(image_base64):
    response = requests.post(
        'http://10.73.3.223:3848/rm_bg', files={'file': image_base64})
    if response.status_code == 200:
        res_image = Image.open(BytesIO(response.content))
        res_image.save('rm_bg.png')
        res_image = Image.open("rm_bg.png")
        image_bytes = BytesIO()
        res_image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        base64_image = b64encode(image_bytes).decode('utf-8')
        return base64_image
    else:
        return None