# Columbus Maximus — Simulation

![ROS](https://img.shields.io/badge/ros-%230A0FF9.svg?style=for-the-badge&logo=ros&logoColor=white)
![Gazebo](https://img.shields.io/badge/gazebo-%23F58113.svg?style=for-the-badge&logo=gazebo&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![XML](https://img.shields.io/badge/xml-%23005FAD.svg?style=for-the-badge&logo=xml&logoColor=white)

## Project Description

Columbus Maximus is a differential-drive mobile robot simulated in Gazebo and visualized in RViz, built as a ROS 2 package (`columbusmaximus`). It carries a 360° 2D LIDAR for perception and is set up to be driven manually or mapped autonomously using `slam_toolbox`.

The robot's full description — chassis, wheels, and sensor mounts — is defined through xacro and brought to life in Gazebo via the differential-drive and laser-scan plugins, with its state continuously published for RViz and downstream ROS 2 nodes.

## Core Idea

The robot's URDF (`description/robot.urdf.xacro`) composes three parts: the chassis and wheel geometry (`robot_core.xacro`), the Gazebo differential-drive control plugin (`gazebo_control.xacro`), and the LIDAR sensor (`lidar.xacro`). On launch, `robot_state_publisher` publishes this description as `/robot_description`, and the robot is spawned into a Gazebo world as `my_bot`.

Once spawned, the robot can be driven with keyboard teleop over `/cmd_vel`, with the diff-drive plugin publishing odometry and TF back out. Its LIDAR streams live scan data on `/scan`, which feeds directly into `slam_toolbox`'s online async mapper — letting the robot build an occupancy-grid map of either provided Gazebo world (`obstacles.world` or `slam_world.world`) as it moves. A previously generated map (`my_map_save.pgm` / `.yaml`) is included as a reference example of this pipeline's output.

## [simulation](.)
This folder — the full `columbusmaximus` ROS 2 package: robot description (`description/`), launch files (`launch/`), Gazebo worlds (`worlds/`), meshes (`meshes/`), RViz configs and SLAM params (`rviz/`), and the Gazebo model definition (`model.sdf` / `model.config`).

---

## Setup Instructions

Create a ROS 2 workspace and package:

```bash
mkdir -p ~/columbus_ws/src
cd ~/columbus_ws/src
ros2 pkg create --build-type ament_python columbusmaximus
```

> The package name must stay exactly `columbusmaximus` — it's hardcoded into `package.xml`, `setup.py`, and both launch files.

Copy the contents of this `simulation/` folder into the generated package:

```bash
cd path/to/simulation

rm -rf ~/columbus_ws/src/columbusmaximus/columbusmaximus
rm -rf ~/columbus_ws/src/columbusmaximus/resource
rm -rf ~/columbus_ws/src/columbusmaximus/test

cp -r description launch rviz worlds meshes resource ~/columbus_ws/src/columbusmaximus/
cp package.xml setup.py setup.cfg model.config model.sdf ~/columbus_ws/src/columbusmaximus/

mkdir -p ~/columbus_ws/src/columbusmaximus/columbusmaximus
touch ~/columbus_ws/src/columbusmaximus/columbusmaximus/__init__.py
```

Install dependencies and build:

```bash
cd ~/columbus_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select columbusmaximus
```

Source the workspace:

```bash
source ~/columbus_ws/install/setup.bash
echo "source ~/columbus_ws/install/setup.bash" >> ~/.bashrc
```

Launch the simulation (robot description + Gazebo + spawn):

```bash
ros2 launch columbusmaximus launch_sim.launch.py
```

In a new terminal, visualize in RViz:

```bash
rviz2 -d ~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/urdf_config.rviz
```

Drive the robot with keyboard teleop:

```bash
sudo apt install ros-humble-teleop-twist-keyboard   # if not already installed
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Map the environment with `slam_toolbox`:

```bash
sudo apt install ros-humble-slam-toolbox   # if not already installed
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/mapper_params_online_async.yaml \
  use_sim_time:=true
```

Save the resulting map:

```bash
sudo apt install ros-humble-nav2-map-server   # if not already installed
ros2 run nav2_map_server map_saver_cli -f ~/columbus_ws/my_map
```

---

## Demos

### LIDAR sensor

<p align="center">
  <a href="media/lidar_sensor.mp4">
    <img src="media/lidar_sensor_thumb.jpg" width="500" alt="LIDAR sensor demo — click to watch" />
  </a>
  <br />
  <sub>Click the thumbnail to play <a href="media/lidar_sensor.mp4">media/lidar_sensor.mp4</a></sub>
</p>

Shows the 360° LIDAR streaming live scan data. To reproduce:

```bash
ros2 launch columbusmaximus launch_sim.launch.py
```

In a second terminal, visualize the scan in RViz:

```bash
rviz2 -d ~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/lidar_scan.rviz
```

You can also inspect the raw data directly:

```bash
ros2 topic echo /scan
```

### SLAM (mapping)

<p align="center">
  <a href="media/slam_mapping.mp4">
    <img src="media/slam_mapping_thumb.jpg" width="500" alt="SLAM mapping demo — click to watch" />
  </a>
  <br />
  <sub>Click the thumbnail to play <a href="media/slam_mapping.mp4">media/slam_mapping.mp4</a></sub>
</p>

Shows the robot building an occupancy-grid map of the world while being driven around. To reproduce:

```bash
# Terminal 1 — simulation
ros2 launch columbusmaximus launch_sim.launch.py

# Terminal 2 — SLAM
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/mapper_params_online_async.yaml \
  use_sim_time:=true

# Terminal 3 — RViz, showing the live map
rviz2 -d ~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/slam.rviz

# Terminal 4 — drive the robot to build the map
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Once the map looks complete, save it:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/columbus_ws/my_map
```

This is the same process that produced the `my_map_save.pgm` / `my_map_save.yaml` files included in this package.

### Nav2 implementation

<p align="center">
  <a href="media/nav2_implementation.mp4">
    <img src="media/nav2_implementation_thumb.jpg" width="500" alt="Nav2 implementation demo — click to watch" />
  </a>
  <br />
  <sub>Click the thumbnail to play <a href="media/nav2_implementation.mp4">media/nav2_implementation.mp4</a></sub>
</p>

Shows the robot autonomously navigating a saved map using the Nav2 stack (global/local planning + obstacle avoidance to a goal pose). To reproduce, using the map generated above:

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup -y   # if not already installed

# Terminal 1 — simulation
ros2 launch columbusmaximus launch_sim.launch.py

# Terminal 2 — Nav2, localized against the saved map
ros2 launch nav2_bringup bringup_launch.py \
  use_sim_time:=true \
  map:=~/columbus_ws/my_map.yaml

# Terminal 3 — RViz, to set the initial pose estimate and send "Nav2 Goal" pose
rviz2 -d ~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/urdf_config.rviz
```

In RViz, use **2D Pose Estimate** to localize the robot on the map, then **Nav2 Goal** to send it a destination — the planner and controller will drive it there while avoiding obstacles.

> Note: this package doesn't currently include a committed `nav2_params.yaml`, so the command above uses Nav2's default params. If you have a tuned params file for this robot, add it under a `config/` folder and pass it with `params_file:=path/to/nav2_params.yaml` for closer-to-demo behavior.

---

## Verify

```bash
ros2 node list
ros2 topic list
ros2 topic echo /scan --once
```

You should see `robot_state_publisher` and the Gazebo diff-drive node running, with `/cmd_vel`, `/odom`, `/scan`, and `/tf` actively publishing.

## Troubleshooting

- **Mesh not showing in Gazebo/RViz:** confirm `meshes/Assembly_1.stl` copied correctly and `robot_core.xacro` references it via a valid `package://columbusmaximus/meshes/...` path.
- **`ros2 launch` says package not found:** re-source (`source ~/columbus_ws/install/setup.bash`) and confirm `colcon build` succeeded for `columbusmaximus`.
- **Package doesn't register:** make sure `resource/columbusmaximus` exists — it's an empty ament marker file, don't delete it.
- **Gazebo won't spawn the robot:** confirm `rsp.launch.py` ran first and `/robot_description` is being published (`ros2 topic echo /robot_description --once`).

---

## Contact

**Maintainer:** Tejoshnanda Chilakalapudi — tejoshnanda.chilakalapudi@gmail.com
