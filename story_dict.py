class StoryInfo:
    def __init__(self):
        self.acts = {
            '1': {
                'role': [],
                'background': [],
                'event': []
            },
            '2': {
                'role': [],
                'background': [],
                'event': []
            },
            '3': {
                'role': [],
                'background': [],
                'event': []
            }
        }

    def add(self, act, key, value):
        self.acts[act][key].append(value)

    def print_act(self, act_name, key=None):
        if act_name not in self.acts:
            print(f"No act named {act_name} found.")
            return
        act = self.acts[act_name]
        if key:
            if key not in act:
                print(f"No key named {key} found in act {act_name}.")
                return
            values = act[key]
            act_str = f"In Act {act_name}, the {key.title()} are:\n"
            for value in values:
                act_str += f"  - {value}\n"
        else:
            act_str = f"Act: {act_name}\n"
            for key, values in act.items():
                act_str += f"  {key.title()}:\n"
                for value in values:
                    act_str += f"    - {value}\n"
        print(act_str)

    def get_act(self, act_name, key=None):
        if act_name not in self.acts:
            print(f"No act named {act_name} found.")
            return
        act = self.acts[act_name]
        if not key:
            return act
        else:
            if key not in act:
                print(f"No key named {key} found in act {act_name}.")
                return
            values = act[key]
            return values
        
    def get_prompt(self, part_id, askterm):
        part_id = int(part_id)
        assert part_id == 1 or part_id == 2 or part_id == 3
        # act1 = self.print_act('act1')
        # act2 = self.print_act('act2')
        str1 = f"""你是一个辅助儿童完成故事的编剧，儿童正在创作一个包含三幕的故事，每一幕都包含人物、场景和事件三个部分。"""
        if part_id == 1:
            str2 = f'目前处于第1幕。'
            if askterm == 'role':
                str3 = f'在第1幕中,'
                str4 = '请你给出四种符合故事逻辑的角色描述供我选择。'
            elif askterm == 'background':
                role = self.get_act('act1', 'role')
                str3 = f'在第1幕中,已经确定了角色是{role}。'
                str4 = f'给出四种符合故事逻辑的场景描述供我选择。'
            else:
                role = self.get_act('act1', 'role')
                background = self.get_act('act1', 'background')
                str3 = f'在第1幕中,已经确定了角色是{role},场景是{background}。'
                str4 = '请你给出四种符合故事逻辑的事件描述供我选择。'
        elif part_id == 2:
            act1 = self.get_act("act1")
            str2 = f"""之前已经确认的部分是：第1幕，{act1}。"""
            if askterm == 'role':
                role_act1 = self.get_act("act1", "role")
                str3 = f'在第1幕中,已经存在的角色是{role_act1}。'
                str4 = f'根据第1幕，请你给出四种符合故事逻辑的角色描述供我选择。'
            elif askterm == 'background':
                role_act2 = self.get_act('act2', 'role')
                str3 = f'在第2幕中,已经确定了角色是{role_act2}。'
                str4 = f'根据第1幕，请你给出四种符合故事逻辑的场景描述供我选择。'
            else:
                role = self.get_act('act2', 'role')
                background = self.get_act('act2', 'background')
                str3 = f'在第2幕中,已经确定了角色是{role},场景是{background}。'
                str4 = f'根据第1幕，请你给出四种符合故事逻辑的事件描述供我选择。'
        elif part_id == 3:
            act1 = self.get_act("act1")
            act2 = self.get_act("act2")
            str2 = f"""之前已经确认的部分是：第1幕{act1}和第2幕{act2}。"""
            if askterm == 'role':
                role_act2 = self.get_act("act2", "role")
                str3 = f'在第2幕中,已经存在的角色是{role_act2}。'
                str4 = f'根据第1幕和第2幕，请你给出四种符合故事逻辑的角色描述供我选择。'
            elif askterm == 'background':
                role = self.get_act('act3', 'role')
                str3 = f'在第3幕中,已经确定了角色是{role}'
                str4 = f'根据第1幕和第2幕，请你给出四种符合故事逻辑的场景描述供我选择。'
            else:
                role = self.get_act('act3', 'role')
                background = self.get_act('act3', 'background')
                str3 = f'在第3幕中,已经确定了角色是{role},场景是{background}'
                str4 = '根据第1幕和第2幕，请你给出四种符合故事逻辑的事件描述供我选择。'
        content = str1 + str2 + str3 + str4
        return {"role": "user", "content": f"""{content}"""}

if __name__ == "__main__":
    from chat import create_chat_completion

    story_info = StoryInfo()
    story_memory = []
    story_info.add("1", "role", "兔子")
    story_info.add("1", "background", "森林")
    story_info.add("1", "event", "兔子在森林里面跑步")

    story_info.add("2", "role", "花儿")
    # story_info.add("act2", "role", "pig")

    story_info.add("2", "background", "小河边")
    # story_info.add("act2", "event", "事件")
    print(story_info.get_act("1"))
    print(story_info.get_act("1", "role"))
    # prompt = story_info.get_prompt("2", askterm="role")
    # print(prompt)
    prompt = story_info.get_prompt("2", askterm="event")
    print(prompt)
    # chat with ai
    story_memory.append(prompt)
    agent_reply = create_chat_completion(
        model="gpt-3.5-turbo",
        messages=story_memory,
    )
    print("agent: ", agent_reply)

    
