"""3D shots for "AB de Villiers at World Cups", rendered with Blender (EEVEE), portrait.

    python3 shots.py <shot> [--res 720x1280] [--frames a-b]
    shots: avg | ducks | y2007 | y2011 | y2015 | trophy      (logo is reused from rohit_reel)
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "records_reel", "blender"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "doc_video", "blender"))
from shots import back_out  # noqa: E402
from shots3d import YELLOW, ease_in_out, ease_out, load_font, mat, reset, studio, text  # noqa: E402

GOLD = (1.0, 0.72, 0.22)


def clamp(x):
    return max(0.0, min(1.0, x))


def sweep_light(z=1.0):
    """An emissive bar out of camera that slides across: shows up as a glint over glossy type."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-6, -3.5, z), rotation=(math.radians(90), math.radians(25), 0))
    sw = bpy.context.object
    sw.scale = (0.5, 6, 1)
    sw.data.materials.append(mat("sweep", (1, 0.95, 0.8), emit=14.0))
    sw.visible_camera = False
    return sw


def shot_avg(sc):
    """'63.5': gold digits drop in one after another out of the dark, the camera pushing in; a glint sweeps
    across and an AVERAGE plate rises underneath."""
    f_end = sc.frame_end
    font = load_font()
    gold = mat("gold", GOLD, metal=0.85, rough=0.18, emit=0.25, emit_color=YELLOW)
    plate_m = mat("plate", (0.95, 0.95, 0.95), rough=0.35, emit=1.2)
    cam = studio(sc, key=1200, rim=1100, cam_loc=(0, -11, 0.9), lens=32, floor_z=-2.2)
    chars, xs = "63.5", (-1.6, -0.12, 0.8, 1.72)
    digs = [text(c, size=2.3, extrude=0.5, bevel=0.05, m=gold, loc=(x, 0, 1.0), font=font) for c, x in zip(chars, xs)]
    plate = text("WORLD CUP AVERAGE", size=0.46, extrude=0.06, bevel=0.01, m=plate_m, loc=(0, 0, -0.95), font=font)
    sw = sweep_light(1.1)

    def upd(scene, *_):
        f = scene.frame_current
        for k, d in enumerate(digs):
            x = back_out((f - 1 - 5 * k) / 16, 1.8)
            d.location = (xs[k], 0, 1.0 + 6 * (1 - x))
            d.rotation_euler = (math.radians(90 - 70 * (1 - clamp(x))), 0, 0)
            d.scale = (max(0.001, clamp(x * 1.4)),) * 3
        y = ease_out((f - 26) / 14)
        plate.location = (0, 0, -0.95 - 0.6 * (1 - y))
        plate.scale = (max(0.001, y),) * 3
        sw.location.x = -6 + 12 * ease_in_out((f - 28) / (f_end - 28))
        cam.location = (0.3 * math.sin(f / f_end * 2), -11 + 1.6 * ease_in_out(f / f_end), 0.9)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_ducks(sc):
    """Four ducks, then 146: four grey 0s thud down in a row, hold, then blow apart as a gold 146 punches
    through from behind them."""
    f_end = sc.frame_end
    font = load_font()
    grey = mat("grey", (0.32, 0.32, 0.35), metal=0.4, rough=0.35)
    gold = mat("gold", GOLD, metal=0.85, rough=0.18, emit=0.35, emit_color=YELLOW)
    cam = studio(sc, key=1100, rim=1200, cam_loc=(0, -11, 0.8), lens=32, floor_z=-2.2)
    xs = (-1.95, -0.65, 0.65, 1.95)
    zeros = [text("0", size=1.9, extrude=0.45, bevel=0.05, m=grey, loc=(x, 0, 0.9), font=font) for x in xs]
    big = text("146", size=3.4, extrude=0.6, bevel=0.06, m=gold, loc=(0, 2.5, 0.9), font=font)
    sw = sweep_light(1.0)
    burst = 34  # frame the 146 breaks through

    def upd(scene, *_):
        f = scene.frame_current
        for k, zr in enumerate(zeros):
            t0 = 1 + 5 * k
            x = back_out((f - t0) / 9, 1.4)
            if f < burst:
                zr.location = (xs[k], 0, 0.9 + 5 * (1 - x))
                zr.rotation_euler = (math.radians(90), 0, math.radians(8 * (k - 1.5) * (1 - clamp(x))))
                zr.scale = (max(0.001, clamp(x * 1.5)),) * 3
            else:
                u = (f - burst) / 12
                zr.location = (xs[k] * (1 + 2.2 * u), -3.5 * u, 0.9 + (2.5 - 1.2 * k % 3) * u - 3 * u * u)
                zr.rotation_euler = (math.radians(90 + 260 * u * (1 if k % 2 else -1)), math.radians(140 * u), 0)
                zr.scale = (max(0.001, 1 - u * 0.9),) * 3
        y = back_out((f - burst + 2) / 12, 1.5)
        big.location = (0, 2.5 - 2.5 * clamp(y), 0.9)
        big.scale = (max(0.001, clamp(y) * (0.4 + 0.6 * y)),) * 3
        sw.location.x = -6 + 12 * ease_in_out((f - burst - 4) / (f_end - burst - 4))
        shake = 0.08 * math.exp(-max(0, f - burst) / 4) if f >= burst else 0
        cam.location = (shake * math.sin(f * 3), -11 + 1.4 * ease_in_out(f / f_end), 0.8 + shake * math.cos(f * 4))

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_year(year):
    """Chapter title: a chunky yellow year slams forward out of the dark with a spin, glint, camera drift."""
    def fn(sc):
        f_end = sc.frame_end
        font = load_font()
        yel = mat("yel", YELLOW, metal=0.35, rough=0.22, emit=0.6)
        white = mat("wht", (0.95, 0.95, 0.95), rough=0.35, emit=1.0)
        cam = studio(sc, key=1100, rim=900, cam_loc=(0, -10, 1.0), lens=38, floor_z=-1.9)
        n = text(year, size=2.15, extrude=0.45, bevel=0.04, m=yel, loc=(0, 0, 1.2), font=font)
        sub = text("WORLD CUP", size=0.62, extrude=0.08, bevel=0.01, m=white, loc=(0, 0, -0.25), font=font)
        sw = sweep_light(1.2)

        def upd(scene, *_):
            f = scene.frame_current
            x = back_out((f - 1) / (f_end * 0.45), 1.2)
            n.location = (0, 9 * (1 - x), 1.2 - 0.4 * (1 - x))
            n.rotation_euler = (math.radians(90), math.radians(-120 * (1 - ease_out((f - 1) / (f_end * 0.5)))), 0)
            y = ease_out((f - f_end * 0.35) / (f_end * 0.3))
            sub.scale = (max(0.001, y),) * 3
            sub.location = (0, 0, -0.25 - 0.5 * (1 - y))
            sw.location.x = -6 + 12 * ease_in_out((f - f_end * 0.45) / (f_end * 0.5))
            cam.location = (0.25 * math.sin(f / f_end), -10 + 1.3 * ease_in_out(f / f_end), 1.0)
            cam.rotation_euler = (math.radians(89), 0, math.radians(-1.5 * math.sin(f / f_end)))

        bpy.app.handlers.frame_change_pre.append(upd)
    return fn


