class StoryInfo:
  def __init__(self):
    self.acts = {'act1':{'role':[],'background':[],'event':[]},'act2':{'role':[],'background':[],'event':[]}, 'act3':{'role':[],'background':[],'event':[]}}
    
  def add(self, act, key, value):
    self.acts[act][key].append(value)
  
  def __str__(self):
        story_str = ""
        for act_name, act in self.acts.items():
            story_str += f"Act: {act_name}\n"
            for key, values in act.items():
                story_str += f"  {key.title()}:\n"
                for value in values:
                    story_str += f"    - {value}\n"
        return story_str
    
    
  
