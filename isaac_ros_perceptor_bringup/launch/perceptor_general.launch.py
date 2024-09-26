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

from isaac_ros_launch_utils.all_types import *
import isaac_ros_launch_utils as lu


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()

    # Dictionary containing an item for all available hawk stereo cameras:
    # - front_stereo_camera, back_stereo_camera, left_stereo_camera, right_stereo_camera
    # The value of each camera key contains a config string listing
    # all the modules and options that should be run for this camera.
    # The config string must be a subset of:
    # - driver,rectify,resize,reformat,ess_full,ess_light,ess_skip_frames,cuvslam,nvblox
    # See an example configuration below:
    # {
    #     'front_stereo_camera': 'driver,rectify,resize,reformat,ess_light,ess_skip_frames,cuvslam,nvblox',
    #     'back_stereo_camera': '',
    #     'left_stereo_camera': '',
    #     'right_stereo_camera': '',
    # }
    args.add_arg('perceptor_configuration')
    args.add_arg('global_frame', 'odom')
    args.add_arg('vslam_image_qos', 'SENSOR_DATA')
    args.add_arg('invert_odom_to_base_tf', False)

    enable_vslam = lu.dict_values_contain_substring(args.perceptor_configuration, 'cuvslam')
    enable_nvblox = lu.dict_values_contain_substring(args.perceptor_configuration, 'nvblox')

    enabled_stereo_cameras_for_vslam = lu.get_keys_with_substring_in_value(
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
            'isaac_ros_perceptor_bringup',
            'launch/algorithms/vslam.launch.py',
            launch_arguments={
                'enabled_stereo_cameras_for_vslam': enabled_stereo_cameras_for_vslam,
                'global_frame': args.global_frame,
                'image_qos': args.vslam_image_qos,
                'invert_odom_to_base_tf': args.invert_odom_to_base_tf,
            },
            condition=IfCondition(enable_vslam),
        ))
    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/algorithms/nvblox.launch.py',
            launch_arguments={
                'enabled_stereo_cameras_for_nvblox': enabled_stereo_cameras_for_nvblox,
                'enabled_stereo_cameras_for_nvblox_people': enabled_stereo_cameras_for_nvblox_people,
                'global_frame': args.global_frame
            },
            condition=IfCondition(enable_nvblox),
        ))

    return LaunchDescription(actions)
