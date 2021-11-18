import bpy
import math
import os
import sys
import json
import numpy as np
import argparse
from mathutils import Matrix, Quaternion, Euler, Vector
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

# Remove the default objects
if 'Cube' in meshes.keys():
    meshes.remove(meshes['Cube'], do_unlink=True)
if 'Light' in lights.keys():
    lights.remove(lights['Light'], do_unlink=True)
if 'Camera' in cameras.keys():
    cameras.remove(cameras['Camera'], do_unlink=True)

# ---------------------------- Setup materials -----------------------------
mat_body = bpy.data.materials.new('BodyMaterial')
mat_body.use_nodes = True
matnodes_body = mat_body.node_tree.nodes
matnodes_body['Principled BSDF'].inputs[5].default_value = 0.1  # BSDF specular
attr_body = matnodes_body.new("ShaderNodeTexImage")

# -------------------------- Load human body ---------------------------
print('now loading the human body')
newimg = images.load(all_meshes_path + folder_list[f] + '/tex/' + texture_list[f])
attr_body.image = newimg
mat_body.node_tree.links.new(attr_body.outputs[0], matnodes_body['Principled BSDF'].inputs[0])
bpy.ops.import_scene.obj(filepath=all_meshes_path + folder_list[f] + '/' + mesh_list[f])

obj_body = bpy.context.selected_objects[0]
obj_body.location = [0, 0, 0]  # [0, 0, 0]  # [1.38672, 2.76761, 1.19611]
obj_body.rotation_euler = mathutils.Euler((math.radians(90.0), 0, 0), 'XYZ')

obj_body.scale = [0.02, 0.02, 0.02]
if obj_body.data.materials:
    obj_body.data.materials[0] = mat_body
else:
    obj_body.data.materials.append(mat_body)
bpy.ops.export_scene.obj(
    filepath=all_meshes_path + folder_list[f] + '/transformed_mesh/' + mesh_list[f], axis_forward='Y')

# ------------------------ Setup light ---------------------------------
lamp_conf = {
    'name': 'Lamp.{:03d}'.format(0),
    'anchor': 0,
    'location': [-2, -2, 2],
    'rotation': (1, 0, 0, 0),
    'local_rotation_angle': -45,  # config['light']['lamps']['local_rotation']['angle'],
    'local_rotation_axis': "X",  # config['light']['lamps']['local_rotation']['axis'],
    'scale': [1, -1, -1],  # camera_conf_dict[cid]['scale'],
    'energy': 350,  # config['light']['lamps']['energy']
}

bpy.ops.object.light_add(type='AREA')
lamp = bpy.context.selected_objects[0]
lamp.name = 'Lamp.{:03d}'.format(0)
lamp.data.name = lamp.name
lamp.data.energy = 35  # config['light']['lamps']['energy']
# NOTE Explicitly compute transformation, as we want to apply local rotation
trans_mat = Matrix.Translation(Vector([-2, -2, 2]))
rot_mat = Quaternion(Vector(lamp_conf['rotation'])).to_matrix().to_4x4()
scale_mat = Matrix.Scale(lamp_conf['scale'][0], 4, Vector((1, 0, 0))) \
            @ Matrix.Scale(lamp_conf['scale'][1], 4, Vector((0, 1, 0))) \
            @ Matrix.Scale(lamp_conf['scale'][2], 4, Vector((0, 0, 1)))
local_rot_mat = Matrix.Rotation(math.radians(lamp_conf['local_rotation_angle']), 4,
                                lamp_conf['local_rotation_axis'])
lamp.matrix_world = trans_mat @ rot_mat @ scale_mat @ local_rot_mat


# ------------------------ Setup sun -----------------------------------
sun_location = [-3, -5, 10]
# sun_rotation = [0.3, 0.2, -0.9, 0.25]

bpy.ops.object.light_add(type='SUN')
sun = bpy.context.selected_objects[0]
sun.location = sun_location
# sun.rotation_mode = 'QUATERNION'
# sun.rotation_quaternion = sun_rotation
sun.rotation_euler = Euler((math.radians(90), 0, 0))


# ------------------------- Setup camera -------------------------------
bpy.ops.object.camera_add()
cam = bpy.context.selected_objects[0]
cam.name = 'camera.001'
cam.data.name = cam.name
cam.location = (0, -10, 2)  # 'camera_conf['location']'
cam.rotation_euler = Euler((math.radians(90.0), 0, 0), 'XYZ')
cam.scale = (1, 1, 1)  # camera_conf['scale']
cam.data.lens_unit = 'FOV'  # 'FOV' # 'MILLIMETERS'
cam.data.angle = 0.69  # camera_conf['fov']
cam.data.show_background_images = True

# ---------------------- Render images ---------------------------------
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_soft_shadows = True
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 90

scene.camera = objs['camera.001']
scene.render.filepath = all_meshes_path + 'rp_aaron_posed_014_OBJ' + "/images1/" + str('camera.001') + ".jpg"
bpy.ops.render.render(write_still=True)


# Remove the default objects
meshes.remove(obj_body.data, do_unlink=True)
lights.remove(lights['Lamp.000'], do_unlink=True)
lights.remove(lights['Sun.001'], do_unlink=True)
cameras.remove(cameras['camera.001'], do_unlink=True)


# images.remove(img, do_unlink=True)
#
# meshes.remove(obj_body.data, do_unlink=True)
# images.remove(newimg, do_unlink=True)
