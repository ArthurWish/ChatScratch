# from https://github.com/danielgatis/rembg
# using this script need install the python module first.
from rembg import remove

# input_path = 'input.png'
# output_path = 'output.png'
def bg_remove(input_path, output_path):
    with open(input_path, 'rb') as i:
        with open(output_path, 'wb') as o:
            input = i.read()
            output = remove(input)
            o.write(output)
