import json
from typing import List
import Levenshtein as lv
from dataclasses import asdict
from block_types import *
import re
from chat import *
from tools import MODEL, extract_answer_content_to_list
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain


class RefinePrompt:
    PROMPT_NEW = json.load(open("./scratch_prompt.json", "r"))
    _template = """
    Your task is to generate a four-level mind map of the Scratch code based on the problem. The four levels are objects, key steps, programming steps and specific Scratch code.
    The results in \"anwser\" must be returned using jsMind's default node_tree data format.
    Here is an example:
    
    Following the previous prompt, write a prompt that describes the following elements:
    {desc}

    You should only respond in JSON format, as described below:
    The return format is as follows:
    {{
        "question":"$YOUR_QUESTION_HERE",
        "answer": "$YOUR_ANSWER_HERE"
    }}
    Make sure the response can be parsed by Python json.loads
    """
    llm = OpenAI(openai_api_key=client.api_key)
    prompt = PromptTemplate(
        input_variables=["desc"],
        template=_template
    )
    chain = LLMChain(prompt=prompt, llm=llm)

    def run(self, text):
        res = self.chain.run(text)
        # 解析json
        result = json.loads(res)
        return result["answer"]


PROMPT2 = """
{"prompt":"点击绿旗，使角色说话 ->","completion":" \"when green flag clicked\",\"say [Hello!] for [2] seconds\",\"say [Imagine if...] for [2] seconds\"\n"}
"""
PROMPT = """
{"prompt":"点击角色，切换到下一个costume ->","completion":" \"when this sprite clicked\",\"switch costume to []\",\"wait [0.3] seconds\",\"switch costume to []\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，改变背景并使角色说话 ->","completion":" \"when gree flag clicked\",\"switch backdrop to [Savanna]\",\"wait [2] seconds\",\"switch backdrop to [Metro]\",\"say [Let's explore] for [2] seconds\"\n"}
{"prompt":"点击绿旗，如果触碰到角色就播放声音 ->","completion":" \"when green flag clicked\",\"forever\",\"if touching [star] then\",\"play sound [Collect] until done\"\n"}
{"prompt":"点击绿旗，如果触碰到角色播放声音并增加分数 ->","completion":" \"when green flag clicked\",\"set [Score] to [0]\",\"forever\",\"if touching [star] then\",\"change [Score] by [1]\",\"play sound [Collect] until done\"\n"}
{"prompt":"点击绿旗，当分数足够切换背景 ->","completion":" \"when green flag clicked\",\"switch backdrop to []\",\"wait until (Score) == (10)\",\"switch backdrop to [Nebula]\",\"when backdrop switches to [Nebula]\",\"play sound [Win] until done\"\n"}
{"prompt":"按下空格，使角色跳起来 ->","completion":" \"when [space] key pressed\",\"change y by [60]\",\"wait [0.3] seconds\",\"change y by [-60]\"\n"}
{"prompt":"按下空格，改变角色姿势 ->","completion":" \"when [space] key pressed\",\"switch costume to [max-c]\",\"wait [0.3] seconds\",\"switch costume to [max-b]\"\n"}
{"prompt":"点击绿旗，实现角色跑步动画 ->","completion":" \"when green flag clicked\",\"go to x:[-140],y:[-60]\",\"repeat [50]\",\"move [10] steps\",\"next costume\"\n"}
{"prompt":"点击绿旗，使两个角色对话 ->","completion":" \"when green flag clicked\",\"say [I have a pet owl!] for [2] seconds\",\"wait [2] seconds\",\"when green flag clicked\",\"wait [2] seconds\",\"say [What's its name] for [2] seconds\"\n"}
{"prompt":"点击角色，改变颜色，播放声音 ->","completion":" “when this sprite clicked\",\"change [color] effect by [25]\",\"play sound [Magic Spell]\n"}
{"prompt":"点击绿旗，播放声音，使角色说话 ->","completion":" \"when green flag clicked\",\"start sound [recording1]\",\"say [let's go] for [2] seconds\"\n"}
{"prompt":"点击绿旗，使角色滑行 ->","completion":" “when green flag clicked\",\"go to x: [-180] y: [140]\",\"glide [1] secs to x: [-30] y: [50]\"\n"}
{"prompt":"点击绿旗，使角色走进舞台 ->","completion":" “when green flag clicked\",“hide\",\"go to x: [-240] y: [-60]\",\"show\",\"glide [2] secs to x: [0] y: [-60]\"\n"}
{"prompt":"角色收到信息，回复 ->","completion":" \"when i receive [message1]\",\"say [To the forest!] for [2] seconds\"\n"}
{"prompt":"点击绿旗，改变背景 ->","completion":" “when green flag clicked\",\"switch backdrop to [Witch House]\",\"hide\",\"wait [4] seconds\",\"switch backdrop to [Mountain]\" \n"}
{"prompt":"改变背景，使角色移动 ->","completion":" “when backdrop switches to [Mountain]\",\"go to x: [80] y: [-100]\",\"show\"\n"}
{"prompt":"点击绿旗，使角色跳舞 ->","completion":" “when green flag clicked\",“switch costume to [Ten80 top R step]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top L step]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top freeze]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top R cross]\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，重复播放音乐 ->","completion":" “when green flag clicked\",“repeat [10]\",\"play sound [Dance Celebrate] until done\"\n"}
{"prompt":"点击绿旗，跳舞完成后说话 ->","completion":" “when green flag clicked\",“switch costume to [anina top L step]\",\"wait [0.3] seconds\",“switch costume to [anina top R step]\",\"wait [0.3] seconds\",“switch costume to [anina stance]\",\"broadcast [message1]\"\n"}
{"prompt":"角色收到信息，回复并跳舞 ->","completion":" \"when i receive [message1]\",\"say [My turn to dance!] for [1] seconds\",\"repeat [4]\",\"next costume\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，设置角色初始位置 ->","completion":" “when green flag clicked\",\"go to x: [-10] y: [20]\",\"set size to [90] %\",\"switch costume to [lb stance]\",\"show\"\n"}
{"prompt":"点击绿旗，角色变成阴影效果 ->","completion":" “when green flag clicked\",“set [brightness] effect to [-100]\",\"forever\",\"next costume\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击箭头按钮，改变角色动作 ->","completion":" “when [left arrow] key pressed\",\"switch costume to [jo pop left]\"\n"}
{"prompt":"点击箭头按钮，改变角色动作 ->","completion":" “when [down arrow] key pressed\",\"switch costume to [jo pop down]\"\n"}
{"prompt":"点击空格键，使角色跳跃 ->","completion":" “when [space] key pressed\",\"repeat [10]\",\"change y by [10]\",“repeat [10]\",\"change y by [-10]\"\n"}
{"prompt":"点击绿旗，移动障碍物 ->","completion":" “when green flag clicked\",“forever”，\"go to x: [240] y: [-145]\"，“glide [3] secs to x: [-240] y: [-145]\"\n"}
{"prompt":"点击绿旗，使角色说话 ->","completion":" “when green flag clicked\",\"go to x: [-50] y: [60]\",\"say [My name is Kiki!] for [2] seconds\"\n"}
{"prompt":"点击角色，播放音效，使角色动起来 ->","completion":" “when [space] key pressed\",“start sound [Chirp]\",\"repeat [4]\",“switch costume to [monkey-a]\",\"wait [0.2] seconds\",“switch costume to [monkey-b]\",\"wait [0.2] seconds\"\n"}
{"prompt":"点击角色，改变状态 ->","completion":" “when the sprite clicked\",\"go to [front] layer\",\"broadcast [drink]\",\"wait [1] seconds\",\"switch costume to [glass water-b]\",start sound [Water Drop]\",\"wait [1] seconds\",\"switch costume to [glass water-a]\"\n"}
{"prompt":"角色收到信息，进行喂水，回到原位 ->","completion":" \"when i receive [drink]\",“glide [1] secs to [Glass water]\",\"wait [1] seconds\",“glide [1] secs to x: [-50] y: [60]\"\n"}
{"prompt":"点击小球，播放音乐，并跳动 ->","completion":" “when the sprite clicked\",\"go to [front] layer\",\"broadcast [play]\",\"wait until touching [Monkey] ?\",\"start sound [Boing]\",\"repeat [10]\",\"change by [-5]\",\"repeat [10]\",\"change by [5]\"\n"}
{"prompt":"点击绿旗，让角色到舞台顶端 ->","completion":" “when green flag clicked\",“go to [random position]\",\"set y to [180]\"\n"}
"""
PROMPT_NEW = json.load(open("./scratch_prompt.json", "r"))
code_prompt = """
    Please provide well-structured Scratch code according to the user's needs. Make sure that the generated code block can be parsed correctly by the Scratch software.
    
    Scratch blocks: 
        askandwait
        backdropnumbername
        control_create_clone_of
        control_delete_this_clone
        control_forever
        control_if_else
        control_if
        control_repeat
        control_start_as_clone
        control_stop
        control_wait
        costumenumbername
        current
        data_addtolist
        data_changevariableby
        data_deletealloflist
        data_deleteoflist
        data_hidelist
        data_hidevariable
        data_insertatlist
        data_itemnumoflist
        data_itemoflist
        data_lengthoflist
        data_listcontainsitem
        data_lists
        data_replaceitemoflist
        data_setvariableto
        data_showlist
        data_showvariable
        data_variable
        direction
        event_broadcastandwait
        event_broadcast
        event_whenbackdropswitchesto
        event_whenbroadcastreceived
        event_whenflagclicked
        event_whengreaterthan
        event_whenkeypressed
        event_whenthisspriteclicked
        looks_changeeffectby
        looks_changesizeby
        looks_cleargraphiceffects
        looks_goforwardbackwardlayers
        looks_gotofrontback
        looks_hide
        looks_nextbackdrop
        looks_nextcostume
        looks_sayforsecs
        looks_say
        looks_seteffectto
        looks_setsizeto
        looks_show
        looks_switchbackdropto
        looks_switchcostumeto
        looks_thinkforsecs
        looks_think
        loudness
        motion_changexby
        motion_changeyby
        motion_glidesecstoxy
        motion_glideto
        motion_gotoxy
        motion_goto
        motion_ifonedgebounce
        motion_movesteps
        motion_pointindirection
        motion_pointtowards
        motion_setrotationstyle
        motion_setx
        motion_sety
        motion_turnleft
        motion_turnright
        my variable
        of
        operator_add
        operator_and
        operator_contains
        operator_divide
        operator_equals
        operator_gt
        operator_join
        operator_length_of
        operator_letter_of
        operator_lt
        operator_mathop
        operator_mod
        operator_multiply
        operator_not
        operator_or
        operator_random
        operator_round
        operator_subtract
        repeat_until
        sensing_colortouchingcolor
        sensing_daysince2000
        sensing_distanceto
        sensing_keypressed
        sensing_mousedown
        sensing_mousex
        sensing_mousey
        sensing_resettimer
        sensing_setdragmode
        sensing_touchingcolor
        sensing_touchingobject
        size
        sound_changeeffectby
        sound_changevolumeby
        sound_clearsoundeffects
        sound_playuntildone
        sound_play
        sound_seteffectto
        sound_setvolumeto
        sound_stopallsounds
        timer
        username
        wait_until
        x_position
        y_position

    Here is an example:
    {{
        "code": [{{'block_type': 'event_whenflagclicked', 'arguments': {{}}}}, {{'block_type': 'control_forever', 'arguments': {{}}}}, {{'block_type': 'control_if', 'arguments': {{'condition': {{'block_type': 'sensing_touchingobject', 'arguments': {{'object': '障碍物'}}}}, {{'block_type': 'looks_seteffectto', 'arguments': {{'effect': 'color', 'value': 100}}, {{'block_type': 'operator_subtract', 'arguments': {{'NUM1': {{'block_type': 'sensing_of', 'arguments': {{'property': 'score', 'object': 'Stage'}}, 'NUM2': 1}}]
    }}
    
    User input: {user_input}
    No need to write down the reasoning process, just tell me the final result. The return format is JSON format:
        {{
            "code": "$block_type"
        }}
"""

