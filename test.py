# import xml.etree.ElementTree as ET


# def Get_size(infile):
#     tree = ET.parse(infile)
#     root = tree.getroot()
#     element_with_width = root.find(".//*[@width]")
#     if element_with_width is not None:
#         width = int(element_with_width.get('width'))
#         height = int(element_with_width.get('height'))
#         return width,height
#     else:
#         return 500,500
    
# print(Get_size('static/scene/0d551a530e6288f4df3b944f1a9ea6de.svg'))
import openai
import os
import configparser

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
def get_api_key():
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    return conf.get("openai", "api")
openai.api_key = get_api_key()

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


print(create_chat_completion(messages=[{"role": "user", "content": "can you help me?"}],model="gpt-3.5-turbo"))