import bpy, math, time
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'; sc.eevee.taa_render_samples=32
sc.render.resolution_x=1920; sc.render.resolution_y=1080
bpy.ops.object.text_add(location=(0,0,0)); t=bpy.context.object; t.data.body="1992"; t.data.extrude=0.18; t.data.bevel_depth=0.03; t.data.align_x='CENTER'; t.data.align_y='CENTER'
t.rotation_euler=(math.radians(90),0,math.radians(-18))
m=bpy.data.materials.new("gold"); m.use_nodes=True; b=m.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value=(1.0,0.73,0.11,1); b.inputs["Metallic"].default_value=1.0; b.inputs["Roughness"].default_value=0.22
t.data.materials.append(m)
bpy.ops.object.camera_add(location=(0,-7,0.4),rotation=(math.radians(88),0,0)); sc.camera=bpy.context.object
bpy.ops.object.light_add(type='AREA',location=(3,-4,4)); l=bpy.context.object; l.data.energy=900; l.data.size=4
bpy.ops.object.light_add(type='AREA',location=(-4,-2,-1)); l=bpy.context.object; l.data.energy=300; l.data.size=3
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.02,0.02,0.025,1)
sc.render.filepath="/home/user/Editing/doc_video/blender/test_eevee.png"
t0=time.time(); bpy.ops.render.render(write_still=True); print("RENDER_SECONDS", round(time.time()-t0,1))
