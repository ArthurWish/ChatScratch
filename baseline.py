import openai
import os
import configparser
import pandas as pd
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"


def get_api_key():
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    return conf.get("openai", "api")


openai.api_key = get_api_key()


def fine_tuned_model(fine_tuned_model, prompt):

    response = openai.Completion.create(model=fine_tuned_model,
                                        prompt=prompt,
                                        max_tokens=1000,
                                        temperature=0.3,
                                        stop=["\n"])
    print(response["choices"][0].text)
    return response["choices"][0].text


def create_completion(question) -> str:
    """Create a chat completion using the OpenAI API"""
    response = openai.Completion.create(
        model="davinci:ft-leroys-2023-05-16-02-56-13",
        prompt=question,
        temperature=0.3,
        top_p=1,
        max_tokens=100,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n"])

    return response["choices"][0].text


def chat_no_memory(question):
    agent_reply = create_completion(question=question, )
    print(agent_reply)
    return agent_reply

def main():
    question = "点击绿旗，使兔子说“你追我啊”，使乌龟向兔子移动"
    # question = "点击绿旗，到达目标分数，切换场景"
    question = "点击绿旗，播放声音并切换costume"
    question = "点击绿旗，使角色说话"
    print("question ->", question)
    prompt = question + " ->"
    # chat_no_memory(question)
    fine_tuned_model("davinci:ft-leroys-2023-05-16-02-56-13", prompt)

def generate_chatgpt_template():
    # 问：prompt 答：completion
    df = pd.read_excel(r"C:\Users\YunNong\Desktop\Codebase.xlsx", sheet_name="Sheet1")
    prompt = df['prompt']
    completion = df['completion']
    for a, b in zip(prompt, completion):
        print(a)

if __name__ == "__main__":
    # generate_chatgpt_template()
    main()
