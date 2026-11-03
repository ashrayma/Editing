"""3D shots for "31 for 4", rendered with Blender EEVEE (bpy) on this machine.

    python3 shots3d.py <shot> [--frames a-b] [--res 1920x1080]
    shots: score314 | eight28 | days1020 | hero82 | ball | logo

Brand look: charcoal studio, theCricketLounge yellow (#FEDE5C) light, white type, a red accent for danger.
Helpers (studio, text, materials) come from the Centurion 2003 shots so both films share one 3D look.
"""
import importlib.util
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "c03", os.path.join(HERE, "..", "..", "doc_video", "blender", "shots3d.py"))
c03 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(c03)
reset, mat, text, load_font = c03.reset, c03.mat, c03.text, c03.load_font


def studio(sc, **kw):
    """Same studio as Centurion 2003, with a darker, rougher floor (no bright hotspot in the corner)."""
    cam = c03.studio(sc, **kw)
    for o in bpy.data.objects:
        if o.active_material and o.active_material.name.startswith("floor"):
            b = o.active_material.node_tree.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (0.006, 0.006, 0.007, 1)
            b.inputs["Roughness"].default_value = 0.85
            b.inputs["Metallic"].default_value = 0.0
    return cam
ease_out, ease_in_out, YELLOW, WHITE = c03.ease_out, c03.ease_in_out, c03.YELLOW, c03.WHITE
RED = (0.85, 0.04, 0.03)


