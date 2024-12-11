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
    args.add_arg('container_name', 'nova_container')

    hesai_node = ComposableNode(
        package='isaac_ros_hesai',
        plugin='nvidia::isaac_ros::hesai::HesaiNode',
        name='hesai',
        namespace='front_3d_lidar',
        remappings=[
            ('pointcloud', 'lidar_points'),
        ],
    )

    load_hesai_pipeline = LoadComposableNodes(
        target_container=args.container_name,
        composable_node_descriptions=[
            hesai_node,
        ],
    )

    actions = args.get_launch_actions()
    actions.append(lu.log_info('Enabling 3D lidar.'))
    actions.append(load_hesai_pipeline)

    return LaunchDescription(actions)
