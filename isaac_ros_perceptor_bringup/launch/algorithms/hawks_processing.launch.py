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

import os

from isaac_ros_launch_utils.all_types import *
import isaac_ros_launch_utils as lu
import isaac_ros_perceptor_constants as pc


def create_imager_pipeline(stereo_camera_name: str, identifier: str,
                           args: lu.ArgumentContainer) -> list[Action]:
    stereo_camera_config = getattr(args, stereo_camera_name)

    actions: list[Action] = []

    rectify_composable_node = ComposableNode(
        name='rectify_node',
        package='isaac_ros_image_proc',
        plugin='nvidia::isaac_ros::image_proc::RectifyNode',
        namespace=f'{stereo_camera_name}/{identifier}',
        parameters=[{
            'input_qos': 'SENSOR_DATA',
            'output_width': pc.HAWK_IMAGE_WIDTH,
            'output_height': pc.HAWK_IMAGE_HEIGHT,
        }],
    )
    rectify_condition = IfCondition(lu.has_substring(stereo_camera_config, 'rectify'))
    actions.append(
        lu.load_composable_nodes(
            args.container_name,
            [rectify_composable_node],
            condition=rectify_condition,
        ))

    return actions


def create_hawk_pipeline(stereo_camera_name: str, args: lu.ArgumentContainer) -> list[Action]:
    actions = []

    # Load the configuration for the stereo camera
    stereo_camera_config = getattr(args, stereo_camera_name)
    run_ess_light = lu.has_substring(stereo_camera_config, 'ess_light')
    run_ess_full = lu.has_substring(stereo_camera_config, 'ess_full')
    run_ess = OrSubstitution(run_ess_light, run_ess_full)

    actions.append(
        lu.assert_condition(
            'Camera config invalid. Can not run ess_light and ess_full at the same time.',
            IfCondition(AndSubstitution(run_ess_light, run_ess_full))),
    )
    engine_file_path = lu.if_else_substitution(run_ess_light, args.ess_light_engine_file_path,
                                               args.ess_full_engine_file_path)
    actions.append(lu.assert_path_exists(
        engine_file_path,
        condition=IfCondition(run_ess),
    ))
    ess_skip_frames = lu.has_substring(stereo_camera_config, 'ess_skip_frames')
    throttler_skip = lu.if_else_substitution(ess_skip_frames, args.ess_number_of_frames_to_skip,
                                             '0')

    # Run the left/right imager pipelines (rectify)
    actions.extend(create_imager_pipeline(stereo_camera_name, 'left', args))
    actions.extend(create_imager_pipeline(stereo_camera_name, 'right', args))

    # Run the depth estimation
    ess_composable_node = ComposableNode(
        name='ess_node',
        package='isaac_ros_ess',
        plugin='nvidia::isaac_ros::dnn_stereo_depth::ESSDisparityNode',
        namespace=stereo_camera_name,
        parameters=[{
            'engine_file_path': engine_file_path,
            'threshold': 0.4,
            'throttler_skip': throttler_skip,
        }],
        remappings=[
            ('left/camera_info', 'left/camera_info_rect'),
            ('left/image_raw', 'left/image_rect'),
            ('right/camera_info', 'right/camera_info_rect'),
            ('right/image_raw', 'right/image_rect'),
        ],
    )
    disparity_composable_node = ComposableNode(
        name='disparity_to_depth',
        package='isaac_ros_stereo_image_proc',
        plugin='nvidia::isaac_ros::stereo_image_proc::DisparityToDepthNode',
        namespace=stereo_camera_name,
    )
    depth_action = lu.load_composable_nodes(
        args.container_name, [ess_composable_node, disparity_composable_node],
        condition=IfCondition(run_ess))
    actions.append(depth_action)

    return actions


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()

    # Config strings for all stereo cameras.
    # The config string must be a subset of:
    # - driver,rectify,resize,ess_full,ess_light,ess_skip_frames,cuvslam,nvblox
    args.add_arg('front_stereo_camera')
    args.add_arg('back_stereo_camera')
    args.add_arg('left_stereo_camera')
    args.add_arg('right_stereo_camera')

    # Additional arguments
    args.add_arg('container_name', 'nova_container')
    args.add_arg('ess_number_of_frames_to_skip', 1)
    args.add_arg('ess_full_engine_file_path',
                 lu.get_isaac_ros_ws_path() +
                 '/isaac_ros_assets/models/dnn_stereo_disparity/dnn_stereo_disparity_v4.0.0/ess.engine')
    args.add_arg('ess_light_engine_file_path',
                 lu.get_isaac_ros_ws_path() +
                 '/isaac_ros_assets/models/dnn_stereo_disparity/dnn_stereo_disparity_v4.0.0/light_ess.engine')

    # Create pipelines for each camera according to the camera config
    actions = args.get_launch_actions()
    actions.extend(create_hawk_pipeline('front_stereo_camera', args))
    actions.extend(create_hawk_pipeline('back_stereo_camera', args))
    actions.extend(create_hawk_pipeline('left_stereo_camera', args))
    actions.extend(create_hawk_pipeline('right_stereo_camera', args))

    return LaunchDescription(actions)
