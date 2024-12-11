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

def create_map_server(map_yaml_file:str, map_frame:str) -> Node:
    return Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': map_yaml_file,
            'frame_id': map_frame,
            'output': 'screen',
        }],
    )


def create_lifecycle_manager() -> TimerAction:
    return TimerAction(
        period=5.0,
        actions=[
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_map_server',
                parameters=[{
                    'autostart': True,
                    'node_names': ['map_server'],
                }],
            )
        ],
    )

def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('omap_frame', default='map')
    args.add_arg('occupancy_map_yaml_file')

    actions = args.get_launch_actions()
    actions.append(lu.log_info(["Loading occupancy map file from '", args.occupancy_map_yaml_file, "'"]))
    actions.append(create_map_server(args.occupancy_map_yaml_file, args.omap_frame))
    actions.append(create_lifecycle_manager())

    return LaunchDescription(actions)
