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
sys.path.append(ROOT_DIR + '/src/blender')

# print(sys.path)
from env_blender import BlenderEnv


if __name__ == '__main__':

    all_meshes_path = ROOT_DIR + "/RenderPeople/raw_data/"
    env = BlenderEnv(all_meshes_path, save_path='/image_test/')

    # Generate path.
    '''
    R = 10
    step_size_r = 10
    kps = []
    for i_theta in range(int(360 / step_size_r)):
        theta = i_theta * step_size_r
        pos = [math.cos(math.radians(theta)) * R, math.sin(math.radians(theta)) * R, 10]
        kps.append(pos)
    '''

    T = 50
    wps1 = np.load(ROOT_DIR + '/archive/dp_path/path_d1_{}.npy'.format(T))
    wps2 = np.load(ROOT_DIR + '/archive/dp_path/path_d2_{}.npy'.format(T))

    # Render images along waypoints.
    env.render_by_waypoints(wps1, prefix='drone1_')
    env.render_by_waypoints(wps2, prefix='drone2_')
