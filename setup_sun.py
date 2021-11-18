import bpy
import math
import os
import sys
import json
import numpy as np
import argparse
from mathutils import Matrix, Quaternion, Euler, Vector
import mathutils

sun_location = [-3, -5, 10]
# sun_rotation = [0.3, 0.2, -0.9, 0.25]

bpy.ops.object.light_add(type='SUN')
sun = bpy.context.selected_objects[0]
sun.location = sun_location
# sun.rotation_mode = 'QUATERNION'
# sun.rotation_quaternion = sun_rotation
sun.rotation_euler = Euler((math.radians(90), 0, 0))