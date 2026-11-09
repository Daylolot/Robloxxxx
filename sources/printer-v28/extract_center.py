"""Extract measured primitives around the printer from the saved office map."""
import json
import math
from pathlib import Path
import sys
import xml.parsers.expat

source, output = map(Path, sys.argv[1:])
parser = xml.parsers.expat.ParserCreate()
stack = []
parts = []
depth = 0
property = None
fields = {"Name", "CFrame", "size", "Size", "Color3uint8", "Transparency", "Material", "shape"}


def start(tag, attributes):
    global depth, property
    depth += 1
    if tag == "Item":
        stack.append({"class": attributes["class"], "name": "?", "props": {}})
    elif stack and property is None and attributes.get("name") in fields:
        property = {"name": attributes["name"], "depth": depth, "tag": tag,
                    "text": [], "values": {}, "field": None}
    elif property is not None and depth == property["depth"] + 1:
        property["field"] = tag
        property["fieldText"] = []


def data(text):
    if property is not None:
        property["fieldText" if property["field"] is not None else "text"].append(text)


def end(tag):
    global depth, property
    if property is not None:
        if property["field"] == tag and depth == property["depth"] + 1:
            property["values"][tag] = "".join(property["fieldText"])
            property["field"] = None
        elif depth == property["depth"] and tag == property["tag"]:
            value = property["values"] or "".join(property["text"])
            name = property["name"]
            stack[-1]["props"][name] = value
            if name == "Name":
                stack[-1]["name"] = value
            property = None
    if tag == "Item":
        item = stack.pop()
        parent_names = [node["name"] for node in stack]
        if item["class"] in {"Part", "WedgePart", "CornerWedgePart", "MeshPart"} and parent_names[:2] == ["Workspace", "OfficeMap"]:
            props = item["props"]
            cf = props.get("CFrame")
            size = props.get("size", props.get("Size"))
            if cf and size:
                center = [float(cf[k]) for k in "XYZ"]
                sizes = [float(size[k]) for k in "XYZ"]
                rotation = [float(cf[f"R{a}{b}"]) for a in range(3) for b in range(3)]
                extent = [sum(abs(rotation[3*a+b])*sizes[b] for b in range(3))/2 for a in range(3)]
                relevant = all(value+delta>=lower and value-delta<=upper for value,delta,lower,upper in
                               zip(center,extent,(1008,0,8),(1056,13,60)))
                transparency = float(props.get("Transparency", 0))
                if relevant and transparency < .98 and math.prod(sizes) > 0.000006:
                    group = "/".join(parent_names[2:5])
                    parts.append({"name":item["name"],"group":group,
                                  "cf":center+rotation,"size":sizes,
                                  "color":int(props.get("Color3uint8", 0xff888888))&0xffffff,
                                  "transparency":transparency,"material":int(props.get("Material",256)),
                                  "shape":int(props.get("shape",1)), "class":item["class"]})
    depth -= 1


parser.StartElementHandler = start
parser.CharacterDataHandler = data
parser.EndElementHandler = end
with source.open("rb") as stream:
    while chunk := stream.read(8*1024*1024):
        parser.Parse(chunk, False)
    parser.Parse(b"", True)
output.write_text(json.dumps(parts, separators=(",",":"))+"\n")
print(f"Extracted {len(parts)} parts to {output}")
