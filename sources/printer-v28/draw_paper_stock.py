"""Draw printable office forms for Blender, with no external image dependencies."""
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFont

out=Path(__file__).parent
font_path="/System/Library/Fonts/Supplemental/Arial.ttf"
header=ImageFont.truetype(font_path,27)
body=ImageFont.truetype(font_path,14)
titles=("УЧЁТ МАТЕРИАЛОВ","ЖУРНАЛ СМЕНЫ","СПИСОК ЗАДАЧ","ПЕРЕДАЧА ДОКУМЕНТОВ","ОТДЕЛ КАДРОВ")
for index,title in enumerate(titles,1):
    rng=Random(850+index)
    canvas=Image.new("RGB",(432,612),(244-index,242-index,231-index))
    draw=ImageDraw.Draw(canvas)
    dark=(70,79,78)
    mid=(113,124,121)
    faint=(172,177,168)
    draw.text((35,37),"КОНТУР / ВНУТРЕННЯЯ ФОРМА",fill=mid,font=body)
    draw.text((35,66),title,fill=dark,font=header)
    draw.line((35,105,397,105),fill=mid,width=2)
    for row in range(11):
        y=133+row*37
        draw.text((35,y),f"{row+1:02d}",fill=mid,font=body)
        x=78
        for _ in range(rng.randint(4,7)):
            length=rng.randint(11,37)
            draw.rounded_rectangle((x,y+5,x+length,y+8),radius=1,fill=mid)
            x+=length+rng.randint(6,12)
            if x>345:
                break
        if index%2 or row%2:
            draw.line((35,y+23,397,y+23),fill=faint,width=1)
    draw.line((272,556,397,556),fill=faint,width=2)
    draw.text((282,563),"ОТМЕТКА СМЕНЫ",fill=mid,font=body)
    canvas.save(out/f"page_{index}.png")
