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

import yaml
from typing import Any, List, Tuple

from isaac_ros_launch_utils.all_types import (
    Action,
    ComposableNode,
    ComposableNodeContainer,
    LaunchDescription,
    LoadComposableNodes
)
import isaac_ros_launch_utils as lu

NVBLOX_CONFIG = 'nvblox_config'
CUVSLAM_CONFIG = 'cuvslam_config'
COMMON_CONFIG = 'common_config'


def get_nvblox_remappings(cameras: dict) -> List[Tuple[str, str]]:
    remappings = []

    for i in range(len(cameras)):
        depth = cameras[i].get('depth')
        color = cameras[i].get('color')
        remappings.append((f'camera_{i}/depth/image', depth.get('image')))
        remappings.append((f'camera_{i}/depth/camera_info', depth.get('info')))
        remappings.append((f'camera_{i}/color/image', color.get('image')))
        remappings.append((f'camera_{i}/color/camera_info', color.get('info')))
    return remappings


def get_nvblox_params(num_cameras: int, nvblox_config: dict, common_config: dict) -> List[Any]:

    parameters = []
    for config_file in nvblox_config.get('config_files', []):
        assert 'path' in config_file, 'No `path` provided in config_files'
        parameters.append(lu.get_path(config_file.get('package', 'isaac_ros_perceptor_bringup'),
                                      config_file.get('path')))
    parameters.extend(nvblox_config.get('parameters', []))
    parameters.append({'num_cameras': num_cameras})

    if 'robot_frame' in common_config:
        parameters.append({'map_clearing_frame_id': common_config.get('robot_frame')})
        parameters.append({'esdf_slice_bounds_visualization_attachment_frame_id':
                           common_config.get('robot_frame')})
        parameters.append({'workspace_height_bounds_visualization_attachment_frame_id':
                           common_config.get('robot_frame')})
    if 'odom_frame' in common_config:
        parameters.append({'global_frame': common_config.get('odom_frame')})

    parameters.append(
        lu.get_path('nvblox_examples_bringup',
                    'config/nvblox/specializations/nvblox_dynamics.yaml'))

    return parameters


def start_nvblox(args: lu.ArgumentContainer, nvblox_config: dict,
                 common_config: dict) -> List[Action]:

    cameras = nvblox_config.get('remappings', [])
    num_cameras = len(cameras)
    assert num_cameras != 0, 'You need to provide at least one input channel'
    assert num_cameras <= 4, 'No more than 4 input channels must be provided'

    parameters = get_nvblox_params(num_cameras, nvblox_config, common_config)

    remappings = get_nvblox_remappings(cameras)

    nvblox_node = ComposableNode(
        name=nvblox_config.get('node_name', 'nvblox_node'),
        package='nvblox_ros',
        plugin='nvblox::NvbloxNode',
        remappings=remappings,
        parameters=parameters,
    )

    actions = []

    container_name = nvblox_config.get('container_name', 'nvblox_container')

    if nvblox_config.get('attach_to_container', False):
        actions.append(
            LoadComposableNodes(
                target_container=container_name,
                composable_node_descriptions=[
                    nvblox_node
                ]
            ))
    else:
        actions.append(
            ComposableNodeContainer(
                name=container_name,
                package='rclcpp_components',
                namespace='',
                executable='component_container_mt',
                arguments=['--ros-args', '--log-level', args.log_level],
                composable_node_descriptions=[
                    nvblox_node,
                ],
            ))

    return actions


