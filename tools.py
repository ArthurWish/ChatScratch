import Levenshtein as lv
from block_types import *
from chat import create_chat_completion
import os
import hashlib
from wand.image import Image as wImage
import xml.etree.ElementTree as ET

MODEL = "gpt-3.5-turbo"


def init_code_agent():
    pass


def question_and_relpy(question):
    messages = []
    messages.append({"role": "user", "content": question})
    agent_reply = create_chat_completion(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    # messages.append({"role": "assistant", "content": agent_reply})
    return agent_reply


def chatgpt_extract_entity():
    pass


def split_to_parts(reply: str):
    lines = reply.split('\n')
    reply_list = []
    for line in lines:
        if line.strip():
            story = line.split('.', 1)[-1]  # 去掉编号部分
            reply_list.append(story)

    return reply_list


def toSVG(infile, outpath, temppath):
    with wImage(filename=infile) as img:
        img.format = 'svg'
        hash_object = hashlib.md5(img.make_blob())
        hex_dig = hash_object.hexdigest()
        outfile = os.path.join(outpath, f"{hex_dig}.svg")
        tempfile = os.path.join(temppath, f"{hex_dig}.svg")
        img.save(filename=outfile)
        img.save(filename=tempfile)


def Get_size(infile):
    tree = ET.parse(infile)
    root = tree.getroot()
    element_with_width = root.find(".//*[@width]")
    if element_with_width is not None:
        width = int(element_with_width.get('width'))
        height = int(element_with_width.get('height'))
        return width//2, height//2
    else:
        return 280, 280


def generate_js():
    backdrop_files = os.listdir('static/scene')
    costume_files = os.listdir('static/role')

    with open(r'c:\Users\YunNong\Desktop\scratch-gui\src\lib\default-project/index.js', 'w') as f:
        f.write('import projectData from \'./project-data\';\n')
        for i, file in enumerate(backdrop_files):
            f.write('import backdrop' + str(i + 1) +
                    ' from \'!raw-loader!./' + file + '\';\n')
        for i, file in enumerate(costume_files):
            f.write('import costume' + str(i + 1) +
                    ' from \'!raw-loader!./' + file + '\';\n')

        f.write('\nconst defaultProject = translator => {\n')
        f.write('let _TextEncoder;\n')
        f.write('if (typeof TextEncoder === \'undefined\') {\n')
        f.write('    _TextEncoder = require(\'text-encoding\').TextEncoder;\n')
        f.write('} else {\n')
        f.write('    _TextEncoder = TextEncoder;\n')
        f.write('}\n')
        f.write('const encoder = new _TextEncoder();\n\n')
        f.write('const projectJson = projectData(translator);\n\n')
        f.write('    return [{\n')
        f.write('        id: 0,\n')
        f.write('        assetType: \'Project\',\n')
        f.write('        dataFormat: \'JSON\',\n')
        f.write('        data: JSON.stringify(projectJson)\n')
        f.write('    },\n')

        for i, file in enumerate(backdrop_files):
            f.write('    {\n')
            f.write('        id: \'' + file.split('.')[0] + '\',\n')
            f.write('        assetType: \'ImageVector\',\n')
            f.write('        dataFormat: \'SVG\',\n')
            f.write('        data: encoder.encode(backdrop' + str(i + 1) + ')\n')
            f.write('    },\n')

        for i, file in enumerate(costume_files):
            f.write('    {\n')
            f.write('        id: \'' + file.split('.')[0] + '\',\n')
            f.write('        assetType: \'ImageVector\',\n')
            f.write('        dataFormat: \'SVG\',\n')
            f.write('        data: encoder.encode(costume' + str(i + 1) + ')\n')
            f.write('    },\n')

        f.write('];\n};\n\nexport default defaultProject;\n')


def generate_js_project():
    backdrop_files = os.listdir('static/scene')
    costume_files = os.listdir('static/role')

    with open(r'c:\Users\YunNong\Desktop\scratch-gui\src\lib\default-project\project-data.js', 'w') as f:
        f.write('import {defineMessages} from \'react-intl\';\n')
        f.write('import sharedMessages from \'../shared-messages\';\n\n')
        f.write('let messages = defineMessages({\n')
        f.write('    meow: {\n')
        f.write('        defaultMessage: \'Meow\',\n')
        f.write('        description: \'Name for the meow sound\',\n')
        f.write('        id: \'gui.defaultProject.meow\'\n')
        f.write('    },\n')
        f.write('    variable: {\n')
        f.write('        defaultMessage: \'my variable\',\n')
        f.write('        description: \'Name for the default variable\',\n')
        f.write('        id: \'gui.defaultProject.variable\'\n')
        f.write('    }\n')
        f.write('});\n\n')
        f.write('messages = {...messages, ...sharedMessages};\n\n')
        f.write('const defaultTranslator = msgObj => msgObj.defaultMessage;\n\n')

        f.write('/**\n')
        f.write(' * Generates the project data.\n')
        f.write(
            ' * @param {function} translateFunction - A function to translate the text in the project.\n')
        f.write(
            ' * @return {object} The project data with multiple targets each with its own properties.\n')
        f.write(' */\n')

        f.write('const projectData = translateFunction => {\n')
        f.write('    const translator = translateFunction || defaultTranslator;\n')
        f.write('    return ({\n')
        f.write('        targets: [\n')

        # for i, file in enumerate(backdrop_files):
        f.write('            {\n')
        f.write('                isStage: true,\n')
        f.write('                name: \'Stage\',\n')
        f.write('                variables: {\n')
        f.write(
            '                    \'`jEk@4|i[#Fk?(8x)AV.-my variable\': [\n')
        f.write('                        translator(messages.variable),\n')
        f.write('                        0\n')
        f.write('                    ]\n')
        f.write('                },\n')
        f.write('                lists: {},\n')
        f.write('                broadcasts: {},\n')
        f.write('                blocks: {},\n')
        f.write('                currentCostume: 0,\n')
        f.write('                costumes: [\n')
        for i, file in enumerate(backdrop_files):
            center_x, center_y = Get_size(os.path.join('static/scene', file))
            f.write('                    {\n')
            f.write('                        assetId: \'' +
                    file.split('.')[0] + '\',\n')
            f.write(
                '                        name: translator(messages.backdrop, {index: ' + str(i+1) + '}),\n')
            f.write('                        md5ext: \'' + file + '\',\n')
            f.write('                        dataFormat: \'svg\',\n')
            f.write(f'                        rotationCenterX: {center_x},\n')
            f.write(f'                        rotationCenterY: {center_y}\n')
            f.write('                    },\n')
        f.write('                ],\n')
        f.write('                sounds: [],\n')
        f.write('                volume: 100\n')
        f.write('            },\n')
        for i, file in enumerate(costume_files):
            center_x, center_y = Get_size(os.path.join('static/role', file))
            f.write('            {\n')
            f.write('                isStage: false,\n')
            f.write(
                '                name: translator(messages.sprite, {index: ' + str(i + 1) + '}),\n')
            f.write('                variables: {},\n')
            f.write('                lists: {},\n')
            f.write('                broadcasts: {},\n')
            f.write('                blocks: {},\n')
            f.write('                currentCostume: 0,\n')
            f.write('                costumes: [\n')

            f.write('                    {\n')
            f.write('                        assetId: \'' +
                    file.split('.')[0] + '\',\n')
            f.write(
                '                        name: translator(messages.costume, {index: ' + str(1) + '}),\n')
            f.write('                        bitmapResolution: 1,\n')
            f.write('                        md5ext: \'' + file + '\',\n')
            f.write('                        dataFormat: \'svg\',\n')
            f.write(f'                        rotationCenterX: {center_x},\n')
            f.write(f'                        rotationCenterY: {center_y}\n')
            f.write('                    },\n')
            f.write('                ],\n')
            f.write('                sounds: [],\n')
            f.write('                volume: 100,\n')
            f.write('                visible: true,\n')
            f.write('                x: 0,\n')
            f.write('                y: 0,\n')
            f.write('                size: 40,\n')
            f.write('                direction: 90,\n')
            f.write('                draggable: true,\n')
            f.write('                rotationStyle: \'all around\'\n')
            f.write('            },\n')

        f.write('        ],\n')
        f.write('        meta: {\n')
        f.write('            semver: \'3.0.0\',\n')
        f.write('            vm: \'0.1.0\',\n')
        f.write('            agent: \'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36\'\n')
        f.write('        }\n')
        f.write('    });\n')
        f.write('};\n\n')
        f.write('export default projectData;\n')


def translate_to_english(content):
    """将我给定的文本翻译为英文，只回答结果："""
    temp_memory = []
    temp_memory.append({
        "role":
        "user",
        "content":
        f"""将我给定的文本翻译为英文，只回答结果：{content}
    """
    })
    # print(temp_memory)
    return create_chat_completion(model=MODEL,
                                  messages=temp_memory,
                                  temperature=0)


def test():
    string = '1. 小明：一个勇敢的男孩，喜欢探险和冒险。他在森林里迷路了，正在寻找回家的路。\n2. 小芳：一个聪明的女孩，喜欢读书和学习。她在图书馆里发现了一本神秘的书，决定破解其中的谜题。\n3. 小华：一个善良的男孩，喜欢帮助别人。他在街上看到一个老奶奶摔倒了，决定去帮助她。\n4. 小玲：一个有想象力的女孩，喜欢画画和创作。她在花园里发现了一只神奇的小鸟，决定和它成为朋友。'
    c = split_to_parts(string)
    print(c)
    # print(c[0][0])
    # print(c[0][1])


if __name__ == "__main__":
    # test generate image and remove background
    # import requests
    # from io import BytesIO
    # prompt = refine_drawing_prompt(askterm="background", content="bear")
    # 需要明确角色的姿势或者动作
    # prompt = "very cute illustration for a children's Scratch project, a brown bear, Watercolor Painting, 4k, no background objects"
    # generate_image_to_image(
    #     prompt, base_image=r"C:\Users\YunNong\Desktop\bear.png")

    # with open('test.png', 'rb') as file:
    #     image_data = file.read()
    # url = 'http://10.73.3.223:3848/rm_bg'
    # # 发送 POST 请求
    # response = requests.post(url, files={'file': image_data}
    #                          )

    # # 检查响应
    # if response.status_code == 200:
    #     res_image = Image.open(BytesIO(response.content))
    #     res_image.save('test_bg.png')
    #     print('请求成功！')
    # else:
    #     print('请求失败！')
    # exit()
    # generate_draw(drawing_type="background", drawing_content="mountain", save_path="1.png")
    # generate_draw_with_dalle("Forest with running track at the end, featuring trees and a running track. Line art, anime, colored, child style.", "2-b")
    # generate_draw_with_stable(
    #     "Art Nouveau, enchanted forest, fairies dancing, intricate patterns and delicate curves, vibrant hues of emerald green and golden sunlight filtering through the trees",
    #     "1")
    # test()
    exit(0)
    agent_reply = '"when green flag clicked","say [你追我啊] for [2] seconds","repeat until <touching [rabbit]>","move [10] steps","end","play sound [Boing] until done"'
    extracted_reply = extract_keywords(agent_reply)
    print(extracted_reply)
    motion_blocks = MotionBlocks()
    looks_blocks = LooksBlocks()
    sound_blocks = SoundBlocks()
    events_blocks = EventsBlocks()
    control_blocks = ControlBlocks()
    sensing_blocks = SensingBlocks()
    ass_block = AssembleBlocks(motion_blocks, looks_blocks, sound_blocks,
                               events_blocks, control_blocks, sensing_blocks)
    block_list = cal_similarity(extracted_reply, ass_block)
    print(block_list)
