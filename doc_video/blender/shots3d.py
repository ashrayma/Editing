"""3D hero shots for the Centurion 2003 documentary, rendered with Blender (EEVEE) on this machine.

    python3 shots3d.py <shot> [--frames a-b] [--res 1920x1080]
    shots: speed | score98 | date | logo

Brand look: charcoal studio, theCricketLounge yellow (#FEDE5C) as the light/emission colour, white type.
Each shot writes a PNG sequence to renders/<shot>/####.png (30 fps).
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
YELLOW = (0.991, 0.730, 0.107)   # #FEDE5C in linear
WHITE = (0.92, 0.92, 0.92)
FPS = 30


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return 3 * x * x - 2 * x * x * x


# ----------------------------------------------------------------------------- scene helpers

def reset(frames, res):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 48
    sc.eevee.use_shadows = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, frames
    # Khronos PBR Neutral keeps the brand yellow true (AgX washes bright yellows out to cream)
    sc.view_settings.view_transform = "Khronos PBR Neutral"
    sc.render.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.012, 0.014, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    add_glow(sc)
    return sc


def add_glow(sc):
    """Soft bloom on the emissive yellow, done in the compositor (EEVEE Next has no built-in bloom)."""
    sc.use_nodes = True
    tree = sc.node_tree if hasattr(sc, "node_tree") and sc.node_tree else None
    if tree is None:
        tree = bpy.data.node_groups.new("comp", "CompositorNodeTree")
        sc.compositing_node_group = tree
        rl = tree.nodes.new("CompositorNodeRLayers")
        out = tree.nodes.new("NodeGroupOutput")
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    else:
        rl = tree.nodes.get("Render Layers") or tree.nodes.new("CompositorNodeRLayers")
        out = tree.nodes.get("Composite") or tree.nodes.new("CompositorNodeComposite")
    glare = tree.nodes.new("CompositorNodeGlare")
    # Blender 5: glare settings are input sockets. A soft, restrained bloom - clean, not streaky.
    for key, val in (("Type", "Bloom"), ("Quality", "High"), ("Threshold", 1.2), ("Smoothness", 0.4),
                     ("Size", 0.55), ("Strength", 0.32)):
        if key in glare.inputs:
            glare.inputs[key].default_value = val
    tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
    tree.links.new(glare.outputs["Image"], out.inputs[0])


def mat(name, color, metal=0.0, rough=0.4, emit=0.0, emit_color=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def text(body, size=1.0, extrude=0.12, bevel=0.012, m=None, loc=(0, 0, 0), rot=(math.radians(90), 0, 0),
         align="CENTER", font=None):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.data.body = body
    t.data.size = size
    t.data.extrude = extrude
    t.data.bevel_depth = bevel
    t.data.bevel_resolution = 3
    t.data.align_x = align
    t.data.align_y = "CENTER"
    if font:
        t.data.font = font
    if m:
        t.data.materials.append(m)
    return t


def load_font(bold=True):
    for p in ("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf" if bold else
              "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            return bpy.data.fonts.load(p)
    return None


def studio(sc, key=900, rim=600, cam_loc=(0, -9, 0.3), lens=50, floor_z=-1.6):
    bpy.ops.object.light_add(type="AREA", location=(4, -5, 5))
    k = bpy.context.object
    k.data.energy, k.data.size = key, 5
    k.rotation_euler = (math.radians(50), 0, math.radians(38))
    bpy.ops.object.light_add(type="AREA", location=(-5, 3, 2))
    r = bpy.context.object
    r.data.energy, r.data.size = rim, 4
    r.data.color = (1.0, 0.86, 0.45)
    r.rotation_euler = (math.radians(70), 0, math.radians(-120))
    # soft-box reflection cards just out of shot: metals need something bright to reflect
    for loc, rot, sz in (((-7, -4, 7.5), (math.radians(45), 0, math.radians(-55)), (5, 3)),
                         ((7, -3, 6.0), (math.radians(50), 0, math.radians(60)), (4, 5)),
                         ((0, -7, 6.5), (math.radians(35), 0, 0), (6, 2))):
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
        card = bpy.context.object
        card.scale = (*sz, 1)
        card.data.materials.append(mat("card", (1, 1, 1), emit=6.0))
        card.visible_camera = False
    # glossy dark floor for reflections
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, floor_z))
    bpy.context.object.data.materials.append(mat("floor", (0.015, 0.015, 0.017), metal=0.2, rough=0.42))
    bpy.ops.object.camera_add(location=cam_loc, rotation=(math.radians(88), 0, 0))
    cam = bpy.context.object
    cam.data.lens = lens
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = abs(cam_loc[1])
    cam.data.dof.aperture_fstop = 2.8
    sc.camera = cam
    return cam


def key(obj, path, frame, value, index=-1):
    setattr_path(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame, index=index)


def setattr_path(obj, path, value):
    setattr(obj, path, value)


def smooth_all():
    for a in bpy.data.actions:
        for fc in getattr(a, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.easing = "EASE_IN_OUT"


# ----------------------------------------------------------------------------- shots

def shot_speed(sc):
    """A gauge: tick ring, needle sweeping to 161.3, the number counting up, KM/H label."""
    f_end = sc.frame_end
    font = load_font()
    font_mid = load_font(False)
    yellow = mat("yel", YELLOW, rough=0.3, emit=6.0)
    white = mat("wht", WHITE, metal=0.0, rough=0.25)
    dark = mat("dark", (0.03, 0.03, 0.035), metal=0.6, rough=0.25)
    cam = studio(sc, cam_loc=(0, -11, 0.2), lens=30, floor_z=-3.4)
    # gauge face
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=3.2, depth=0.15, location=(0, 0.25, 0.2),
                                        rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(dark)
    # tick marks over a 240-degree arc (0 .. 180 km/h)
    ticks = []
    for i in range(37):
        frac = i / 36
        ang = math.radians(210 - 240 * frac)
        long_ = i % 4 == 0
        r = 2.75
        bpy.ops.mesh.primitive_cube_add(size=1, location=(r * math.cos(ang), 0.1, 0.2 + r * math.sin(ang)))
        t = bpy.context.object
        t.scale = (0.05, 0.05, 0.34 if long_ else 0.18)
        t.rotation_euler = (0, -(ang - math.pi / 2), 0)
        t.data.materials.append(white)
        ticks.append((frac, t))
    # needle
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.05, 0.2))
    needle = bpy.context.object
    needle.scale = (0.05, 0.05, 2.4)
    bpy.ops.object.transform_apply(scale=True)
    for v in needle.data.vertices:
        v.co.z += 1.2
    needle.data.materials.append(yellow)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.22, depth=0.2, location=(0, 0.0, 0.2),
                                        rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(white)
    num = text("0.0", size=1.05, extrude=0.08, m=yellow, loc=(0, 0.0, -1.0), font=font)
    unit = text("KM/H", size=0.32, extrude=0.03, m=white, loc=(0, 0.0, -1.85), font=font_mid)
    # animation
    target = 161.3
    sweep_end = int(f_end * 0.7)

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out((f - 6) / max(1, sweep_end - 6))
        v = target * x
        frac = v / 180
        needle.rotation_euler = (0, math.radians(-120 + 240 * frac), 0)
        num.data.body = f"{v:.1f}"
        for tf, t in ticks:
            t.active_material = yellow if tf <= frac + 1e-6 and f > 6 else white
        cam.location = (0.6 * math.sin(f / f_end * 0.8), -12.5 + 1.5 * ease_in_out(f / f_end), 0.2)
        cam.rotation_euler = (math.radians(88), 0, math.radians(-3 * math.sin(f / f_end * 0.8)))

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_score98(sc):
    """Gold '98' rising out of the dark with a camera arc; a thin yellow line draws underneath."""
    f_end = sc.frame_end
    font = load_font()
    gold = mat("gold", (1.0, 0.72, 0.16), metal=1.0, rough=0.2)
    yellow = mat("yel", YELLOW, rough=0.3, emit=8.0)
    cam = studio(sc, key=1200, rim=900, cam_loc=(0, -8, 0.4), lens=50)
    t = text("98", size=3.2, extrude=0.35, bevel=0.03, m=gold, loc=(0, 0, -6), font=font)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.2, -1.45))
    line = bpy.context.object
    line.scale = (0.001, 0.03, 0.03)
    line.data.materials.append(yellow)

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out((f - 1) / (f_end * 0.45))
        t.location = (0, 0, -6 + 6.15 * x)
        t.rotation_euler = (math.radians(90), 0, math.radians(-22 * (1 - x) + 4 * ease_in_out(f / f_end)))
        line.scale = (2.4 * ease_out((f - f_end * 0.4) / (f_end * 0.3)) + 0.001, 0.03, 0.03)
        a = 0.35 * (1 - f / f_end)
        cam.location = (8 * math.sin(a), -8 * math.cos(a) + 0.8 * ease_in_out(f / f_end), 0.4)
        cam.rotation_euler = (math.radians(88), 0, a)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_date(sc):
    """'1 MARCH 2003' flips up into place beside a yellow bar (the logo motif), slow push-in."""
    f_end = sc.frame_end
    font = load_font()
    white = mat("wht", WHITE, rough=0.3)
    yellow = mat("yel", YELLOW, rough=0.3, emit=6.0)
    cam = studio(sc, cam_loc=(0, -10, 0.2), lens=40)
    words = [text("1 MARCH", size=1.25, extrude=0.14, m=white, loc=(0.4, 0, 0.55), font=font, align="LEFT"),
             text("2003", size=1.6, extrude=0.18, m=yellow, loc=(0.4, 0, -0.95), font=font, align="LEFT")]
    for w in words:
        w.location.x = -2.6
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-3.0, 0, -0.15))
    bar = bpy.context.object
    bar.scale = (0.14, 0.14, 0.001)
    bar.data.materials.append(yellow)

    def upd(scene, *_):
        f = scene.frame_current
        bar.scale = (0.14, 0.14, 2.9 * ease_out((f - 1) / 14) + 0.001)
        for i, w in enumerate(words):
            x = ease_out((f - 8 - 6 * i) / 18)
            w.rotation_euler = (math.radians(90 - 90 * (1 - x)), 0, 0)
            w.location.y = 1.5 * (1 - x)
        cam.location = (0.3 + 0.4 * ease_in_out(f / f_end), -10 + 1.2 * ease_in_out(f / f_end), 0.0)

    bpy.app.handlers.frame_change_pre.append(upd)


def shot_logo(sc):
    """The theCricketLounge logo on a glass slab, a light sweep crossing it, gentle turn toward camera."""
    f_end = sc.frame_end
    cam = studio(sc, key=500, rim=400, cam_loc=(0, -7, 0.1), lens=50)
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
    b.inputs["Emission Strength"].default_value = 2.2
    m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    aspect = img.size[0] / img.size[1]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
    plane = bpy.context.object
    plane.scale = (4.6, 4.6 / aspect, 1)
    plane.data.materials.append(m)
    # light sweep: an emissive strip passing behind/through
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-6, 0.3, 0), rotation=(math.radians(90), 0, math.radians(0)))
    sweep = bpy.context.object
    sweep.scale = (0.25, 4, 1)
    sweep.rotation_euler = (math.radians(90), math.radians(20), 0)
    sweep.data.materials.append(mat("sweep", YELLOW, emit=3.0))

    def upd(scene, *_):
        f = scene.frame_current
        x = ease_out(f / (f_end * 0.6))
        plane.rotation_euler = (math.radians(90), 0, math.radians(-25 * (1 - x)))
        plane.location = (0, 1.5 * (1 - x), 0)
        sweep.location.x = -6 + 12 * ease_in_out((f - f_end * 0.35) / (f_end * 0.5))
        cam.location = (0, -7 + 0.7 * ease_in_out(f / f_end), 0.1)

    bpy.app.handlers.frame_change_pre.append(upd)


SHOTS = {"speed": (shot_speed, 105), "score98": (shot_score98, 90), "date": (shot_date, 75), "logo": (shot_logo, 75)}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    name = argv[0]
    fn, frames = SHOTS[name]
    res = (1920, 1080)
    fr = None
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
