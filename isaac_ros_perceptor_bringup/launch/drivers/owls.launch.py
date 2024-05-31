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


def add_owl(name: str, module_id: int, camera_id: int,
            args: lu.ArgumentContainer) -> ComposableNode:
    node = ComposableNode(
        name=f'{name}_node',
        package='isaac_ros_owl',
        plugin='nvidia::isaac_ros::owl::OwlNode',
        namespace=name,
        remappings=[
            (f'/{name}/correlated_timestamp', '/correlated_timestamp'),
            (f'/{name}/camerainfo', f'/{name}/camera_info'),
        ],
        parameters=[{
            'module_id': module_id,
            'camera_id': camera_id,
            'camera_link_frame_name': name,
            'optical_frame_name': f'{name}_optical',
        }],
    )

    actions: list[Action] = []
    actions.append(lu.log_info(f"Adding owl driver '{name}'."))
    actions.append(
        LoadComposableNodes(
            target_container=args.container_name,
            composable_node_descriptions=[node],
        ))

    return GroupAction(
        actions,
        condition=IfCondition(lu.has_substring(args.enabled_fisheye_cameras, name)),
    )


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('container_name', 'nova_container')
    args.add_arg('enabled_fisheye_cameras')
    actions = args.get_launch_actions()

    system_info = lu.get_nova_system_info()
    for sensor_name, sensor_config in system_info['sensors'].items():
        if sensor_config['type'] != 'owl':
            continue
        actions.append(
            add_owl(sensor_name, sensor_config['module_id'], sensor_config['camera_id'], args))

    return LaunchDescription(actions)