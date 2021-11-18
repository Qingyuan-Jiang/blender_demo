import bpy
import os
import sys

# Add parent directory to path
ROOT_DIR = 'D:/03_Workspace/01_projects/multidrone_nri'

fname = 'exp_dynamic_v1/gts/'
save_path = ROOT_DIR + "/archive/airsim/" + fname

model_name = 'Silly_Dancing_base.fbx'
# bpy.ops.import_scene.fbx(filepath=model_name, directory=save_path)
bpy.ops.import_scene.fbx(filepath=save_path + model_name)
num_frames = 120

for ii in range(num_frames):
    # bpy.ops.export_scene.obj(filepath=save_path + '/gits/gt_{:03d}.obj'.format(ii))
    # bpy.ops.export_mesh.ply(filepath=save_path + 'gt_{:03d}.ply'.format(ii))
    bpy.ops.export_mesh.stl(filepath=save_path + 'gt_{:03d}.stl'.format(ii))
    bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
