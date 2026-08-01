# Columbus-Maximus
Project Description

GPS fails indoors yet robots in warehouses and factories navigate with remarkable precision. Columbus Maximus solves this by fusing three sensing technologies: UWB anchors for absolute position, LiDAR-based SLAM for real-time mapping, and wheel odometry for motion tracking. Since no single sensor is fully reliable, an Extended Kalman Filter (EKF) continuously blends all three, correcting drift and noise to produce a stable, accurate pose estimate. Built on ROS2, the system visualizes the robot’s live position and generates a map in RViz, the same workflow used in professional autonomous navigation systems.

Beyond building a working robot, the project compares SLAM-only, UWB-only, and full EKF fusion approaches giving you real experimental insight into sensor trade-offs and robustness. Columbus Maximus gives you hands-on experience with sensor fusion, probabilistic estimation, embedded hardware, and autonomous navigation, the core skills behind self-driving robots and industrial AGVs.
