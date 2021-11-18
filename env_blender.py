import math
import os
import sys

import bpy
import mathutils
import numpy as np
from mathutils import Matrix, Quaternion, Euler, Vector

# Add parent directory to path
ROOT_DIR = os.path.abspath("../../")
sys.path.append(ROOT_DIR)


def read_name_list(file_path):
    with open(file_path) as f:
        lines = f.readlines()

    l = lines
    for i in range(len(lines)):
        b = lines[i]
        c = b[0:-1]
        l[i] = c
    return l


class BlenderDrone:
    def __init__(self, mesh_path):
        self.cid = 0
        self.cname = 'camera_{:03d}'.format(self.cid)
        self.mesh_path = mesh_path

    def render_image(self, objs, pose, render_path='/images1/'):
        pos, ori = pose
        print("Render image at position and orientation. ", pos, ori)

        # ------------------------- Setup camera -------------------------------
        bpy.ops.object.camera_add()
        cam = bpy.context.selected_objects[0]
        cam.name = self.cname
        cam.data.name = cam.name
        cam.location = pos
        cam.rotation_euler = Euler(ori, 'XYZ')
        cam.scale = (1, 1, 1)  # camera_conf['scale']
        cam.data.lens_unit = 'FOV'  # 'FOV' # 'MILLIMETERS'
        cam.data.angle = 0.69  # camera_conf['fov']
        cam.data.show_background_images = True

        # ---------------------- Render images ---------------------------------
        scene = bpy.data.scenes['Scene']
        scene.render.engine = 'BLENDER_EEVEE'
        scene.eevee.use_soft_shadows = True
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'JPEG'
        scene.render.image_settings.quality = 90

        scene.camera = objs[self.cname]
        scene.render.filepath = self.mesh_path + render_path + str(self.cname) + ".jpg"
        bpy.ops.render.render(write_still=True)

        # ---------------------- Update Camera id ------------------------------
        self.update_cname()

    def update_cname(self):
        self.cid = self.cid + 1
        self.cname = 'camera_{:03d}'.format(self.cid)

    def clear_trajectory(self):
        cameras = bpy.data.cameras
        for cid in range(self.cid):
            cameras.remove(cameras['camera_{:03d}'.format(cid)], do_unlink=True)
        self.cid = 0
        self.cname = 'camera_{:03d}'.format(self.cid)


