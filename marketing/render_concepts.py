"""Concept first-frames for the TikTok videos (product is the real print model).
   blender -b --factory-startup marketing_scenes.blend --python render_concepts.py -- [preview] [concept ...]
"""
import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREVIEW = "preview" in argv
WANT = [a for a in argv if a != "preview"]
OUT = os.path.join(os.path.dirname(os.path.abspath(bpy.data.filepath)), "concepts")
os.makedirs(OUT, exist_ok=True)

ns = {}
exec(open(os.path.join(os.path.dirname(os.path.abspath(bpy.data.filepath)), "render_shots.py")).read().split("use_gpu()\n")[0], ns)
ns["use_gpu"]()
BLUE, GREEN, RED = ns["COLOURS"]["blue"], ns["COLOURS"]["green"], ns["COLOURS"]["red"]
LED_ENERGY, LED_EMIT = ns["LED_ENERGY"], ns["LED_EMIT"]

DAY = {"MK_TopLED": 1.4, "MK_Fill": 0.12, "MK_Rim": 1.2, "MK_Caustics": 3.5e7, "MK_Key": 0.9e7, "CN_Moon": 0}
NIGHT = {"MK_TopLED": 0, "MK_Fill": 0.0, "MK_Rim": 0.0, "MK_Caustics": 0, "MK_Key": 0, "CN_Moon": 9.0e7}

CONCEPTS = {
    # name: camera, extra collections, led colour, led level, pixel level, lights, backdrop strength
    "1_warning_red": ("CN_CamRoom", ["CN_Room"], RED, 40.0, 0.6, NIGHT, 0.04),
    "2_aesthetic_tank": ("MK_CamVert", [], GREEN, 1.0, 1.0, DAY, 0.55),
    "4_asmr_macro": ("CN_CamMacro", ["CN_AsmrBubbles"], BLUE, 0.35, 0.03, DAY, 0.55),
    "6_shipwreck_theme": ("CN_CamWreck", ["CN_Wreck"], GREEN, 1.0, 1.0, DAY, 0.55),
}
HIDE = {"6_shipwreck_theme": ["MK_Rock0", "MK_Rock1"]}   # rocks that would hide the wreck
OPTIONAL = ["CN_Room", "CN_AsmrBubbles", "CN_Wreck"]


def apply(name):
    cam, extra, colour, level, pix, lights, backdrop = CONCEPTS[name]
    sc = bpy.data.scenes["Marketing"]
    sc.camera = bpy.data.objects[cam]
    for cname in OPTIONAL:
        for o in bpy.data.collections[cname].objects:
            if o is not None:   # Blender 5.2 can list empty slots here
                o.hide_render = cname not in extra
    for rock in ("MK_Rock0", "MK_Rock1"):
        bpy.data.objects[rock].hide_render = rock in HIDE.get(name, [])
    emit = bpy.data.materials["MK_LED"].node_tree.nodes["Emit"].inputs
    emit["Color"].default_value = (*colour, 1)
    emit["Strength"].default_value = LED_EMIT * pix
    led = bpy.data.objects["MK_LED_Light"].data
    led.color, led.energy = colour, LED_ENERGY * level
    for lname, energy in lights.items():
        if lname in bpy.data.objects:
            bpy.data.objects[lname].data.energy = energy
    bpy.data.materials["MK_Backdrop"].node_tree.nodes["Emission"].inputs["Strength"].default_value = backdrop
    return sc


for name in (WANT or CONCEPTS):
    sc = apply(name)
    sc.render.resolution_x, sc.render.resolution_y = (540, 960) if PREVIEW else (1440, 2560)
    sc.render.resolution_percentage = 100
    sc.cycles.samples = 24 if PREVIEW else 384
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.join(OUT, f"{name}{'_preview' if PREVIEW else ''}.png")
    t = time.time()
    bpy.ops.render.render(write_still=True, scene=sc.name)
    print(f"[concept] {name}: {time.time() - t:.0f}s", flush=True)
print("[concept] done", flush=True)
