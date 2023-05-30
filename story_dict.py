class StoryInfo:
  def __init__(self):
    self.acts = {'act1':{'role':[],'background':[],'event':[]},'act2':{'role':[],'background':[],'event':[]}, 'act3':{'role':[],'background':[],'event':[]}}
    
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
      

      
  def get_prompt(self,id,askterm):
    act1 = self.print_act('act1')
    act2 = self.print_act('act2')
    
    cur = id+1
    next = cur+1
    str1 = f"""你是一个辅助儿童完成故事的编剧，儿童正在创作一个包含三幕的故事，每一幕都包含人物、场景和事件三个部分，目前处于第{cur}幕。"""
    if id ==0:
      str2 = '在第{next}幕中,'
      if askterm =='role':
        str3 = '在第{next}幕中,'
        str4 = '请你给出四种符合逻辑的角色描述供我选择。'
      elif askterm =='background':
        role = self.print_act('act1','role')
        str3 = '在第{next}幕中,已经确定了角色是{role}'
        str4 = '请你给出四种符合逻辑的场景描述供我选择。'
      else:
        role = self.print_act('act1','role')
        background =  self.print_act('act1','background')
        str3 = '在第{next}幕中,已经确定了角色是{role},场景是{background}'
        str4 = '请你给出四种符合逻辑的事件描述供我选择。'
    elif id ==1:
      str2 = f"""之前已经确认的部分是：第一幕{act1}。"""
      if askterm =='role':
        str3 = '在第{next}幕中,'
        str4 = '请你给出四种符合逻辑的角色描述供我选择。'
      elif askterm =='background':
        role = self.print_act('act2','role')
        str3 = '在第{next}幕中,已经确定了角色是{role}'
        str4 = '请你给出四种符合逻辑的场景描述供我选择。'
      else:
        role = self.print_act('act2','role')
        background =  self.print_act('act2','background')
        str3 = '在第{next}幕中,已经确定了角色是{role},场景是{background}'
        str4 = '请你给出四种符合逻辑的事件描述供我选择。'
    elif id ==2:
      str2 = f"""之前已经确认的部分是：第一幕{act1}和第二幕{act2}。"""
      if askterm =='role':
        str3 = '在第{next}幕中,'
        str4 = '请你给出四种符合逻辑的角色描述供我选择。'
      elif askterm =='background':
        role = self.print_act('act3','role')
        str3 = '在第{next}幕中,已经确定了角色是{role}'
        str4 = '请你给出四种符合逻辑的场景描述供我选择。'
      else:
        role = self.print_act('act3','role')
        background =  self.print_act('act3','background')
        str3 = '在第{next}幕中,已经确定了角色是{role},场景是{background}'
        str4 = '请你给出四种符合逻辑的事件描述供我选择。'
    content = str1+str2+str3+str4 
    return {
            "role":
            "user",
            "content":
            f"""{content}
            """
      }
    
       
    
   
  

    
    
  
