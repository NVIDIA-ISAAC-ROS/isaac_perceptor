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

import pathlib

# flake8: noqa: F403,F405
from isaac_ros_launch_utils.all_types import *
import isaac_ros_launch_utils as lu


def add_rviz(args: lu.ArgumentContainer) -> list[Action]:
    if lu.is_valid(args.rviz_config):
        rviz_config_path = pathlib.Path(args.rviz_config)
    else:
        if lu.is_true(args.enable_people_segmentation):
            rviz_config_name = 'perceptor_people.rviz'
        else:
            rviz_config_name = 'perceptor.rviz'
        rviz_config_path = lu.get_path('isaac_ros_perceptor_bringup', 'params/' + rviz_config_name)

    actions = []
    assert rviz_config_path.exists(), f'Rviz config {rviz_config_path} does not exist.'
    actions.append(
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", str(rviz_config_path), "-f", args.rviz_frame],
            output="screen"))
    return actions


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('rviz_config', 'None', cli=True)
    args.add_arg('rviz_frame', 'odom')
    args.add_arg('enable_people_segmentation')

    args.add_opaque_function(add_rviz)
    return LaunchDescription(args.get_launch_actions())