def ease_back(x, s=1.7):
    x = max(0.0, min(1.0, x)) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def shot_score314(sc):
    """'31/4' slams down character by character, red-lit, camera drifting in; '7 OVERS' rises under it."""
    f_end = sc.frame_end
    font = load_font()
    red = mat("red", RED, rough=0.35, emit=4.0)
    white = mat("wht", WHITE, rough=0.3)
    cam = studio(sc, key=700, rim=900, cam_loc=(0, -11, 0.3), lens=45)
    chars = []
    for k, (ch, x) in enumerate([("3", -2.1), ("1", -0.85), ("/", 0.4), ("4", 1.75)]):
        chars.append(text(ch, size=2.5, extrude=0.35, bevel=0.03, m=red if ch != "/" else white,
                          loc=(x, 0, 6), font=font))
    sub = text("7 OVERS", size=0.55, extrude=0.05, m=white, loc=(0, 0, -2.6), font=load_font(False))

    def upd(scene, *_):
        f = scene.frame_current
        for k, c in enumerate(chars):
            x = ease_out((f - 3 - 5 * k) / 9)
            c.location.z = 0.0 + 7 * (1 - x)
            c.rotation_euler = (math.radians(90 + 25 * (1 - x)), 0, 0)
        y = ease_out((f - 32) / 14)
        sub.location.z = -2.2 + 0.4 * y
        sub.scale = (y + 1e-3,) * 3
        shake = 0.06 * max(0.0, 1 - ((f - 3) % 5) / 5) if f < 25 else 0
        cam.location = (shake, -11 + 2.0 * ease_in_out(f / f_end), 0.3 + shake)
        cam.rotation_euler = (math.radians(88), 0, math.radians(-2 + 4 * f / f_end))

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_eight28(sc):
    """Eight balls roll into an arc; the first four grey out (3 runs); '28' and 'OFF 8 BALLS' glow above."""
    f_end = sc.frame_end
    font = load_font()
    yellow = mat("yel", YELLOW, rough=0.3, emit=6.0)
    white = mat("wht", WHITE, rough=0.3)
    leather = mat("ball", (0.55, 0.02, 0.02), rough=0.35)
    grey = mat("grey", (0.08, 0.08, 0.09), rough=0.6)
    seam = mat("seam", (0.95, 0.92, 0.85), rough=0.5)
    cam = studio(sc, key=900, rim=700, cam_loc=(0, -12, 0.6), lens=40, floor_z=-1.5)
    num = text("28", size=2.6, extrude=0.3, bevel=0.03, m=yellow, loc=(0, 0, 1.75), font=font)
    lab = text("OFF 8 BALLS", size=0.55, extrude=0.05, m=white, loc=(0, 0, 0.2), font=load_font(False))
    balls = []
    for k in range(8):
        x = -3.85 + 1.1 * k
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, segments=48, ring_count=24, location=(x, 0, -1.05))
        b = bpy.context.object
        bpy.ops.object.shade_smooth()
        b.data.materials.append(leather)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.425, minor_radius=0.02, location=(x, 0, -1.05),
                                         rotation=(0, math.radians(90), 0))
        s = bpy.context.object
        s.data.materials.append(seam)
        s.parent = b
        s.matrix_parent_inverse = b.matrix_world.inverted()
        balls.append(b)

    def upd(scene, *_):
        f = scene.frame_current
        for k, b in enumerate(balls):
            x = ease_out((f - 2 - 3 * k) / 14)
            b.location.x = -3.85 + 1.1 * k + 9 * (1 - x)
            b.rotation_euler = (0, -6 * (1 - x), 0)
            b.active_material = grey if (k < 4 and f > 40 + 4 * k) else leather
        y = ease_back((f - 20) / 16)
        num.scale = (max(y, 1e-3),) * 3
        lab.scale = (max(ease_out((f - 30) / 12), 1e-3),) * 3
        cam.location = (0.8 * math.sin(f / f_end), -12 + 1.6 * ease_in_out(f / f_end), 0.6)
        cam.rotation_euler = (math.radians(88), 0, math.radians(-4 * math.sin(f / f_end)))

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_days1020(sc):
    """A flip counter runs 0 -> 1,020 on a dark slab; 'DAYS WITHOUT A CENTURY' underneath; cold grey light."""
    f_end = sc.frame_end
    font = load_font()
    white = mat("wht", (0.8, 0.8, 0.82), rough=0.3)
    red = mat("red", RED, rough=0.35, emit=3.0)
    slab = mat("slab", (0.02, 0.02, 0.025), metal=0.5, rough=0.3)
    cam = studio(sc, key=600, rim=500, cam_loc=(0, -12, 0.3), lens=45, floor_z=-1.9)
    tiles, digits = [], []
    for k in range(4):
        x = -2.4 + 1.6 * k
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0.25, 0.5))
        t = bpy.context.object
        t.scale = (1.4, 0.3, 2.0)
        t.data.materials.append(slab)
        bpy.ops.object.modifier_add(type="BEVEL")
        t.modifiers["Bevel"].width = 0.08
        t.modifiers["Bevel"].segments = 4
        tiles.append(t)
        digits.append(text("0", size=1.6, extrude=0.06, m=white, loc=(x, -0.02, -0.05), font=font))
    lab = text("DAYS WITHOUT A CENTURY", size=0.4, extrude=0.04, m=red, loc=(0, 0, -1.25), font=load_font(False))
    run_end = int(f_end * 0.72)

    def upd(scene, *_):
        f = scene.frame_current
        v = int(round(1020 * ease_in_out((f - 4) / (run_end - 4))))
        s = f"{v:04d}"
        for k, d in enumerate(digits):
            if d.data.body != s[k]:
                d.data.body = s[k]
            d.active_material = red if f >= run_end else white
        lab.scale = (max(ease_out((f - run_end + 4) / 12), 1e-3),) * 3
        cam.location = (0.3 * math.sin(f / f_end * 2), -12 + 1.4 * ease_in_out(f / f_end), 0.3)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_hero82(sc):
    """Gold '82*' rises out of the dark in a camera arc, a yellow line draws underneath."""
    f_end = sc.frame_end
    font = load_font()
    gold = mat("gold", (1.0, 0.72, 0.16), metal=0.85, rough=0.22, emit=0.6, emit_color=(1.0, 0.62, 0.1))
    yellow = mat("yel", YELLOW, rough=0.3, emit=8.0)
    white = mat("wht", WHITE, rough=0.3)
    cam = studio(sc, key=1200, rim=900, cam_loc=(0, -8, 0.4), lens=50)
    t = text("82*", size=2.6, extrude=0.35, bevel=0.03, m=gold, loc=(0, 0, -6), font=font)
    sub = text("OFF 53 BALLS", size=0.42, extrude=0.04, m=white, loc=(0, 0, -2.05), font=load_font(False))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.2, -1.5))
    line = bpy.context.object
    line.scale = (0.001, 0.03, 0.03)
    line.data.materials.append(yellow)

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out((f - 1) / (f_end * 0.45))
        t.location = (0, 0, -6 + 6.0 * x)
        t.rotation_euler = (math.radians(90), 0, math.radians(-22 * (1 - x) + 4 * ease_in_out(f / f_end)))
        line.scale = (2.6 * ease_out((f - f_end * 0.4) / (f_end * 0.3)) + 0.001, 0.03, 0.03)
        sub.scale = (max(ease_out((f - f_end * 0.5) / 12), 1e-3),) * 3
        a = 0.35 * (1 - f / f_end)
        cam.location = (8 * math.sin(a), -8 * math.cos(a) + 0.8 * ease_in_out(f / f_end), 0.4)
        cam.rotation_euler = (math.radians(88), 0, a)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_ball(sc):
    """A cricket ball spins toward the lens and fills the frame: a transition wipe into the cold open."""
    f_end = sc.frame_end
    leather = mat("ball", (0.6, 0.02, 0.02), rough=0.3)
    seam = mat("seam", (0.95, 0.92, 0.85), rough=0.5)
    cam = studio(sc, key=1000, rim=1200, cam_loc=(0, -10, 0), lens=50)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=(0, 30, 0))
    b = bpy.context.object
    bpy.ops.object.shade_smooth()
    b.data.materials.append(leather)
    for dx in (-0.03, 0.03):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.005, minor_radius=0.018, location=(0, 30, 0),
                                         rotation=(0, math.radians(90), 0))
        s = bpy.context.object
        s.location.x = dx
        s.data.materials.append(seam)
        s.parent = b
        s.matrix_parent_inverse = b.matrix_world.inverted()

    def upd(scene, *_):
        f = scene.frame_current
        x = (f - 1) / (f_end - 1)
        b.location = (0.6 * (1 - x), 30 - 39.2 * x ** 2.2, 0.2 * (1 - x))
        b.rotation_euler = (f * 0.55, 0.3, 0.2)

    bpy.app.handlers.frame_change_pre.append(upd)


SHOTS = {"score314": (shot_score314, 75), "eight28": (shot_eight28, 90), "days1020": (shot_days1020, 105),
         "hero82": (shot_hero82, 90), "ball": (shot_ball, 24), "logo": (c03.shot_logo, 75)}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    name = argv[0]
    fn, frames = SHOTS[name]
    res, fr = (1920, 1080), None
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
