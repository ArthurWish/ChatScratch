import hashlib
import os
from PIL import Image

def toSVG(infile, outfile):
    image = Image.open(infile).convert('RGBA')
    data = image.load()
    width, height = image.size
    out = open(outfile, "w")
    out.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    out.write('<svg id="svg2" xmlns="http://www.w3.org/2000/svg" version="1.1" \
                width="%(x)i" height="%(y)i" viewBox="0 0 %(x)i %(y)i">\n' % \
              {'x': width, 'y': height})
    
    for y in range(height):
        for x in range(width):
            rgba = data[x, y]
            rgb = '#%02x%02x%02x' % rgba[:3]
            if rgba[3] > 0:
                out.write('<rect width="1" height="1" x="%i" y="%i" fill="%s" \
                    fill-opacity="%.2f" />\n' % (x, y, rgb, rgba[3]/255.0))
    out.write('</svg>\n')
    out.close()
    
toSVG('heart.jpeg', 'heart.svg')

def get_md5_hash_of_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            bytes = file.read() # 读取文件的内容，返回字节数据
            readable_hash = hashlib.md5(bytes).hexdigest() # 使用md5算法进行哈希，然后将结果转换为十六进制表示
            return readable_hash
    except Exception as e:
        print(f'无法打开文件: {file_path}')
        print(e)

def rename_file_based_on_hash(file_path):
    md5_hash = get_md5_hash_of_file(file_path)
    if md5_hash is not None:
        base = os.path.dirname(file_path)
        extension = os.path.splitext(file_path)[1]
        new_path = os.path.join(base, md5_hash + extension)
        os.rename(file_path, new_path)
        print(f'文件已经被重命名为: {new_path}')
    else:
        print('哈希值计算失败，文件没有被重命名。')

file_path = 'static/警车.svg' # 这里替换为你的图片文件的路径
rename_file_based_on_hash(file_path)
