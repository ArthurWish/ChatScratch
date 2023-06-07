from wand.image import Image

with Image(filename="test.png") as img:
    img.format = 'svg'
    img.save(filename="output.svg")