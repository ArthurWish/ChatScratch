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

    def add(self, act, key,  id,  value):
        id = int(id)
        if id < len(self.acts[act][key]):
            self.acts[act][key][id] = value
        else:
            self.acts[act][key].append(value)
        self.print_act(act)

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
        print("get_act", act_name, key)
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
        # total settings
        str1 = f"""You are a story writer and children are working on a story in three acts, each of which contains three parts: characters, scenes and events."""
        if part_id == 1:
            str2 = f'Previously in Act 1.'
            if askterm == 'role':
                role = self.get_act('1', 'role')
                str3 = f'In Act 1,'
                if role == []:
                    str4 = 'Please provide four characters for me to use in my artwork, not exceeding 100 words, in Chinese.'
                else:
                    str4 = f'I have the {role} role. Please provide four related roles for illustration purposes. Provide descriptions of the roles without mentioning {role}. No more than 100 words, in Chinese'
            elif askterm == 'background':
                role = self.get_act('1', 'role')
                background = self.get_act('1', 'background')
                str3 = f'In Act 1, it has been established that the character is {role}.'
                if background == []:
                    str4 = f'Provide me with four scenaios that make sense in the story for me to draw, in no more than 100 words, in Chinese'
                else:
                    str4 = f'I have already drawn the scene: {background}. Could you please provide me with four scenarios related to the scene {background} for me to draw? Keep it under 100 words, in Chinese'
            else:
                role = self.get_act('1', 'role')
                background = self.get_act('1', 'background')
                str3 = f'In Act 1, the character has been identified as {role} and the scene as {background}.'
                str4 = 'Please give me four events that fit logically into the story for use in my drawing, in no more than 100 words, in Chinese'
        elif part_id == 2:
            act1 = self.get_act("1")
            role_act1 = self.get_act("1", "role")
            str2 = f"""The previously identified part is: Act 1, {act1}."""
            if askterm == 'role':
                role_act2 = self.get_act("2", "role")
                if role_act2 == []:
                    str3 = f'The role that already setting is {role_act1}.'
                else:
                    str3 = f'The roles that already exist are {role_act1+role_act2}.'
                str4 = f'According to these established characters, provide me with four fitting characters for the story logic, which I can draw and use.'
            elif askterm == 'background':
                role_act2 = self.get_act('2', 'role')
                background = self.get_act('2', 'background')
                str3 = f'In Act 2, the roles that already exist are {role_act1+role_act2}.'
                if background == []:
                    str4 = f'Based on Act 1, please give me four scenes that fit the logic of the story for use in my painting.'
                else:
                    str4 = f'I have drawn scene:{background}, can you please give four four scenes related to scene {background} for me to draw and use in no more than 100 words, in Chinese'
            else:
                role = self.get_act('2', 'role')
                background = self.get_act('2', 'background')
                str3 = f'In Act 2, the character has been identified as {role} and the scene as {background}.'
                str4 = f'Based on Act 1, please give me four events that fit logically into the story for me to use in my drawing.'
        elif part_id == 3:
            act1 = self.get_act("1")
            act2 = self.get_act("2")
            role_act1 = self.get_act("1", "role")
            role_act2 = self.get_act("2", "role")
            str2 = f"""The parts that have been previously identified are: Act 1, {act1} and Act 2, {act2}."""
            if askterm == 'role':
                role_act3 = self.get_act("3", "role")
                if role_act3 == []:
                    str3 = f'The established characters are:{role_act1+role_act2}'
                else:
                    str3 = f'The established characters are:{role_act1+role_act2+role_act3}.'
                str4 = f'Based on these characters, please give me four characters that fit logically into the story for me to draw and use.'
                
            elif askterm == 'background':
                role_act3 = self.get_act('3', 'role')
                background = self.get_act('3', 'background')
                str3 = f'The established characters are:{role_act1+role_act2+role_act3}.'
                if background == []:
                    str4 = f'Based on Act 1 and Act 2, give me four scenes that fit the logic of the story to use in my painting.'
                else:
                    str4 = f'Based on Act 1 and Act 2, and the scene {background} from Act 3, give me four scenes that fit the logic of the story to use in my painting.'
            else:
                role = self.get_act('3', 'role')
                background = self.get_act('3', 'background')
                str3 = f'In Act 3, the character has been identified as {role} and the scene as {background}.'
                str4 = 'Based on Acts 1 and 2, please give me four events that fit logically into the story for me to use in my drawing.'
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

    
