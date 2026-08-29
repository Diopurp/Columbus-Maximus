import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/durva/ros2_ws/src/Columbus-Maximus/columbus_serial_bridge/install/columbus_serial_bridge'
