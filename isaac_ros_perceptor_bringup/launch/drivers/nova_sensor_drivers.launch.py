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
    args.add_arg('enable_3d_lidar')
    args.add_arg('enabled_2d_lidars')
    args.add_arg('enabled_stereo_cameras')
    args.add_arg('enabled_fisheye_cameras')
    args.add_arg('container_name', 'nova_container')

    actions = args.get_launch_actions()

    enabled_cameras = lu.union(args.enabled_stereo_cameras, args.enabled_fisheye_cameras)
    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/drivers/correlated_timestamp_driver.launch.py',
            launch_arguments=dict(container_name=args.container_name),
            condition=IfCondition(lu.is_valid(enabled_cameras)),
        ))

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/drivers/rplidars.launch.py',
            launch_arguments=dict(container_name=args.container_name),
            condition=IfCondition(lu.is_valid(args.enabled_2d_lidars)),
        ))

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/drivers/hesai.launch.py',
            launch_arguments=dict(container_name=args.container_name),
            condition=IfCondition(args.enable_3d_lidar),
        ))

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/drivers/hawks.launch.py',
            launch_arguments=dict(container_name=args.container_name),
            condition=IfCondition(lu.is_valid(args.enabled_stereo_cameras)),
        ))

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/drivers/owls.launch.py',
            launch_arguments=dict(container_name=args.container_name),
            condition=IfCondition(lu.is_valid(args.enabled_fisheye_cameras)),
        ))

    return LaunchDescription(actions)
