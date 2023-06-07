import xml.etree.ElementTree as ET


def Get_size(infile):
    tree = ET.parse(infile)
    root = tree.getroot()
    element_with_width = root.find(".//*[@width]")
    if element_with_width is not None:
        width = int(element_with_width.get('width'))
        height = int(element_with_width.get('height'))
        return width,height
    else:
        return 500,500
    
print(Get_size('static/scene/0d551a530e6288f4df3b944f1a9ea6de.svg'))