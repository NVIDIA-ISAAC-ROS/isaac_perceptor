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

# flake8: noqa: F403,F405
from isaac_ros_launch_utils.all_types import *
import isaac_ros_launch_utils as lu

# Camera config string is a subset of:
# - driver,rectify,ess_full,ess_light,ess_skip_frames,cuvslam,nvblox
perceptor_configurations = {
    'no_cameras': {
        'front_stereo_camera': '',
        'back_stereo_camera': '',
        'left_stereo_camera': '',
        'right_stereo_camera': '',
    },
    'front_configuration': {
        'front_stereo_camera': 'driver,rectify,ess_full,vgl,cuvslam,nvblox',
        'back_stereo_camera': '',
        'left_stereo_camera': '',
        'right_stereo_camera': '',
    },
    'front_people_configuration': {
        'front_stereo_camera': 'driver,rectify,ess_full,vgl,cuvslam,nvblox_people',
        'back_stereo_camera': '',
        'left_stereo_camera': '',
        'right_stereo_camera': '',
    },
    'front_left_right_configuration': {
        'front_stereo_camera': 'driver,rectify,ess_full,vgl,cuvslam,nvblox',
        'back_stereo_camera': '',
        'left_stereo_camera': 'driver,rectify,ess_light,ess_skip_frames,vgl,cuvslam,nvblox',
        'right_stereo_camera': 'driver,rectify,ess_light,ess_skip_frames,vgl,cuvslam,nvblox',
    },
    'front_left_right_vslam_configuration': {
        'front_stereo_camera': 'driver,rectify,ess_full,vgl,cuvslam,nvblox',
        'back_stereo_camera': '',
        'left_stereo_camera': 'driver,rectify,vgl,cuvslam',
        'right_stereo_camera': 'driver,rectify,vgl,cuvslam',
    },
    'front_back_left_right_vgl_configuration': {
        'front_stereo_camera': 'driver,rectify,ess_full,vgl,cuvslam,nvblox',
        'back_stereo_camera': 'driver,rectify,vgl',
        'left_stereo_camera': 'driver,rectify,ess_full,vgl,cuvslam,nvblox',
        'right_stereo_camera': 'driver,rectify,ess_full,vgl,cuvslam,nvblox',
    },
    'front_driver_rectify': {
        'front_stereo_camera': 'driver,rectify',
        'back_stereo_camera': '',
        'left_stereo_camera': '',
        'right_stereo_camera': '',
    },
    'front_left_right_configuration_nodriver': {
        'front_stereo_camera': 'ess_full,vgl,cuvslam,nvblox',
        'back_stereo_camera': '',
        'left_stereo_camera': 'ess_light,ess_skip_frames,vgl,cuvslam,nvblox',
        'right_stereo_camera': 'ess_light,ess_skip_frames,vgl,cuvslam,nvblox',
    },
    'front_back_left_right_vo_configuration': {
        'front_stereo_camera': 'driver,cuvslam',
        'back_stereo_camera': 'driver,cuvslam',
        'left_stereo_camera': 'driver,cuvslam',
        'right_stereo_camera': 'driver,cuvslam',
    },
    'front_left_right_ess_full_configuration': {
        'front_stereo_camera': 'driver,rectify,ess_full,cuvslam,nvblox',
        'back_stereo_camera': '',
        'left_stereo_camera': 'driver,rectify,ess_full,cuvslam,nvblox',
        'right_stereo_camera': 'driver,rectify,ess_full,cuvslam,nvblox',
    },
}

def remove_cuvslam_from_configuration(perceptor_configuration: Substitution):
    # Removing cuvslam steps from the perceptor configuration.
    return lu.remove_substring_from_dict_values(perceptor_configuration, 'cuvslam')


def remove_nvblox_from_configuration(perceptor_configuration: Substitution):
    # Removing ess and nvblox steps from the perceptor configuration.
    return lu.remove_substrings_from_dict_values(
        perceptor_configuration, ['ess_full', 'ess_light', 'ess_skip_frames', 'nvblox'])


def remove_vgl_from_configuration(perceptor_configuration: Substitution):
    # Removing camera localization steps from the perceptor configuration.
    return lu.remove_substring_from_dict_values(perceptor_configuration, 'vgl')

def load_perceptor_configuration(stereo_camera_configuration, disable_cuvslam, disable_nvblox, disable_vgl):
    perceptor_configuration = lu.get_dict_value(str(perceptor_configurations),
                                                stereo_camera_configuration)
    actions=[]
    # Remove cuvslam if cuvslam is disabled (e.g. when enabling wheel odometry).
    perceptor_configuration = lu.if_else_substitution(
        disable_cuvslam, remove_cuvslam_from_configuration(perceptor_configuration),
        perceptor_configuration)
    actions.append(lu.log_info("Disabling cuvslam.", IfCondition(disable_cuvslam)))

    # Remove nvblox (and ESS) if nvblox is disabled.
    perceptor_configuration = lu.if_else_substitution(
        disable_nvblox, remove_nvblox_from_configuration(perceptor_configuration),
        perceptor_configuration)
    actions.append(lu.log_info("Disabling nvblox.", IfCondition(disable_nvblox)))

    # Remove camera localization if camera localization is disabled.
    perceptor_configuration = lu.if_else_substitution(
        disable_vgl,
        remove_vgl_from_configuration(perceptor_configuration),
        perceptor_configuration)
    actions.append(lu.log_info("Disabling vgl.", IfCondition(disable_vgl)))

    # Remove rectify if both nvblox and camera localization are disabled
    # and stereo_camera_configuration is not front_driver_rectify
    front_driver_rectify = lu.is_equal(stereo_camera_configuration, 'front_driver_rectify')

    disable_rectify = AndSubstitution(
        AndSubstitution(disable_nvblox, disable_vgl),
        NotSubstitution(front_driver_rectify))
    perceptor_configuration = lu.if_else_substitution(
        disable_rectify, lu.remove_substrings_from_dict_values(perceptor_configuration,
                                                               ['rectify']),
        perceptor_configuration)
    actions.append(lu.log_info("Disabling camera rectification.", IfCondition(disable_rectify)))

    return perceptor_configuration, actions
