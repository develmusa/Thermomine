"""Render the marketing shots headless:
   blender -b --factory-startup marketing_scenes.blend --python render_shots.py
"""
import os
import time

import bpy

OUT = os.path.dirname(os.path.abspath(bpy.data.filepath))
# SHOTS_QUALITY=high: more samples, meant for the GPU machine
HIGH = os.environ.get("SHOTS_QUALITY") == "high"


def use_gpu():
    """Render on the first GPU backend Cycles finds; fall back to the CPU."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = backend
        except TypeError:
            continue
        prefs.refresh_devices()
        gpus = [d for d in prefs.devices if d.type == backend]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == backend
            for sc in bpy.data.scenes:
                sc.cycles.device = "GPU"
            print(f"[shots] GPU: {backend} {[d.name for d in gpus]}", flush=True)
            return
    print("[shots] no GPU, rendering on CPU", flush=True)
COLOURS = {
    "blue": (0.10, 0.38, 1.00),   # too cold
    "green": (0.15, 1.00, 0.35),  # in range
    "red": (1.00, 0.14, 0.05),    # too warm
}


LED_ENERGY = bpy.data.objects["MK_LED_Light"].data.energy
LED_EMIT = bpy.data.materials["MK_LED"].node_tree.nodes["Emit"].inputs["Strength"].default_value


def set_led(rgb, level=1.0):
    """level < 1 keeps the slots from clipping to white in close-ups."""
    emit = bpy.data.materials["MK_LED"].node_tree.nodes["Emit"].inputs
    emit["Color"].default_value = (*rgb, 1)
    # the pixel itself is seen straight through the centre slot; dim it harder so it keeps its colour
    emit["Strength"].default_value = LED_EMIT * level * (0.08 if level < 1 else 1.0)
    light = bpy.data.objects["MK_LED_Light"].data
    light.color = rgb
    light.energy = LED_ENERGY * level


def render(scene, camera, name, res, samples):
    sc = bpy.data.scenes[scene]
    sc.camera = bpy.data.objects[camera]
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.join(OUT, name)
    t = time.time()
    bpy.ops.render.render(write_still=True, scene=sc.name)
    print(f"[shots] {name}: {time.time() - t:.0f}s", flush=True)


use_gpu()
set_led(COLOURS["green"])
if HIGH:
    render("Packshot", "PS_Cam", "03_packshot_white.png", (2400, 2400), 512)
    render("Marketing", "MK_Cam", "01_hero_aquarium.png", (2400, 1500), 384)
    close = ((1200, 1500), 256)
else:
    render("Packshot", "PS_Cam", "03_packshot_white.png", (1600, 1600), 64)
    render("Marketing", "MK_Cam", "01_hero_aquarium.png", (1600, 1000), 48)
    close = ((800, 1000), 40)
for key in ("blue", "green", "red"):
    set_led(COLOURS[key], level=0.3)
    render("Marketing", "MK_CamClose", f"02_glance_{key}.png", *close)
print("[shots] done", flush=True)
