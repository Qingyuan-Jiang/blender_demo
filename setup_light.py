import bpy
import math
import os
import sys
import json
import numpy as np
import argparse
from mathutils import Matrix, Quaternion, Euler, Vector
import mathutils

lamp_conf = {
    'name': 'Lamp.{:03d}'.format(0),
    'anchor': 0,
    'location': [-2, -2, 2],
    'rotation': (1, 0, 0, 0),
    'local_rotation_angle': -45,  # config['light']['lamps']['local_rotation']['angle'],
    'local_rotation_axis': "X",  # config['light']['lamps']['local_rotation']['axis'],
    'scale': [1, -1, -1],  # camera_conf_dict[cid]['scale'],
    'energy': 35,  # config['light']['lamps']['energy']
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
