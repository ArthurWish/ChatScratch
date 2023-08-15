import base64
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
from rembg import remove

MODEL = "gpt-3.5-turbo"


#解码图像
def decode_base64_to_image(encoding):
    if encoding.startswith("data:image/"):
        encoding=encoding.split(":")[1].split(",")[1]
    image=Image.open(io.BytesIO(base64.b64decode(encoding)))
    return image


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


def rule_refine_drawing_prompt_for_role(content):
    content=content[0:-1]
    return f"very cute illustration for a children's Scratch project, {content} with a transparent background, by Katie Risor,Cartoonish Illustration Style,Acrylic, 4k"

def rule_refine_drawing_prompt(content):
    """
    very cute illustration for a children's Scratch project, A runnnig bear, Bold and Bright Illustration Styles, Digital Painting, by Pixar style, no background objects
    """
    return f"landscape painting, {content}, no character in the picture,  by studio ghibli, makoto shinkai, by artgerm, by wlop, by greg rutkowski, Watercolor Painting, 4k"


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


def generate_draw(drawing_type, drawing_content, save_path):
    temp_memory = []
    if drawing_type == "role":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是人工智能程序的提示生成器。这里有一个描述<{drawing_content}>。我给你一个模板，然后你根据提示模板生成图像提示。提示模板："[type of art], [subject or topic], [style], [colors]"，图像提示例子：Very cute children's illustration,by studio ghibli, makoto shinkai, by artgerm, by wlop, by greg rutkowski, a cat, playing, Vivid Colors, white background, soft lines and textures. Respond the prompt only, in English.
        """
        })
    elif drawing_type == "background":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是人工智能程序的提示生成器。这里有一个关于描述<{drawing_content}>，我给你一个模板，然后你根据提示模板生成图像提示。提示模板："[type of art], [subject or topic], [aesthetic details, lighting, and styles], [colors]"，图像提示例子：Very cute children's illustration,by studio ghibli, makoto shinkai, by artgerm, by wlop, by greg rutkowski, a tree, Vivid Colors, white background, soft lines and textures. Respond the prompt only, in English.
        """
        })
    else:
        raise "Not valid drawing type"
    # print(temp_memory)
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=1.2)
    print("agent: ", agent_reply)
    # TODO 多卡推断
    image_data = generate_draw_with_stable_v2(agent_reply, save_path)
    return image_data


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
            "image_strength": 0.25,
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


def generate_draw_with_dalle(prompt, save_path):
    # image_data_list = []
    response = openai.Image.create(prompt=prompt,
                                   n=1,
                                   size="256x256",
                                   response_format="b64_json")
    for index, image_dict in enumerate(response["data"]):
        image_data_return = image_dict["b64_json"]
        # image_data_list.append(image_data)
        with open(f"{save_path}.png", mode="wb") as png:
            png.write(b64decode(image_dict["b64_json"]))
    return image_data_return

def rm_img_bg_local(in_path, out_path):
    with open(in_path, 'rb') as i:
        with open(out_path, 'wb') as o:
            input = i.read()
            output = remove(input)
            o.write(output)
    with open(out_path, 'rb') as o:
        encoded_data = base64.b64encode(o.read())
        return encoded_data.decode('utf-8') 

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


def generate_draw_with_stable_v2(prompt, save_path):
    url = "http://10.73.3.223:55233"
   
    payload = {
        "prompt": prompt,
        "negative_prompt": "ugly, ugly arms, ugly hands, ugly teeth, ugly nose, ugly mouth, ugly eyes, ugly ears,",
        "steps": 50,
        "sampler_name": "Euler a",
        "cfg_scale": 7,
        "width":512,
        "height":512
    }
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    data = response.json()
    for encoded_result in data['images']:
        result_data = base64.b64decode(encoded_result)
        with open(f"{save_path}.png", "wb") as f:
            f.write(result_data)
        # image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))
    # for i, image in enumerate(data["artifacts"]):
        # image_data = image["base64"]
        # with open(f"{save_path}.png", "wb") as f:
            # f.write(b64decode(image["base64"]))
    # only use for single image
    return encoded_result

def generate_image_to_image_v2(prompt, base_image):
    url = "http://10.73.3.223:55233"
    print("[image to image]starting generating image from base image...")
    print("[image to prompt]", prompt)
    image = Image.open(base_image)
    resized_image = image.resize((512, 512))
    with io.BytesIO() as buffer:
        resized_image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    img2img_payload = {
        "init_images": [img_base64],
        "prompt": prompt,
        "negative_prompt": "ugly, ugly arms, ugly hands, ugly teeth, ugly nose, ugly mouth, ugly eyes, ugly ears",
        "denoising_strength": 0.5,
        "width": 512,
        "height": 512,
        "cfg_scale": 7,
        "sampler_name": "Euler a",
        "restore_faces": False,
        "steps": 25,
        "script_args": ["outpainting mk2", ]
    }
    response = requests.post(
        url=f'{url}/sdapi/v1/img2img', json=img2img_payload)

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    for encoded_result in data["images"]:
        result_data = base64.b64decode(encoded_result)
        # image_data = Image.open(io.BytesIO(base64.b64decode(image.split(",",1)[0])))
        # image_data = image["base64"]
        # only for test
        with open("image_to_image.png", "wb") as f:
            f.write(result_data)
    # only use for single image
    return encoded_result


# generate_draw_with_stable_v2("a cute cat", "1")
# generate_image_to_image_v2(prompt="a cute cat, child's style",
#                            base_image=r"C:\Users\YunNong\Desktop\ScratchGPT\static\temp.png")
def generate_controlnet(prompt, base_image):
    url = "http://10.73.3.223:55233"
    print("[image to image]starting generating image on the basis of controlnet...")
    print("[txt to image with controlnet]starting generating image on the basis of controlnet...")
    print("[image to prompt]", prompt)
    image = Image.open(base_image)
    resized_image = image.resize((512, 512))
    with io.BytesIO() as buffer:
        resized_image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    payload = {
        "prompt":prompt,
        #"Digital art, a colorful bird, by studio ghibli, makoto shinkai, by artgerm, by wlop, by greg rutkowski, Vivid Colors, white background,simple background",
        "negative_prompt": "ugly, ugly arms, ugly hands, ugly teeth, ugly nose, ugly mouth, ugly eyes, ugly ears,scary,handicapped,",
        "batch_size":1,
        "steps": 50,
        "sampler_name": "Euler a",
        "cfg_scale": 7,
        "width":512,
        "height":512,
        "script_args": ["outpainting mk2", ],
        "alwayson_scripts":{
            "ControlNet":{
                "args":[
                    {
                    "enabled":True,
                    "input_image":img_base64,
                    #"control_type":"Scribble"
                    "module":'scribble_xdog',
                    "model":'control_v11p_sd15_scribble [d4ba51ff]',
                    # "starting_control_step":0,
                    # "ending_control_step":1,
                    #"guessmode":False
                }
                ]
            }
        }
    }
    response = requests.post(
        url=f'{url}/sdapi/v1/txt2img', json=payload)

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()
    image=decode_base64_to_image(response.json()['images'][0])
    image.save("image_to_image.png",format='PNG')

    return data['images'][0]



def extract_from_sketch(img):
    url = "http://10.73.3.223:55233"
    print("[Extracting txt from image]...")
    image = Image.open(img)
    resized_image = image.resize((512, 512))
    with io.BytesIO() as buffer:
        resized_image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    in_load = {
        "image": img_base64,
        "model":"clip"
    }
    response = requests.post(url=f'{url}/sdapi/v1/interrogate', json=in_load)
    return response.json()['caption']