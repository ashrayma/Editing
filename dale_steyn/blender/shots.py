"""Vertical 3D shots for the Dale Steyn Short (Blender EEVEE): #2 reveal, 150 KM/H.

    python3 shots.py <shot> [--frames a-b] [--res 720x1280]
Reuses the studio, materials and type from kohli_mcg/blender/shots3d.py so the channel's 3D looks the same.
"""
import importlib.util
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("k", os.path.join(HERE, "..", "..", "kohli_mcg", "blender", "shots3d.py"))
k = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(k)
reset, mat, text, load_font, studio = k.reset, k.mat, k.text, k.load_font, k.studio
ease_out, ease_in_out, ease_back, YELLOW, WHITE, RED = k.ease_out, k.ease_in_out, k.ease_back, k.YELLOW, k.WHITE, k.RED


def vcam(cam):
    cam.data.sensor_fit = "VERTICAL"
    return cam


def shot_556(sc):
    """'556' slams down digit by digit in Australian gold-green light; 'AUSTRALIA' rises under it."""
    f_end = sc.frame_end
    gold = mat("gold", (1.0, 0.72, 0.16), metal=0.85, rough=0.22, emit=0.6, emit_color=(1.0, 0.62, 0.1))
    white = mat("wht", WHITE, rough=0.3)
    cam = vcam(studio(sc, key=900, rim=900, cam_loc=(0, -17, 0.6), lens=50))
    digits = [text(c, size=2.2, extrude=0.35, bevel=0.03, m=gold, loc=(x, 0, 6), font=load_font())
              for c, x in (("5", -1.3), ("5", 0.0), ("6", 1.3))]
    sub = text("AUSTRALIA", size=0.5, extrude=0.05, m=white, loc=(0, 0, -0.9), font=load_font(False))

    def upd(scene, *_):
        f = scene.frame_current
        for i, d in enumerate(digits):
            x = ease_out((f - 3 - 6 * i) / 9)
            d.location.z = 1.0 + 7 * (1 - x)
            d.rotation_euler = (math.radians(90 + 30 * (1 - x)), 0, 0)
        sub.scale = (max(ease_out((f - 28) / 12), 1e-3),) * 3
        sh = 0.05 * max(0.0, 1 - ((f - 3) % 6) / 6) if f < 24 else 0
        cam.location = (sh, -17 + 2.2 * ease_in_out(f / f_end), 0.6 + sh)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_196(sc):
    """'556' tips over and falls away; red '196' drops in its place; 'ALL OUT' under it."""
    f_end = sc.frame_end
    white = mat("wht", (0.8, 0.8, 0.82), rough=0.3)
    red = mat("red", RED, rough=0.35, emit=4.0)
    cam = vcam(studio(sc, key=700, rim=900, cam_loc=(0, -17, 0.6), lens=50))
    old = text("556", size=2.4, extrude=0.3, bevel=0.03, m=white, loc=(0, 0, 1.0), font=load_font())
    new = text("196", size=2.6, extrude=0.35, bevel=0.03, m=red, loc=(0, 0, 8), font=load_font())
    sub = text("ALL OUT", size=0.55, extrude=0.05, m=white, loc=(0, 0, -0.9), font=load_font(False))

    def upd(scene, *_):
        f = scene.frame_current
        x = min(1.0, max(0.0, (f - 10) / 16)) ** 2
        old.rotation_euler = (math.radians(90 - 95 * x), 0, 0)
        old.location.z = 1.0 - 4.0 * x
        y = ease_out((f - 26) / 10)
        new.location.z = 1.0 + 8 * (1 - y)
        sub.scale = (max(ease_out((f - 38) / 12), 1e-3),) * 3
        sh = 0.07 * max(0.0, 1 - (f - 34) / 8) if 34 <= f < 42 else 0
        cam.location = (sh, -17 + 2.0 * ease_in_out(f / f_end), 0.6 + sh)

    bpy.app.handlers.frame_change_pre.append(upd)


def rise(sc, label, sub_text, size=2.1):
    """Gold number rises out of the dark in a slow camera arc; a caption and a yellow line under it."""
    f_end = sc.frame_end
    gold = mat("gold", (1.0, 0.72, 0.16), metal=0.85, rough=0.22, emit=0.6, emit_color=(1.0, 0.62, 0.1))
    yellow = mat("yel", YELLOW, rough=0.3, emit=8.0)
    white = mat("wht", WHITE, rough=0.3)
    cam = vcam(studio(sc, key=1200, rim=900, cam_loc=(0, -15, 0.6), lens=50))
    t = text(label, size=size, extrude=0.35, bevel=0.03, m=gold, loc=(0, 0, -6), font=load_font())
    sub = text(sub_text, size=0.5, extrude=0.05, m=white, loc=(0, 0, -0.95), font=load_font(False))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.2, -0.45))
    line = bpy.context.object
    line.scale = (0.001, 0.03, 0.03)
    line.data.materials.append(yellow)

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out((f - 1) / (f_end * 0.4))
        t.location = (0, 0, -6 + 7.0 * x)
        t.rotation_euler = (math.radians(90), 0, math.radians(-20 * (1 - x)))
        line.scale = (2.0 * ease_out((f - f_end * 0.35) / (f_end * 0.3)) + 0.001, 0.03, 0.03)
        sub.scale = (max(ease_out((f - f_end * 0.45) / 10), 1e-3),) * 3
        a = 0.3 * (1 - f / f_end)
        cam.location = (15 * math.sin(a), -15 * math.cos(a) + 1.2 * ease_in_out(f / f_end), 0.6)
        cam.rotation_euler = (math.radians(88), 0, a)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_72(sc):
    """Gold '72*' rises out of the dark in a slow camera arc; 'NOT OUT' and a yellow line under it."""
    f_end = sc.frame_end
    gold = mat("gold", (1.0, 0.72, 0.16), metal=0.85, rough=0.22, emit=0.6, emit_color=(1.0, 0.62, 0.1))
    yellow = mat("yel", YELLOW, rough=0.3, emit=8.0)
    white = mat("wht", WHITE, rough=0.3)
    cam = vcam(studio(sc, key=1200, rim=900, cam_loc=(0, -15, 0.6), lens=50))
    t = text("72*", size=2.1, extrude=0.35, bevel=0.03, m=gold, loc=(0, 0, -6), font=load_font())
    sub = text("NOT OUT", size=0.5, extrude=0.05, m=white, loc=(0, 0, -0.95), font=load_font(False))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.2, -0.45))
    line = bpy.context.object
    line.scale = (0.001, 0.03, 0.03)
    line.data.materials.append(yellow)

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out((f - 1) / (f_end * 0.45))
        t.location = (0, 0, -6 + 7.0 * x)
        t.rotation_euler = (math.radians(90), 0, math.radians(-20 * (1 - x)))
        line.scale = (2.0 * ease_out((f - f_end * 0.4) / (f_end * 0.3)) + 0.001, 0.03, 0.03)
        sub.scale = (max(ease_out((f - f_end * 0.5) / 12), 1e-3),) * 3
        a = 0.3 * (1 - f / f_end)
        cam.location = (15 * math.sin(a), -15 * math.cos(a) + 1.2 * ease_in_out(f / f_end), 0.6)
        cam.rotation_euler = (math.radians(88), 0, a)

    bpy.app.handlers.frame_change_pre.append(upd)


SHOTS = {"s2": (lambda sc: rise(sc, "#2", "MOST FEARED", 2.6), 66), "s150": (lambda sc: rise(sc, "150", "KM/H", 2.3), 66)}


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
