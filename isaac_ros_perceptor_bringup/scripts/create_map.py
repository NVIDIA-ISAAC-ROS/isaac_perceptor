#!/usr/bin/env python3

import argparse
import datetime
import os
import pathlib
import subprocess
import time
import shutil


import ament_index_python.packages

from isaac_common_py import subprocess_utils
from isaac_common_py import filesystem_utils

ROS_WS = pathlib.Path(os.environ.get('ISAAC_ROS_WS'))


def get_path(package: str, path: str) -> pathlib.Path:
    package_share = pathlib.Path(ament_index_python.packages.get_package_share_directory(package))
    return package_share / path


def parse_args():
    parser = argparse.ArgumentParser(description='Script to build multiple maps from a rosbag.')
    parser.add_argument(
        '--sensor_data_bag',
        required=True,
        type=pathlib.Path,
        help='Path to the sensor data rosbag file.',
    )
    parser.add_argument(
        '--base_output_folder',
        default='/mnt/nova_ssd/maps',
        type=pathlib.Path,
        help='Base output folder for the generated maps.',
    )
    parser.add_argument(
        '--replay_rate',
        default=0.1,
        type=float,
        help='Replay rate for the rosbag playback.',
    )
    parser.add_argument(
        '--stereo_camera_configuration',
        default='front_left_right_configuration',
        help='Stereo camera configuration to use.',
    )
    parser.add_argument(
        '--prebuilt_bow_vocabulary_folder',
        type=pathlib.Path,
        default=None,
        help='Folder containing prebuilt BoW vocabulary files.',
    )
    parser.add_argument(
        '--print_mode',
        type=str,
        default='tail',
        choices=['none', 'tail', 'all'],
        help='Determines what is printed to stdout.',
    )
    parser.add_argument(
        '--steps_to_run',
        nargs='+',
        choices=['cuvslam', 'occupancy', 'keyframes', 'cuvgl'],
        help='Specify which steps to run.',
    )
    parser.add_argument(
        '--map_dir',
        type=pathlib.Path,
        help='Directory containing existing map data.',
    )
    parser.add_argument(
        '--remap_tf',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='If set, remap /tf to /tf_old.',
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Setup the output folder.
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    bag_name = args.sensor_data_bag.name
    if not args.map_dir:
        output_folder = filesystem_utils.create_workdir(
            args.base_output_folder,
            f'{timestamp}_{bag_name}',
            allow_sudo=True,
        )
    else:
        output_folder = args.map_dir
    print(f'Storing all maps and logs in {output_folder}.')

    poses_bag = output_folder / 'poses'
    log_folder = output_folder / 'logs'
    log_folder.mkdir(parents=True, exist_ok=True)

    # Create a metadata file.
    metadata_file = output_folder / 'metadata.yaml'
    metadata_file.write_text(f'output_folder: {output_folder}\n')

    steps_to_run = args.steps_to_run if args.steps_to_run else [
        'cuvslam', 'occupancy', 'keyframes', 'cuvgl'
    ]

    if 'cuvslam' in steps_to_run:
        create_cuvslam_map(args.sensor_data_bag, output_folder, log_folder, args.print_mode)

    if 'occupancy' in steps_to_run:
        create_global_occupancy_map(args.sensor_data_bag, output_folder, log_folder,
                                    args.replay_rate, args.stereo_camera_configuration,
                                    args.print_mode, args.remap_tf)

    cuvgl_map_folder = output_folder / 'cuvgl_map'
    cuvgl_map_folder.mkdir(parents=True, exist_ok=True)
    if 'keyframes' in steps_to_run:
        extract_keyframes(args.sensor_data_bag, poses_bag, cuvgl_map_folder, args.print_mode)

    if 'cuvgl' in steps_to_run:
        create_cuvgl_map(cuvgl_map_folder, args.print_mode, args.prebuilt_bow_vocabulary_folder)

    print(f'All maps can be found in {output_folder}.')


def create_cuvslam_map(sensor_data_bag: pathlib.Path, output_folder: pathlib.Path,
                       log_folder: pathlib.Path, print_mode: str):
    # Extract the EDEX.
    subprocess_utils.run_command(
        mnemonic='Install pip requirements',
        command=[
            'python3', '-m', 'pip', 'install', '-r',
            get_path('isaac_ros_rosbag_utils', 'requirements.txt')
        ],
        log_file=log_folder / 'install_requirements.log',
        print_mode=print_mode,
    )
    edex_path = output_folder / 'edex'
    subprocess_utils.run_command(
        mnemonic='Extract EDEX',
        command=[
            'ros2',
            'run',
            'isaac_ros_rosbag_utils',
            'extract_edex',
            '--config_path',
            get_path('isaac_ros_rosbag_utils', 'config/edex_extraction_nova.yaml'),
            f'--rosbag_path={sensor_data_bag}',
            f'--edex_path={edex_path}',
        ],
        log_file=log_folder / 'extract_edex.log',
        print_mode=print_mode,
    )

    # Create the cuVSLAM map.
    additional_path = get_path('isaac_ros_visual_slam', '../cuvslam/lib/').resolve()
    ld_library_path = os.environ['LD_LIBRARY_PATH']
    os.environ['LD_LIBRARY_PATH'] = f'{ld_library_path}:{additional_path}'
    subprocess_utils.run_command(
        mnemonic='Create cuVSLAM map',
        command=[
            'ros2',
            'run',
            'isaac_ros_visual_slam',
            'cuvslam_api_launcher',
            f'--dataset={edex_path}',
            f'--output_map={output_folder/"cuvslam_map"}',
            '--ros_frame_conversion=true',
            '--cfg_enable_slam=true',
            '--cfg_sync_slam',
            '--max_fps=15',
            '--print_format=tum',
            f'--print_odom_poses={output_folder/"odom_poses.tum"}',
            f'--print_slam_poses={output_folder/"slam_poses.tum"}',
        ],
        log_file=log_folder / 'create_cuvslam_map.log',
        print_mode=print_mode,
    )


def create_global_occupancy_map(sensor_data_bag: pathlib.Path, output_folder: pathlib.Path,
                                log_folder: pathlib.Path, replay_rate: float,
                                stereo_camera_configuration: str, print_mode: str,
                                remap_tf: bool = True):
    print("Starting recording pose rosbag...")

    # Create the occupancy map and store the poses:
    poses_bag = output_folder / 'poses'

    # Remove the folder pose bag first if it exists
    if poses_bag.exists():
        shutil.rmtree(poses_bag)

    record_command = [
        'ros2',
        'bag',
        'record',
        '--storage',
        'mcap',
        '--output',
        str(poses_bag),
        '/visual_slam/vis/slam_odometry',
    ]

    record_rosbag = subprocess.Popen(
        record_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    rosbag_record_initialized = False
    timeout = 30  # Timeout in seconds
    start_time = time.time()

    while not rosbag_record_initialized and time.time() - start_time < timeout:
        output = record_rosbag.stdout.readline()
        if output:
            print(f"Subprocess output: {output.strip()}")
            if "Recording..." in output:
                rosbag_record_initialized = True
                break
        else:
            time.sleep(0.1)  # Short sleep to prevent CPU overuse

    if not rosbag_record_initialized:
        print("Failed to record rosbag or timed out")
        record_rosbag.terminate()
    else:
        print("Rosbag recording is running")

    print("Creating global occupancy map...")

    # Localize in the cuVSLAM map and create the occupancy map
    command = [
            'ros2',
            'launch',
            'nova_carter_bringup',
            'perceptor.launch.py',
            'nvblox_param_filename:=params/nvblox_global_mapping.yaml',
            'mode:=rosbag',
            f'rosbag:={sensor_data_bag}',
            f'vslam_load_map_folder_path:={output_folder / "cuvslam_map"}',
            'vslam_localize_on_startup:=True',
            f'replay_rate:={replay_rate}',
            f'stereo_camera_configuration:={stereo_camera_configuration}',
            f'nvblox_after_shutdown_map_save_path:={output_folder / "occupancy_map"}',
            'replay_shutdown_on_exit:=True',
            'nvblox_global_frame:=map',
            'vslam_enable_slam:=True',
        ]

    if remap_tf:
        command.append('replay_additional_args:=--remap /tf:=/tf_old')

    subprocess_utils.run_command(
        mnemonic='Create global occupancy map',
        command=command,
        log_file=log_folder / 'create_global_occupancy_map.log',
        print_mode=print_mode,
        allow_failure=True,
    )

    record_rosbag.terminate()
    record_rosbag.wait()


def extract_keyframes(sensor_data_bag: pathlib.Path, poses_bag: pathlib.Path,
                      cuvgl_map_folder: pathlib.Path, print_mode: str):
    # Extract keyframes.
    keyframes_folder = cuvgl_map_folder / 'keyframes'
    command = [
        'ros2',
        'run',
        'isaac_mapping_ros',
        'run_rosbag_to_mapping_data.py',
        f'--sensor_data_bag={sensor_data_bag}',
        f'--pose_bag={poses_bag}',
        f'--output_folder={keyframes_folder}',
        '--extract_feature',
        '--rot_dist=5',
        '--trans_dist=0.2',
        f'--print_mode={print_mode}',
    ]
    subprocess.run(command, check=True)


def create_cuvgl_map(cuvgl_map_folder: pathlib.Path,
                     print_mode: str,
                     prebuilt_bow_vocabulary_folder: pathlib.Path = None):
    # Create global localization map.
    command = [
        'ros2',
        'run',
        'isaac_mapping_ros',
        'create_cuvgl_map.py',
        f'--map_folder={cuvgl_map_folder}',
        '--no-extract_feature',
        f'--print_mode={print_mode}',
    ]
    if prebuilt_bow_vocabulary_folder:
        command.append(f'--prebuilt_bow_vocabulary_folder={prebuilt_bow_vocabulary_folder}')
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
