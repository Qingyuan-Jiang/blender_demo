import bpy
import math
import os
import sys
import json
import numpy as np
import argparse
from mathutils import Matrix, Quaternion, Euler
import mathutils


bpy.ops.object.camera_add()
cam = bpy.context.selected_objects[0]
cam.name = 'camera.001'
cam.data.name = cam.name
cam.location = (0, -10, 0)  # 'camera_conf['location']'
# cam.rotation_quaternion = (1, 0, 0, 0)  # camera_conf['rotation']
cam.rotation_euler = Euler((math.radians(90.0), 0, 0), 'XYZ')
cam.scale = (1, 1, 1)  # camera_conf['scale']
cam.data.lens_unit = 'FOV'  # 'FOV' # 'MILLIMETERS'
cam.data.angle = 0.69  # camera_conf['fov']
cam.data.show_background_images = True
