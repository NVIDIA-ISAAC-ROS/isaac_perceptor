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

from typing import List
from isaac_ros_launch_utils.all_types import *
from isaac_ros_launch_utils import ArgumentContainer
from launch.action import Action
import isaac_ros_launch_utils as lu

# Whitelisted topics are the only ones propagated to Foxglove. Set "use_foxglove_whitelist:=False"
# to make all topics available.
TOPIC_WHITELIST = [
    # nvblox
    '/nvblox_human_node/.*_layer',
    '/nvblox_human_node/combined_esdf_pointcloud',
    '/nvblox_node/.*_layer',
    '/nvblox_node/map_slice_bounds',
    '/nvblox_node/mesh',
    '/nvblox_node/static_esdf_pointcloud',
    # CUVSLAM
    '/visual_slam/status',
    '/visual_slam/tracking/odometry',
    '/visual_slam/tracking/slam_path',
    '/visual_slam/tracking/vo_path',
    '/visual_slam/tracking/vo_pose',
    '/visual_slam/vis/landmarks_cloud',
    '/visual_slam/vis/observations_cloud',
    # Navigation
    '/map',
    '/plan',
    '/local_costmap/costmap',
    '/local_costmap/local_costmap',
    '/local_costmap/published_footprint',
    '/global_costmap/costmap',
    '/global_costmap/global_costmap',
    '/global_costmap/published_footprint',
    '/initialpose',
    '/goal_pose',
    # Lidar
    '/back_2d_lidar/scan',
    '/front_2d_lidar/scan',
    '/front_3d_lidar/scan',
    # Robot
    '/robot_description',
    '/tf',
    '/tf_static',
    '/diagnostics',
]

IMAGE_TOPIC_WHITELIST = ["depth", "left/image_resized"]


def get_topic_whitelist():
    topic_whitelist = TOPIC_WHITELIST

    for camera in [
            '/front_stereo_camera', '/back_stereo_camera', '/left_stereo_camera',
            '/right_stereo_camera'
    ]:
        topic_whitelist.extend([f'{camera}/{topic}' for topic in IMAGE_TOPIC_WHITELIST])

    return topic_whitelist


def add_foxglove(args: lu.ArgumentContainer) -> List[Action]:

    params = [{
        'send_buffer_limit': int(args.send_buffer_limit),
        'max_qos_depth': 1,
        'use_compression': False,
        'capabilities': ['clientPublish', 'connectionGraph', 'assets'],
    }]

    if lu.is_true(args.use_foxglove_whitelist):
        params[0].update({'topic_whitelist': get_topic_whitelist()})

    actions = []
    actions.append(
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            parameters=params,
            # Use error log level to reduce terminal cluttering from "send_buffer_limit reached" warnings.
            arguments=['--ros-args', '--log-level', 'ERROR'],
        ))

    return actions


def generate_launch_description() -> LaunchDescription:
    args = ArgumentContainer()
    args.add_arg('send_buffer_limit', 10000000)
    args.add_arg('use_foxglove_whitelist', True)

    args.add_opaque_function(add_foxglove)
    return LaunchDescription(args.get_launch_actions())
