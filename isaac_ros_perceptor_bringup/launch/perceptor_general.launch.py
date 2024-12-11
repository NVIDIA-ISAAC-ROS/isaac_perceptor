# SPDX-FileCopyrightText: NVIDIA CORPORATION & AFFILIATES
# Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import isaac_ros_launch_utils.all_types as lut
import isaac_ros_launch_utils as lu


def generate_launch_description() -> lut.LaunchDescription:
    args = lu.ArgumentContainer()

    # Dictionary containing an item for all available hawk stereo cameras:
    # - front_stereo_camera, back_stereo_camera, left_stereo_camera, right_stereo_camera
    # The value of each camera key contains a config string listing
    # all the modules and options that should be run for this camera.
    # The config string must be a subset of:
    # - driver,rectify,resize,reformat,ess_full,ess_light,ess_skip_frames,cuvslam,nvblox,vgl
    # See an example configuration below:
    # {
    #     'front_stereo_camera': 'driver,rectify,resize,reformat,ess_light,ess_skip_frames,cuvslam,
    # nvblox,vgl',
    #     'back_stereo_camera': '',
    #     'left_stereo_camera': '',
    #     'right_stereo_camera': '',
    # }
    args.add_arg('perceptor_configuration')
    args.add_arg('nvblox_global_frame', 'odom')
    args.add_arg('vslam_odom_frame', 'odom')
    args.add_arg('vslam_map_frame', 'map')
    args.add_arg('vslam_image_qos', 'SENSOR_DATA')
    args.add_arg('invert_odom_to_base_tf', False)
    args.add_arg('nvblox_param_filename', 'params/nvblox_perceptor.yaml', cli=True)
    args.add_arg('nvblox_after_shutdown_map_save_path', '', cli=True)
    args.add_arg('occupancy_map_yaml_file', '')
    args.add_arg('is_sim', False)
    args.add_arg('enable_3d_lidar', False)

    enable_vslam = lu.dict_values_contain_substring(args.perceptor_configuration, 'cuvslam')
    enable_nvblox = lu.dict_values_contain_substring(args.perceptor_configuration, 'nvblox')
    enable_visual_global_localization = lu.dict_values_contain_substring(
        args.perceptor_configuration, 'vgl')

    vgl_enabled_stereo_cameras = lu.get_keys_with_substring_in_value(
        args.perceptor_configuration, 'vgl')
    vslam_enabled_stereo_cameras = lu.get_keys_with_substring_in_value(
        args.perceptor_configuration, 'cuvslam')
    enabled_stereo_cameras_for_nvblox = lu.get_keys_with_substring_in_value(
        args.perceptor_configuration, 'nvblox')
    enabled_stereo_cameras_for_nvblox_people = lu.get_keys_with_substring_in_value(
        args.perceptor_configuration, 'nvblox_people')

    actions = args.get_launch_actions()
    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/algorithms/hawks_processing.launch.py',
            launch_arguments={
                'front_stereo_camera': lu.get_dict_value(args.perceptor_configuration,
                                                         'front_stereo_camera'),
                'back_stereo_camera': lu.get_dict_value(args.perceptor_configuration,
                                                        'back_stereo_camera'),
                'left_stereo_camera': lu.get_dict_value(args.perceptor_configuration,
                                                        'left_stereo_camera'),
                'right_stereo_camera': lu.get_dict_value(args.perceptor_configuration,
                                                         'right_stereo_camera'),
            },
        ))
    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/algorithms/owls_processing.launch.py',
        ))
    actions.append(
        lu.include(
            'isaac_ros_visual_global_localization',
            'launch/include/visual_global_localization.launch.py',
            launch_arguments={
                'container_name': 'nova_container',
                'vgl_enabled_stereo_cameras': vgl_enabled_stereo_cameras,
                'vgl_rectified_images': True,
            },
            condition=lut.IfCondition(enable_visual_global_localization),
        ))
    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/algorithms/vslam.launch.py',
            launch_arguments={
                'vslam_enabled_stereo_cameras': vslam_enabled_stereo_cameras,
                'vslam_map_frame': args.vslam_map_frame,
                'vslam_odom_frame': args.vslam_odom_frame,
                'vslam_image_qos': args.vslam_image_qos,
                'invert_odom_to_base_tf': args.invert_odom_to_base_tf,
                'is_sim': args.is_sim,
            },
            condition=lut.IfCondition(enable_vslam),
        ))
    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/algorithms/nvblox.launch.py',
            launch_arguments={
                'enabled_stereo_cameras_for_nvblox': enabled_stereo_cameras_for_nvblox,
                'enabled_stereo_cameras_for_nvblox_people': (
                    enabled_stereo_cameras_for_nvblox_people),
                'nvblox_global_frame': args.nvblox_global_frame,
                'param_filename': args.nvblox_param_filename,
                'after_shutdown_map_save_path': args.nvblox_after_shutdown_map_save_path
            },
            condition=lut.IfCondition(enable_nvblox),
        ))

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/algorithms/occupancy_map_server.launch.py',
            condition=lut.IfCondition(lu.is_valid(args.occupancy_map_yaml_file)),
            launch_arguments={
                'occupancy_map_yaml_file': args.occupancy_map_yaml_file,
            },
        ))

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/algorithms/lidar_processing.launch.py',
            condition=lut.IfCondition(args.enable_3d_lidar),
        ))

    return lut.LaunchDescription(actions)
