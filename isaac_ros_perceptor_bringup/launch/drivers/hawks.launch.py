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


def add_hawk(name: str, module_id: int, args: lu.ArgumentContainer) -> ComposableNode:
    node = ComposableNode(
        name=f'{name}_node',
        package='isaac_ros_hawk',
        plugin='nvidia::isaac_ros::hawk::HawkNode',
        namespace=name,
        remappings=[
            (f'/{name}/correlated_timestamp', '/correlated_timestamp'),
            (f'/{name}/left/camerainfo', f'/{name}/left/camera_info'),
            (f'/{name}/right/camerainfo', f'/{name}/right/camera_info'),
        ],
        parameters=[{
            'module_id': module_id,
            'camera_link_frame_name': name,
            'left_camera_frame_name': f'{name}_left',
            'right_camera_frame_name': f'{name}_right',
        }],
    )

    actions: list[Action] = []
    actions.append(lu.log_info(f"Adding hawk driver '{name}'."))
    actions.append(
        LoadComposableNodes(
            target_container=args.container_name,
            composable_node_descriptions=[node],
        ))

    return GroupAction(
        actions,
        condition=IfCondition(lu.has_substring(args.enabled_stereo_cameras, name)),
    )


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('container_name', 'nova_container')
    args.add_arg('enabled_stereo_cameras')
    actions = args.get_launch_actions()

    system_info = lu.get_nova_system_info()
    for sensor_name, sensor_config in system_info['sensors'].items():
        if sensor_config['type'] != 'hawk':
            continue
        if 'module_id' not in sensor_config:
            # This happens for the front_stereo_imu.
            continue
        actions.append(add_hawk(sensor_name, sensor_config['module_id'], args))

    return LaunchDescription(actions)