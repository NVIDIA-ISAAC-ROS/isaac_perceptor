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
    args.add_arg('device_path', '/dev/input/js0')
    args.add_arg('joy_config_file_path',
                 lu.get_path('isaac_ros_perceptor_bringup', 'params/joystick_ps5.yaml'))

    actions = args.get_launch_actions()
    actions.append(lu.log_info('Enabling joystick.'))
    actions.append(
        Node(
            package='joy_linux',
            executable='joy_linux_node',
            name='joy_linux_node',
            namespace='joy',
            parameters=[{
                'dev': args.device_path,
                'deadzone': 0.3,
                'autorepeat_rate': 20.0,
            }],
            on_exit=Shutdown(),
        ))

    actions.append(
        Node(
            package='teleop_twist_joy',
            executable='teleop_node',
            name='teleop_twist_joy_node',
            namespace='joy',
            parameters=[args.joy_config_file_path],
            on_exit=Shutdown(),
        ))

    actions.append(
        Node(
            package='teleop_twist_joy',
            executable='teleop_node',
            name='teleop_twist_joy_node',
            namespace='virtual_joy',
            parameters=[args.joy_config_file_path],
            on_exit=Shutdown(),
        ))

    return LaunchDescription(actions)
