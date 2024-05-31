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
    args.add_arg('map_yaml_path')
    args.add_arg('enable_3d_lidar_localization')
    args.add_arg('container_name', 'nova_container')

    actions = args.get_launch_actions()

    scan_topic = lu.if_else_substitution(args.enable_3d_lidar_localization,
                                         '/front_3d_lidar/flatscan',
                                         '/front_2d_lidar/flatscan')

    occupancy_grid_localizer = ComposableNode(
        package='isaac_ros_occupancy_grid_localizer',
        plugin=
        'nvidia::isaac_ros::occupancy_grid_localizer::OccupancyGridLocalizerNode',
        name='occupancy_grid_localizer',
        parameters=[
            args.map_yaml_path,
            {
                'loc_result_frame': 'map',
                'map_yaml_path': args.map_yaml_path,
            },
        ],
        remappings=[
            ('localization_result', '/initialpose'),
            ('flatscan', scan_topic),
        ])

    actions.append(
        LoadComposableNodes(
            target_container=args.container_name,
            composable_node_descriptions=[occupancy_grid_localizer],
        ))

    return LaunchDescription(actions)