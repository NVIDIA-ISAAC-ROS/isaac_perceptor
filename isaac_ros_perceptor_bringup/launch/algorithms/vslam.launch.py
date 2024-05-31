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

from typing import Tuple


def remap(i: int, name: str, identifier: str) -> list[Tuple[str, str]]:
    return [
        (f'visual_slam/image_{i}', f'/{name}/{identifier}/image_raw'),
        (f'visual_slam/camera_info_{i}', f'/{name}/{identifier}/camera_info'),
    ]


def add_vslam(args: lu.ArgumentContainer) -> list[Action]:
    camera_names = args.enabled_stereo_cameras_for_vslam.split(',')

    camera_optical_frames = []
    remappings = [('visual_slam/imu', '/front_stereo_imu/imu')]
    for i, camera_name in enumerate(camera_names):
        camera_optical_frames.append(f'{camera_name}_left_optical')
        camera_optical_frames.append(f'{camera_name}_right_optical')
        remappings.extend(remap(2 * i, camera_name, 'left'))
        remappings.extend(remap(2 * i + 1, camera_name, 'right'))

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            # Images:
            'num_cameras': 2 * len(camera_names),
            'min_num_images': 2 * len(camera_names),
            'enable_image_denoising': False,
            'enable_localization_n_mapping': ParameterValue(args.enable_slam_for_vslam, value_type=bool),
            'enable_ground_constraint_in_odometry': True,
            'enable_imu_fusion': ParameterValue(args.enable_imu_for_vslam, value_type=bool),
            'gyro_noise_density': 0.000244,
            'gyro_random_walk': 0.000019393,
            'accel_noise_density': 0.001862,
            'accel_random_walk': 0.003,
            'calibration_frequency': 200.0,
            # It's recommended to use image masking with unrectified images.
            'rectified_images': False,
            'img_mask_bottom': 30,
            'img_mask_left': 150,
            'img_mask_right': 30,
            # Frames:
            'map_frame': 'map',
            'odom_frame': args.global_frame,
            'base_frame': 'base_link',
            'imu_frame': 'front_stereo_camera_imu',
            'publish_map_to_odom_tf': False,
            'invert_odom_to_base_tf': args.invert_odom_to_base_tf,
            # Visualization:
            'path_max_size': 1024,
            'enable_slam_visualization': False,
            'enable_landmarks_view': False,
            'enable_observations_view': False,
        }],
        remappings=remappings,
    )

    actions = []
    actions.append(lu.load_composable_nodes(args.container_name, [visual_slam_node]))
    actions.append(
        lu.log_info(["Enabling vslam for cameras '", args.enabled_stereo_cameras_for_vslam, "'"]))

    return actions


def generate_launch_description() -> LaunchDescription:
    args = lu.ArgumentContainer()
    args.add_arg('enabled_stereo_cameras_for_vslam')
    args.add_arg('enable_imu_for_vslam', False)
    args.add_arg('enable_slam_for_vslam', False)
    args.add_arg('min_num_images_used_in_vslam', 2)
    args.add_arg('container_name', 'nova_container')
    args.add_arg('global_frame', 'odom')
    args.add_arg('invert_odom_to_base_tf', False)
    args.add_arg('publish_odom_to_base_tf', True)
    args.add_opaque_function(add_vslam)

    return LaunchDescription(args.get_launch_actions())