def shot_trophy(sc):
    """Out of reach: a gold trophy (stepped base, three twisting gold bands, a globe on top) turns on a plinth
    under a spotlight; the camera starts close then pulls back and the light slowly dims around it."""
    f_end = sc.frame_end
    gold = mat("tgold", GOLD, metal=1.0, rough=0.16)
    band = mat("tband", (0.08, 0.35, 0.12), metal=0.3, rough=0.3)
    plinth = mat("plinth", (0.03, 0.03, 0.035), rough=0.5)
    cam = studio(sc, key=700, rim=1400, cam_loc=(0, -6, 1.6), lens=50, floor_z=-1.6)
    bpy.ops.object.empty_add(location=(0, 0, -1.0))
    root = bpy.context.object
    parts = []

    def part(obj, m):
        bpy.ops.object.shade_smooth()
        obj.data.materials.append(m)
        obj.parent = root
        parts.append(obj)

    # base: two green bands between gold rings
    for z, r, h, m in ((0.0, 0.62, 0.12, gold), (0.15, 0.58, 0.16, band), (0.3, 0.55, 0.08, gold),
                       (0.42, 0.5, 0.15, band), (0.56, 0.46, 0.08, gold)):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=96, location=(0, 0, z))
        part(bpy.context.object, m)
    # the body: three twisting ribbons rising to hold the globe
    for k in range(3):
        a0 = k * 2 * math.pi / 3
        cu = bpy.data.curves.new(f"rib{k}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.085
        cu.bevel_resolution = 6
        cu.use_fill_caps = True
        sp = cu.splines.new("NURBS")
        n = 24
        sp.points.add(n - 1)
        for j in range(n):
            u = j / (n - 1)
            a = a0 + u * 1.9
            r = 0.38 - 0.18 * math.sin(math.pi * u) + 0.12 * u
            sp.points[j].co = (r * math.cos(a), r * math.sin(a), 0.6 + 1.65 * u, 1)
        sp.use_endpoint_u = True
        sp.order_u = 4
        ob = bpy.data.objects.new(f"rib{k}", cu)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(gold)
        ob.parent = root
        parts.append(ob)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=96, ring_count=48, location=(0, 0, 2.6))
    part(bpy.context.object, gold)
    # plinth
    bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=0.6, vertices=96, location=(0, 0, -1.3))
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(plinth)
    # spotlight from above
    bpy.ops.object.light_add(type="SPOT", location=(0, -1.0, 6.5))
    spot = bpy.context.object
    spot.data.energy = 2600
    spot.data.spot_size = math.radians(34)
    spot.data.spot_blend = 0.6
    spot.data.color = (1.0, 0.9, 0.7)
    spot.rotation_euler = (math.radians(9), 0, 0)
    lights = [o for o in bpy.data.objects if o.type == "LIGHT" and o is not spot]
    base_e = [l.data.energy for l in lights]

    def upd(scene, *_):
        f = scene.frame_current
        u = f / f_end
        root.rotation_euler = (0, 0, math.radians(-40 + 120 * u))
        p = ease_in_out(u)
        cam.location = (0, -6 - 7 * p, 1.6 + 0.9 * p)
        cam.rotation_euler = (math.radians(86 - 2 * p), 0, 0)
        cam.data.dof.focus_distance = 6 + 7 * p
        for l, e0 in zip(lights, base_e):
            l.data.energy = e0 * (1 - 0.75 * ease_in_out((u - 0.35) / 0.65))

    bpy.app.handlers.frame_change_pre.append(upd)


SHOTS = {"avg": (shot_avg, 54), "ducks": (shot_ducks, 66), "y2007": (shot_year("2007"), 42),
         "y2011": (shot_year("2011"), 42), "y2015": (shot_year("2015"), 42), "trophy": (shot_trophy, 96)}


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
