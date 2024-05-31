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
import isaac_ros_perceptor_constants as pc

from nvblox_ros_python_utils.nvblox_launch_utils import NvbloxPeopleSegmentation
import nvblox_ros_python_utils.nvblox_constants as nc

from typing import Any, List, Tuple


def get_nvblox_remappings(camera_names: List[str],
                          enable_people_segmentation: bool) -> List[Tuple[str, str]]:
    remappings = []
    for i, name in enumerate(camera_names):
        remappings.append((f'camera_{i}/depth/image', f'{name}/depth'))
        remappings.append((f'camera_{i}/depth/camera_info', f'{name}/camera_info'))
        # NOTE(alexmillane): If in people mapping mode the first camera subscribes to color
        #                    image coming from the segmentation graph.
        if enable_people_segmentation and name == 'front_stereo_camera':
            remappings.append((f'camera_{i}/color/image', f'/segmentation/image_resized'))
            remappings.append((f'camera_{i}/color/camera_info', f'/segmentation/camera_info_resized'))
        else:
            remappings.append((f'camera_{i}/color/image', f'{name}/left/image_rect'))
            remappings.append((f'camera_{i}/color/camera_info', f'{name}/left/camera_info_rect'))
    if enable_people_segmentation:
        remappings.append((f'mask/image', f'/unet/raw_segmentation_mask'))
        remappings.append((f'mask/camera_info', f'/segmentation/camera_info_resized'))
    return remappings


def get_nvblox_params(camera_names: List[str], enable_people_segmentation: bool,
                      global_frame: str) -> List[Any]:
    parameters = []
    parameters.append(lu.get_path('nvblox_examples_bringup', 'config/nvblox/nvblox_base.yaml'))
    parameters.append(lu.get_path('isaac_ros_perceptor_bringup', 'params/nvblox_perceptor.yaml'))
    parameters.append({'num_cameras': len(camera_names)})
    parameters.append({'global_frame': global_frame})
    if enable_people_segmentation:
        parameters.append(
            lu.get_path('nvblox_examples_bringup',
                        'config/nvblox/specializations/nvblox_segmentation.yaml'))
    return parameters


def check_valid_nvblox_configuration(args: lu.ArgumentContainer, enable_people_segmentation: bool):
    if enable_people_segmentation:
        # For now, we only allow people segmentation on the front camera.
        segmentation_camera_names = args.enabled_stereo_cameras_for_nvblox_people.split(',')
        assert len(
            segmentation_camera_names) <= 1, 'People segmentation is only possible for one camera.'
        assert segmentation_camera_names[0] == 'front_stereo_camera', \
            'People segmentation is only possible for the front stereo camera.'


def add_nvblox(args: lu.ArgumentContainer) -> List[Action]:
    camera_names = args.enabled_stereo_cameras_for_nvblox.split(',')
    enable_people_segmentation = len(args.enabled_stereo_cameras_for_nvblox_people) > 0

    remappings = get_nvblox_remappings(camera_names, enable_people_segmentation)
    parameters = get_nvblox_params(camera_names, enable_people_segmentation, args.global_frame)
    check_valid_nvblox_configuration(args, enable_people_segmentation)

    # Add the nvblox node.
    if enable_people_segmentation:
        nvblox_node_name = 'nvblox_human_node'
        nvblox_plugin_name = 'nvblox::NvbloxHumanNode'
    else:
        nvblox_node_name = 'nvblox_node'
        nvblox_plugin_name = 'nvblox::NvbloxNode'

    nvblox_node = ComposableNode(
        name=nvblox_node_name,
        package='nvblox_ros',
        plugin=nvblox_plugin_name,
        remappings=remappings,
        parameters=parameters,
    )

    actions = []
    actions.append(lu.load_composable_nodes(args.container_name, [nvblox_node]))
    actions.append(
        lu.log_info(["Enabling nvblox for cameras '", args.enabled_stereo_cameras_for_nvblox, "'"]))

    # Add people segmentation if enabled.
    if enable_people_segmentation:
        actions.append(
            lu.include(
                'nvblox_examples_bringup',
                'launch/perception/segmentation.launch.py',
                launch_arguments={
                    'container_name': args.container_name,
                    'input_topic': '/front_stereo_camera/left/image_rect',
                    'input_camera_info_topic': '/front_stereo_camera/left/camera_info_rect',
                    'people_segmentation': NvbloxPeopleSegmentation.peoplesemsegnet_shuffleseg,
                }))

    return actions


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('enabled_stereo_cameras_for_nvblox')
    args.add_arg('enabled_stereo_cameras_for_nvblox_people')
    args.add_arg('container_name', 'nova_container')
    args.add_arg('global_frame', 'odom')
    args.add_opaque_function(add_nvblox)
    return LaunchDescription(args.get_launch_actions())