class BlenderEnv:

    def __init__(self, all_meshes_path, model_idx=0, save_path='/renders',
                 z_offset=1.5):
        # good_mesh_path = ROOT_DIR + "/RenderPeople/raw_data/good_mesh_frames.txt"
        # all_meshes_path = ROOT_DIR + "/RenderPeople/raw_data/"

        self.all_meshes_path = all_meshes_path
        self.model_idx = model_idx
        self.save_path = save_path
        self.z_offset = z_offset

        folder_list = read_name_list(all_meshes_path + 'folders.txt')
        mesh_list = read_name_list(all_meshes_path + 'meshes.txt')
        texture_list = read_name_list(all_meshes_path + 'textures.txt')
        mesh_num = len(folder_list)

        print('processing mesh number  ', model_idx + 1, '  out of  ', mesh_num, '  meshes.')
        print('all_meshes_path', all_meshes_path)
        print('folder_list[f]', folder_list[model_idx])
        print('texture_list[f]', texture_list[model_idx])

        if not os.path.exists(all_meshes_path + folder_list[model_idx] + save_path):
            os.mkdir(all_meshes_path + folder_list[model_idx] + save_path)

        self.objs = bpy.data.objects
        self.scene = bpy.data.scenes['Scene']
        self.meshes = bpy.data.meshes
        self.lights = bpy.data.lights
        self.cameras = bpy.data.cameras
        self.images = bpy.data.images

        # Remove the default objects
        if 'Cube' in self.meshes.keys():
            self.meshes.remove(self.meshes['Cube'], do_unlink=True)
        if 'Light' in self.lights.keys():
            self.lights.remove(self.lights['Light'], do_unlink=True)
        if 'Camera' in self.cameras.keys():
            self.cameras.remove(self.cameras['Camera'], do_unlink=True)

        # ---------------------------- Setup materials -----------------------------
        mat_body = bpy.data.materials.new('BodyMaterial')
        mat_body.use_nodes = True
        matnodes_body = mat_body.node_tree.nodes
        matnodes_body['Principled BSDF'].inputs[5].default_value = 0.1  # BSDF specular
        attr_body = matnodes_body.new("ShaderNodeTexImage")

        # -------------------------- Load human body ---------------------------
        print('now loading the human body')
        newimg = self.images.load(all_meshes_path + folder_list[model_idx] + '/tex/' + texture_list[model_idx])
        attr_body.image = newimg
        mat_body.node_tree.links.new(attr_body.outputs[0], matnodes_body['Principled BSDF'].inputs[0])
        bpy.ops.import_scene.obj(filepath=all_meshes_path + folder_list[model_idx] + '/' + mesh_list[model_idx])

        self.body_config = {
            'location': [0, 0, 0],
            'rotation': [math.radians(90.0), 0, 0],
            'scale': [0.02, 0.02, 0.02]
        }

        self.obj_body = bpy.context.selected_objects[0]
        self.obj_body.location = self.body_config['location']  # [0, 0, 0]  # [1.38672, 2.76761, 1.19611]
        self.obj_body.rotation_euler = mathutils.Euler(self.body_config['rotation'], 'XYZ')

        self.obj_body.scale = self.body_config['scale']
        if self.obj_body.data.materials:
            self.obj_body.data.materials[0] = mat_body
        else:
            self.obj_body.data.materials.append(mat_body)
        bpy.ops.export_scene.obj(
            filepath=all_meshes_path + folder_list[model_idx] + '/transformed_mesh/' + mesh_list[model_idx],
            axis_forward='Y')

        # ------------------------ Setup light ---------------------------------
        self.lamp_conf = self.get_light_conf()
        self.lamp_conf['name'] = self.lamp_conf['name'].format(0)
        self.setup_light(self.lamp_conf)

        # ------------------------ Setup sun -----------------------------------
        self.sun_location = [-3, -5, 10]
        self.setup_sun(self.sun_location)

        # ----------------------- Setup drone and renderer -----------------------
        self.drone = BlenderDrone(all_meshes_path + 'rp_aaron_posed_014_OBJ')

    def setup_light(self, lamp_config):
        bpy.ops.object.light_add(type='AREA')
        lamp = bpy.context.selected_objects[0]
        lamp.name = lamp_config['name']  # 'Lamp.{:03d}'.format(0)
        lamp.data.name = lamp.name
        lamp.data.energy = lamp_config['energy']  # 35  # config['light']['lamps']['energy']

        # NOTE Explicitly compute transformation, as we want to apply local rotation
        trans_mat = Matrix.Translation(Vector(lamp_config['location']))
        rot_mat = Quaternion(Vector(lamp_config['rotation'])).to_matrix().to_4x4()
        scale_mat = Matrix.Scale(lamp_config['scale'][0], 4, Vector((1, 0, 0))) \
                    @ Matrix.Scale(lamp_config['scale'][1], 4, Vector((0, 1, 0))) \
                    @ Matrix.Scale(lamp_config['scale'][2], 4, Vector((0, 0, 1)))
        local_rot_mat = Matrix.Rotation(math.radians(lamp_config['local_rotation_angle']), 4,
                                        lamp_config['local_rotation_axis'])
        lamp.matrix_world = trans_mat @ rot_mat @ scale_mat @ local_rot_mat

    def setup_sun(self, location, rotation=(math.radians(90), 0, 0)):
        bpy.ops.object.light_add(type='SUN')
        sun = bpy.context.selected_objects[0]
        sun.location = location
        sun.rotation_euler = Euler(rotation, 'XYZ')

    def render_by_waypoints(self, wps, prefix=None):
        num_kps = len(wps)
        for i in range(num_kps):
            pos_d = np.asarray(wps[i])
            pos_a = np.asarray(self.body_config['location'])
            pos = pos_d - pos_a
            x, y, z = pos
            z = z - self.z_offset  # Offset on z direction to focus on the middle of the actor.
            ori = [math.atan2(math.sqrt(x ** 2 + y ** 2), z), 0, math.radians(180) - math.atan2(x, y)]
            render_path = self.save_path + prefix
            self.drone.render_image(self.objs, [pos_d, ori], render_path=render_path)
        self.drone.clear_trajectory()

    def clear_scenes(self):
        # Remove the default objects
        self.meshes.remove(self.obj_body.data, do_unlink=True)
        self.lights.remove(self.lights['Lamp.000'], do_unlink=True)
        self.lights.remove(self.lights['Sun'], do_unlink=True)
        self.drone.clear_trajectory()

    def get_light_conf(self):
        conf = {'name': 'Lamp.{:03d}',
                'anchor': 0,
                'location': [-2, -2, 2],
                'rotation': (1, 0, 0, 0),
                'local_rotation_angle': -45,
                'local_rotation_axis': "X",
                'scale': [1, -1, -1],
                'energy': 350}
        return conf


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
