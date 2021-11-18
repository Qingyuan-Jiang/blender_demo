# Example usage.
#  blender --background --python synthesize_images.py -- \
#          -c conf.json

import bpy
import math
import os
import sys
import json
import numpy as np
import argparse
from mathutils import Matrix, Quaternion, Euler
import mathutils

# from functions import read_cameras, read_camera_names

# Add parent directory to path
ROOT_DIR = os.path.abspath("../../")
sys.path.append(ROOT_DIR)

# Add parent directory to path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

data_folder = ROOT_DIR + '/Walking/data_human3D/train_128'
cam_name_path = data_folder + "/camera_names.txt"
good_mesh_path = ROOT_DIR + "/RenderPeople/raw_data/good_mesh_frames.txt"
BG_path = ROOT_DIR + "/Walking/BG/"  # "/home/yasamin/Desktop/00000014/BG/"
all_meshes_path = ROOT_DIR + "/RenderPeople/raw_data/"


def read_cameras(data_path):
    cen = np.genfromtxt(data_path + "/cen.txt", delimiter=",")
    cen = np.array(cen, dtype='f')

    K = np.genfromtxt(data_path + "/K.txt", delimiter=",")
    K = np.array(K, dtype='f')

    R = np.genfromtxt(data_path + "/R.txt", delimiter=",")
    R = np.array(R, dtype='f')

    return cen, K, R


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


# ------------------------- Redirect stdout ------------------------------------
from contextlib import contextmanager


def fileno(file_or_fd):
    fd = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd


@contextmanager
def stdout_redirected(to=os.devnull, stdout=None):
    if stdout is None:
        stdout = sys.stdout

    stdout_fd = fileno(stdout)
    # copy stdout_fd before it is overwritten
    # NOTE: `copied` is inheritable on Windows when duplicating a standard stream
    with os.fdopen(os.dup(stdout_fd), 'wb') as copied:
        stdout.flush()  # flush library buffers that dup2 knows nothing about
        try:
            os.dup2(fileno(to), stdout_fd)  # $ exec >&to
        except ValueError:  # filename
            with open(to, 'wb') as to_file:
                os.dup2(to_file.fileno(), stdout_fd)  # $ exec > to
        try:
            yield stdout  # allow code to be run with the redirected stdout
        finally:
            # restore stdout to its previous value
            # NOTE: dup2 makes stdout_fd inheritable unconditionally
            stdout.flush()
            os.dup2(copied.fileno(), stdout_fd)  # $ exec >&copied


# ------------------------------------------------------------------------------


def parse_sync_info(sync_file, skip_rows=2):
    sync_info_list = []
    with open(sync_file, 'r') as f:
        for i in range(skip_rows):
            f.readline()
        for line in f:
            s = line.strip().split(' ')
            sync_info = {
                'camera_name': s[0],
                'video_filename': s[1],
                'time': float(s[2])
            }
            sync_info_list.append(sync_info)
    return sync_info_list


def dcm2quat(dcm):
    """
    Arguments
        dcm  - Rotation represented by direction cosine matrix
    Return
        quat - Rotation represented by quaternion (w, x, y, z)
    """
    decision_matrix = np.empty([4, ])
    decision_matrix[:3] = dcm.diagonal()
    decision_matrix[3] = decision_matrix[:3].sum()
    choice = decision_matrix.argmax()

    quat = np.empty([4, ])

    if choice != 3:
        i = choice
        j = (i + 1) % 3
        k = (j + 1) % 3

        quat[i] = 1 - decision_matrix[3] + 2 * dcm[i, i]
        quat[j] = dcm[j, i] + dcm[i, j]
        quat[k] = dcm[k, i] + dcm[i, k]
        quat[3] = dcm[k, j] - dcm[j, k]
    else:
        quat[0] = dcm[2, 1] - dcm[1, 2]
        quat[1] = dcm[0, 2] - dcm[2, 0]
        quat[2] = dcm[1, 0] - dcm[0, 1]
        quat[3] = 1 + decision_matrix[3]

    quat /= np.linalg.norm(quat)
    # Rearrange from (x, y, z, w) to (w, x, y, z)
    quat = quat[[3, 0, 1, 2]]

    return quat


def deselect_all():
    for ob in bpy.context.selected_objects:
        ob.select_set(False)


