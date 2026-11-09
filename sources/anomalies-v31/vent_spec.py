"""Shared hatch measurements. x is along the wall, y is up, z is into the hall."""
import math
from pathlib import Path
import sys


def parts(revision=5):
    rows=[]
    def part(name, p, size, rgb, moving=False, angle=0):
        rows.append((name,*p,*size,*rgb,moving,angle))

    body=(115,128,118)
    edge=(145,154,139)
    dark=(46,55,49)
    part("DuctShadow",(0,0,.031),(2,1.85,.042),(31,39,32))
    for y in (-.98,.98):
        part("Flange",(0,y,.067),(2.24,.17,.132),body)
        if revision>=2:
            part("InnerLip",(0,y*.896,.125),(1.96,.047,.10),edge)
    for x in (-1.037,1.037):
        part("Flange",(x,0,.067),(.17,1.86,.132),body)
        if revision>=2:
            part("InnerLip",(x*.91,0,.125),(.047,1.76,.10),edge)
    for x in (-.91,.91):
        part("HatchRail",(x,0,.17),(.085,1.70,.085),edge,True)
    for y in (-.81,.81):
        part("HatchRail",(0,y,.17),(1.75,.085,.085),edge,True)
    for i in range(7):
        part("Louver",(0,-.65+i*.214,.17),(1.75,.118,.048),
            (120+i*3,132+i*3,119+i*2),True,math.radians(-22))
        if revision>=3:
            part("SlatReturn",(0,-.683+i*.214,.193),(1.74,.019,.031),dark,True)
    if revision>=2:
        for x in (-1.017,1.017):
            for y in (-.81,0,.81):
                part("Fastener",(x,y,.14),(.048,.048,.021),(164,166,146))
                part("FastenerSlot",(x,y,.153),(.029,.007,.008),(63,69,57))
        for y in (-.6,.6):
            part("HingeBarrel",(-1.0,y,.174),(.106,.26,.095),dark)
            part("HingePin",(-1.0,y+.14,.174),(.076,.034,.072),edge)
    if revision>=4:
        part("Latch",(.985,-.02,.205),(.126,.24,.094),dark,True)
        part("LatchFace",(.985,-.02,.261),(.082,.142,.029),edge,True)
        part("Gasket",(0,-.89,.114),(1.88,.022,.035),dark)
    return rows


if __name__=="__main__":
    lines=["-- Exported from the shared Blender hatch dimensions.", "local ventParts = {"]
    for name,*spec in parts():
        fields=[f'"{name}"',*(str(value).lower() for value in spec)]
        lines.append("    {"+",".join(fields)+"},")
    lines.extend(("}",""))
    Path(sys.argv[1]).write_text("\n".join(lines))
