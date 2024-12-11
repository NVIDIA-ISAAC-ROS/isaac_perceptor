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
    args.add_arg('run_foxglove', True, cli=True)
    args.add_arg('run_rviz', False, cli=True)
    args.add_arg('use_foxglove_whitelist')
    args.add_arg('enable_people_segmentation')
    actions = args.get_launch_actions()

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/tools/foxglove_bridge.launch.py',
            launch_arguments={'use_foxglove_whitelist': args.use_foxglove_whitelist},
            condition=IfCondition(args.run_foxglove)))

    actions.append(
        lu.include(
            'isaac_ros_perceptor_bringup',
            'launch/tools/rviz.launch.py',
            launch_arguments={'enable_people_segmentation': args.enable_people_segmentation},
            condition=IfCondition(args.run_rviz)))

    return LaunchDescription(actions)