def chatgpt_extract_code(text):
    code_agent = []
    code_agent.append({
        "role":
        "user",
        "content":
        f"""
        Solve a question answering task with interleaving Thought. Extract the code contained within question.
        Here are some examples.
        Question:['when green flag clicked', 'forever', 'go to x: (pick random [-240] to [240]) y: (pick random [-180] to [180])', 'wait [1] seconds']
        Answer:["when green flag clicked","forever","go to x: (pick random [-240] to [240]) y: (pick random [-180] to [180])","wait [1] seconds"]
        Question:['when green flag clicked', 'switch backdrop to [Savanna]', 'wait [2] seconds', 'switch backdrop to [Metro]']
        Answer:["when green flag clicked","switch backdrop to [Savanna]","wait [2] seconds","switch backdrop to [Metro]"]
        Question:{text}
        """
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=code_agent,
                                         temperature=0)
    print(agent_reply, type(agent_reply))
    # agent_reply = json.loads(agent_reply)["code"]
    agent_reply = extract_answer_content_to_list(agent_reply)
    print('agent_reply agagin: ', agent_reply)
    if isinstance(agent_reply, list):
        print('sure, a list')
        return agent_reply
    elif isinstance(agent_reply, str):
        return agent_reply.splitlines()
    else:
        return f"{agent_reply},Not valid:{type(agent_reply)}, please check the content"


def extract_code(text):
    code_blocks = re.findall(r"```([^`]+)```", text, re.DOTALL)
    extracted_code = []

    for code_block in code_blocks:
        lines = code_block.strip('`').split('\n')
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                extracted_code.append(line.strip())

    return extracted_code


def extract_keywords(s) -> List:
    code_lines = extract_code(s)
    # 删除所有的","
    s = s.replace('",', '')
    # 使用""来分割字符串
    arr = s.split("\"")
    # 用于保存关键词的列表
    keywords = []
    # 遍历列表，把非空的子字符串（即关键词）存入keywords列表
    for i in arr:
        if i.strip() != '':
            keywords.append(i.strip())
    return keywords


def test():
    s = '"when green flag clicked","say [你追我啊] for [2] seconds","repeat until <touching [rabbit]>","move [10] steps","end","play sound [Boing] until done"'
    keywords = extract_keywords(s)
    print(keywords)


def cal_similarity(reply_list, blocks):
    def extract_block_types(data):
        block_types = []
        for block in data:
            block_types.append(block['block_type'])
            if 'substack' in block:
                block_types.extend(extract_block_types(block['substack']))
            if 'arguments' in block:
                for arg in block['arguments'].values():
                    if isinstance(arg, dict) and 'block_type' in arg:
                        block_types.extend(extract_block_types([arg]))
        return block_types
    # 计算相似度
    block_list = []
    reply_list = extract_block_types(reply_list)
    for str in reply_list:
        if str == "end" or str == "else":
            continue
        if "wait" in str and "second" in str:
            block_list.append("control_wait")
            continue
        if "if" in str:
            block_list.append("control_if_else")
            continue
        if "turn" in str:
            block_list.append("motion_turnleft")
            continue
        similarity, max_similarity = 0, 0
        temp_block = ""
        for value in asdict(blocks).values():
            similarity = [lv.ratio(str, v) for v in value]
            max_value = max(similarity)
            max_index = similarity.index(max_value)
            block_by_index = list(value.items())[max_index][1]
            # similarity = lv.ratio(str, value)
            if max_value > max_similarity:
                max_similarity = max_value
                temp_block = block_by_index
                # print('Similarity is', max_similarity, value)
        block_list.append(temp_block)
    # print('this is the list I find: ', block_list)
    return block_list


class GPTFineTuned:

    def __init__(self, model_id) -> None:
        self.model_id = model_id

    def code_generation(self, user_message):
        response = client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system",
                    "content": "You are a Scratch programming expert."},
                {"role": "user", "content": user_message}
            ]
        )
        return re.findall(r'\"(.*?)\"', response.choices[0].message.content)


