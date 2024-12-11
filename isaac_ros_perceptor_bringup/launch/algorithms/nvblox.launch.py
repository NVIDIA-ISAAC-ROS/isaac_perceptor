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

import isaac_ros_launch_utils.all_types as lut
import isaac_ros_launch_utils as lu

from nvblox_ros_python_utils.nvblox_launch_utils import NvbloxPeopleSegmentation

from typing import Any, List, Tuple


def get_nvblox_remappings(camera_names: List[str],
                          enable_people_segmentation: bool) -> List[Tuple[str, str]]:
    remappings = []
    for i, name in enumerate(camera_names):
        remappings.append((f'camera_{i}/depth/image', f'{name}/depth'))
        remappings.append((f'camera_{i}/depth/camera_info', f'{name}/camera_info'))
        # NOTE(alexmillane): If in people mapping mode the first camera subscribes to color
        #                    image coming from the segmentation graph.
        if enable_people_segmentation:
            remappings.append((f'camera_{i}/color/image', f'/{name}/segmentation/image_resized'))
            remappings.append((f'camera_{i}/color/camera_info',
                               f'/{name}/segmentation/camera_info_resized'))
            remappings.append((f'camera_{i}/mask/image', f'/{name}/segmentation/people_mask'))
            remappings.append((f'camera_{i}/mask/camera_info',
                               f'/{name}/segmentation/camera_info_resized'))
        else:
            remappings.append((f'camera_{i}/color/image', f'{name}/left/image_rect'))
            remappings.append((f'camera_{i}/color/camera_info', f'{name}/left/camera_info_rect'))
    return remappings


def get_nvblox_params(
    camera_names: List[str],
    enable_people_segmentation: bool,
    global_frame: str,
    param_filename: str,
) -> List[Any]:
    parameters = []
    parameters.append(lu.get_path('nvblox_examples_bringup', 'config/nvblox/nvblox_base.yaml'))

    # Dynamics is always enabled, unless we're running in people segmentation mode
    if enable_people_segmentation:
        parameters.append(
            lu.get_path('nvblox_examples_bringup',
                        'config/nvblox/specializations/nvblox_segmentation.yaml'))
    else:
        parameters.append(
            lu.get_path('nvblox_examples_bringup',
                        'config/nvblox/specializations/nvblox_dynamics.yaml'))

    parameters.append(lu.get_path('isaac_ros_perceptor_bringup', param_filename))
    parameters.append({'num_cameras': len(camera_names)})
    parameters.append({'global_frame': global_frame})

    return parameters


def add_nvblox(args: lu.ArgumentContainer) -> List[lut.Action]:
    camera_names = args.enabled_stereo_cameras_for_nvblox.split(',')
    enable_people_segmentation = len(args.enabled_stereo_cameras_for_nvblox_people) > 0

    remappings = get_nvblox_remappings(camera_names, enable_people_segmentation)
    parameters = get_nvblox_params(camera_names, enable_people_segmentation,
                                   args.nvblox_global_frame, args.param_filename)
    parameters.append({'after_shutdown_map_save_path': args.after_shutdown_map_save_path})

    # Add the nvblox node.
    nvblox_node = lut.ComposableNode(
        name='nvblox_node',
        package='nvblox_ros',
        plugin='nvblox::NvbloxNode',
        remappings=remappings,
        parameters=parameters,
    )

    actions = []
    actions.append(lu.load_composable_nodes(args.container_name, [nvblox_node]))
    actions.append(
        lu.log_info(["Enabling nvblox for cameras '",
                     args.enabled_stereo_cameras_for_nvblox, "'"]))

    # Add people segmentation if enabled.
    if enable_people_segmentation:
        camera_namespaces = []
        camera_input_topics = []
        input_camera_info_topics = []
        output_resized_image_topics = []
        output_resized_camera_info_topics = []
        for _, name in enumerate(camera_names):
            camera_namespaces.append(name)
            camera_input_topics.append(f'/{name}/left/image_rect')
            input_camera_info_topics.append(f'/{name}/left/camera_info_rect')
            output_resized_image_topics.append(f'/{name}/segmentation/image_resized')
            output_resized_camera_info_topics.append(f'/{name}/segmentation/camera_info_resized')

        actions.append(
            lu.include(
                'nvblox_examples_bringup',
                'launch/perception/segmentation.launch.py',
                launch_arguments={
                    'container_name': args.container_name,
                    'namespace_list': camera_namespaces,
                    'input_topic_list': camera_input_topics,
                    'input_camera_info_topic_list': input_camera_info_topics,
                    'output_resized_image_topic_list': output_resized_image_topics,
                    'output_resized_camera_info_topic_list': output_resized_camera_info_topics,
                    'num_cameras': len(camera_names),
                    # Isaac 3.0 enabled people seg only on front camera, and fps drops during
                    # replay is not reported.
                    'one_container_per_camera': False,
                    'people_segmentation': NvbloxPeopleSegmentation.peoplesemsegnet_vanilla,
                }))

    return actions


def generate_launch_description() -> lut.LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('enabled_stereo_cameras_for_nvblox')
    args.add_arg('enabled_stereo_cameras_for_nvblox_people')
    args.add_arg('container_name', 'nova_container')
    args.add_arg('param_filename', 'params/nvblox_perceptor.yaml')
    args.add_arg('after_shutdown_map_save_path', '')
    args.add_arg('nvblox_global_frame', 'odom')
    args.add_opaque_function(add_nvblox)
    return lut.LaunchDescription(args.get_launch_actions())
