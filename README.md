# Isaac Perceptor

This repository contains the integrated Isaac Perceptor launch files.

## Setup and Documentation

Visit [Isaac Perceptor](https://nvidia-isaac-ros.github.io/reference_workflows/isaac_perceptor/index.html) to learn how to use this repository.

## Performance

| Sample Graph<br/><br/>                                                                                                                                                                                                                                                                    | Input Size<br/><br/>                | Nova Carter<br/><br/>                                                                                                                                                                                                                   |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [DNN Stereo Disparity Live Graph](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_benchmark/blob/main/benchmarks/isaac_ros_ess_nova_benchmark/scripts/isaac_ros_hawk_1f_2lt_ess_depth_graph.py)<br/><br/><br/>3 Hawk Cameras<br/><br/><br/>1x Full ESS and 2x Throttled Light ESS<br/><br/> | 1200p<br/><br/><br/><br/><br/><br/> | Full: [30.2 fps](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_benchmark/blob/main/results/isaac_ros_hawk_1f_2lt_ess_depth_graph-carter-v2.4-jp6.json)<br/><br/><br/>Light: 15.2 fps (avg)<br/><br/><br/><br/>                          |
| [Perceptor Graph](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_benchmark/blob/main/benchmarks/isaac_ros_perceptor_nova_benchmark/scripts/isaac_ros_perceptor_graph.py)<br/><br/><br/>3 Hawk Cameras<br/><br/><br/><br/>                                                                  | 1200p<br/><br/><br/><br/><br/><br/> | Nvblox ESDF: [9.45 fps](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_benchmark/blob/main/results/isaac_ros_perceptor_graph-carter-v2.4-jp6.json)<br/><br/><br/>Nvblox Mesh: 2.63 fps<br/><br/><br/>Visual Odometry: 30.0 fps<br/><br/> |
