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
    """
    This launch file creates an abstraction for the Nova sensor suite. It allows to switch
    between using the real sensors, the simulated sensors from Isaac Sim or an rosbag.
    """
    args = lu.ArgumentContainer()
    args.add_arg('mode', choices=['real_world', 'simulation', 'rosbag'])
    args.add_arg('rosbag')
    args.add_arg('enabled_stereo_cameras')
    args.add_arg('type_negotiation_duration_s')
    actions = args.get_launch_actions()

    # Sensor data from ROS 2 bag.
    actions.append(
        lu.include(
            'isaac_ros_data_replayer',
            'launch/include/data_replayer_include.launch.py',
            launch_arguments={
                'rosbag': args.rosbag,
                'replay_delay': args.type_negotiation_duration_s,
                'enabled_stereo_cameras': args.enabled_stereo_cameras,
            },
            condition=IfCondition(lu.is_equal(args.mode, 'rosbag')),
        ))

    # Sensor data from physical sensor drivers.
    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/drivers/nova_sensor_drivers.launch.py',
            launch_arguments={
                'enabled_stereo_cameras': args.enabled_stereo_cameras,
            },
            condition=IfCondition(lu.is_equal(args.mode, 'real_world')),
        ))

    return LaunchDescription(actions)