def generate_code_step(content, steps):
    '''
    使用哪些模块（Motion,Looks,Sound,Events,Control,Sensing,Operators,Variables）
    运动、外观、声音、事件、控制、侦测、运算、变量
    '''
    code_agent = []
    code_agent2 = []
    if steps == "step1":
        code_agent.append({
            "role":
            "user",
            "content":
            f"""
            Solve a question answering task with interleaving Thought. Please select the answer from the Scratch 3.0 categories below: Motion,Looks,Sound,Events,Control,Sensing,Operators,Variables.
            Here are some examples.
            Question:How do I make a character walk from sitting to right?
            Answer:Use Motion to control character movement, Looks to switch character actions, and Control to repeat execution.
            Question:How do I use the keyboard to control my character's movement?
            Answer:Use Motion to control character movement and Events to detect keyboard input.
            Question:{content}
            """
        })
        step1 = create_chat_completion(model=MODEL,
                                       messages=code_agent,
                                       temperature=0)
        return step1
    elif steps == "step2":
        # gpt_tuned = GPTFineTuned("ft:gpt-3.5-turbo-0613:personal::8HnuPdtX")
        code_agent2.append({
            "role":
            "user",
            "content":
            code_prompt.format(user_input=content)
        })
        step2 = create_chat_completion(model=MODEL,
                                       messages=code_agent2,
                                       temperature=0)
        return step2


