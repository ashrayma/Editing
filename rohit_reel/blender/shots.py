"""3D shots for "Rohit Sharma is not from this planet", rendered with Blender (EEVEE), portrait.

    python3 shots.py <shot> [--res 720x1280] [--frames a-b]
    shots: num5 | num4 | six | planet       (num3/num2/num1 + logo are reused from records_reel)
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "records_reel", "blender"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "doc_video", "blender"))
from shots import back_out, shot_num  # noqa: E402  (records_reel: same chapter-number look)
from shots3d import YELLOW, ease_in_out, ease_out, mat, reset, studio  # noqa: E402


def make_ball(root):
    red = mat("leather", (0.32, 0.015, 0.02), rough=0.32)
    seam = mat("seam", (0.78, 0.72, 0.6), rough=0.5)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=96, ring_count=48)
    ball = bpy.context.object
    bpy.ops.object.shade_smooth()
    ball.data.materials.append(red)
    ball.parent = root
    for off, minor, m in ((0.0, 0.03, red), (0.07, 0.022, seam), (-0.07, 0.022, seam)):
        bpy.ops.mesh.primitive_torus_add(major_radius=math.sqrt(1 - off * off) + 0.005, minor_radius=minor,
                                         major_segments=160, minor_segments=12, location=(0, 0, off))
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        bpy.context.object.parent = root


def shot_six(sc):
    """The six: the ball rockets up from below through a floodlit night, a yellow light trail behind it,
    camera tilting up after it; floodlight towers flare as it passes."""
    f_end = sc.frame_end
    cam = studio(sc, key=1800, rim=2000, cam_loc=(0, -12, 0.0), lens=32, floor_z=-30)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    make_ball(root)
    root.scale = (0.75, 0.75, 0.75)
    # light trail: a chain of glowing spheres that follow the ball's path
    trail_m = mat("trail", YELLOW, rough=0.3, emit=9.0)
    trail = []
    for k in range(16):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22 * (1 - k / 18), segments=16, ring_count=8)
        t = bpy.context.object
        t.data.materials.append(trail_m)
        trail.append(t)
    # floodlight towers: emissive panels high left and right
    flood = mat("flood", (1, 0.97, 0.9), emit=30.0)
    for x in (-7.5, 7.5):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 6, 9))
        p = bpy.context.object
        p.scale = (1.6, 0.1, 0.9)
        p.data.materials.append(flood)

    def pos(f):
        u = max(0.0, (f - 1) / f_end)
        return (1.2 * u - 0.6, 8 * u, -9 + 22 * ease_out(u * 1.1))

    def upd(scene, *_):
        f = scene.frame_current
        root.location = pos(f)
        root.rotation_euler = (math.radians(25), math.radians(30), math.radians(f * 38))
        for k, t in enumerate(trail):
            t.location = pos(max(1, f - 0.7 * (k + 2.2)))
            t.scale = (1, 1, 1) if f - 0.7 * (k + 2.2) > 1 else (0.001,) * 3
        b = root.location
        cam.location = (0, -12, 0.0)
        aim = math.atan2(b.z - 0.0, b.y + 12)
        cam.rotation_euler = (math.radians(90) + 0.85 * aim, 0, 0)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_planet(sc):
    """'Not from this planet': a planet with a ring turns in the dark, a cricket ball orbits it like a moon."""
    f_end = sc.frame_end
    cam = studio(sc, key=700, rim=2200, cam_loc=(0, -13, 1.5), lens=40, floor_z=-40)
    body = mat("planet", (0.08, 0.1, 0.22), rough=0.45, emit=0.15, emit_color=(0.25, 0.35, 0.9))
    ring = mat("ring", YELLOW, rough=0.3, emit=4.0)
    # banded surface: noise between two blues
    nt = body.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.03, 0.05, 0.16, 1)
    ramp.color_ramp.elements[1].color = (0.22, 0.3, 0.75, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.6, segments=128, ring_count=64, location=(0, 0, 0.6))
    planet = bpy.context.object
    bpy.ops.object.shade_smooth()
    planet.data.materials.append(body)
    bpy.ops.mesh.primitive_torus_add(major_radius=2.6, minor_radius=0.05, major_segments=200, minor_segments=8,
                                     location=(0, 0, 0.6))
    hoop = bpy.context.object
    hoop.rotation_euler = (math.radians(14), math.radians(-16), 0)  # near edge-on to the camera
    hoop.data.materials.append(ring)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    moon = bpy.context.object
    make_ball(moon)
    moon.scale = (0.32, 0.32, 0.32)
    stars = mat("star", (1, 1, 1), emit=12.0)
    import random
    rnd = random.Random(4)
    for _ in range(120):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=rnd.uniform(0.015, 0.045), subdivisions=1,
                                              location=(rnd.uniform(-9, 9), rnd.uniform(6, 14), rnd.uniform(-10, 12)))
        bpy.context.object.data.materials.append(stars)

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out(f / (f_end * 0.5))
        planet.rotation_euler = (0, 0, math.radians(40 * f / f_end))
        planet.scale = (0.6 + 0.4 * x,) * 3
        hoop.scale = (0.4 + 0.6 * x,) * 3
        a = math.radians(-80 + 220 * f / f_end)
        moon.location = (2.9 * math.cos(a), -1.2 + 0.4 * math.sin(a), 0.6 + 1.4 * math.sin(a))
        moon.rotation_euler = (0, math.radians(f * 12), math.radians(f * 20))
        cam.location = (0, -13 + 2 * ease_in_out(f / f_end), 1.5)

    bpy.app.handlers.frame_change_pre.append(upd)


SHOTS = {"num5": (shot_num("5"), 42), "num4": (shot_num("4"), 42), "six": (shot_six, 48), "planet": (shot_planet, 66)}


def main():
    argv = sys.argv[1:]
    name = argv[0]
    fn, frames = SHOTS[name]
    res, fr = (720, 1280), None
    for i, a in enumerate(argv):
        if a == "--res":
            res = tuple(int(v) for v in argv[i + 1].split("x"))
        if a == "--frames":
            fr = tuple(int(v) for v in argv[i + 1].split("-"))
    sc = reset(frames, res)
    fn(sc)
    out = os.path.join(HERE, "renders", name)
    os.makedirs(out, exist_ok=True)
    a, b = fr or (1, frames)
    for f in range(a, b + 1):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, f"{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"FRAME {name} {f}/{frames}", flush=True)


if __name__ == "__main__":
    main()