def start_cuvslam(args: lu.ArgumentContainer, cuvslam_config: dict, common_config: dict) -> Action:
    parameters = []
    remappings = []
    stereo_images = cuvslam_config.get('remappings', {}).get('stereo_images', [])
    assert len(stereo_images) != 0, 'You need to provide at least one input image pair'

    optical_frames = []
    for i in range(len(stereo_images)):
        idx = 2 * i
        left = stereo_images[i].get('left')
        right = stereo_images[i].get('right')
        assert 'image' in left, '`image` is missing in the left field'
        assert 'info' in left, '`info` is missing in the left field'
        assert 'optical_frame' in left, '`optical_frame` is missing in the left field'
        assert 'image' in right, '`image` is missing in the right field'
        assert 'info' in right, '`info` is missing in the right field'
        assert 'optical_frame' in right, '`optical_frame` is missing in the right field'
        remappings.append((f'visual_slam/image_{idx}', left.get('image')))
        remappings.append((f'visual_slam/camera_info_{idx}', left.get('info')))
        remappings.append((f'visual_slam/image_{idx + 1}', right.get('image')))
        remappings.append((f'visual_slam/camera_info_{idx + 1}', right.get('info')))
        optical_frames.append(left.get('optical_frame'))
        optical_frames.append(right.get('optical_frame'))

    # Add the imu topic if provided
    imu_topic = cuvslam_config.get('remappings', {}).get('imu')
    if imu_topic is not None:
        remappings.append(('visual_slam/imu', imu_topic))
        parameters.append({'enable_imu_fusion': True})

    parameters.append({'num_cameras': 2 * len(stereo_images)})
    parameters.append({'min_num_images': 2 * len(stereo_images)})
    parameters.append({'camera_optical_frames': optical_frames})
    for config_file in cuvslam_config.get('config_files', []):
        assert 'path' in config_file, 'No `path` provided in config_files'
        parameters.append(lu.get_path(config_file.get('package', 'isaac_ros_perceptor_bringup'),
                                      config_file.get('path')))
    parameters.extend(cuvslam_config.get('parameters', []))
    if 'odom_frame' in common_config:
        parameters.append({'odom_frame': common_config.get('odom_frame')})
    if 'map_frame' in common_config:
        parameters.append({'map_frame': common_config.get('map_frame')})
    if 'robot_frame' in common_config:
        parameters.append({'base_frame': common_config.get('robot_frame')})

    cuvslam_node = ComposableNode(
        name=cuvslam_config.get('node_name', 'cuvslam_node'),
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        remappings=remappings,
        parameters=parameters,
    )

    if cuvslam_config.get('attach_to_container', False):
        cuvslam_container = LoadComposableNodes(
            target_container=cuvslam_config.get('container_name', 'cuvslam_container'),
            composable_node_descriptions=[
                cuvslam_node
            ]
        )
    else:
        cuvslam_container = ComposableNodeContainer(
            name=cuvslam_config.get('container_name', 'cuvslam_container'),
            package='rclcpp_components',
            namespace='',
            executable='component_container_mt',
            arguments=['--ros-args', '--log-level', args.log_level],
            composable_node_descriptions=[
                cuvslam_node,
            ],
        )
    return cuvslam_container


def start_recording(args: lu.ArgumentContainer, config: dict) -> List[Action]:
    # Bag recording
    topics = config.get('extra_topics', [])

    if NVBLOX_CONFIG in config:
        cameras = config.get(NVBLOX_CONFIG).get('remappings', [])
        for i in range(len(cameras)):
            depth = cameras[i].get('depth')
            color = cameras[i].get('color')
            topics.append(depth.get('image'))
            topics.append(depth.get('info'))
            topics.append(color.get('image'))
            topics.append(color.get('info'))

    if CUVSLAM_CONFIG in config:
        remappings = config.get(CUVSLAM_CONFIG).get('remappings', {})
        if 'imu' in remappings:
            topics.append(remappings.get('imu'))
        cameras = remappings.get('stereo_images', [])
        for i in range(len(cameras)):
            left = cameras[i].get('left')
            right = cameras[i].get('right')
            topics.append(left.get('image'))
            topics.append(left.get('info'))
            topics.append(right.get('image'))
            topics.append(right.get('info'))

    topics = list(set(topics))
    record_action = lu.record_rosbag(topics=" ".join(topics), bag_path=args.rosbag_output)
    recording_started_msg =\
        '''\n\n\n
        -----------------------------------------------------
                    BAG RECORDING IS STARTING NOW

                 (make sure the rgbd cameras are up)
        -----------------------------------------------------

        List of topics:\n - ''' + "\n - ".join(topics)

    return [record_action, lu.log_info(recording_started_msg)]


def generate_launch_description_impl(args: lu.ArgumentContainer) -> List[Action]:
    config_file = lu.get_path('isaac_ros_perceptor_bringup', args.config_file)
    with open(config_file, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    actions = []
    if len(args.rosbag_output) > 0:
        actions.extend(start_recording(args, config))
    else:
        common_config = config.get(COMMON_CONFIG, {})
        if NVBLOX_CONFIG in config and lu.is_false(args.disable_nvblox):
            nvblox_config = config.get(NVBLOX_CONFIG)
            actions.extend(start_nvblox(args, nvblox_config, common_config))

        if CUVSLAM_CONFIG in config and lu.is_false(args.disable_cuvslam):
            actions.append(start_cuvslam(args, config.get(CUVSLAM_CONFIG), common_config))
    if 'urdf_transforms' in config:
        actions.append(
            lu.add_robot_description(robot_calibration_path=config.get('urdf_transforms')))

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/tools/visualization.launch.py',
            launch_arguments={'use_foxglove_whitelist': args.use_foxglove_whitelist},
        ))

    return actions


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('rosbag_output', '', description='Path to the output', cli=True)
    args.add_arg('disable_nvblox', False, description='Disable nvblox', cli=True)
    args.add_arg('disable_cuvslam', False, description='Disable cuvslam', cli=True)
    args.add_arg('log_level', 'info', choices=['debug', 'info', 'warn'], cli=True)
    args.add_arg('config_file', 'params/my_rgbd_perceptor.yaml',
                 description='Path to the config file', cli=True)
    args.add_arg('use_foxglove_whitelist', False, cli=True)

    args.add_opaque_function(generate_launch_description_impl)
    return LaunchDescription(args.get_launch_actions())