def chatgpt_extract_step1(text):
    code_agent = []
    code_agent.append({
        "role":
        "user",
        "content":
        f"""Solve a question answering task with interleaving Thought. Please select the answer from the Scratch 3.0 categories below: Motion,Looks,Sound,Events,Control,Sensing,Operators,Variables.
        Here are some examples. 
        Question:使用Motion来控制角色移动，使用Operators生成随机数，以及使用Control来重复执行。
        Answer:["Motion", "Operators", "Control"]
        Question:使用Looks来切换场景，使用Variables创建变量，以及使用Events来广播消息。
        Answer:"Looks", "Variables", "Events"]
        Question:{text}
        """
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=code_agent,
                                         temperature=0)
    print("chatgpt_extract_step1", agent_reply)
    agent_reply = extract_answer_content_to_list(agent_reply)
    if isinstance(agent_reply, list):
        return ["scratchCategoryId-"+reply.lower() for reply in agent_reply]
    elif isinstance(agent_reply, str):
        return ["scratchCategoryId-"+agent_reply.lower()]
    else:
        print(f"Not valid:{type(agent_reply)}, please check the content")


def chatgpt_extract_step2(step2):
    motion_blocks = MotionBlocks()
    looks_blocks = LooksBlocks()
    sound_blocks = SoundBlocks()
    events_blocks = EventsBlocks()
    control_blocks = ControlBlocks()
    sensing_blocks = SensingBlocks()
    ass_block = AssembleBlocks(motion_blocks, looks_blocks, sound_blocks,
                               events_blocks, control_blocks, sensing_blocks)
    extracted_reply = chatgpt_extract_code(step2)
    block_list = cal_similarity(extracted_reply, ass_block)
    block_list = [block for block in block_list if block]
    return block_list


if __name__ == "__main__":
    motion_blocks = MotionBlocks()
    looks_blocks = LooksBlocks()
    sound_blocks = SoundBlocks()
    events_blocks = EventsBlocks()
    control_blocks = ControlBlocks()
    sensing_blocks = SensingBlocks()
    ass_block = AssembleBlocks(motion_blocks, looks_blocks, sound_blocks,
                               events_blocks, control_blocks, sensing_blocks)
    block_list = cal_similarity("when the kitten successfully catches a fish", ass_block)
    block_list = [block for block in block_list if block]
    print(block_list)
