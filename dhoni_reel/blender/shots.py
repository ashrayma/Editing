"""3D hero shots for "MS Dhoni: I didn't grow out of it", rendered with Blender (EEVEE), portrait.

    python3 shots.py <shot> [--res 720x1280] [--frames a-b]
    shots: seven | stumps | trophies | n91 | goat

Same studio as the other reels (charcoal, glossy floor, theCricketLounge yellow), reusing their helpers.
Each shot writes renders/<shot>/####.png at 30 fps; render.sh encodes them to mp4.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "records_reel", "blender"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "doc_video", "blender"))
from shots import back_out  # noqa: E402  (records_reel)
from shots3d import YELLOW, WHITE, ease_in_out, ease_out, load_font, mat, reset, studio, text  # noqa: E402

GOLD = (1.0, 0.66, 0.16)
SILVER = (0.8, 0.81, 0.83)


def lathe(profile, m, loc=(0, 0, 0), steps=96):
    """Solid of revolution from (radius, z) points around the Z axis."""
    me = bpy.data.meshes.new("lathe")
    verts = [(r, 0, z) for r, z in profile]
    me.from_pydata(verts, [(k, k + 1) for k in range(len(verts) - 1)], [])
    ob = bpy.data.objects.new("lathe", me)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    sc = ob.modifiers.new("screw", "SCREW")
    sc.angle, sc.steps, sc.render_steps, sc.axis = 2 * math.pi, steps, steps, "Z"
    sc.use_smooth_shade = True
    ob.data.materials.append(m)
    return ob


def shot_seven(sc):
    """The #7: a chunky yellow 7 swings round out of the dark, 'DHONI' slides in under it, light glints across."""
    f_end = sc.frame_end
    font = load_font()
    yel = mat("yel", YELLOW, metal=0.35, rough=0.22, emit=0.6)
    wht = mat("wht", WHITE, rough=0.3)
    cam = studio(sc, key=1200, rim=1100, cam_loc=(0, -11, 1.2), lens=38, floor_z=-2.4)
    seven = text("7", size=5.2, extrude=0.55, bevel=0.05, m=yel, loc=(0, 0, 1.4), font=font)
    name = text("DHONI", size=0.95, extrude=0.12, bevel=0.01, m=wht, loc=(0, -0.4, -1.55), font=font)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-6, -3.5, 1.0), rotation=(math.radians(90), math.radians(25), 0))
    sweep = bpy.context.object
    sweep.scale = (0.5, 7, 1)
    sweep.data.materials.append(mat("sweep", (1, 0.95, 0.8), emit=14.0))
    sweep.visible_camera = False

    def upd(scene, *_):
        f = scene.frame_current
        x = back_out((f - 1) / (f_end * 0.5), 1.1)
        seven.location = (0, 6 * (1 - x), 1.4)
        seven.rotation_euler = (math.radians(90), 0, math.radians(-170 * (1 - ease_out((f - 1) / (f_end * 0.55)))))
        y = ease_out((f - f_end * 0.35) / (f_end * 0.35))
        name.location = (0, -0.4, -1.55 - 1.2 * (1 - y))
        name.scale = (max(0.001, y),) * 3
        sweep.location.x = -6 + 12 * ease_in_out((f - f_end * 0.45) / (f_end * 0.45))
        cam.location = (0.3 * math.sin(f / f_end), -11 + 1.5 * ease_in_out(f / f_end), 1.2)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_stumps(sc):
    """Stumping: three stumps under a low camera, the bails pop off spinning in slow motion, LED bails flash."""
    f_end = sc.frame_end
    wood = mat("wood", (0.85, 0.78, 0.62), rough=0.35)
    led = mat("led", (1.0, 0.12, 0.08), rough=0.3, emit=0.001, emit_color=(1.0, 0.08, 0.04))
    cam = studio(sc, key=1000, rim=1300, cam_loc=(0.6, -6.5, 0.6), lens=42, floor_z=-2.2)
    cam.rotation_euler = (math.radians(86), 0, math.radians(5))
    for x in (-0.42, 0, 0.42):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.085, depth=3.4, location=(x, 0, -0.5))
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(wood)
    bails = []
    for x in (-0.21, 0.21):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.045, depth=0.46, location=(x, 0, 1.25),
                                            rotation=(0, math.radians(90), 0))
        bpy.ops.object.shade_smooth()
        b = bpy.context.object
        b.data.materials.append(led)
        bails.append(b)
    hit = int(f_end * 0.22)
    em = led.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]

    def upd(scene, *_):
        f = scene.frame_current
        t = max(0, f - hit) / 30.0 * 0.35  # slow motion after the hit
        for k, b in enumerate(bails):
            d = -1 if k == 0 else 1
            b.location = (d * (0.21 + 1.6 * t), -0.9 * t, 1.25 + 3.2 * t - 4.9 * t * t)
            b.rotation_euler = (math.radians(260 * t * (k + 1)), math.radians(90 + 400 * t * d), 0)
        em.default_value = 0.0 if f < hit else 14.0 * (0.6 + 0.4 * math.sin(f * 1.3))
        cam.location = (0.6 - 0.5 * ease_in_out(f / f_end), -6.5 + 1.2 * ease_in_out(f / f_end), 0.6)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_trophies(sc):
    """The three ICC white-ball trophies rise one after another on plinths: 2007, 2011, 2013."""
    f_end = sc.frame_end
    font = load_font()
    # half-metal so they read bright in a dark studio (pure metal only mirrors the black)
    gold = mat("gold", GOLD, metal=0.55, rough=0.2, emit=0.25)
    silver = mat("silver", SILVER, metal=0.7, rough=0.15, emit=0.03)
    dark = mat("dark", (0.03, 0.03, 0.035), metal=0.3, rough=0.3)
    yel = mat("yel", YELLOW, rough=0.3, emit=5.0)
    cam = studio(sc, key=2200, rim=1600, cam_loc=(0, -10.5, 1.1), lens=38, floor_z=-2.6)
    xs = (-1.62, 0, 1.62)
    # T20 World Cup: slim silver cup with a flared top
    t20 = lathe([(0, 0), (0.55, 0), (0.55, 0.25), (0.22, 0.4), (0.16, 1.6), (0.32, 2.4), (0.55, 3.0), (0.6, 3.15), (0, 3.15)], silver)
    # ODI World Cup: gold globe on a silver column cage
    odi = lathe([(0, 0), (0.6, 0), (0.6, 0.3), (0.3, 0.45), (0.38, 1.6), (0.52, 2.0), (0, 2.05)], silver)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.62, segments=64, ring_count=32)
    bpy.ops.object.shade_smooth()
    globe = bpy.context.object
    globe.data.materials.append(gold)
    globe.parent = odi
    globe.location = (0, 0, 2.6)
    # Champions Trophy: tall silver bowl, gold top
    ct = lathe([(0, 0), (0.55, 0), (0.55, 0.22), (0.25, 0.4), (0.3, 1.2), (0.55, 2.3), (0.62, 2.9), (0, 2.95)], silver)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, segments=48, ring_count=24)
    bpy.ops.object.shade_smooth()
    cap = bpy.context.object
    cap.data.materials.append(gold)
    cap.parent = ct
    cap.location = (0, 0, 3.15)
    cups = [t20, odi, ct]
    labels = []
    for x, yr in zip(xs, ("2007", "2011", "2013")):
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.66, depth=0.6, location=(x, 0, -2.3))
        bpy.context.object.data.materials.append(dark)
        labels.append(text(yr, size=0.48, extrude=0.06, m=yel, loc=(x, -0.9, -2.3), font=font))

    def upd(scene, *_):
        f = scene.frame_current
        for k, (c, lab) in enumerate(zip(cups, labels)):
            x = back_out((f - 4 - 9 * k) / (f_end * 0.35), 1.3)
            c.scale = (0.78, 0.78, 0.78)
            c.location = (xs[k], 0, -2.0 - 4.5 * (1 - x))
            c.rotation_euler = (0, 0, math.radians(120 * (1 - min(1, x)) + 12 * f / f_end))
            lab.scale = (max(0.001, min(1, x)),) * 3
        cam.location = (0.0, -10.5 + 1.4 * ease_in_out(f / f_end), 1.1 - 0.3 * ease_in_out(f / f_end))

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_n91(sc):
    """Gold 91* rising and turning to camera with a light sweep."""
    f_end = sc.frame_end
    font = load_font()
    gold = mat("gold", YELLOW, metal=0.6, rough=0.2, emit=0.4)
    cam = studio(sc, key=1300, rim=1000, cam_loc=(0, -11, 1.0), lens=40, floor_z=-2.0)
    n = text("91*", size=3.6, extrude=0.45, bevel=0.04, m=gold, font=font)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-6, -3.5, 1.0), rotation=(math.radians(90), math.radians(25), 0))
    sweep = bpy.context.object
    sweep.scale = (0.5, 7, 1)
    sweep.data.materials.append(mat("sweep", (1, 0.95, 0.8), emit=14.0))
    sweep.visible_camera = False

    def upd(scene, *_):
        f = scene.frame_current
        b = back_out((f - 1) / (f_end * 0.5), 1.3)
        n.location = (0, 0, -4 + 5.6 * b)
        n.rotation_euler = (math.radians(90 + 90 * (1 - min(1, b))), 0, math.radians(10 * (1 - b)))
        sweep.location.x = -6 + 12 * ease_in_out((f - f_end * 0.45) / (f_end * 0.45))
        cam.location = (0, -11 + 1.5 * ease_in_out(f / f_end), 1.0)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_goat(sc):
    """G . O . A . T . — each letter drops in from above and bounces, one after another."""
    f_end = sc.frame_end
    font = load_font()
    yel = mat("yel", YELLOW, metal=0.35, rough=0.22, emit=0.6)
    dot = mat("dot", YELLOW, rough=0.3, emit=7.0)
    cam = studio(sc, key=1200, rim=1000, cam_loc=(0, -12, 0.8), lens=38, floor_z=-1.4)
    xs = (-2.0, -0.62, 0.72, 2.02)
    letters = [text(ch, size=1.55, extrude=0.35, bevel=0.03, m=yel, loc=(x, 0, 0), font=font) for ch, x in zip("GOAT", xs)]
    dots = []
    for x in xs:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x + 0.62, -0.1, -0.52))
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(dot)
        dots.append(bpy.context.object)

    def upd(scene, *_):
        f = scene.frame_current
        for k, (l, d) in enumerate(zip(letters, dots)):
            x = back_out((f - 2 - 7 * k) / 16, 1.8)
            l.location = (xs[k], 0, 0.0 + 6 * (1 - x))
            l.rotation_euler = (math.radians(90), 0, math.radians(-20 * (1 - min(1, x))))
            y = back_out((f - 10 - 7 * k) / 10, 2.4)
            d.scale = (max(0.001, y),) * 3
        cam.location = (0, -12 + 1.4 * ease_in_out(f / f_end), 0.8)

    bpy.app.handlers.frame_change_pre.append(upd)


SHOTS = {"seven": (shot_seven, 54), "stumps": (shot_stumps, 60), "trophies": (shot_trophies, 72),
         "n91": (shot_n91, 48), "goat": (shot_goat, 60)}


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
