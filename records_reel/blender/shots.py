"""3D hero shots for "3 Records Kohli Owns", rendered with Blender (EEVEE), portrait.

    python3 shots.py <shot> [--res 720x1280] [--frames a-b]
    shots: num1 | num2 | num3 | ball | fifty | logo

Same studio look as the Centurion film (charcoal, glossy floor, theCricketLounge yellow #FEDE5C), reusing
its helpers. Each shot writes renders/<shot>/####.png at 30 fps; render.sh encodes them to mp4.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "doc_video", "blender"))
from shots3d import YELLOW, WHITE, ease_in_out, ease_out, load_font, mat, reset, studio, text  # noqa: E402


def back_out(x, s=1.6):
    x = max(0.0, min(1.0, x)) - 1
    return 1 + x * x * ((s + 1) * x + s)


def shot_num(digit):
    """Chapter number: a chunky yellow 'N.' spins in out of the dark, lands with a little overshoot,
    a light bar sweeps across it, the camera keeps drifting in."""
    def fn(sc):
        f_end = sc.frame_end
        font = load_font()
        yel = mat("yel", YELLOW, metal=0.35, rough=0.22, emit=0.6)
        dot = mat("dot", YELLOW, rough=0.3, emit=7.0)
        cam = studio(sc, key=1100, rim=900, cam_loc=(0, -10, 1.2), lens=38, floor_z=-1.9)
        n = text(digit, size=4.2, extrude=0.45, bevel=0.04, m=yel, loc=(0, 0, 0), font=font)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.36, location=(1.75, 0, -1.2), segments=48, ring_count=24)
        d = bpy.context.object
        d.data.materials.append(dot)
        bpy.ops.object.shade_smooth()
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-6, -3.5, 1.0), rotation=(math.radians(90), math.radians(25), 0))
        sweep = bpy.context.object
        sweep.scale = (0.5, 6, 1)
        sweep.data.materials.append(mat("sweep", (1, 0.95, 0.8), emit=14.0))
        sweep.visible_camera = False  # only shows up as a glint travelling across the glossy digit

        def upd(scene, *_):
            f = scene.frame_current
            x = back_out((f - 1) / (f_end * 0.5), 1.2)
            n.location = (-0.3, 9 * (1 - x), 1.4 - 0.4 * (1 - x))
            n.rotation_euler = (math.radians(90), 0, math.radians(-200 * (1 - ease_out((f - 1) / (f_end * 0.55)))))
            y = back_out((f - f_end * 0.35) / (f_end * 0.3), 2.2)
            d.scale = (max(0.001, y),) * 3
            d.location = (1.4, -0.2, 0.32)
            sweep.location.x = -6 + 12 * ease_in_out((f - f_end * 0.45) / (f_end * 0.45))
            cam.location = (0.25 * math.sin(f / f_end), -10 + 1.3 * ease_in_out(f / f_end), 1.2)
            cam.rotation_euler = (math.radians(89), 0, math.radians(-1.5 * math.sin(f / f_end)))

        bpy.app.handlers.frame_change_pre.append(upd)
    return fn


def shot_ball(sc):
    """Red leather ball with a raised seam, spinning hard toward camera and settling, yellow rim light."""
    f_end = sc.frame_end
    red = mat("leather", (0.32, 0.015, 0.02), rough=0.32)
    red.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.6
    seam = mat("seam", (0.78, 0.72, 0.6), rough=0.5)
    cam = studio(sc, key=900, rim=1400, cam_loc=(0, -9, 0.6), lens=45, floor_z=-2.2)
    bpy.ops.object.empty_add(location=(0, 0, 0.4))
    root = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=96, ring_count=48)
    ball = bpy.context.object
    bpy.ops.object.shade_smooth()
    ball.data.materials.append(red)
    ball.parent = root
    parts = [ball]
    for off, minor, m in ((0.0, 0.03, red), (0.07, 0.022, seam), (-0.07, 0.022, seam)):
        bpy.ops.mesh.primitive_torus_add(major_radius=math.sqrt(1 - off * off) + 0.005, minor_radius=minor,
                                         major_segments=160, minor_segments=12, location=(0, 0, off))
        t = bpy.context.object
        bpy.ops.object.shade_smooth()
        t.data.materials.append(m)
        t.parent = root
        parts.append(t)
    # stitches: little bumps along both stitch rows
    for row in (0.07, -0.07):
        r = math.sqrt(1 - row * row) + 0.02
        for i in range(70):
            a = 2 * math.pi * i / 70
            bpy.ops.mesh.primitive_cube_add(size=1, location=(r * math.cos(a), r * math.sin(a), row))
            s = bpy.context.object
            s.scale = (0.012, 0.035, 0.012)
            s.rotation_euler = (0, 0, a + math.radians(30 if row > 0 else -30))
            s.data.materials.append(seam)
            s.parent = root
    root.rotation_euler = (math.radians(15), math.radians(35), 0)

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out((f - 1) / (f_end * 0.6))
        root.location = (-1.8 * (1 - x), 16 * (1 - x), 0.4 + 2.2 * (1 - x))
        spin = 2200 * (1 - (1 - min(1, f / f_end)) ** 2.4) / 2.4
        root.rotation_euler = (math.radians(15 + 6 * math.sin(f / 6)), math.radians(35), math.radians(spin))
        cam.location = (0.3 * math.sin(f / f_end * 2), -9 + 1.0 * ease_in_out(f / f_end), 0.6)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_fifty(sc):
    """Silver 49 slides back and sinks; gold 50 flips up in front of it and takes the light."""
    f_end = sc.frame_end
    font = load_font()
    silver = mat("silver", (0.75, 0.76, 0.78), metal=1.0, rough=0.28)
    gold = mat("gold", YELLOW, metal=0.6, rough=0.2, emit=0.4)
    cam = studio(sc, key=1300, rim=1000, cam_loc=(0, -11, 1.0), lens=40, floor_z=-2.0)
    n49 = text("49", size=3.0, extrude=0.35, bevel=0.03, m=silver, font=font)
    n50 = text("50", size=3.6, extrude=0.45, bevel=0.04, m=gold, font=font)

    def upd(scene, *_):
        f = scene.frame_current
        a = ease_in_out((f - f_end * 0.15) / (f_end * 0.45))
        n49.location = (0, 0 + 5 * a, 1.6 - 3.6 * a)
        n49.rotation_euler = (math.radians(90 - 25 * a), 0, 0)
        b = back_out((f - f_end * 0.3) / (f_end * 0.45), 1.4)
        n50.location = (0, -1.5, -4 + 5.6 * b)
        n50.rotation_euler = (math.radians(90 + 90 * (1 - min(1, b))), 0, math.radians(8 * (1 - b)))
        cam.location = (0, -11 + 1.5 * ease_in_out(f / f_end), 1.0 + 0.3 * ease_in_out(f / f_end))

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_logo(sc):
    """theCricketLounge wordmark on a floating slab: yellow bar grows, wordmark wipes on, light sweep."""
    f_end = sc.frame_end
    cam = studio(sc, key=500, rim=400, cam_loc=(0, -9, 0.1), lens=42)
    img = bpy.data.images.load(os.path.join(HERE, "..", "..", "kohli_countdown", "assets", "logo.png"))
    m = bpy.data.materials.new("logo")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Emission Strength"].default_value = 2.4
    aspect = img.size[0] / img.size[1]
    bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.radians(90), 0, 0))
    plane = bpy.context.object
    w = 3.7
    plane.scale = (w, w / aspect, 1)
    plane.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-6, 0.3, 0))
    sweep = bpy.context.object
    sweep.scale = (0.2, 4, 1)
    sweep.rotation_euler = (math.radians(90), math.radians(20), 0)
    sweep.data.materials.append(mat("sweep", YELLOW, emit=3.0))

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out(f / (f_end * 0.6))
        plane.rotation_euler = (math.radians(90 - 20 * (1 - x)), 0, math.radians(-30 * (1 - x)))
        plane.location = (0, 2.0 * (1 - x), 0.4 * (1 - x))
        sweep.location.x = -5 + 10 * ease_in_out((f - f_end * 0.35) / (f_end * 0.5))
        cam.location = (0, -9 + 0.8 * ease_in_out(f / f_end), 0.1)

    bpy.app.handlers.frame_change_pre.append(upd)


SHOTS = {"num1": (shot_num("1"), 42), "num2": (shot_num("2"), 42), "num3": (shot_num("3"), 42),
         "ball": (shot_ball, 54), "fifty": (shot_fifty, 60), "logo": (shot_logo, 54)}


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
