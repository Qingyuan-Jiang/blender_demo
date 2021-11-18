import bpy
import math
import os
import sys
import json
import numpy as np
import argparse
from mathutils import Matrix, Quaternion, Euler
import mathutils

# Add parent directory to path
ROOT_DIR = os.path.abspath("../../")
sys.path.append(ROOT_DIR)

good_mesh_path = ROOT_DIR + "/RenderPeople/raw_data/good_mesh_frames.txt"
all_meshes_path = ROOT_DIR + "/RenderPeople/raw_data/"


def read_camera_names(file_path):
    cams = np.genfromtxt(file_path, delimiter=",")
    cam_names = np.array(cams, dtype='i')
    return cam_names


def read_name_list(file_path):
    with open(file_path) as f:
        lines = f.readlines()

    l = lines
    for i in range(len(lines)):
        b = lines[i]
        c = b[0:-1]
        l[i] = c
    return l


# camera_names = read_camera_names(cam_name_path)
good_meshes = read_camera_names(good_mesh_path)
folder_list = read_name_list(all_meshes_path + 'folders.txt')
mesh_list = read_name_list(all_meshes_path + 'meshes.txt')
texture_list = read_name_list(all_meshes_path + 'textures.txt')
mesh_num = len(folder_list)

f = good_meshes[0] - 1
print('processing mesh number  ', f + 1, '  out of  ', mesh_num, '  meshes.')
print('all_meshes_path', all_meshes_path)
print('folder_list[f]', folder_list[f])
print('texture_list[f]', texture_list[f])

if not os.path.exists(all_meshes_path + folder_list[f] + "/images1"):
    os.mkdir(all_meshes_path + folder_list[f] + "/images1")

objs = bpy.data.objects
scene = bpy.data.scenes['Scene']
meshes = bpy.data.meshes
lights = bpy.data.lights
cameras = bpy.data.cameras
images = bpy.data.images

# ---------------------------- Setup materials -----------------------------
mat_body = bpy.data.materials.new('BodyMaterial')
mat_body.use_nodes = True
matnodes_body = mat_body.node_tree.nodes
matnodes_body['Principled BSDF'].inputs[5].default_value = 0.1  # BSDF specular
# matnodes_body['Principled BSDF'].inputs[17].default_value[0] = 1 # BSDF specular
# matnodes_body['Principled BSDF'].inputs[17].default_value[1] = 1  # BSDF specular
# matnodes_body['Principled BSDF'].inputs[17].default_value[2] = 1  # BSDF specular

attr_body = matnodes_body.new("ShaderNodeTexImage")

# with stdout_redirected():
print('now loading the human body')
# -------------------------- Load human body ---------------------------
newimg = images.load(all_meshes_path + folder_list[f] + '/tex/' + texture_list[f])
attr_body.image = newimg
mat_body.node_tree.links.new(attr_body.outputs[0], matnodes_body['Principled BSDF'].inputs[0])
bpy.ops.import_scene.obj(filepath=all_meshes_path + folder_list[f] + '/' + mesh_list[f])

obj_body = bpy.context.selected_objects[0]
obj_body.location = [0, 0, 0] # [0, 0, 0]  # [1.38672, 2.76761, 1.19611]
# obj_body.rotation_mode = 'XYZ' # 'QUATERNION'
# obj_body.rotation_euler = [0.7071068, 0, 0, 0.7071068] # [1, 0, 0, 0]  # [-0.008228, 0.955793, -0.006987, -0.293842]
obj_body.rotation_euler = mathutils.Euler((math.radians(90.0), 0, 0), 'XYZ')
# obj_body.rotation_euler = mathutils.Euler((0, 0, 0), 'XYZ')
# (Matrix.Rotation(math.pi, 3, 'X') * obj_body.rotation_euler.to_matrix()).to_euler()
# obj_body.scale = [0.02, 0.02, 0.02] # [1, 1, 1] # [0.02, 0.02, 0.02]
obj_body.scale = [1.0, 1.0, 1.0]
if obj_body.data.materials:
    obj_body.data.materials[0] = mat_body
else:
    obj_body.data.materials.append(mat_body)
bpy.ops.export_scene.obj(
    filepath=all_meshes_path + folder_list[f] + '/transformed_mesh/' + mesh_list[f], axis_forward='Y')
