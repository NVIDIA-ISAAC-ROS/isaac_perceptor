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


def create_owl_pipeline(name: str, args: lu.ArgumentContainer) -> list[Action]:
    resize = ComposableNode(
        name=f'{name}_resize_node',
        package='isaac_ros_image_proc',
        plugin='nvidia::isaac_ros::image_proc::ResizeNode',
        namespace=name,
        parameters=[{
            'output_width': args.output_width,
            'output_height': args.output_height,
        }],
    )

    actions = []
    actions.append(
        LoadComposableNodes(
            target_container=args.container_name,
            composable_node_descriptions=[resize],
            condition=IfCondition(lu.has_substring(args.enabled_fisheye_cameras, name)),
        ))
    return actions


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('enabled_fisheye_cameras')
    args.add_arg('container_name', 'nova_container')
    args.add_arg('output_width', 192)
    args.add_arg('output_height', 120)

    actions = args.get_launch_actions()
    actions.extend(create_owl_pipeline('front_fisheye_camera', args))
    actions.extend(create_owl_pipeline('back_fisheye_camera', args))
    actions.extend(create_owl_pipeline('left_fisheye_camera', args))
    actions.extend(create_owl_pipeline('right_fisheye_camera', args))

    return LaunchDescription(actions)
