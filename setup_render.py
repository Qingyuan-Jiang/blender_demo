import bpy
import math
import os
import sys
import json
import numpy as np
import argparse
from mathutils import Matrix, Quaternion, Euler
import mathutils

ROOT_DIR = os.path.abspath("../../")
sys.path.append(ROOT_DIR)

all_meshes_path = ROOT_DIR + "/RenderPeople/raw_data/"

objs = bpy.data.objects
scene = bpy.data.scenes['Scene']
meshes = bpy.data.meshes
lights = bpy.data.lights
cameras = bpy.data.cameras
images = bpy.data.images

scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_soft_shadows = True
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 90

print('Now render the scene.')
# for cid, camera_conf in camera_conf_dict.items():
# image_file = BG_path + str(camera_names[cid]) + ".jpg"
# image_file = BG_path + str(camera_names[0]) + ".jpg"
# if not os.path.exists(image_file):
#     continue
# img = images.load(image_file)
# image_node_scene.image = img

# scene.camera = objs[camera_conf['name']]
scene.camera = objs['camera.001']

# scene.render.filepath = all_meshes_path + folder_list[f] + "/images2/" + str(camera_names[cid]) + ".jpg"
scene.render.filepath = all_meshes_path + 'rp_aaron_posed_014_OBJ' + "/images1/" + str('camera.001') + ".jpg"

print('bpy.ops.render.render(write_still=True)')
bpy.ops.render.render(write_still=True)

print('salam1 ')

# images.remove(img, do_unlink=True)

# meshes.remove(obj_body.data, do_unlink=True)
# images.remove(newimg, do_unlink=True)
