# # import xml.etree.ElementTree as ET


# # def Get_size(infile):
# #     tree = ET.parse(infile)
# #     root = tree.getroot()
# #     element_with_width = root.find(".//*[@width]")
# #     if element_with_width is not None:
# #         width = int(element_with_width.get('width'))
# #         height = int(element_with_width.get('height'))
# #         return width,height
# #     else:
# #         return 500,500
    
# # print(Get_size('static/scene/0d551a530e6288f4df3b944f1a9ea6de.svg'))
# import openai
import os
# import configparser

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
# def get_api_key():
#     conf = configparser.ConfigParser()
#     conf.read("./envs/keys.ini")
#     return conf.get("openai", "api")
# openai.api_key = get_api_key()

# def create_chat_completion(messages,
#                            model=None,
#                            temperature=0,
#                            max_tokens=None) -> str:
#     """Create a chat completion using the OpenAI API"""
#     response = None
#     response = openai.ChatCompletion.create(model=model,
#                                             messages=messages,
#                                             temperature=temperature,
#                                             max_tokens=max_tokens)
#     if response is None:
#         raise RuntimeError("Failed to get response")

#     return response.choices[0].message["content"]


# # print(create_chat_completion(messages=[{"role": "user", "content": "can you help me?"}],model="gpt-3.5-turbo"))

# from wand.image import Image as wImage
# infile = "/media/sda1/cyn-workspace/Scratch-project/ScratchGPT/static/1/image-0.png"
# with wImage(filename=infile) as img:
#         print(img.format)
#         img.save(filename='/media/sda1/cyn-workspace/scratch-gui/src/playground/assets/testimage.png')
#         img.format = 'svg'
#         print(img.format)
#         img.save(filename='/media/sda1/cyn-workspace/scratch-gui/src/playground/assets/testimage.svg')
#         print('finish')
#         print(img.make_blob())
        
        

       
# import requests
# import openai
# import os
# from openai import OpenAI
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
# client = OpenAI(
#     # 修改api_key为网站生成的令牌
#     api_key="sk-nHyluroPegJcPHVz72118968635942DaAbD4C689Be339bE6",
#     base_url="https://api.openai.com/v1"
# )
# client.base_url="https://ai-yyds.com/v1"

# response = client.chat.completions.create(
#     messages=[
#       {"role": "system", "content": "你是一个擅长说冷笑话的AI。"},
#       {"role": "user", "content": "给我讲个笑话?"}
#     ],
#     model="gpt-4o"
# )

# print(response.choices[0].message.content)

import base64
import configparser
import io
import requests
from block_types import *
from chat import *
import openai
from base64 import b64decode, b64encode
from PIL import Image
from io import BytesIO
from rembg import remove
from tools import MODEL
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
import json


def generate_draw_with_stable_v2(prompt, save_path):
    url = "http://10.73.3.223:55233"
    
    payload = {
        "prompt": prompt,
        "negative_prompt": "ugly, ugly arms, ugly hands, ugly teeth, ugly nose, ugly mouth, ugly eyes, ugly ears,",
        "steps": 25,
        "sampler_name": "Euler a",
        "cfg_scale": 7,
        "width": 512,
        "height": 512
    }
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    data = response.json()
    for encoded_result in data['images']:
        result_data = base64.b64decode(encoded_result)
        with open(f"{save_path}.png", "wb") as f:
            f.write(result_data)

    return encoded_result
generate_draw_with_stable_v2('a cute dog', '/media/sda1/cyn-workspace/Scratch-project/ScratchGPT')