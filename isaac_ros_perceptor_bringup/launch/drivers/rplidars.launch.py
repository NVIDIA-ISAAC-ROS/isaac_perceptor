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


def add_rplidar(name: str, ip: str, enabled_2d_lidars: LaunchConfiguration,
                container_name: LaunchConfiguration) -> Action:
    driver_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name=f'{name}_node',
        parameters=[{
            'channel_type': 'udp',
            'udp_ip': ip,
            'udp_port': 8089,
            'frame_id': name,
            'inverted': False,
            'angle_compensate': True,
            'scan_mode': 'Sensitivity'
        }],
        namespace=name,
        on_exit=Shutdown(),
    )

    laserscan_to_flatscan_node = ComposableNode(
        package='isaac_ros_pointcloud_utils',
        plugin='nvidia::isaac_ros::pointcloud_utils::LaserScantoFlatScanNode',
        name='laserscan_to_flatscan',
        namespace=name,
    )

    load_composable_node = LoadComposableNodes(
        target_container=container_name,
        composable_node_descriptions=[laserscan_to_flatscan_node],
    )

    return GroupAction(
        actions=[
            driver_node,
            load_composable_node,
            lu.log_info(["Enabling 2D lidar: '", name, "'"]),
        ],
        condition=IfCondition(lu.has_substring(enabled_2d_lidars, name)),
    )


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('enabled_2d_lidars')
    args.add_arg('container_name', 'nova_container')

    actions = args.get_launch_actions()
    actions.append(
        lu.log_info(["Enabling 2D lidars: '", args.enabled_2d_lidars, "'"]))

    system_info = lu.get_nova_system_info()
    for sensor_name, sensor_config in system_info['sensors'].items():
        if sensor_config['type'] != 'rplidar':
            continue
        actions.append(
            add_rplidar(sensor_name, sensor_config['ip'],
                        args.enabled_2d_lidars, args.container_name))
    return LaunchDescription(actions)