def synthesize_images(config):
    # -------------------------- Parse configuration ---------------------------
    camera_names = read_camera_names(cam_name_path)
    good_meshes = read_camera_names(good_mesh_path)
    folder_list = read_name_list(all_meshes_path + 'folders.txt')
    mesh_list = read_name_list(all_meshes_path + 'meshes.txt')
    texture_list = read_name_list(all_meshes_path + 'textures.txt')
    mesh_num = len(folder_list)

    # camera_conf_dict = {}
    # cid = 0
    # for num in camera_names:
    #     cam_path = data_folder + "/" + str(num) + "/camera"
    #     t, K, R = read_cameras(cam_path)
    #     C = t  # - np.matmul(R.T, 1*t)
    #     R_quat = dcm2quat(R.T)
    #
    #     f = K[0, 0]
    #     x0 = K[0, 2]
    #     y0 = K[1, 2]
    #     fov = (2 * np.arctan2(np.sqrt(x0 ** 2 + y0 ** 2), f)) - (0.1361)
    #     print("C  ", C)
    #     print("Q  ", R_quat)
    #     print("fov  ", fov)
    #     camera_conf_dict[cid] = {
    #         'name': 'Camera.{:03d}'.format(cid),
    #         'location': C,
    #         'rotation': R_quat,
    #         'scale': [1, -1, -1],
    #         'fov': fov
    #     }
    #     cid = cid + 1
    #
    # lamp_conf_dict = {}
    # for cid in config['light']['lamps']['anchors']:
    #     lamp_conf_dict[cid] = {
    #         'name': 'Lamp.{:03d}'.format(cid),
    #         'anchor': cid,
    #         'location': camera_conf_dict[cid]['location'] + config['light']['lamps']['location_offset'],
    #         'rotation': camera_conf_dict[cid]['rotation'],
    #         'local_rotation_angle': config['light']['lamps']['local_rotation']['angle'],
    #         'local_rotation_axis': config['light']['lamps']['local_rotation']['axis'],
    #         'scale': camera_conf_dict[cid]['scale'],
    #         'energy': config['light']['lamps']['energy']
    #     }
    #
    # sun_location = config['light']['sun']['location']
    # sun_rotation = config['light']['sun']['rotation']
    #
    # body_location = config['body']['transform']['location']
    # body_rotation = config['body']['transform']['rotation']
    # body_scale = config['body']['transform']['scale']
    #
    # render_engine = config['render']['engine']
    # render_image_format = config['render']['image_format']
    # render_image_quality = config['render']['image_quality']
    # # --------------------------------------------------------------------------

    lamp_conf_dict = {0: {
        'name': 'Lamp.{:03d}'.format(0),
        'anchor': 0,
        'location': [0, -1, 10],
        'rotation': (1, 0, 0, 0),
        'local_rotation_angle': -45,  # config['light']['lamps']['local_rotation']['angle'],
        'local_rotation_axis': "X",  # config['light']['lamps']['local_rotation']['axis'],
        'scale': [1, -1, -1],  # camera_conf_dict[cid]['scale'],
        'energy': 35,  # config['light']['lamps']['energy']
    }}

    sun_location = [-3, -5, -5]
    sun_rotation = [0.3, 0.2, -0.9, 0.25]

    render_engine = 'EEVEE'
    render_image_format = 'JPEG'
    render_image_quality = 90

    objs = bpy.data.objects
    scene = bpy.data.scenes['Scene']
    meshes = bpy.data.meshes
    lights = bpy.data.lights
    cameras = bpy.data.cameras
    images = bpy.data.images

    if str.upper(render_engine) == 'EEVEE':
        scene.render.engine = 'BLENDER_EEVEE'
        scene.eevee.use_soft_shadows = True
    elif str.upper(render_engine) == 'CYCLES':
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'GPU'
    elif str.upper(render_engine) == 'WORKBENCH':
        scene.render.engine = 'BLENDER_WORKBENCH'
    else:
        raise ValueError(
            'Unsupported render engine {}. Please use one of "EEVEE", "CYCLES" and "WORKBENCH"'.format(render_engine))
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = render_image_format
    scene.render.image_settings.quality = render_image_quality

    # Remove the default objects
    meshes.remove(meshes['Cube'], do_unlink=True)
    lights.remove(lights['Light'], do_unlink=True)
    cameras.remove(cameras['Camera'], do_unlink=True)

    # ------------------------------ Setup cameras -----------------------------
    # for cid, camera_conf in camera_conf_dict.items():
    bpy.ops.object.camera_add()
    cam = bpy.context.selected_objects[0]
    cam.name = 'camera.001'
    cam.data.name = cam.name
    cam.location = (0, 0, 10)  # 'camera_conf['location']'
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (1, 0, 0, 0)  # camera_conf['rotation']
    cam.scale = (1, 1, 1)  # camera_conf['scale']
    cam.data.lens_unit = 'MILLIMETERS'  # 'FOV'
    cam.data.angle = 0.69  # camera_conf['fov']
    cam.data.show_background_images = True

    # ------------------------------ Setup lights ------------------------------
    for cid, lamp_conf in lamp_conf_dict.items():
        bpy.ops.object.light_add(type='AREA')
        lamp = bpy.context.selected_objects[0]
        lamp.name = lamp_conf['name']
        lamp.data.name = lamp.name
        lamp.data.energy = lamp_conf['energy']
        # NOTE Explicitly compute transformation, as we want to apply local rotation
        trans_mat = Matrix.Translation(lamp_conf['location'])
        rot_mat = Quaternion(lamp_conf['rotation']).to_matrix().to_4x4()
        scale_mat = Matrix.Scale(lamp_conf['scale'][0], 4, (1, 0, 0)) \
                    @ Matrix.Scale(lamp_conf['scale'][1], 4, (0, 1, 0)) \
                    @ Matrix.Scale(lamp_conf['scale'][2], 4, (0, 0, 1))
        local_rot_mat = Matrix.Rotation(math.radians(lamp_conf['local_rotation_angle']), 4,
                                        lamp_conf['local_rotation_axis'])
        lamp.matrix_world = trans_mat @ rot_mat @ scale_mat @ local_rot_mat

    bpy.ops.object.light_add(type='SUN')
    sun = bpy.context.selected_objects[0]
    sun.location = sun_location
    sun.rotation_mode = 'QUATERNION'
    sun.rotation_quaternion = sun_rotation

    # ---------------------------- Setup materials -----------------------------
    mat_body = bpy.data.materials.new('BodyMaterial')
    mat_body.use_nodes = True
    matnodes_body = mat_body.node_tree.nodes
    matnodes_body['Principled BSDF'].inputs[5].default_value = 0.1  # BSDF specular
    # matnodes_body['Principled BSDF'].inputs[17].default_value[0] = 1 # BSDF specular
    # matnodes_body['Principled BSDF'].inputs[17].default_value[1] = 1  # BSDF specular
    # matnodes_body['Principled BSDF'].inputs[17].default_value[2] = 1  # BSDF specular

    attr_body = matnodes_body.new("ShaderNodeTexImage")

    # ------------------------ Setup compositing nodes -------------------------
    scene.use_nodes = True
    scene_nodes = scene.node_tree.nodes
    image_node_scene = scene_nodes.new('CompositorNodeImage')
    mix_node_scene = scene_nodes.new('CompositorNodeMixRGB')
    mix_node_scene.use_alpha = True
    scene_links = scene.node_tree.links
    scene_links.new(scene_nodes['Render Layers'].outputs[0], mix_node_scene.inputs[2])
    scene_links.new(image_node_scene.outputs[0], mix_node_scene.inputs[1])
    scene_links.new(mix_node_scene.outputs[0], scene_nodes['Composite'].inputs[0])

    deselect_all()

    for fi in range(0, 1):  # mesh_num 329
        f = good_meshes[fi] - 1
        print('processing mesh number  ', f + 1, '  out of  ', mesh_num, '  meshes.')
        print('all_meshes_path', all_meshes_path)
        print('folder_list[f]', folder_list[f])
        print('texture_list[f]', texture_list[f])

        if not os.path.exists(all_meshes_path + folder_list[f] + "/images1"):
            os.mkdir(all_meshes_path + folder_list[f] + "/images1")

        # with stdout_redirected():
        print('now loading the human body')
        # -------------------------- Load human body ---------------------------
        newimg = images.load(all_meshes_path + folder_list[f] + '/tex/' + texture_list[f])
        attr_body.image = newimg
        mat_body.node_tree.links.new(attr_body.outputs[0], matnodes_body['Principled BSDF'].inputs[0])
        bpy.ops.import_scene.obj(filepath=all_meshes_path + folder_list[f] + '/' + mesh_list[f])

        obj_body = bpy.context.selected_objects[0]
        obj_body.location = [0, 0, 0]  # [1.38672, 2.76761, 1.19611]
        # obj_body.rotation_mode = 'QUATERNION'
        obj_body.rotation_euler = mathutils.Euler((math.radians(90.0), 0, 0), 'XYZ')
        obj_body.scale = [0.02, 0.02, 0.02]
        if obj_body.data.materials:
            obj_body.data.materials[0] = mat_body
        else:
            obj_body.data.materials.append(mat_body)
        bpy.ops.export_scene.obj(
            filepath=all_meshes_path + folder_list[f] + '/transformed_mesh/' + mesh_list[f], axis_forward='Y')

        # -------------------------- Render the scene --------------------------
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
        scene.render.filepath = all_meshes_path + folder_list[f] + "/images1/" + str(camera_names[0]) + ".jpg"

        print('bpy.ops.render.render(write_still=True)')
        bpy.ops.render.render(write_still=True)

        print('salam1 ')

        # images.remove(img, do_unlink=True)

        meshes.remove(obj_body.data, do_unlink=True)
        images.remove(newimg, do_unlink=True)


def main():
    # get the args passed to blender after "--", all of which are ignored by
    # blender so activeMoCap may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = (
            "Run blender in background mode with this script:"
            "  blender --background --python " + __file__ + " -- [options]"
    )
    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument('-c', '--config_file', type=str,
                        help='Configuration file.')

    args = parser.parse_args(argv)
    if not argv:
        parser.print_help()
        return

    with open(args.config_file, 'r') as f:
        config = json.load(f)

    synthesize_images(config)


if __name__ == '__main__':
    main()
